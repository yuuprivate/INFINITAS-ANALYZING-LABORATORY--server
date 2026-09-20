import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from src.routers import users, songs, scores

app = FastAPI(title="beatmania IIDX IRT Recommend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 絶対パスの設定などの必要に応じた処理
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 各ルーターの登録
app.include_router(users.router)
app.include_router(songs.router)
app.include_router(scores.router)

@app.get("/")
def read_root():
    return {"message": "IIDX IRT Recommend API is running"}