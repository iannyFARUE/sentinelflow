from __future__ import annotations

import re
from app.agent.types import AgentPlan, Intent, PlanStep, PlanStepType, ToolCall, ToolName


def simple_planner(user_message: str, *, user_id: str | None) -> AgentPlan:
    msg = user_message.lower().strip()

    # check balance intent
    if any(k in msg for k in ["balance", "how much do i have", "my funds"]):
        if not user_id:
            return AgentPlan(
                intent=Intent.check_balance,
                steps=[PlanStep(step_type=PlanStepType.ask_user, user_message="What is your user_id?")],
                risk_level="low",
            )
        return AgentPlan(
            intent=Intent.check_balance,
            steps=[
                PlanStep(
                    step_type=PlanStepType.tool_call,
                    tool_call=ToolCall(tool_name=ToolName.check_balance, arguments={"user_id": user_id}),
                ),
                PlanStep(step_type=PlanStepType.done),
            ],
            risk_level="low",
        )

    # purchase intent: expects product_id in message for now
    if any(k in msg for k in ["buy", "purchase", "order"]):
        # naive extraction: product_id=... and qty=...
        product_id = None
        m = re.search(r"product_id\s*=\s*([a-f0-9\-]{8,})", msg)
        if m:
            product_id = m.group(1)

        qty = 1
        m2 = re.search(r"qty\s*=\s*(\d+)", msg)
        if m2:
            qty = int(m2.group(1))

        if not user_id:
            return AgentPlan(
                intent=Intent.purchase,
                steps=[PlanStep(step_type=PlanStepType.ask_user, user_message="What is your user_id?")],
                requires_confirmation=True,
                risk_level="high",
            )

        if not product_id:
            return AgentPlan(
                intent=Intent.purchase,
                steps=[
                    PlanStep(
                        step_type=PlanStepType.ask_user,
                        user_message="Please provide product_id (e.g., 'buy product_id=<id> qty=1').",
                    )
                ],
                requires_confirmation=True,
                risk_level="high",
            )

        return AgentPlan(
            intent=Intent.purchase,
            steps=[
                PlanStep(
                    step_type=PlanStepType.tool_call,
                    tool_call=ToolCall(
                        tool_name=ToolName.execute_purchase,
                        arguments={
                            "user_id": user_id,
                            "product_id": product_id,
                            "qty": qty,
                            # idempotency + confirm injected later by orchestrator/policy
                        },
                    ),
                ),
                PlanStep(step_type=PlanStepType.done),
            ],
            requires_confirmation=True,
            risk_level="high",
        )

    return AgentPlan(
        intent=Intent.unknown,
        steps=[PlanStep(step_type=PlanStepType.ask_user, user_message="I can help with balance checks or purchases. What would you like to do?")],
        risk_level="low",
    )
