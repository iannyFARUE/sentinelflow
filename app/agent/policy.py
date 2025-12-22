from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from sqlalchemy.orm import Session

from app.agent.types import AgentPlan, ToolName
from app.services.accounts import get_balance
from app.services.inventory import check_available


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    needs_confirmation: bool = False
    confirmation_summary: str | None = None
    reason: str | None = None


MAX_SINGLE_PURCHASE = Decimal("1500.00")


def evaluate_plan(db: Session, plan: AgentPlan, *, user_id: str | None) -> PolicyDecision:
    # If we don't know user, we cannot do anything sensitive.
    if not user_id:
        return PolicyDecision(allowed=False, reason="missing_user_id")

    # Only enforce deeper checks if the plan includes a purchase tool call
    purchase_steps = [
        s for s in plan.steps
        if s.step_type.value == "tool_call" and s.tool_call and s.tool_call.tool_name == ToolName.execute_purchase
    ]

    if not purchase_steps:
        return PolicyDecision(allowed=True)

    # Extract purchase parameters (assume first purchase step)
    args = purchase_steps[0].tool_call.arguments
    product_id = args.get("product_id")
    qty = int(args.get("qty", 1))

    # Check inventory and compute total
    unit_price, currency = check_available(db, product_id, qty)
    total = (unit_price * Decimal(qty)).quantize(Decimal("0.01"))

    # Hard cap
    if total > MAX_SINGLE_PURCHASE:
        return PolicyDecision(allowed=False, reason="purchase_amount_exceeds_limit")

    # Check funds
    bal, _ = get_balance(db, user_id)
    if Decimal(bal) < total:
        return PolicyDecision(allowed=False, reason="insufficient_funds")

    # Always require confirmation for purchases
    summary = f"Confirm purchase of {qty} item(s) (product_id={product_id}) for {total} {currency}?"
    return PolicyDecision(allowed=True, needs_confirmation=True, confirmation_summary=summary)
