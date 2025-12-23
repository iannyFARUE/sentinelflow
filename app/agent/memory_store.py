from __future__ import annotations

import json
from sqlalchemy.orm import Session
from app.db.models import SessionMemory


def get_memory(db: Session, session_id: str) -> dict:
    row = db.query(SessionMemory).filter(SessionMemory.session_id == session_id).one_or_none()
    if not row:
        return {}
    try:
        return json.loads(row.memory_json) or {}
    except Exception:
        return {}


def patch_memory(db: Session, session_id: str, patch: dict) -> dict:
    mem = get_memory(db, session_id)
    mem.update(patch)

    row = db.query(SessionMemory).filter(SessionMemory.session_id == session_id).one_or_none()
    if not row:
        row = SessionMemory(session_id=session_id, memory_json=json.dumps(mem, ensure_ascii=False))
        db.add(row)
    else:
        row.memory_json = json.dumps(mem, ensure_ascii=False)

    db.commit()
    return mem
