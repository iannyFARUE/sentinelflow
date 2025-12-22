from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.seed import seed_synthetic_data

router = APIRouter(tags=["admin"])

@router.post("/admin/seed")
def seed(db: Session = Depends(get_db)):
    return seed_synthetic_data(db)
