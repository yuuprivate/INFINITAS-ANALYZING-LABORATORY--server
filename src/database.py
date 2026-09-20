from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# DB接続情報
DATABASE_URL = "postgresql://iidx_user:iidx_secure_password@localhost:5432/iidx_recommend_db"

# エンジンの作成
engine = create_engine(DATABASE_URL, echo=True)

# セッションクラスの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# モデルのベースクラス
Base = declarative_base()

# APIでリクエストごとにDBセッションを取得・開放する依存関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()