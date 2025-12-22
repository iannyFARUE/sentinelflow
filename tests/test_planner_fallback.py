from app.agent.llm_planner import llm_plan
from app.core.config import settings


def test_llm_planner_falls_back_without_key(monkeypatch):
    monkeypatch.setattr(settings, "planner_mode", "llm")
    monkeypatch.setattr(settings, "openai_api_key", None)

    plan = llm_plan("what is my balance", user_id="u123")
    assert plan.intent.value in {"check_balance", "unknown"}  # heuristic decides
    assert len(plan.steps) > 0
