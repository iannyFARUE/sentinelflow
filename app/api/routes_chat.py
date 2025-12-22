from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.agent.orchestrator import handle_message, handle_confirmation

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    # If this is a confirmation, route it
    conf = handle_confirmation(db, session_id=req.session_id, user_id=req.user_id, message=req.message)
    if conf is not None:
        return ChatResponse(
            trace_id=conf.trace_id,
            session_id=req.session_id,
            message=conf.message,
            needs_confirmation=False,
            confirmation_token=None,
        )

    res = handle_message(db, session_id=req.session_id, user_id=req.user_id, message=req.message)
    return ChatResponse(
        trace_id=res.trace_id,
        session_id=req.session_id,
        message=res.message,
        needs_confirmation=res.needs_confirmation,
        confirmation_token=res.confirmation_token,
    )
