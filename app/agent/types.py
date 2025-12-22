from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class Intent(str, Enum):
    check_balance = "check_balance"
    purchase = "purchase"
    update_record = "update_record"
    unknown = "unknown"


class PlanStepType(str, Enum):
    tool_call = "tool_call"
    ask_user = "ask_user"
    done = "done"


class ToolName(str, Enum):
    check_balance = "check_balance"
    execute_purchase = "execute_purchase"
    update_database = "update_database"


class ToolCall(BaseModel):
    tool_name: ToolName
    arguments: dict = Field(default_factory=dict)


class PlanStep(BaseModel):
    step_type: PlanStepType
    tool_call: ToolCall | None = None
    user_message: str | None = None


class AgentPlan(BaseModel):
    intent: Intent = Intent.unknown
    steps: list[PlanStep] = Field(default_factory=list)
    requires_confirmation: bool = False
    confirmation_summary: str | None = None
    risk_level: str = "low"  # low/medium/high
