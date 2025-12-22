from __future__ import annotations

from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models import Product


class ProductNotFound(Exception):
    pass


def get_product(db: Session, product_id: str) -> Product:
    p = db.query(Product).filter(Product.id == product_id, Product.is_active == True).one_or_none()  # noqa: E712
    if not p:
        raise ProductNotFound(f"Product not found: {product_id}")
    return p


def check_available(db: Session, product_id: str, qty: int) -> tuple[Decimal, str]:
    p = get_product(db, product_id)
    if qty <= 0:
        raise ValueError("qty must be >= 1")
    if p.inventory_qty < qty:
        raise ValueError("out_of_stock")
    return Decimal(p.price), p.currency


def reserve(db: Session, product_id: str, qty: int) -> None:
    p = get_product(db, product_id)
    if p.inventory_qty < qty:
        raise ValueError("out_of_stock")
    p.inventory_qty -= qty
    db.flush()
