from __future__ import annotations

import json
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models import Transaction, TransactionStatus
from app.services.accounts import debit
from app.services.inventory import check_available, reserve


class DuplicateIdempotency(Exception):
    pass


def _existing_tx(db: Session, user_id: str, idempotency_key: str) -> Transaction | None:
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id, Transaction.idempotency_key == idempotency_key)
        .one_or_none()
    )


def execute_purchase(
    db: Session,
    *,
    user_id: str,
    product_id: str,
    qty: int,
    idempotency_key: str,
) -> Transaction:
    # idempotency guard
    existing = _existing_tx(db, user_id, idempotency_key)
    if existing:
        return existing

    unit_price, currency = check_available(db, product_id, qty)
    total = (unit_price * Decimal(qty)).quantize(Decimal("0.01"))

    # Reserve inventory first (in real life you might do more robust locking)
    reserve(db, product_id, qty)

    # Debit account
    remaining_balance, _ = debit(db, user_id, total)

    tx = Transaction(
        user_id=user_id,
        product_id=product_id,
        qty=qty,
        unit_price=unit_price,
        total_amount=total,
        currency=currency,
        status=TransactionStatus.confirmed,
        idempotency_key=idempotency_key,
        metadata_json=json.dumps({"remaining_balance": str(remaining_balance)}),
    )
    db.add(tx)
    db.flush()
    return tx
