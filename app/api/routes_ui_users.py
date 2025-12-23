from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.models import User, Account

router = APIRouter(prefix="/ui", tags=["ui"])


@router.get("/users")
def ui_list_users(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.created_at.desc()).limit(limit).all()
    return [{"id": u.id, "full_name": u.full_name, "email": u.email} for u in users]


@router.get("/users/{user_id}")
def ui_user_detail(user_id: str, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    acct = db.query(Account).filter(Account.user_id == user_id).one_or_none()
    return {
        "id": u.id,
        "full_name": u.full_name,
        "email": u.email,
        "account": (
            {"balance": str(acct.balance), "currency": acct.currency} if acct else None
        ),
    }
