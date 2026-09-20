import sys
from pathlib import Path

import logging
from datetime import datetime

# 絶対パスからの指定
project_root = Path(__file__).resolve().parent.parent  # 階層の深さに応じて .parent を調整
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

BASE_LOG_DIR = Path("logs")

CATEGORIES = {
    "app": BASE_LOG_DIR / "app",
    "batch": BASE_LOG_DIR / "batch",
    "admin": BASE_LOG_DIR / "admin",
    "auth": BASE_LOG_DIR / "auth",
}

LOG_FORMAT = logging.Formatter(
    fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def _ensure_log_directories():
    """ログディレクトリが存在しない場合は作成する"""
    for path in CATEGORIES.values():
        path.mkdir(parents=True, exist_ok=True)

def get_logger(category: str = "app", name: str | None = None) -> logging.Logger:
    """
    カテゴリ別・日付名入りロガーを取得する関数
    
    :param category: "app" | "batch" | "admin" | "auth"
    :param name: 処理名（例: "calibrate"）
    :return: logging.Logger インスタンス
    """
    _ensure_log_directories()

    if category not in CATEGORIES:
        category = "app"

    logger_name = name or category
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # 重複ハンドラ登録を防止
    if logger.handlers:
        return logger

    # 1. コンソール出力ハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(LOG_FORMAT)
    logger.addHandler(console_handler)

    # 2. 日付入りファイル出力ハンドラ (例: logs/batch/calibrate_20260909.log)
    today_str = datetime.now().strftime("%Y%m%d")
    file_prefix = name if name else category
    log_file_path = CATEGORIES[category] / f"{file_prefix}_{today_str}.log"

    file_handler = logging.FileHandler(
        filename=log_file_path,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(LOG_FORMAT)
    logger.addHandler(file_handler)

    # app カテゴリ用のエラー隔離ログ
    if category == "app":
        error_file_path = CATEGORIES["app"] / f"error_{today_str}.log"
        error_handler = logging.FileHandler(
            filename=error_file_path,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(LOG_FORMAT)
        logger.addHandler(error_handler)

    return logger