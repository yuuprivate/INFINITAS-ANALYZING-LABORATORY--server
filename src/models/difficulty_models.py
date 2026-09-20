import sys
from pathlib import Path

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, SmallInteger, BigInteger,
    ForeignKeyConstraint, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from src.database import Base

# 絶対パスからの指定
project_root = Path(__file__).resolve().parent.parent  # 階層の深さに応じて .parent を調整
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# ==========================================
# 難易度系
# ==========================================

class MDifficulty(Base):
    __tablename__ = "m_difficulty"

    difficulty_id = Column(Integer, primary_key=True)
    difficulty_name = Column(String)