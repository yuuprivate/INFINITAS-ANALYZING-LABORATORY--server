import math
from sqlalchemy.orm import Session
from .models import score_models

LAMP_MAPPING = {
    2: "easy",
    3: "normal",
    4: "hard",
    5: "ex_hard",
    6: "fc"
}

def calculate_ability(db: Session, user_id: int, max_iter: int = 20, tol: float = 1e-4) -> float:
    scores = db.query(score_models.Score, score_models.Song).join(
        score_models.Song, score_models.Score.chart_id == score_models.Song.chart_id
    ).filter(score_models.Score.user_id == user_id).all()

    if not scores:
        return 0.0

    user = db.query(score_models.User).filter(score_models.User.user_id == user_id).first()
    theta = user.irt_ability if user and user.irt_ability is not None else 0.0

    for _ in range(max_iter):
        first_derivative = 0.0
        second_derivative = 0.0

        for score, song in scores:
            a = song.irt_discrimination
            diffs = song.irt_difficulties or {}

            # 各ランプの困難度（b）に対して、仮想的な二値判定を行う
            for required_state, lamp_key in LAMP_MAPPING.items():
                if lamp_key not in diffs:
                    continue  # そのランプの困難度データがない場合はスキップ
                
                b = diffs[lamp_key]
                # ユーザーのクリア状態が、要求ステータス以上なら「1(達成)」、未満なら「0(未達成)」
                x = 1 if score.clear_state >= required_state else 0

                z = a * (theta - b)
                if z > 30:
                    p = 1.0
                elif z < -30:
                    p = 0.0
                else:
                    p = 1.0 / (1.0 + math.exp(-z))

                first_derivative += a * (x - p)
                second_derivative -= (a ** 2) * p * (1.0 - p)

        if abs(second_derivative) < 1e-6:
            break

        delta = first_derivative / second_derivative
        theta -= delta

        if abs(delta) < tol:
            break

    return max(min(theta, 5.0), -5.0)

def get_recommendations(db: Session, user_id: int, target_lamp: str = "hard", limit: int = 5):
    """
    指定した目標ランプ(例: easy, normal, hard, ex_hard, fc)の
    達成確率が約50%になる（困難度bがthetaに最も近い）未達成譜面を推薦する
    """
    user = db.query(score_models.User).filter(score_models.User.user_id == user_id).first()
    if not user:
        return []

    theta = user.irt_ability if user.irt_ability is not None else 0.0

    # 各ランプに必要な clear_state の値
    LAMP_STATE_NUM = {
        "easy": 2,
        "normal": 3,
        "hard": 4,
        "ex_hard": 5,
        "fc": 6
    }
    required_state = LAMP_STATE_NUM.get(target_lamp, 4)  # デフォルトは hard

    # ユーザーの全スコア（chart_id -> clear_state）をマップ化
    user_scores = {
        s.chart_id: s.clear_state 
        for s in db.query(score_models.Score).filter(score_models.Score.user_id == user_id).all()
    }

    songs = db.query(score_models.Song).all()
    recommendations = []

    for song in songs:
        current_state = user_scores.get(song.chart_id, 0)

        # すでに目標ランプ以上を達成している譜面はおすすめから除外
        if current_state >= required_state:
            continue

        diffs = song.irt_difficulties or {}
        if target_lamp not in diffs:
            continue

        a = song.irt_discrimination
        b = diffs[target_lamp]

        # 2PLMによる目標ランプ達成確率
        z = a * (theta - b)
        if z > 30:
            p = 1.0
        elif z < -30:
            p = 0.0
        else:
            p = 1.0 / (1.0 + math.exp(-z))

        diff = abs(b - theta)

        recommendations.append({
            "chart_id": song.chart_id,
            "title": song.title,
            "difficulty_type": song.difficulty_type,
            "level": song.level,
            "target_lamp": target_lamp,
            "target_irt_difficulty": b,
            "clear_probability": round(p, 3),
            "diff": diff
        })

    # 困難度 b と実力 theta の差が小さい順にソート
    recommendations.sort(key=lambda x: x["diff"])

    for r in recommendations:
        del r["diff"]

    return recommendations[:limit]