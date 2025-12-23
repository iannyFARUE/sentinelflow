from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.models import Trace, AuditLog
from app.schemas.observability import TraceOut, AuditLogOut

router = APIRouter(tags=["observability"])


@router.get("/sessions/{session_id}/traces", response_model=list[TraceOut])
def list_session_traces(
    session_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Trace)
        .filter(Trace.session_id == session_id)
        .order_by(Trace.created_at.asc())
        .limit(limit)
        .all()
    )
    return [
        TraceOut(
            id=t.id,
            session_id=t.session_id,
            user_message=t.user_message,
            assistant_message=t.assistant_message,
            plan_json=t.plan_json,
            created_at=t.created_at,
        )
        for t in rows
    ]


@router.get("/traces/{trace_id}", response_model=TraceOut)
def get_trace(trace_id: str, db: Session = Depends(get_db)):
    t = db.get(Trace, trace_id)
    if not t:
        # FastAPI will convert this into 404 JSON automatically if you prefer HTTPException
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Trace not found")

    return TraceOut(
        id=t.id,
        session_id=t.session_id,
        user_message=t.user_message,
        assistant_message=t.assistant_message,
        plan_json=t.plan_json,
        created_at=t.created_at,
    )


@router.get("/traces/{trace_id}/audit_logs", response_model=list[AuditLogOut])
def list_audit_logs(trace_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(AuditLog)
        .filter(AuditLog.trace_id == trace_id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )
    return [
        AuditLogOut(
            id=a.id,
            trace_id=a.trace_id,
            tool_name=a.tool_name,
            status=str(a.status),
            input_json=a.input_json,
            output_json=a.output_json,
            error_message=a.error_message,
            created_at=a.created_at,
        )
        for a in rows
    ]
