from __future__ import annotations

from decimal import Decimal
from sqlalchemy.orm import Session

from app.schemas.tool_io import CheckBalanceIn, CheckBalanceOut
from app.services.accounts import get_balance
from app.tools.registry import ToolResult


def check_balance_tool(db: Session, args: dict) -> ToolResult:
    inp = CheckBalanceIn.model_validate(args)
    bal, cur = get_balance(db, inp.user_id)
    out = CheckBalanceOut(user_id=inp.user_id, balance=Decimal(bal), currency=cur)
    return ToolResult(ok=True, output=out.model_dump(mode="json"))
