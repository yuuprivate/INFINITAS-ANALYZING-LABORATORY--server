import sys
from pathlib import Path

import time
import torch
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models import user_models, chart_models, score_models
from src.logger.logger import get_logger

logger = get_logger(category="batch", name="calibrate_clear")

# 絶対パスからの指定
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# ==========================================
# 1. 実行環境・ハイパーパラメータ設定
# ==========================================
USE_GPU = True
DEVICE = torch.device("cuda" if USE_GPU and torch.cuda.is_available() else "cpu")

MIN_PLAYED_CHARTS = 10  # キャリブレーション対象とする最小プレイ譜面数
TARGET_MEAN = 10.0      # Z-Score標準化の目標平均
TARGET_STD = 2.0        # Z-Score標準化の目標標準偏差

# 評価対象: 3:EASY, 4:NORMAL, 5:HARD, 6:EX-HARD, 7:FULL COMBO
LAMP_REQUIREMENTS = [3, 4, 5, 6, 7]  


def calibrate_clear(max_outer_iter: int = 15, max_inner_iter: int = 5):
    start_time = time.time()
    logger.info(f"=== ベクトル化キャリブレーション処理を開始します (Device: {DEVICE}) ===")

    db: Session = SessionLocal()

    try:
        for target_style in [0, 1]:  # 0: SP, 1: DP
            style_name = "SP" if target_style == 0 else "DP"
            logger.info(f"--- [{style_name}] データロード・前処理中 ---")

            # ----------------------------------------------------
            # 1. アクティブユーザーのフィルタリング (10譜面以上プレイ)
            # ----------------------------------------------------
            raw_users = db.query(user_models.MUser).filter(user_models.MUser.delete_flag == 0).all()
            user_play_counts = {}
            for u in raw_users:
                played_count = db.query(score_models.Score).filter(
                    score_models.Score.user_id == u.user_id,
                    score_models.Score.play_style == target_style,
                    score_models.Score.clear_state >= 1  # FAILED(1)以上をカウント (NO_PLAYは除外)
                ).count()
                if played_count >= MIN_PLAYED_CHARTS:
                    user_play_counts[u.user_id] = played_count

            active_user_ids = list(user_play_counts.keys())
            charts = db.query(chart_models.MChart).filter(chart_models.MChart.play_style == target_style).all()
            scores = db.query(score_models.Score).filter(
                score_models.Score.play_style == target_style,
                score_models.Score.user_id.in_(active_user_ids)
            ).all() if active_user_ids else []

            if not active_user_ids or not charts or not scores:
                logger.warning(f"【SKIPPED】[{style_name}] 条件を満たすアクティブデータが不足しているためスキップします。")
                continue

            N = len(active_user_ids)
            M = len(charts)
            K = len(LAMP_REQUIREMENTS)

            logger.info(f"[{style_name}] 計算対象: アクティブユーザー {N} 名 | 譜面 {M} 件 | プレイログ {len(scores)} 件")

            # IDとマトリクスインデックスの相互マッピング
            user_id_to_idx = {uid: i for i, uid in enumerate(active_user_ids)}
            chart_id_to_idx = {c.chart_id: j for j, c in enumerate(charts)}

            # ----------------------------------------------------
            # 2. テンソル行列の事前構築 (N, M, K)
            # ----------------------------------------------------
            X = torch.zeros((N, M, K), dtype=torch.float32, device=DEVICE)
            Mask = torch.zeros((N, M, 1), dtype=torch.float32, device=DEVICE)

            for s in scores:
                if s.user_id in user_id_to_idx and s.chart_id in chart_id_to_idx:
                    if s.clear_state == 0:
                        continue  # NO_PLAY は明示的に無視
                    
                    i = user_id_to_idx[s.user_id]
                    j = chart_id_to_idx[s.chart_id]
                    
                    Mask[i, j, 0] = 1.0
                    for k, req_state in enumerate(LAMP_REQUIREMENTS):
                        X[i, j, k] = 1.0 if s.clear_state >= req_state else 0.0

            # ----------------------------------------------------
            # 3. パラメータテンソルの初期化
            # ----------------------------------------------------
            theta = torch.full((N, 1, 1), TARGET_MEAN, dtype=torch.float32, device=DEVICE)
            a = torch.ones((1, M, 1), dtype=torch.float32, device=DEVICE)
            B = torch.zeros((1, M, K), dtype=torch.float32, device=DEVICE)

            # 初期能力値と難易度パラメータをDBからロード
            for i, uid in enumerate(active_user_ids):
                u_obj = db.query(user_models.MUser).get(uid)
                if u_obj and u_obj.irt_param:
                    val = u_obj.irt_param.ability_clear_sp if target_style == 0 else u_obj.irt_param.ability_clear_dp
                    if val is not None:
                        theta[i, 0, 0] = val

            for j, c in enumerate(charts):
                if c.clear_irt:
                    a[0, j, 0] = c.clear_irt.irt_discrimination or 1.0
                    B[0, j, 0] = c.clear_irt.b_easy
                    B[0, j, 1] = c.clear_irt.b_normal
                    B[0, j, 2] = c.clear_irt.b_hard
                    B[0, j, 3] = c.clear_irt.b_ex_hard
                    B[0, j, 4] = c.clear_irt.b_fc

            # ----------------------------------------------------
            # 4. ベクトル化 JMLE 計算ループ
            # ----------------------------------------------------
            for outer in range(max_outer_iter):
                # --- Step A: ユーザー能力値 theta の更新 ---
                for _ in range(max_inner_iter):
                    Z = a * (theta - B)  # Broadcast Shape: (N, M, K)
                    P = torch.sigmoid(torch.clamp(Z, -30.0, 30.0))

                    d1_theta = torch.sum(Mask * a * (X - P), dim=(1, 2), keepdim=True)  # (N, 1, 1)
                    d2_theta = -torch.sum(Mask * (a ** 2) * P * (1.0 - P), dim=(1, 2), keepdim=True)

                    delta_theta = d1_theta / (d2_theta - 1e-6)
                    delta_theta = torch.clamp(delta_theta, -0.5, 0.5)
                    theta -= delta_theta

                    if torch.max(torch.abs(delta_theta)).item() < 1e-3:
                        break

                # --- Step B: 譜面難易度 B の更新 ---
                for _ in range(max_inner_iter):
                    Z = a * (theta - B)
                    P = torch.sigmoid(torch.clamp(Z, -30.0, 30.0))

                    d1_B = torch.sum(Mask * (-a) * (X - P), dim=0, keepdim=True)  # (1, M, K)
                    d2_B = -torch.sum(Mask * (a ** 2) * P * (1.0 - P), dim=0, keepdim=True)

                    delta_B = d1_B / (d2_B - 1e-6)
                    delta_B = torch.clamp(delta_B, -0.5, 0.5)
                    B -= delta_B

                    if torch.max(torch.abs(delta_B)).item() < 1e-3:
                        break

                # 単調増加性の保障 (EASY <= NORMAL <= HARD <= EX-HARD <= FC)
                for k in range(1, K):
                    B[:, :, k] = torch.maximum(B[:, :, k], B[:, :, k - 1] + 0.05)

                # --- Step C: Z-Score 標準化 (Mean = 10.0, StdDev = 2.0) ---
                current_mean = torch.mean(theta)
                current_std = torch.std(theta, unbiased=False)

                if current_std > 1e-6:
                    scale = TARGET_STD / current_std
                    theta = (theta - current_mean) * scale + TARGET_MEAN
                    B = (B - current_mean) * scale + TARGET_MEAN

            # ----------------------------------------------------
            # 5. DBへ一括保存
            # ----------------------------------------------------
            theta_cpu = theta.squeeze().cpu().tolist()
            if isinstance(theta_cpu, float):
                theta_cpu = [theta_cpu]

            for i, uid in enumerate(active_user_ids):
                u_obj = db.query(user_models.MUser).get(uid)
                if u_obj:
                    if not u_obj.irt_param:
                        u_obj.irt_param = user_models.DUserIrt(user_id=uid)
                    
                    val = round(float(theta_cpu[i]), 4)
                    if target_style == 0:
                        u_obj.irt_param.ability_clear_sp = val
                    else:
                        u_obj.irt_param.ability_clear_dp = val

            B_cpu = B.squeeze(0).cpu().tolist()
            a_cpu = a.squeeze(0).squeeze(-1).cpu().tolist()

            for j, c in enumerate(charts):
                if not c.clear_irt:
                    c.clear_irt = chart_models.DChartIrt(chart_id=c.chart_id, play_style=target_style)
                    db.add(c.clear_irt)

                c.clear_irt.irt_discrimination = round(float(a_cpu[j]), 4)
                c.clear_irt.b_easy = round(float(B_cpu[j][0]), 4)
                c.clear_irt.b_normal = round(float(B_cpu[j][1]), 4)
                c.clear_irt.b_hard = round(float(B_cpu[j][2]), 4)
                c.clear_irt.b_ex_hard = round(float(B_cpu[j][3]), 4)
                c.clear_irt.b_fc = round(float(B_cpu[j][4]), 4)

            logger.info(f"[{style_name}] キャリブレーション成功 (ユーザー: {N}名, 譜面: {M}件)")

        db.commit()
        elapsed = round(time.time() - start_time, 2)
        logger.info(f"=== 全キャリブレーション処理完了 (処理時間: {elapsed}秒) ===")

    except Exception as e:
        db.rollback()
        logger.error(f"キャリブレーション中にエラーが発生しました: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    calibrate_clear()