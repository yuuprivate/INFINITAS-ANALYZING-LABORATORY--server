from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.database import SessionLocal
from src.schema import schemas
from src.models import score_models
from src.irt import calculate_ability, get_recommendations

router = APIRouter(tags=["scores & recommendations"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/scores", response_model=schemas.ScoreResponse)
def upsert_score(score_data: schemas.ScoreCreate, db: Session = Depends(get_db)):
    existing_score = db.query(score_models.Score).filter(
        score_models.Score.user_id == score_data.user_id,
        score_models.Score.chart_id == score_data.chart_id
    ).first()

    if existing_score:
        for key, value in score_data.model_dump().items():
            setattr(existing_score, key, value)
    else:
        db_score = score_models.Score(**score_data.model_dump())
        db.add(db_score)

    db.commit()

    new_ability = calculate_ability(db, score_data.user_id)
    user = db.query(score_models.User).filter(score_models.User.user_id == score_data.user_id).first()
    if user:
        user.irt_ability = round(new_ability, 4)
        db.commit()
        db.refresh(user)

    target_score = db.query(score_models.Score).filter(
        score_models.Score.user_id == score_data.user_id,
        score_models.Score.chart_id == score_data.chart_id
    ).first()
    
    return target_score

@router.get("/scores")
def read_scores(db: Session = Depends(get_db)):
    return db.query(score_models.Score).all()

@router.get("/recommendations/{user_id}")
def get_user_recommendations(
    user_id: int, 
    target_lamp: str = "hard", 
    limit: int = 5, 
    db: Session = Depends(get_db)
):
    user = db.query(score_models.User).filter(score_models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    recommendations = get_recommendations(db, user_id, target_lamp=target_lamp, limit=limit)
    return {
        "user_id": user_id,
        "irt_ability": user.irt_ability,
        "target_lamp": target_lamp,
        "recommendations": recommendations
    }