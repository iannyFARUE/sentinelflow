from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, List

from pydantic import BaseModel


class UserOut(BaseModel):
    id: str
    full_name: str
    email: str


class SessionOut(BaseModel):
    session_id: str
    last_message_at: datetime | None = None
    last_user_message: str | None = None



class TraceOut(BaseModel):
    id: str
    session_id: str
    user_message: str
    assistant_message: Optional[str]
    plan_json: Optional[str]
    created_at: datetime


class AuditLogOut(BaseModel):
    id: str
    trace_id: str
    tool_name: str
    status: str
    input_json: Optional[str]
    output_json: Optional[str]
    error_message: Optional[str]
    created_at: datetime
