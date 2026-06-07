from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import decode_token
import models
from fastapi.security import OAuth2PasswordBearer
import calendar
from datetime import date
from typing import Optional

from sqlalchemy import func

router = APIRouter(prefix="/transactions", tags=["transactions"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = decode_token(token)
        user = db.query(models.User).filter(models.User.id == int(payload["sub"])).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/summary")
def get_summary(
    month: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    base = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    )

    if month:
        year, m = month.split("-")
        last_day = calendar.monthrange(int(year), int(m))[1]
        base = base.filter(
            models.Transaction.date >= f"{year}-{m}-01",
            models.Transaction.date <= f"{year}-{m}-{last_day}"
        )

    total_income = base.filter(
        models.Transaction.type == models.TransactionType.income
    ).with_entities(func.sum(models.Transaction.amount)).scalar() or 0

    total_expenses = base.filter(
        models.Transaction.type == models.TransactionType.expense
    ).with_entities(func.sum(models.Transaction.amount)).scalar() or 0

    by_category = base.with_entities(
        models.Category.name,
        func.sum(models.Transaction.amount)
    ).join(models.Category).group_by(models.Category.name).all()

    return {
        "income": total_income,
        "expenses": total_expenses,
        "balance": total_income - total_expenses,
        "by_category": [{"category": r[0], "total": r[1]} for r in by_category]
    }


@router.post("/")
def create_transaction(
    amount: float,
    description: str,
    type: models.TransactionType,
    category_id: int,
    date: date,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    transaction = models.Transaction(
        amount=amount,
        description=description,
        type=type,
        category_id=category_id,
        date=date,
        user_id=current_user.id
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction



@router.get("/")
def get_transactions(
    month: Optional[str] = None,
    category_id: Optional[int] = None,
    type: Optional[models.TransactionType] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    )
    if month:
        year, m = month.split("-")
        query = query.filter(
            models.Transaction.date >= f"{year}-{m}-01",
            models.Transaction.date <= f"{year}-{m}-{calendar.monthrange(int(year), int(m))[1]}"
        )
    if category_id:
        query = query.filter(models.Transaction.category_id == category_id)
    if type:
        query = query.filter(models.Transaction.type == type)
    return query.all()


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    t = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(t)
    db.commit()
    return {"message": "deleted"}



@router.put("/{transaction_id}")
def update_transaction(
    transaction_id: int,
    amount: float = None,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    t = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if amount is not None:
        t.amount = amount
    if description is not None:
        t.description = description
    db.commit()
    return t
