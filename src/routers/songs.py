from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from src.database import SessionLocal
from src.models import chart_models, song_models, difficulty_models,version_models

router = APIRouter(prefix="/api/v1/songs", tags=["songs"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/versions")
def get_versions(db: Session = Depends(get_db)):
    versions = db.query(version_models.MVersion).order_by(version_models.MVersion.version_id).all()
    return [{"version_id": v.version_id, "version_name": v.version_name} for v in versions]
    
@router.get("")
def get_songs(
    style: str = Query("SP"),             # SP = 0, DP = 1
    mode: str = Query("level"),           # "level" または "version"
    p1: Optional[str] = Query("12"),      # level(1~12) または version(0~33)
    p2: Optional[str] = Query(None),      # difficulty (0:BEGINNER ~ 4:LEGGENDARIA または 識別子)
    db: Session = Depends(get_db)
):
    play_style_val = 0 if style.upper() == "SP" else 1

    # MChart, MSong, MVersion の3つを取得対象に含める
    query = (
        db.query(chart_models.MChart, song_models.MSong, difficulty_models.MDifficulty, version_models.MVersion)
        .join(song_models.MSong, chart_models.MChart.song_id == song_models.MSong.song_id)
        .join(difficulty_models.MDifficulty, chart_models.MChart.difficulty_type == difficulty_models.MDifficulty.difficulty_id)
        .join(version_models.MVersion, chart_models.MChart.version == version_models.MVersion.version_id)
        .filter(chart_models.MChart.play_style == play_style_val)
    )

    # フィルタリング判定
    if mode == "level":
        if p1 is not None:
            query = query.filter(chart_models.MChart.level == int(p1))
    elif mode == "version":
        if p1 is not None:
            query = query.filter(chart_models.MChart.version == int(p1))
        if p2 is not None and p2 != "":
            query = query.filter(chart_models.MChart.difficulty_type == target_diff)

    results = query.all()

    songs_data = []
    # 3つのモデルが取得されるため、ループで version も受け取る
    for chart, song, difficulty, version in results:
        songs_data.append({
            "chart_id": chart.chart_id,
            "song_id": song.song_id,
            "title": getattr(song, "title", "Unknown"),
            "artist": getattr(song, "artist", ""),
            "play_style": chart.play_style,
            "difficulty_name": difficulty.difficulty_name,
            "level": chart.level,
            "version": version.version_name,  # MVersionのversion_nameを使用
            "notes": chart.notes,
        })

    return songs_data