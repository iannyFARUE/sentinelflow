from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.models import AuditLog, Trace

router = APIRouter(tags=["logs"])

@router.get("/logs/{trace_id}")
def get_logs(trace_id: str, db: Session = Depends(get_db)):
    trace = db.get(Trace, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    audit = db.query(AuditLog).filter(AuditLog.trace_id == trace_id).order_by(AuditLog.created_at.asc()).all()

    return {
        "trace": {
            "id": trace.id,
            "session_id": trace.session_id,
            "user_message": trace.user_message,
            "assistant_message": trace.assistant_message,
            "plan_json": trace.plan_json,
            "created_at": str(trace.created_at),
        },
        "audit_logs": [
            {
                "id": a.id,
                "tool_name": a.tool_name,
                "status": a.status.value,
                "input_json": a.input_json,
                "output_json": a.output_json,
                "error_message": a.error_message,
                "created_at": str(a.created_at),
            }
            for a in audit
        ],
    }
