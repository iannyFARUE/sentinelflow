from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.models import Product

router = APIRouter(tags=["products"])


@router.get("/products")
def list_products(
    q: str | None = Query(default=None, description="Search by name"),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.is_active == True)  # noqa: E712
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    items = query.order_by(Product.created_at.desc()).limit(limit).all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "price": str(p.price),
            "currency": p.currency,
            "inventory_qty": p.inventory_qty,
        }
        for p in items
    ]
