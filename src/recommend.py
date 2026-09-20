import math
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from src.database import SessionLocal
from models import score_models
from logger.logger import get_logger

logger = get_logger(category="recommend", name="recommend_engine")

# プレイスタイルの定数定義
PLAY_STYLE_SP = 0
PLAY_STYLE_DP = 1


def sigmoid(z: float) -> float:
    """ロジスティックシグモイド関数 P(θ) = 1 / (1 + exp(-(θ - b)))"""
    if z < -30:
        return 0.0
    if z > 30:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


def get_user_theta(db: Session, user_id: int, play_style: int) -> Optional[float]:
    """
    d_user_irt テーブルから指定されたユーザーの実力値(θ)を取得
    play_style: 0 -> sp_theta, 1 -> dp_theta
    """
    irt_record = (
        db.query(score_models.DUserIrt)
        .filter(score_models.DUserIrt.user_id == user_id)
        .first()
    )
    if irt_record is None:
        return None

    if play_style == PLAY_STYLE_SP:
        return float(irt_record.ability_clear_sp) if irt_record.ability_clear_sp is not None else None
    elif play_style == PLAY_STYLE_DP:
        return float(irt_record.ability_clear_dp) if irt_record.ability_clear_dp is not None else None
    else:
        logger.error(f"無効な play_style が指定されました: {play_style}")
        return None


def get_played_chart_ids(db: Session, user_id: int, play_style: int) -> set:
    """ユーザーが既にクリア済み/プレイ済みの chart_id の集合を取得"""
    scores = (
        db.query(score_models.Score.chart_id)
        .filter(
            score_models.Score.user_id == user_id,
            score_models.Score.play_style == play_style,
            score_models.Score.clear_state > 1  # 1: FAILED を除外（クリア済みのみ対象）
        )
        .all()
    )
    return {s.chart_id for s in scores}


def recommend_charts(
    user_id: int,
    play_style: int = PLAY_STYLE_SP,
    target_clear_rate: float = 0.50,
    rate_margin: float = 0.20,
    top_n: int = 10,
    exclude_played: bool = True
) -> List[Dict[str, Any]]:
    """
    ユーザーの実力値(θ)に基づいておすすめ譜面を推薦する

    :param user_id: 対象ユーザーID
    :param play_style: 0: SP, 1: DP
    :param target_clear_rate: 目標クリア確率 (デフォルト: 0.50 = 50%勝率の挑戦適性曲)
    :param rate_margin: クリア確率の許容誤差幅 (±20% -> 30%〜70%)
    :param top_n: 取得する最大件数
    :param exclude_played: 既プレイ・既クリア曲を除外するかどうか
    :return: 推薦譜面リスト (辞書型の配列)
    """
    db: Session = SessionLocal()
    try:
        # 1. ユーザーの θ (sp_theta または dp_theta) を取得
        theta = get_user_theta(db, user_id, play_style)
        style_label = "SP" if play_style == PLAY_STYLE_SP else "DP"

        if theta is None:
            logger.warning(f"ユーザー ID={user_id} ({style_label}) の IRT データ(θ)が見つかりません。")
            return []

        # 2. プレイ済み譜面の ID セットを取得
        played_chart_ids = set()
        if exclude_played:
            played_chart_ids = get_played_chart_ids(db, user_id, play_style)

        # 3. m_charts と m_songs を INNER JOIN して、指定プレイスタイルの全譜面とタイトルを取得
        results = (
            db.query(score_models.MChart, score_models.MSong.title)
            .join(score_models.MSong, score_models.MChart.song_id == score_models.MSong.song_id)
            .filter(score_models.MChart.play_style == play_style)
            .all()
        )

        recommendations = []
        min_rate = max(0.01, target_clear_rate - rate_margin)
        max_rate = min(0.99, target_clear_rate + rate_margin)

        for chart, title in results:
            if exclude_played and chart.chart_id in played_chart_ids:
                continue

            # 難易度パラメータ b
            b = float(chart.level)

            # クリア推定確率 P(θ) = 1 / (1 + exp(-(θ - b)))
            p_clear = sigmoid(theta - b)

            # ターゲットクリア確率の範囲内に入っているかチェック
            if min_rate <= p_clear <= max_rate:
                diff = abs(p_clear - target_clear_rate)

                recommendations.append({
                    "chart_id": chart.chart_id,
                    "title": title,
                    "difficulty_type": chart.difficulty_type,
                    "level": chart.level,
                    "estimated_clear_rate": round(p_clear * 100, 1),
                    "diff_from_target": diff
                })

        # 4. 目標クリア確率に最も近い順 (diff昇順) でソートして top_n 件取得
        recommendations.sort(key=lambda x: x["diff_from_target"])
        result = recommendations[:top_n]

        # ソート用の一時キーを削除
        for res in result:
            del res["diff_from_target"]

        logger.info(f"ユーザー ID={user_id} [{style_label}] (θ={theta:.2f}) に対する推薦完了: {len(result)} 件")
        return result

    except Exception as e:
        logger.error(f"推薦処理中にエラーが発生しました: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_user_id = 1
    
    # SP の推薦テスト
    print(f"=== ユーザー {test_user_id} (SP) への推薦結果テスト ===")
    recs_sp = recommend_charts(
        user_id=test_user_id,
        play_style=PLAY_STYLE_SP,
        target_clear_rate=0.50,
        top_n=5,
        exclude_played=True
    )
    for rank, item in enumerate(recs_sp, 1):
        print(f"[{rank}位] {item['title']} ({item['difficulty_type']}) - Level {item['level']} | 推定クリア率: {item['estimated_clear_rate']}%")