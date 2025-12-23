# app/tools/products.py
from __future__ import annotations

import re
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import Product
from app.schemas.tool_io import SearchProductsIn, SearchProductsOut
from app.tools.registry import ToolResult


_STOPWORDS = {
    "buy", "purchase", "order", "need", "want", "me", "a", "an", "the", "please", "can", "you", "to", "for"
}


def _normalize_query(q: str) -> list[str]:
    q = q.lower().strip()
    # keep letters/numbers/spaces only
    q = re.sub(r"[^a-z0-9\s]+", " ", q)
    tokens = [t for t in q.split() if t and t not in _STOPWORDS]
    # fallback: if everything got removed, use original single token-ish
    fallback = q.strip()
    return tokens or ([fallback] if fallback else [])


def search_products_tool(db: Session, args: dict) -> ToolResult:
    inp = SearchProductsIn.model_validate(args)

    tokens = _normalize_query(inp.query)
    print(tokens)

    query = db.query(Product).filter(Product.is_active == True)  # noqa: E712

    # OR match: any token appears in name
    conditions = []
    for t in tokens:
        conditions.append(Product.name.ilike(f"%{t}%"))
        conditions.append(Product.description.ilike(f"%{t}%"))
    query = query.filter(or_(*conditions))

    items = (
        query.order_by(Product.inventory_qty.desc())
        .limit(inp.limit)
        .all()
    )

    results = [
        {"id": p.id, "name": p.name, "price": str(p.price), "currency": p.currency, "inventory_qty": p.inventory_qty}
        for p in items
    ]

    out = SearchProductsOut(results=results)
    return ToolResult(ok=True, output=out.model_dump(mode="json"))
