from __future__ import annotations

from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models import Account


class AccountNotFound(Exception):
    pass


def get_account(db: Session, user_id: str) -> Account:
    acct = db.query(Account).filter(Account.user_id == user_id).one_or_none()
    if not acct:
        raise AccountNotFound(f"Account not found for user_id={user_id}")
    return acct


def get_balance(db: Session, user_id: str) -> tuple[Decimal, str]:
    acct = get_account(db, user_id)
    return Decimal(acct.balance), acct.currency


def debit(db: Session, user_id: str, amount: Decimal) -> tuple[Decimal, str]:
    acct = get_account(db, user_id)
    bal = Decimal(acct.balance)
    if amount <= Decimal("0"):
        raise ValueError("amount must be > 0")
    if bal < amount:
        raise ValueError("insufficient_funds")
    acct.balance = bal - amount
    db.flush()
    return Decimal(acct.balance), acct.currency
