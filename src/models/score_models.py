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
# プレイデータ系
# ==========================================

class Score(Base):
    __tablename__ = "scores"

    score_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    chart_id = Column(Integer, nullable=False)
    play_style = Column(SmallInteger, nullable=False)
    clear_state = Column(Integer, nullable=False)
    ex_score = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['m_users.user_id'], ondelete="CASCADE"),
        ForeignKeyConstraint(
            ['chart_id', 'play_style'],
            ['m_charts.chart_id', 'm_charts.play_style'],
            ondelete="CASCADE"
        ),
        UniqueConstraint('user_id', 'chart_id', 'play_style', name='uq_user_chart_style'),
        Index('idx_scores_user_id', 'user_id'),
        Index('idx_scores_chart_style', 'chart_id', 'play_style'),
    )

    user = relationship("MUser", back_populates="scores")
    chart = relationship("MChart", back_populates="scores")