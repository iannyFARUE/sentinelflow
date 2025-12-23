from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


class PlannerModeIn(BaseModel):
    planner_mode: str  # "llm" or "heuristic"


@router.post("/planner_mode")
def set_planner_mode(body: PlannerModeIn):
    mode = body.planner_mode.lower().strip()
    if mode not in {"llm", "heuristic"}:
        return {"ok": False, "error": "planner_mode must be 'llm' or 'heuristic'"}
    settings.planner_mode = mode
    return {"ok": True, "planner_mode": settings.planner_mode}
