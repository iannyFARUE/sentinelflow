from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.agent.memory_store import get_memory
from app.db.models import Trace
from app.schemas.api import TraceOut

router = APIRouter(tags=["sessions"])


@router.get("/sessions/{session_id}/memory")
def session_memory(session_id: str, db: Session = Depends(get_db)):
    return get_memory(db, session_id)

@router.get("/sessions/{session_id}/traces", response_model=list[TraceOut])
def list_traces(session_id: str, db: Session = Depends(get_db)):
    traces = (
        db.query(Trace)
        .filter(Trace.session_id == session_id)
        .order_by(Trace.created_at.asc())
        .all()
    )
    return traces