import sys
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models import score_models, chart_models, song_models, user_models
from src.logger.logger import get_logger

logger = get_logger(category="admin", name="calibrate_score")

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def sigmoid_model(b, theta):
    z = np.clip(theta - b, -30, 30)
    return 1.0 / (1.0 + np.exp(-z))

def sigmoid_model_user(x, theta, b):
    z = np.clip(theta - x, -30, 30)
    return 1.0 / (1.0 + np.exp(-z))

def calibrate_scores():
    logger.info("=== スコア力（EXスコア IRT）のキャリブレーションを開始します ===")
    db: Session = SessionLocal()

    try:
        charts = db.query(chart_models.MChart).all()
        logger.info(f"取得した譜面数: {len(charts)}")
        
        for chart in charts:
            existing = db.query(chart_models.DChartScoreIrt).filter(
                chart_models.DChartScoreIrt.chart_id == chart.chart_id,
                chart_models.DChartScoreIrt.play_style == chart.play_style
            ).first()
            if not existing:
                db.add(chart_models.DChartScoreIrt(
                    chart_id=chart.chart_id,
                    play_style=chart.play_style,
                    b_score=float(chart.level)
                ))
        db.commit()

        users = db.query(user_models.MUser).all()
        logger.info(f"取得したユーザー数: {len(users)}")
        for user in users:
            if not db.query(user_models.DUserIrt).filter(user_models.DUserIrt.user_id == user.user_id).first():
                db.add(user_models.DUserIrt(user_id=user.user_id))
        db.commit()

        # ==========================================================
        # 1. 譜面ごとの難易度 (b_score) のキャリブレーション
        # ==========================================================
        logger.info("--- 譜面難易度 (b_score) の最適化を開始します ---")
        updated_chart_count = 0
        debug_chart_loops = 0

        for chart in charts:
            for play_style in [0, 1]:
                scores = (
                    db.query(score_models.Score, user_models.DUserIrt)
                    .join(user_models.DUserIrt, score_models.Score.user_id == user_models.DUserIrt.user_id)
                    .filter(
                        score_models.Score.chart_id == chart.chart_id,
                        score_models.Score.play_style == play_style,
                        score_models.Score.ex_score != None
                    )
                    .all()
                )

                if debug_chart_loops < 3:
                    logger.info(f"[DEBUG 譜面] chart_id={chart.chart_id}, style={play_style}, ヒットスコア数={len(scores)}, notes={chart.notes}")
                    debug_chart_loops += 1

                if len(scores) < 5 or chart.notes is None or chart.notes <= 0:
                    continue

                theta_list = []
                rate_list = []
                max_ex = chart.notes * 2

                for score, user_irt in scores:
                    theta = getattr(user_irt, "ability_score_sp" if play_style == 0 else "ability_score_dp")
                    if theta is None:
                        continue
                    rate = score.ex_score / max_ex
                    theta_list.append(theta)
                    rate_list.append(max(0.01, min(0.99, rate)))

                if len(theta_list) < 5:
                    continue

                try:
                    popt, _ = curve_fit(
                        lambda b, theta: sigmoid_model(b, theta),
                        np.array(theta_list),
                        np.array(rate_list),
                        p0=[float(chart.level)],
                        bounds=([0.0], [25.0])
                    )
                    estimated_b = float(popt[0])

                    chart_irt = db.query(chart_models.DChartScoreIrt).filter(
                        chart_models.DChartScoreIrt.chart_id == chart.chart_id,
                        chart_models.DChartScoreIrt.play_style == play_style
                    ).first()
                    
                    if chart_irt:
                        chart_irt.b_score = round(estimated_b, 4)
                        updated_chart_count += 1
                except Exception as e:
                    continue

        db.commit()
        logger.info(f"--- 譜面難易度 (b_score) の最適化が完了しました (更新譜面数: {updated_chart_count}) ---")

        # ==========================================================
        # 2. ユーザーごとのスコア力 のキャリブレーション
        # ==========================================================
        logger.info("--- ユーザー能力値 (ability_score) の最適化を開始します ---")
        updated_user_count = 0

        for user in users:
            for play_style, style_attr in [(0, "ability_score_sp"), (1, "ability_score_dp")]:
                scores = (
                    db.query(score_models.Score, chart_models.MChart, chart_models.DChartScoreIrt)
                    .join(chart_models.MChart, (score_models.Score.chart_id == chart_models.MChart.chart_id) & (score_models.Score.play_style == chart_models.MChart.play_style))
                    .join(chart_models.DChartScoreIrt, (score_models.Score.chart_id == chart_models.DChartScoreIrt.chart_id) & (score_models.Score.play_style == chart_models.DChartScoreIrt.play_style))
                    .filter(
                        score_models.Score.user_id == user.user_id,
                        score_models.Score.play_style == play_style,
                        score_models.Score.ex_score != None,
                        chart_models.MChart.notes > 0
                    )
                    .all()
                )

                logger.info(f"[DEBUG ユーザー] user_id={user.user_id}, style={play_style}, ヒットスコア数={len(scores)}")

                if len(scores) < 5:
                    continue

                b_list = []
                rate_list = []

                for score, chart, chart_irt in scores:
                    max_ex = chart.notes * 2
                    rate = score.ex_score / max_ex
                    b_list.append(chart_irt.b_score)
                    rate_list.append(max(0.01, min(0.99, rate)))

                b_arr = np.array(b_list)
                rate_arr = np.array(rate_list)

                try:
                    popt, _ = curve_fit(
                        lambda x, theta: sigmoid_model_user(x, theta, b_arr),
                        b_arr,
                        rate_arr,
                        p0=[10.0],
                        bounds=([0.0], [25.0])
                    )
                    estimated_theta = float(popt[0])
                except Exception as e:
                    logger.warning(f"ユーザーID {user.user_id} ({play_style}) のスコア力推定に失敗しました: {e}")
                    continue

                user_irt = db.query(user_models.DUserIrt).filter(user_models.DUserIrt.user_id == user.user_id).first()
                if not user_irt:
                    user_irt = user_models.DUserIrt(user_id=user.user_id)
                    db.add(user_irt)

                setattr(user_irt, style_attr, round(estimated_theta, 4))
                updated_user_count += 1

        db.commit()
        logger.info(f"=== スコア力のキャリブレーションが正常に完了しました (更新ユーザーパラメータ数: {updated_user_count}) ===")

    except Exception as e:
        db.rollback()
        logger.error(f"スコアキャリブレーション中にエラーが発生しました: {e}", exc_info=True)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    calibrate_scores()