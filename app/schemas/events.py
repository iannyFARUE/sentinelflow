from __future__ import annotations

from pydantic import BaseModel


class TraceCreate(BaseModel):
    session_id: str
    user_message: str


class TraceUpdate(BaseModel):
    assistant_message: str | None = None
    plan_json: str | None = None


class AuditEvent(BaseModel):
    trace_id: str
    tool_name: str
    status: str
    input_json: str | None = None
    output_json: str | None = None
    error_message: str | None = None
