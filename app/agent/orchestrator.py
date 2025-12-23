# app/agent/orchestrator.py
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.agent.llm_planner import llm_plan
from app.agent.memory import PendingConfirmation, save_pending_confirmation
from app.agent.memory_store import get_memory, patch_memory
from app.agent.policy import evaluate_plan
from app.agent.resolver import parse_selection_index
from app.agent.types import AgentPlan, PlanStepType, ToolName,ToolCall, PlanStep
from app.db.models import Trace
from app.tools.balance import check_balance_tool
from app.tools.products import search_products_tool
from app.tools.purchase import execute_purchase_tool
from app.tools.records import update_database_tool
from app.tools.registry import ToolRegistry
from app.utils.ids import new_confirmation_token, new_idempotency_key


@dataclass(frozen=True)
class OrchestratorResult:
    trace_id: str
    message: str
    needs_confirmation: bool = False
    confirmation_token: str | None = None


def _init_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(ToolName.check_balance.value, check_balance_tool)
    reg.register(ToolName.search_products.value, search_products_tool)
    reg.register(ToolName.execute_purchase.value, execute_purchase_tool)
    reg.register(ToolName.update_database.value, update_database_tool)
    return reg

def _plan_needs_product_search(plan: AgentPlan, message: str) -> bool:
    msg = message.lower()
    wants_purchase = any(k in msg for k in ["buy", "purchase", "order"])
    if not wants_purchase:
        return False

    # If plan already calls search_products, we're good
    for s in plan.steps:
        if s.step_type == PlanStepType.tool_call and s.tool_call and s.tool_call.tool_name == ToolName.search_products:
            return False

    # If plan already has a purchase tool_call with a product_id, we're good
    for s in plan.steps:
        if s.step_type == PlanStepType.tool_call and s.tool_call and s.tool_call.tool_name == ToolName.execute_purchase:
            args = s.tool_call.arguments or {}
            if args.get("product_id"):
                return False

    # product_id not present and no search_products step => we should force search
    return True


def create_trace(db: Session, *, session_id: str, user_message: str) -> Trace:
    tr = Trace(session_id=session_id, user_message=user_message, assistant_message=None, plan_json=None)
    db.add(tr)
    db.commit()
    db.refresh(tr)
    return tr


def update_trace(db: Session, *, trace_id: str, assistant_message: str | None, plan: AgentPlan | None) -> None:
    tr = db.get(Trace, trace_id)
    if not tr:
        return
    if assistant_message is not None:
        tr.assistant_message = assistant_message
    if plan is not None:
        tr.plan_json = plan.model_dump_json()
    db.commit()


def _format_product_candidates(candidates: list[dict[str, Any]]) -> str:
    if not candidates:
        return "No matching products found."
    lines = ["Here are matching products:"]
    for i, p in enumerate(candidates, start=1):
        lines.append(
            f"{i}) {p.get('name')} — {p.get('price')} {p.get('currency')} (stock: {p.get('inventory_qty')})"
        )
    lines.append("")
    lines.append("Reply with the option number (e.g., `2`) or say `cancel`.")
    return "\n".join(lines)


def _try_handle_selection_flow(
    db: Session,
    *,
    session_id: str,
    user_id: str | None,
    message: str,
) -> OrchestratorResult | None:
    """
    If we previously showed product candidates, allow:
      - "2" / "second" / "option 2" -> select product_id
      - then automatically proceed to purchase confirmation flow.
    """
    msg = message.strip().lower()
    if msg in {"cancel", "stop", "nevermind", "never mind"}:
        # Clear selection memory
        patch_memory(db, session_id, {"last_product_candidates": [], "selected_product_id": None, "pending_qty": None})
        tr = create_trace(db, session_id=session_id, user_message=message)
        out = "Okay — canceled. What would you like to do next?"
        update_trace(db, trace_id=tr.id, assistant_message=out, plan=None)
        return OrchestratorResult(trace_id=tr.id, message=out)

    idx = parse_selection_index(message)
    if idx is None:
        return None

    mem = get_memory(db, session_id)
    candidates = mem.get("last_product_candidates") or []
    if not isinstance(candidates, list) or len(candidates) == 0:
        return None

    if idx < 1 or idx > len(candidates):
        tr = create_trace(db, session_id=session_id, user_message=message)
        out = f"That option number is out of range (1–{len(candidates)}). Please try again."
        update_trace(db, trace_id=tr.id, assistant_message=out, plan=None)
        return OrchestratorResult(trace_id=tr.id, message=out)
    
    chosen = candidates[idx - 1]
    product_id = chosen.get("id")
    qty = int(mem.get("pending_qty") or 1)

    patch_memory(db, session_id, {"selected_product_id": product_id})

    # Create a pending confirmation directly (NO LLM)
    token = new_confirmation_token()

    pending = PendingConfirmation(
        confirmation_token=token,
        tool_name=ToolName.execute_purchase.value,
        tool_args={
            "user_id": user_id,
            "product_id": product_id,
            "qty": qty,
            "idempotency_key": new_idempotency_key(),
            "confirm": True,
        },
    )
    # Persist it linked to a trace
    tr = create_trace(db, session_id=session_id, user_message=message)
    save_pending_confirmation(db, tr.id, pending)

    out = (
        f"Confirm purchase:\n"
        f"- Product: {chosen.get('name')}\n"
        f"- Qty: {qty}\n\n"
        f"Reply with: confirm {token}\n"
        f"(or say cancel)"
    )
    update_trace(db, trace_id=tr.id, assistant_message=out, plan=None)
    return OrchestratorResult(trace_id=tr.id, message=out, needs_confirmation=True, confirmation_token=token)
    


def handle_confirmation(
    db: Session,
    *,
    session_id: str,
    user_id: str | None,
    message: str,
) -> OrchestratorResult | None:
    """
    Confirmation protocol:
      User replies: "confirm <token>"
    We search recent traces for the token stored in Trace.plan_json (pending_confirmation).
    """
    parts = message.strip().split()
    if len(parts) != 2 or parts[0].lower() != "confirm":
        return None
    token = parts[1]

    recent = (
        db.query(Trace)
        .filter(Trace.session_id == session_id)
        .order_by(Trace.created_at.desc())
        .limit(25)
        .all()
    )

    pending = None
    for tr in recent:
        if not tr.plan_json:
            continue
        try:
            payload = json.loads(tr.plan_json)
            pc = payload.get("pending_confirmation")
            if pc and pc.get("confirmation_token") == token:
                pending = pc
                break
        except Exception:
            continue

    exec_trace = create_trace(db, session_id=session_id, user_message=message)

    if not pending:
        out = "Invalid or expired confirmation token."
        update_trace(db, trace_id=exec_trace.id, assistant_message=out, plan=None)
        return OrchestratorResult(trace_id=exec_trace.id, message=out)

    if not user_id:
        out = "Missing user_id. Cannot confirm purchase."
        update_trace(db, trace_id=exec_trace.id, assistant_message=out, plan=None)
        return OrchestratorResult(trace_id=exec_trace.id, message=out)

    reg = _init_registry()
    tool_name = pending["tool_name"]
    args = dict(pending["tool_args"])
    args["user_id"] = user_id  # enforce current context user

    result = reg.run_with_audit(db=db, trace_id=exec_trace.id, tool_name=tool_name, args=args)
    if not result.ok:
        out = f"Purchase failed: {result.error}"
        update_trace(db, trace_id=exec_trace.id, assistant_message=out, plan=None)
        return OrchestratorResult(trace_id=exec_trace.id, message=out)

    outp = result.output or {}
    out = (
        f"Purchase confirmed ✅\n"
        f"Transaction: {outp.get('transaction_id')}\n"
        f"Total: {outp.get('total_amount')} {outp.get('currency')}\n"
        f"Remaining balance: {outp.get('remaining_balance')} {outp.get('currency')}"
    )
    update_trace(db, trace_id=exec_trace.id, assistant_message=out, plan=None)
    return OrchestratorResult(trace_id=exec_trace.id, message=out)


def handle_message(
    db: Session,
    *,
    session_id: str,
    user_id: str | None,
    message: str,
) -> OrchestratorResult:
    # 1) Confirmation path
    conf = handle_confirmation(db, session_id=session_id, user_id=user_id, message=message)
    if conf is not None:
        return conf

    # 2) Selection path ("2", "second", etc.)
    sel = _try_handle_selection_flow(db, session_id=session_id, user_id=user_id, message=message)
    if sel is not None:
        return sel

    # 3) Normal planned flow
    return _handle_planned_flow(db, session_id=session_id, user_id=user_id, message=message)


def _handle_planned_flow(
    db: Session,
    *,
    session_id: str,
    user_id: str | None,
    message: str,
    original_user_message: str | None = None,
) -> OrchestratorResult:
    """
    Core path:
      Trace -> Plan -> Ask user OR Policy gate -> Tool calls -> Response
    """
    
    reg = _init_registry()
    trace = create_trace(db, session_id=session_id, user_message=original_user_message or message)

    # Pull memory to help planning (e.g., reuse selected product)
    mem = get_memory(db, session_id)

    # If user previously selected a product and is now saying "buy it" or similar, help the model.
    # Also, if selected_product_id exists and user says "buy" without product_id, we can inject.
    msg_lower = (message or "").lower()
    if mem.get("selected_product_id") and any(k in msg_lower for k in ["buy", "purchase", "order"]) and "product_id=" not in msg_lower:
        # inject product_id to make the plan deterministic
        qty = int(mem.get("pending_qty") or 1)
        message = f"buy product_id={mem['selected_product_id']} qty={qty}"

    # Plan (LLM planner with fallback)
    plan = llm_plan(message, user_id=user_id)
    if _plan_needs_product_search(plan, message):
        # Force a deterministic search step
        # naive query extraction: use the full message; later you can improve extraction
        query = message.strip()
        plan = AgentPlan(
            intent=plan.intent,
            steps=[
                # search first
                PlanStep(
                    step_type=PlanStepType.tool_call,
                    tool_call=ToolCall(
                        tool_name=ToolName.search_products,
                        arguments={"query": query, "limit": 5},
                    ),
                ),
                # then ask user to pick
                PlanStep(
                    step_type=PlanStepType.ask_user,
                    user_message="Pick an option number (1–5) from the results. If you want more, say 'show more'.",
                ),
            ],
            requires_confirmation=True,
            confirmation_summary=plan.confirmation_summary,
            risk_level=plan.risk_level,
        )
    update_trace(db, trace_id=trace.id, assistant_message=None, plan=plan)

    # If plan asks user something, return that immediately
    for step in plan.steps:
        if step.step_type == PlanStepType.ask_user and step.user_message:
            # Guard: don't ask to pick 1-5 unless we actually have candidates stored
            msg = step.user_message.lower()
            if ("option" in msg or "1-5" in msg or "1–5" in msg) and not (mem.get("last_product_candidates") or []):
                # Instead, force a search_products call immediately
                query = (original_user_message or message).strip()
                print(query)
                # run search directly
                result = reg.run_with_audit(
                    db=db,
                    trace_id=trace.id,
                    tool_name=ToolName.search_products.value,
                    args={"query": query, "limit": 5},
                )
                if not result.ok:
                    out = f"Tool error (search_products): {result.error}"
                    update_trace(db, trace_id=trace.id, assistant_message=out, plan=plan)
                    return OrchestratorResult(trace_id=trace.id, message=out)

                candidates = (result.output or {}).get("results") or []
                if not candidates:
                    out = "I couldn’t find any matching products. Try a more specific keyword."
                    update_trace(db, trace_id=trace.id, assistant_message=out, plan=plan)
                    return OrchestratorResult(trace_id=trace.id, message=out)

                patch_memory(db, session_id, {
                    "last_product_candidates": candidates,
                    "selected_product_id": None,
                    "pending_qty": int(mem.get("pending_qty") or 1),
                })

                out = _format_product_candidates(candidates)
                update_trace(db, trace_id=trace.id, assistant_message=out, plan=plan)
                return OrchestratorResult(trace_id=trace.id, message=out)

            # Normal ask_user
            out = step.user_message
            update_trace(db, trace_id=trace.id, assistant_message=out, plan=plan)
            return OrchestratorResult(trace_id=trace.id, message=out)

    # Policy decision (safety)
    decision = evaluate_plan(db, plan, user_id=user_id)

    if not decision.allowed:
        out = f"Cannot proceed: {decision.reason}."
        update_trace(db, trace_id=trace.id, assistant_message=out, plan=plan)
        return OrchestratorResult(trace_id=trace.id, message=out)

    # Execute tool calls in order
    for step in plan.steps:
        if step.step_type != PlanStepType.tool_call or not step.tool_call:
            continue

        tool_name = step.tool_call.tool_name.value
        args = dict(step.tool_call.arguments)
        # Tools that require user_id
        if tool_name in {ToolName.check_balance.value, ToolName.execute_purchase.value}:
            if not args:
                args = {}
            if user_id and not args.get("user_id"):
                args["user_id"] = user_id


        # ---- Tool: search_products ----
        if tool_name == ToolName.search_products.value:
            # Ensure args is a dict
            args = args or {}

            # Repair missing/empty query ONLY if needed
            if not args.get("query"):
                raw = (original_user_message or message).lower()

                # lightweight cleanup
                raw = raw.replace("buy", " ").replace("purchase", " ").replace("order", " ")
                raw = raw.replace("please", " ").replace("can you", " ").replace("i want to", " ").replace("i want", " ")

                # remove common filler words
                stop = {"me", "a", "an", "the", "to", "for", "of", "some", "one"}
                tokens = [t for t in raw.split() if t not in stop]

                # if we removed too much, fallback to original
                q = " ".join(tokens).strip()[:120] or raw.strip()[:120] or (original_user_message or message)[:120]
                args["query"] = q

            # Default limit if missing
            args.setdefault("limit", 5)

            result = reg.run_with_audit(db=db, trace_id=trace.id, tool_name=tool_name, args=args)
            if not result.ok:
                out = f"Tool error ({tool_name}): {result.error}"
                update_trace(db, trace_id=trace.id, assistant_message=out, plan=plan)
                return OrchestratorResult(trace_id=trace.id, message=out)

            candidates = (result.output or {}).get("results") or []

            # If no candidates, don't ask them to pick 1-5
            if not candidates:
                out = "I couldn’t find any matching products. Try a more specific keyword (e.g., 'wireless keyboard', 'mechanical keyboard')."
                update_trace(db, trace_id=trace.id, assistant_message=out, plan=plan)
                return OrchestratorResult(trace_id=trace.id, message=out)

            # Persist candidates for selection turn
            pending_qty = int(mem.get("pending_qty") or 1)
            patch_memory(
                db,
                session_id,
                {
                    "last_product_candidates": candidates,
                    "selected_product_id": None,
                    "pending_qty": pending_qty,
                },
            )

            out = _format_product_candidates(candidates)
            update_trace(db, trace_id=trace.id, assistant_message=out, plan=plan)
            return OrchestratorResult(trace_id=trace.id, message=out)


        # ---- Tool: execute_purchase ----
        if tool_name == ToolName.execute_purchase.value:
            # Inject idempotency key
            args["idempotency_key"] = args.get("idempotency_key") or new_idempotency_key()

            # Enforce confirmation flow (we never execute purchase in the first pass)
            if decision.needs_confirmation:
                token = new_confirmation_token()
                pending = PendingConfirmation(
                    confirmation_token=token,
                    tool_name=tool_name,
                    tool_args={**args, "confirm": True},
                )
                save_pending_confirmation(db, trace.id, pending)

                out = decision.confirmation_summary or "Please confirm this purchase."
                out = f"{out}\n\nReply with: confirm {token}"
                update_trace(db, trace_id=trace.id, assistant_message=out, plan=plan)
                return OrchestratorResult(
                    trace_id=trace.id,
                    message=out,
                    needs_confirmation=True,
                    confirmation_token=token,
                )

            # (Should not reach here; safety: execute_purchase_tool also blocks if confirm=False)
            result = reg.run_with_audit(db=db, trace_id=trace.id, tool_name=tool_name, args={**args, "confirm": False})
            if not result.ok:
                out = f"Tool error ({tool_name}): {result.error}"
                update_trace(db, trace_id=trace.id, assistant_message=out, plan=plan)
                return OrchestratorResult(trace_id=trace.id, message=out)

        # ---- Tool: check_balance ----
        if tool_name == ToolName.check_balance.value:
            result = reg.run_with_audit(db=db, trace_id=trace.id, tool_name=tool_name, args=args)
            if not result.ok:
                out = f"Tool error ({tool_name}): {result.error}"
                update_trace(db, trace_id=trace.id, assistant_message=out, plan=plan)
                return OrchestratorResult(trace_id=trace.id, message=out)

            bal = (result.output or {}).get("balance")
            cur = (result.output or {}).get("currency")
            out = f"Your balance is {bal} {cur}."
            update_trace(db, trace_id=trace.id, assistant_message=out, plan=plan)
            return OrchestratorResult(trace_id=trace.id, message=out)

        # ---- Tool: update_database ----
        if tool_name == ToolName.update_database.value:
            result = reg.run_with_audit(db=db, trace_id=trace.id, tool_name=tool_name, args=args)
            if not result.ok:
                out = f"Tool error ({tool_name}): {result.error}"
                update_trace(db, trace_id=trace.id, assistant_message=out, plan=plan)
                return OrchestratorResult(trace_id=trace.id, message=out)

            out = f"Update recorded: {(result.output or {}).get('status')}"
            update_trace(db, trace_id=trace.id, assistant_message=out, plan=plan)
            return OrchestratorResult(trace_id=trace.id, message=out)

    out = "Done."
    update_trace(db, trace_id=trace.id, assistant_message=out, plan=plan)
    return OrchestratorResult(trace_id=trace.id, message=out)
