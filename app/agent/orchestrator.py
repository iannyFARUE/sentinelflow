from __future__ import annotations

import json
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.agent.planner import simple_planner
from app.agent.llm_planner import llm_plan
from app.agent.policy import evaluate_plan
from app.agent.types import AgentPlan, PlanStepType, ToolName
from app.agent.memory import PendingConfirmation, save_pending_confirmation
from app.db.models import Trace
from app.schemas.chat import ChatResponse
from app.tools.registry import ToolRegistry
from app.tools.balance import check_balance_tool
from app.tools.purchase import execute_purchase_tool
from app.tools.records import update_database_tool
from app.utils.ids import new_idempotency_key, new_confirmation_token


@dataclass(frozen=True)
class OrchestratorResult:
    trace_id: str
    message: str
    needs_confirmation: bool = False
    confirmation_token: str | None = None


def _init_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(ToolName.check_balance.value, check_balance_tool)
    reg.register(ToolName.execute_purchase.value, execute_purchase_tool)
    reg.register(ToolName.update_database.value, update_database_tool)
    return reg


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


def handle_message(
    db: Session,
    *,
    session_id: str,
    user_id: str | None,
    message: str,
) -> OrchestratorResult:
    reg = _init_registry()

    trace = create_trace(db, session_id=session_id, user_message=message)

    # If user is responding to a confirmation, handle that pathway later.
    # For now: simplest confirmation UX: user types "yes" or "confirm".
    if message.strip().lower() in {"yes", "confirm", "y"}:
        # In professional version we'd look up most recent pending confirmation by session.
        # For now: ask user to confirm with token (more robust), implemented below via normal flow.
        pass

    plan = llm_plan(message, user_id=user_id)

    update_trace(db, trace_id=trace.id, assistant_message=None, plan=plan)

    # If plan asks user something
    for step in plan.steps:
        if step.step_type == PlanStepType.ask_user and step.user_message:
            update_trace(db, trace_id=trace.id, assistant_message=step.user_message, plan=plan)
            return OrchestratorResult(trace_id=trace.id, message=step.user_message)

    # Policy decision (safety)
    decision = evaluate_plan(db, plan, user_id=user_id)

    if not decision.allowed:
        msg = f"Cannot proceed: {decision.reason}."
        update_trace(db, trace_id=trace.id, assistant_message=msg, plan=plan)
        return OrchestratorResult(trace_id=trace.id, message=msg)

    # Execute tool calls (with confirmation handling)
    for step in plan.steps:
        if step.step_type != PlanStepType.tool_call or not step.tool_call:
            continue

        tool_name = step.tool_call.tool_name.value
        args = dict(step.tool_call.arguments)

        # Inject idempotency + confirm handling for purchases
        if tool_name == ToolName.execute_purchase.value:
            args["idempotency_key"] = args.get("idempotency_key") or new_idempotency_key()
            if decision.needs_confirmation:
                # Do NOT execute yet. Store pending confirmation.
                token = new_confirmation_token()
                pending = PendingConfirmation(
                    confirmation_token=token,
                    tool_name=tool_name,
                    tool_args={**args, "confirm": True},  # commit-ready payload
                )
                save_pending_confirmation(db, trace.id, pending)

                msg = decision.confirmation_summary or "Please confirm this purchase (reply with token)."
                msg = f"{msg}\n\nReply with: confirm {token}"
                update_trace(db, trace_id=trace.id, assistant_message=msg, plan=plan)
                return OrchestratorResult(
                    trace_id=trace.id,
                    message=msg,
                    needs_confirmation=True,
                    confirmation_token=token,
                )

        # Normal tool execution
        result = reg.run_with_audit(db=db, trace_id=trace.id, tool_name=tool_name, args=args)
        if not result.ok:
            msg = f"Tool error ({tool_name}): {result.error}"
            update_trace(db, trace_id=trace.id, assistant_message=msg, plan=plan)
            return OrchestratorResult(trace_id=trace.id, message=msg)

        # Create human-friendly response for known tools
        if tool_name == ToolName.check_balance.value:
            bal = result.output.get("balance")
            cur = result.output.get("currency")
            msg = f"Your balance is {bal} {cur}."
            update_trace(db, trace_id=trace.id, assistant_message=msg, plan=plan)
            return OrchestratorResult(trace_id=trace.id, message=msg)

        if tool_name == ToolName.update_database.value:
            msg = f"Update recorded: {result.output.get('status')}"
            update_trace(db, trace_id=trace.id, assistant_message=msg, plan=plan)
            return OrchestratorResult(trace_id=trace.id, message=msg)

    # If plan finished without a tool response
    msg = "Done."
    update_trace(db, trace_id=trace.id, assistant_message=msg, plan=plan)
    return OrchestratorResult(trace_id=trace.id, message=msg)


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
    We find latest trace with matching token in plan_json (simple approach).
    Professional upgrade later: store pending confirmations in a dedicated table.
    """
    parts = message.strip().split()
    if len(parts) != 2 or parts[0].lower() != "confirm":
        return None
    token = parts[1]

    # Find latest trace for this session (quick and good enough for demo)
    trace = (
        db.query(Trace)
        .filter(Trace.session_id == session_id)
        .order_by(Trace.created_at.desc())
        .limit(25)
        .all()
    )

    pending = None
    pending_trace_id = None
    for tr in trace:
        if not tr.plan_json:
            continue
        try:
            payload = json.loads(tr.plan_json)
            pc = payload.get("pending_confirmation")
            if pc and pc.get("confirmation_token") == token:
                pending = pc
                pending_trace_id = tr.id
                break
        except Exception:
            continue

    if not pending or not pending_trace_id:
        new_trace = create_trace(db, session_id=session_id, user_message=message)
        msg = "Invalid or expired confirmation token."
        update_trace(db, trace_id=new_trace.id, assistant_message=msg, plan=None)
        return OrchestratorResult(trace_id=new_trace.id, message=msg)

    if not user_id:
        new_trace = create_trace(db, session_id=session_id, user_message=message)
        msg = "Missing user_id. Cannot confirm purchase."
        update_trace(db, trace_id=new_trace.id, assistant_message=msg, plan=None)
        return OrchestratorResult(trace_id=new_trace.id, message=msg)

    # Execute the stored tool call with confirm=True
    reg = _init_registry()
    exec_trace = create_trace(db, session_id=session_id, user_message=message)

    tool_name = pending["tool_name"]
    args = dict(pending["tool_args"])

    # ensure user_id matches current context
    args["user_id"] = user_id
    result = reg.run_with_audit(db=db, trace_id=exec_trace.id, tool_name=tool_name, args=args)

    if not result.ok:
        msg = f"Purchase failed: {result.error}"
        update_trace(db, trace_id=exec_trace.id, assistant_message=msg, plan=None)
        return OrchestratorResult(trace_id=exec_trace.id, message=msg)

    out = result.output
    msg = (
        f"Purchase confirmed ✅\n"
        f"Transaction: {out.get('transaction_id')}\n"
        f"Total: {out.get('total_amount')} {out.get('currency')}\n"
        f"Remaining balance: {out.get('remaining_balance')} {out.get('currency')}"
    )
    update_trace(db, trace_id=exec_trace.id, assistant_message=msg, plan=None)
    return OrchestratorResult(trace_id=exec_trace.id, message=msg)
