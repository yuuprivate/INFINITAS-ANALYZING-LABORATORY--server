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
# 譜面系
# ==========================================

class MChart(Base):
    __tablename__ = "m_charts"

    chart_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    play_style = Column(SmallInteger, primary_key=True) # 0:SP, 1:DP
    song_id = Column(Integer, nullable=True)
    difficulty_type = Column(Integer, nullable=True)
    level = Column(Integer, nullable=True)
    notes = Column(Integer, nullable=True)
    version = Column(Integer, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(['song_id'], ['m_songs.song_id'], ondelete="CASCADE"),
    )

    song = relationship("MSong", back_populates="charts")
    clear_irt = relationship("DChartClearIrt", back_populates="chart", uselist=False, cascade="all, delete-orphan")
    score_irt = relationship("DChartScoreIrt", back_populates="chart", uselist=False, cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="chart", cascade="all, delete-orphan")


class DChartClearIrt(Base):
    __tablename__ = "d_charts_clear_irt"

    chart_id = Column(Integer, primary_key=True)
    play_style = Column(SmallInteger, primary_key=True)
    irt_discrimination = Column(Float, default=1.0)
    b_easy = Column(Float, nullable=False)
    b_normal = Column(Float, nullable=False)
    b_hard = Column(Float, nullable=False)
    b_ex_hard = Column(Float, nullable=False)
    b_fc = Column(Float, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        ForeignKeyConstraint(
            ['chart_id', 'play_style'],
            ['m_charts.chart_id', 'm_charts.play_style'],
            ondelete="CASCADE"
        ),
    )

    chart = relationship("MChart", back_populates="clear_irt")


class DChartScoreIrt(Base):
    __tablename__ = "d_charts_score_irt"

    chart_id = Column(Integer, primary_key=True)
    play_style = Column(SmallInteger, primary_key=True)
    b_score = Column(Float, nullable=False)  # スコア難易度パラメータ
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        ForeignKeyConstraint(
            ['chart_id', 'play_style'],
            ['m_charts.chart_id', 'm_charts.play_style'],
            ondelete="CASCADE"
        ),
    )

    chart = relationship("MChart", back_populates="score_irt")