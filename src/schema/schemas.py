import sys
from pathlib import Path

from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

# 絶対パスからの指定
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- ユーザースキーマ ---
class UserCreate(BaseModel):
    dj_name: str
    iidx_id: Optional[str] = None
    irt_ability: float = 0.0

class UserResponse(UserCreate):
    user_id: int

    class Config:
        from_attributes = True

# --- 楽曲・譜面スキーマ ---
class SongBase(BaseModel):
    chart_id: str
    title: str
    difficulty_type: str
    level: int = Field(..., ge=1, le=12)
    irt_discrimination: Optional[float] = 1.0
    irt_difficulties: Optional[Dict[str, float]] = None

class SongCreate(SongBase):
    pass

class SongResponse(SongBase):
    class Config:
        from_attributes = True

# --- スコアスキーマ ---
class ScoreCreate(BaseModel):
    user_id: int
    chart_id: str
    clear_state: int
    ex_score: Optional[int] = None

class ScoreResponse(ScoreCreate):
    score_id: int

    class Config:
        from_attributes = True