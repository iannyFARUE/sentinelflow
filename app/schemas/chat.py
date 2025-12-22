from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=64)
    user_id: str | None = Field(default=None, description="Optional: if known; otherwise agent can ask/select.")
    message: str = Field(..., min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    trace_id: str
    session_id: str
    message: str
    needs_confirmation: bool = False
    confirmation_token: str | None = None
