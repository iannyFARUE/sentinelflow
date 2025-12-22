from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel

from app.agent.types import AgentPlan
from app.core.config import settings
from app.agent.planner import simple_planner

logger = logging.getLogger(__name__)


# ---------- Tool specs for the model (descriptions only; execution happens in our system) ----------
def tool_catalog_for_prompt() -> str:
    return """You can plan using ONLY these tools:

1) check_balance
- args: { "user_id": "<string>" }
- purpose: returns user balance and currency

2) execute_purchase
- args: { "user_id": "<string>", "product_id": "<string>", "qty": <int> }
- purpose: purchase a product (NOTE: system will require confirmation before execution)

3) update_database
- args: { "table": "<users|accounts|products|transactions>", "key": "<string>", "value": "<string>" }
- purpose: record/update a safe backend record (no raw SQL)
"""


# ---------- Prompt ----------
def build_planner_prompt(user_message: str, user_id: str | None) -> str:
    return f"""You are the planning module for SentinelFlow, a SAFE agent-based system.
Your job: output a JSON object that matches the AgentPlan schema EXACTLY.

Rules:
- Only plan tool calls using the provided tool catalog.
- Do NOT execute anything. Only plan.
- Purchases are always high risk and MUST set requires_confirmation=true.
- If user_id is missing and a tool needs it, ask the user for user_id instead of guessing.
- If product_id is missing for purchase, ask the user to provide product_id.
- Keep steps minimal and correct.

TOOL CATALOG:
{tool_catalog_for_prompt()}

Context:
- user_id (may be null): {user_id}

User message:
{user_message}
"""


# ---------- OpenAI call with Structured Outputs ----------
def llm_plan(user_message: str, user_id: str | None) -> AgentPlan:
    """
    Returns a validated AgentPlan.
    If anything goes wrong, falls back to simple_planner().
    """
    if settings.planner_mode.lower() != "llm":
        return simple_planner(user_message, user_id=user_id)

    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY missing; falling back to heuristic planner.")
        return simple_planner(user_message, user_id=user_id)

    try:
        # OpenAI SDK usage (Responses API)
        from openai import OpenAI  # imported lazily so tests don't require it
        client = OpenAI(api_key=settings.openai_api_key)

        prompt = build_planner_prompt(user_message, user_id)

        # Structured Outputs: request schema-adherent JSON for AgentPlan
        # (Structured Outputs is recommended over plain JSON mode) :contentReference[oaicite:3]{index=3}
        resp = client.responses.create(
            model=settings.openai_model,
            input=prompt,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "agent_plan",
                    "schema": AgentPlan.model_json_schema(),
                    "strict": True,
                },
            },
        )

        # Responses API provides output_text convenience for text; here we expect JSON text
        raw = getattr(resp, "output_text", None)
        if not raw:
            # fallback: try to find JSON inside resp object
            raw = json.dumps(resp.model_dump(), ensure_ascii=False)

        # First parse JSON, then validate against Pydantic schema
        data: Any
        try:
            data = json.loads(raw)
        except Exception:
            # Sometimes output may include whitespace; attempt extraction
            raw_str = str(raw).strip()
            data = json.loads(raw_str)

        return AgentPlan.model_validate(data)

    except Exception as e:
        logger.exception("LLM planner failed; falling back to heuristic. Error=%s", e)
        return simple_planner(user_message, user_id=user_id)
