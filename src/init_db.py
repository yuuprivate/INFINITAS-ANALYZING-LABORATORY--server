from sqlalchemy import text
from src.database import engine, Base
from logger.logger import get_logger

logger = get_logger(category="admin", name="init_db")

def init_database(drop_existing: bool = True):
    """
    データベースの初期化（全テーブルの再作成）を行うスクリプト。
    SQLite / PostgreSQL 対応
    """
    logger.info("=== データベース初期化処理を開始します ===")
    
    with engine.connect() as conn:
        db_type = engine.dialect.name
        logger.info(f"対象データベース: {db_type}")

        if drop_existing:
            logger.info("既存のテーブルおよび制約を解除・削除しています...")
            if db_type == "postgresql":
                # PostgreSQL環境でCASCADEドロップを実行してスキーマを初期化
                conn.execute(text("DROP SCHEMA public CASCADE;"))
                conn.execute(text("CREATE SCHEMA public;"))
                conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
                conn.commit()
                logger.info("PostgreSQL public スキーマを完全にリセットしました。")
            else:
                # SQLite / MySQL 等
                conn.execute(text("PRAGMA foreign_keys = OFF;") if db_type == "sqlite" else text("SET FOREIGN_KEY_CHECKS = 0;"))
                Base.metadata.drop_all(bind=conn)
                conn.execute(text("PRAGMA foreign_keys = ON;") if db_type == "sqlite" else text("SET FOREIGN_KEY_CHECKS = 1;"))
                logger.info("既存テーブルの削除が完了しました。")

    logger.info("新しいスキーマでテーブル群を作成しています...")
    Base.metadata.create_all(bind=engine)
    logger.info("=== データベースの初期化・再構築が正常に完了しました ===")

if __name__ == "__main__":
    init_database(drop_existing=True)