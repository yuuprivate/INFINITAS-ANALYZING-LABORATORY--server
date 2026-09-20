###################################
## 投入先テーブル:m_users, scores ##
###################################

import sys
from pathlib import Path
import random
import math

from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.logger.logger import get_logger

# 関連するすべてのモデルを明示的にインポートしてレジストリに登録させる
from src.models import user_models, chart_models, score_models

logger = get_logger(category="admin", name="generate_dummy")

# 絶対パスからの指定
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def generate_dummy_data(num_users: int = 20):
    logger.info("=== テスト用ダミーユーザーおよびスコアデータの作成を開始します ===")
    db: Session = SessionLocal()

    try:
        # 1. 既存のダミーデータを削除（DUserIrt は chart_models から取得）
        db.query(score_models.Score).delete()
        db.query(user_models.DUserIrt).delete()
        db.query(user_models.MUser).delete()
        db.commit()

        # 2. ダミーユーザーの作成
        users = []
        for i in range(1, num_users + 1):
            user = user_models.MUser(
                user_id=i,
                dj_name=f"TEST{i:02d}",
                iidx_id_first=1234,
                iidx_id_second=5678,
                iidx_id_third=9000 + i,
                password_hash="dummy_hash",
                delete_flag=0
            )
            db.add(user)
            users.append(user)
        db.commit()

        charts_sp = db.query(chart_models.MChart).filter(chart_models.MChart.play_style == 0).all()
        charts_dp = db.query(chart_models.MChart).filter(chart_models.MChart.play_style == 1).all()

        total_scores = 0

        for user in users:
            true_theta_sp = random.gauss(10.0, 2.5)
            true_theta_dp = random.gauss(10.0, 2.5)

            for play_style, charts, true_theta in [(0, charts_sp, true_theta_sp), (1, charts_dp, true_theta_dp)]:
                if not charts:
                    continue
                played_charts = random.sample(charts, k=min(len(charts), random.randint(20, 50)))

                for chart in played_charts:
                    if not chart.notes or chart.notes <= 0:
                        continue

                    b_lvl = float(chart.level)
                    z = true_theta - b_lvl
                    p_clear = 1.0 / (1.0 + math.exp(-z)) if -30 <= z <= 30 else (1.0 if z > 30 else 0.0)

                    rand_val = random.random()
                    if rand_val > p_clear:
                        clear_state = 1  # FAILED
                        base_rate = random.uniform(0.3, 0.6)
                    else:
                        lamp_rand = random.random()
                        if lamp_rand < 0.1:
                            clear_state = 6  # FC
                            base_rate = random.uniform(0.92, 1.0)
                        elif lamp_rand < 0.3:
                            clear_state = 5  # EX-HARD
                            base_rate = random.uniform(0.82, 0.95)
                        elif lamp_rand < 0.6:
                            clear_state = 4  # HARD
                            base_rate = random.uniform(0.70, 0.88)
                        elif lamp_rand < 0.85:
                            clear_state = 3  # NORMAL
                            base_rate = random.uniform(0.60, 0.78)
                        else:
                            clear_state = 2  # EASY
                            base_rate = random.uniform(0.50, 0.72)

                    expected_rate = 1.0 / (1.0 + math.exp(-z)) if -30 <= z <= 30 else (1.0 if z > 30 else 0.0)
                    target_rate = (expected_rate * 0.5) + (base_rate * 0.5)
                    target_rate = random.gauss(target_rate, 0.05)
                    target_rate = max(0.1, min(0.99, target_rate))

                    max_ex = chart.notes * 2
                    ex_score = int(max_ex * target_rate)
                    ex_score = max(1, min(max_ex, ex_score))

                    score_obj = score_models.Score(
                        score_id=total_scores,
                        user_id=user.user_id,
                        chart_id=chart.chart_id,
                        play_style=play_style,
                        clear_state=clear_state,
                        ex_score=ex_score
                    )
                    db.add(score_obj)
                    total_scores += 1

        db.commit()
        logger.info(f"ダミーデータ作成完了: ユーザー {num_users} 名 | スコア {total_scores} 件")

    except Exception as e:
        db.rollback()
        logger.error(f"ダミーデータ作成中にエラーが発生しました: {e}", exc_info=True)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    generate_dummy_data()