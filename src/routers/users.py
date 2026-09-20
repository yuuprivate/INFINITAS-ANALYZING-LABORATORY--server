from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from src.database import SessionLocal
from src.schema import schemas
from src.models import song_models, user_models, score_models, chart_models, difficulty_models ,version_models

router = APIRouter(prefix="/api/v1/users", tags=["users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_users(db: Session = Depends(get_db)):
    results = (
        db.query(user_models.MUser, user_models.DUserIrt)
        .outerjoin(user_models.DUserIrt, user_models.MUser.user_id == user_models.DUserIrt.user_id)
        .all()
    )
    
    users_data = []
    for user, irt in results:
        users_data.append({
            "user_id": user.user_id,
            "dj_name": user.dj_name,
            "iidx_id": getattr(user, "iidx_id", None),
            "irt_ability": getattr(user, "irt_ability", 0),
            "ability_clear_sp": irt.ability_clear_sp if irt else None,
            "ability_score_sp": irt.ability_score_sp if irt else None,
            "ability_clear_dp": irt.ability_clear_dp if irt else None,
            "ability_score_dp": irt.ability_score_dp if irt else None,
        })
        
    return users_data

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = user_models.MUser(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/details-with-irt")
def get_users_with_irt(db: Session = Depends(get_db)):
    results = (
        db.query(user_models.MUser, user_models.DUserIrt)
        .outerjoin(user_models.DUserIrt, user_models.MUser.user_id == user_models.DUserIrt.user_id)
        .all()
    )
    users_data = []
    for user, irt in results:
        users_data.append({
            "user_id": user.user_id,
            "dj_name": user.dj_name,
            "ability_clear_sp": irt.ability_clear_sp if irt else None,
            "ability_score_sp": irt.ability_score_sp if irt else None,
            "ability_clear_dp": irt.ability_clear_dp if irt else None,
            "ability_score_dp": irt.ability_score_dp if irt else None,
        })
    return users_data

@router.get("/{user_id}/records")
def get_user_records_with_all_charts(
    user_id: int,
    style: str = Query(..., regex="^(SP|DP)$"),
    mode: str = Query("all"),
    p1: int = None,
    p2: int = None,
    db: Session = Depends(get_db)
):
    play_style = 0 if style == "SP" else 1
    
    # 1. 検索条件に合致する譜面とバージョン情報を一緒に取得
    query = (
        db.query(chart_models.MChart, song_models.MSong, difficulty_models.MDifficulty, version_models.MVersion)
        .join(song_models.MSong, chart_models.MChart.song_id == song_models.MSong.song_id)
        .join(difficulty_models.MDifficulty, chart_models.MChart.difficulty_type == difficulty_models.MDifficulty.difficulty_id)
        .join(version_models.MVersion, chart_models.MChart.version == version_models.MVersion.version_id)
        .filter(chart_models.MChart.play_style == play_style)
    )
    
    if mode == "level":
        if p1 is not None:
            query = query.filter(chart_models.MChart.level == p1)
    elif mode == "version":
        if p1 is not None:
            query = query.filter(chart_models.MChart.version == p1)
        if p2 is not None:
            query = query.filter(chart_models.MChart.difficulty_type == p2)
            
    results = query.all()

    # 2. 該当ユーザーの指定スタイル・条件のレコードを取得
    user_records = db.query(score_models.Score).filter(
        score_models.Score.user_id == user_id,
        score_models.Score.play_style == play_style
    ).all()
    
    record_map = {r.chart_id: r for r in user_records}

    # 3. 譜面データとバージョン名をベースにレコードをマージ
    result = []
    for chart, song, difficulty, version in results:
        rec = record_map.get(chart.chart_id)
        
        result.append({
            "chart_id": chart.chart_id,
            "title": song.title,
            "play_style": chart.play_style,
            "level": chart.level,
            "difficulty_name" : difficulty.difficulty_name,
            "version": version.version_name,  # MVersionのversion_nameを使用
            "clear_state": rec.clear_state if rec else None,
            "ex_score": rec.ex_score if rec else None
        })

    return result