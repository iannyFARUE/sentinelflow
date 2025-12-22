from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models import Trace


@dataclass
class PendingConfirmation:
    confirmation_token: str
    tool_name: str
    tool_args: dict


def save_pending_confirmation(db: Session, trace_id: str, pending: PendingConfirmation) -> None:
    tr = db.get(Trace, trace_id)
    if not tr:
        return
    tr.plan_json = json.dumps({"pending_confirmation": pending.__dict__}, ensure_ascii=False)
    db.commit()


def load_pending_confirmation(db: Session, trace_id: str) -> PendingConfirmation | None:
    tr = db.get(Trace, trace_id)
    if not tr or not tr.plan_json:
        return None
    try:
        payload = json.loads(tr.plan_json)
        pc = payload.get("pending_confirmation")
        if not pc:
            return None
        return PendingConfirmation(**pc)
    except Exception:
        return None
