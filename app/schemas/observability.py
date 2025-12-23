from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class TraceOut(BaseModel):
    id: str
    session_id: str
    user_message: str
    assistant_message: str | None
    plan_json: str | None
    created_at: datetime


class AuditLogOut(BaseModel):
    id: str
    trace_id: str
    tool_name: str
    status: str
    input_json: str | None
    output_json: str | None
    error_message: str | None
    created_at: datetime
