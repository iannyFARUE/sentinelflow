from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.models import User, Account

router = APIRouter(tags=["users"])


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [{"id": u.id, "full_name": u.full_name, "email": u.email} for u in users]


@router.get("/users/{user_id}/account")
def get_account(user_id: str, db: Session = Depends(get_db)):
    acct = db.query(Account).filter(Account.user_id == user_id).one_or_none()
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"user_id": user_id, "balance": str(acct.balance), "currency": acct.currency}
