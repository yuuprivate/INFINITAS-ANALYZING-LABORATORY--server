import sys
from pathlib import Path

from src.logger.logger import get_logger
from src.calibrate.scripts.calibrate_clear_irt import calibrate_clear  # 既存のクリア用キャリブレーション関数
from src.calibrate.scripts.calibrate_score_irt import calibrate_scores  # 先ほど作成したスコア用関数

logger = get_logger(category="admin", name="run_calibration")

# 絶対パスからの指定
project_root = Path(__file__).resolve().parent.parent  # 階層の深さに応じて .parent を調整
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def main():
    logger.info("=== 定期キャリブレーション処理を開始します ===")
    try:
        # 1. クリア力 (Clear IRT) のキャリブレーション
        logger.info("-> クリア力キャリブレーション実行中...")
        calibrate_clear()
        
        # 2. スコア力 (Score IRT) のキャリブレーション
        logger.info("-> スコア力キャリブレーション実行中...")
        calibrate_scores()
        
        logger.info("=== 全ての定期キャリブレーションが正常に完了しました ===")
    except Exception as e:
        logger.error(f"定期キャリブレーション中に致命的なエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()