from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.models import AuditLog, Trace

router = APIRouter(prefix="/ui", tags=["ui"])


def _safe_json_loads(s: str | None) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return s


@router.get("/audit_logs")
def ui_audit_logs(
    session_id: str | None = Query(default=None),
    trace_id: str | None = Query(default=None),
    tool_name: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Filterable audit log feed for UI.
    """
    q = db.query(AuditLog)

    if trace_id:
        q = q.filter(AuditLog.trace_id == trace_id)

    if session_id:
        # join traces to filter by session
        q = q.join(Trace, Trace.id == AuditLog.trace_id).filter(Trace.session_id == session_id)

    if tool_name:
        q = q.filter(AuditLog.tool_name == tool_name)

    if status:
        q = q.filter(AuditLog.status == status)

    logs = q.order_by(AuditLog.created_at.desc()).limit(limit).all()

    return [
        {
            "id": l.id,
            "trace_id": l.trace_id,
            "tool_name": l.tool_name,
            "status": str(l.status),
            "input": _safe_json_loads(l.input_json),
            "output": _safe_json_loads(l.output_json),
            "error_message": l.error_message,
            "created_at": l.created_at,
        }
        for l in logs
    ]
