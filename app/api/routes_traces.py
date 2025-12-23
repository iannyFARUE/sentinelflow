from __future__ import annotations

import json
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.models import Trace
from app.schemas.api import TraceOut
from app.db.models import AuditLog
from app.schemas.api import AuditLogOut

router = APIRouter(tags=["traces"])


@router.get("/traces")
def list_traces(
    session_id: str = Query(...),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Trace)
        .filter(Trace.session_id == session_id)
        .order_by(Trace.created_at.desc())
        .limit(limit)
        .all()
    )

    out = []
    for tr in reversed(rows):  # chronological
        plan = None
        if tr.plan_json:
            try:
                plan = json.loads(tr.plan_json)
            except Exception:
                plan = tr.plan_json
        out.append(
            {
                "id": tr.id,
                "created_at": tr.created_at.isoformat() if tr.created_at else None,
                "user_message": tr.user_message,
                "assistant_message": tr.assistant_message,
                "plan_json": plan,
            }
        )
    return out

@router.get("/traces/{trace_id}", response_model=TraceOut)
def get_trace(trace_id: str, db: Session = Depends(get_db)):
    tr = db.query(Trace).filter(Trace.id == trace_id).first()
    if not tr:
        raise HTTPException(status_code=404, detail="Trace not found")
    return tr


@router.get("/traces/{trace_id}/audit-logs", response_model=list[AuditLogOut])
def get_audit_logs(trace_id: str, db: Session = Depends(get_db)):
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.trace_id == trace_id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )
    return logs