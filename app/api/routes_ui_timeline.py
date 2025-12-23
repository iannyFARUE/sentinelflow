from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.models import Trace, AuditLog

router = APIRouter(prefix="/ui", tags=["ui"])


def _safe_json_loads(s: str | None) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return s  # keep raw string if it isn't valid JSON


@router.get("/sessions")
def ui_list_sessions(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Returns distinct session_ids ordered by most recent trace time.
    Perfect for a left sidebar in the frontend.
    """
    rows = (
        db.query(Trace.session_id, Trace.created_at)
        .order_by(Trace.created_at.desc())
        .limit(5000)
        .all()
    )

    seen: set[str] = set()
    sessions: list[dict[str, Any]] = []
    for session_id, created_at in rows:
        if session_id in seen:
            continue
        seen.add(session_id)
        sessions.append({"session_id": session_id, "last_activity": created_at})
        if len(sessions) >= limit:
            break

    return sessions


@router.get("/sessions/{session_id}/timeline")
def ui_session_timeline(
    session_id: str,
    limit_traces: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Returns a session timeline: traces with nested audit logs.
    This is the single best endpoint for a "conversation + tool calls" UI.
    """
    traces = (
        db.query(Trace)
        .filter(Trace.session_id == session_id)
        .order_by(Trace.created_at.asc())
        .limit(limit_traces)
        .all()
    )

    if not traces:
        return {"session_id": session_id, "traces": []}

    trace_ids = [t.id for t in traces]
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.trace_id.in_(trace_ids))
        .order_by(AuditLog.created_at.asc())
        .all()
    )

    logs_by_trace: dict[str, list[dict[str, Any]]] = {}
    for l in logs:
        logs_by_trace.setdefault(l.trace_id, []).append(
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
        )

    out_traces: list[dict[str, Any]] = []
    for t in traces:
        out_traces.append(
            {
                "id": t.id,
                "session_id": t.session_id,
                "user_message": t.user_message,
                "assistant_message": t.assistant_message,
                "plan": _safe_json_loads(t.plan_json),
                "created_at": t.created_at,
                "audit_logs": logs_by_trace.get(t.id, []),
            }
        )

    return {"session_id": session_id, "traces": out_traces}
