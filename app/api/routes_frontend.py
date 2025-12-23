from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.models import AuditLog, Trace, User
from app.schemas.api import AuditLogOut, SessionOut, TraceOut, UserOut

router = APIRouter(tags=["frontend"])


@router.get("/users", response_model=list[UserOut])
def list_users(
    limit: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.created_at.desc()).limit(limit).all()  # type: ignore[attr-defined]
    return [UserOut(id=u.id, full_name=u.full_name, email=u.email) for u in users]


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    # Get last trace per session_id
    subq = (
        db.query(
            Trace.session_id.label("session_id"),
            func.max(Trace.created_at).label("last_message_at"),
        )
        .group_by(Trace.session_id)
        .subquery()
    )

    rows = (
        db.query(Trace)
        .join(subq, (Trace.session_id == subq.c.session_id) & (Trace.created_at == subq.c.last_message_at))
        .order_by(Trace.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        SessionOut(
            session_id=t.session_id,
            last_message_at=t.created_at,
            last_user_message=t.user_message,
        )
        for t in rows
    ]


@router.get("/sessions/{session_id}/traces", response_model=list[TraceOut])
def get_session_traces(
    session_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    traces = (
        db.query(Trace)
        .filter(Trace.session_id == session_id)
        .order_by(Trace.created_at.asc())
        .limit(limit)
        .all()
    )

    out: list[TraceOut] = []
    for t in traces:
        plan_dict: dict[str, Any] | None = None
        if t.plan_json:
            try:
                plan_dict = json.loads(t.plan_json)
            except Exception:
                plan_dict = None

        out.append(
            TraceOut(
                id=t.id,
                session_id=t.session_id,
                user_message=t.user_message,
                assistant_message=t.assistant_message,
                created_at=t.created_at,
                plan_json=plan_dict,
            )
        )
    return out


@router.get("/traces/{trace_id}", response_model=TraceOut)
def get_trace(
    trace_id: str,
    db: Session = Depends(get_db),
):
    t = db.get(Trace, trace_id)
    if not t:
        # keep it simple; frontend can handle 404
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Trace not found")

    plan_dict: dict[str, Any] | None = None
    if t.plan_json:
        try:
            plan_dict = json.loads(t.plan_json)
        except Exception:
            plan_dict = None

    return TraceOut(
        id=t.id,
        session_id=t.session_id,
        user_message=t.user_message,
        assistant_message=t.assistant_message,
        created_at=t.created_at,
        plan_json=plan_dict,
    )


@router.get("/traces/{trace_id}/audit_logs", response_model=list[AuditLogOut])
def get_trace_audit_logs(
    trace_id: str,
    db: Session = Depends(get_db),
):
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.trace_id == trace_id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )

    return [
        AuditLogOut(
            id=l.id,
            trace_id=l.trace_id,
            tool_name=l.tool_name,
            status=str(l.status),
            input_json=l.input_json,
            output_json=l.output_json,
            error_message=l.error_message,
            created_at=l.created_at,
        )
        for l in logs
    ]
