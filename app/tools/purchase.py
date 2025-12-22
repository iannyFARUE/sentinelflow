from __future__ import annotations

from decimal import Decimal
from sqlalchemy.orm import Session

from app.schemas.tool_io import ExecutePurchaseIn, ExecutePurchaseOut
from app.services.accounts import get_balance
from app.services.payments import execute_purchase
from app.tools.registry import ToolResult


def execute_purchase_tool(db: Session, args: dict) -> ToolResult:
    inp = ExecutePurchaseIn.model_validate(args)

    # Hard safety: purchase tool will NOT execute unless confirm=True
    if not inp.confirm:
        return ToolResult(ok=False, error="confirmation_required")

    tx = execute_purchase(
        db,
        user_id=inp.user_id,
        product_id=inp.product_id,
        qty=inp.qty,
        idempotency_key=inp.idempotency_key,
    )
    bal, cur = get_balance(db, inp.user_id)

    out = ExecutePurchaseOut(
        transaction_id=tx.id,
        status=tx.status.value,
        total_amount=Decimal(tx.total_amount),
        currency=tx.currency,
        remaining_balance=Decimal(bal),
    )
    db.commit()
    return ToolResult(ok=True, output=out.model_dump(mode="json"))
