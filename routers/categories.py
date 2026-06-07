from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("/")
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

@router.post("/")
def create_category(name: str, db: Session = Depends(get_db)):
    category = models.Category(name=name)
    db.add(category)
    db.commit()
    return category