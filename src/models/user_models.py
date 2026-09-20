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
# ユーザーアカウント系
# ==========================================

class MUser(Base):
    __tablename__ = "m_users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    dj_name = Column(String, nullable=False)
    iidx_id_first = Column(Integer, nullable=False)
    iidx_id_second = Column(Integer, nullable=False)
    iidx_id_third = Column(Integer, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    delete_flag = Column(SmallInteger, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint('dj_name', name='uq_dj_name'),
        UniqueConstraint('iidx_id_first', 'iidx_id_second', 'iidx_id_third', name='uq_iidx_id'),
    )

    irt_param = relationship("DUserIrt", back_populates="user", uselist=False, cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="user", cascade="all, delete-orphan")


class DUserIrt(Base):
    __tablename__ = "d_users_irt"

    user_id = Column(Integer, primary_key=True)
    ability_clear_sp = Column(Float, default=10.0)
    ability_clear_dp = Column(Float, default=10.0)
    ability_score_sp = Column(Float, default=10.0)
    ability_score_dp = Column(Float, default=10.0)

    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['m_users.user_id'], ondelete="CASCADE"),
    )

    user = relationship("MUser", back_populates="irt_param")