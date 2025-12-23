from __future__ import annotations

import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.models import AuditLog  # adjust if your model name differs

router = APIRouter(tags=["audit"])


@router.get("/audit_logs")
def list_audit_logs(
    trace_id: str = Query(...),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(AuditLog)
        .filter(AuditLog.trace_id == trace_id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )
    out = []
    for r in rows:
        def _j(v):
            if v is None:
                return None
            if isinstance(v, (dict, list)):
                return v
            try:
                return json.loads(v)
            except Exception:
                return v

        out.append(
            {
                "id": r.id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "tool_name": r.tool_name,
                "ok": bool(r.ok),
                "args": _j(r.args_json),
                "output": _j(r.output_json),
                "error": r.error,
            }
        )
    return out
