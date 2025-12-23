from __future__ import annotations

import json
import logging

from pydantic import BaseModel

from app.agent.types import AgentPlan
from app.core.config import settings
from app.agent.planner import simple_planner
from copy import deepcopy
from typing import Any
import re


logger = logging.getLogger(__name__)


# # # ---------- Tool specs for the model (descriptions only; execution happens in our system) ----------
# # def tool_catalog_for_prompt() -> str:
# #     return """You can plan using ONLY these tools:

# # 1) check_balance
# # - args: { "user_id": "<string>" }
# # - purpose: returns user balance and currency

# # 2) execute_purchase
# # - args: { "user_id": "<string>", "product_id": "<string>", "qty": <int> }
# # - purpose: purchase a product (NOTE: system will require confirmation before execution)

# # 3) update_database
# # - args: { "table": "<users|accounts|products|transactions>", "key": "<string>", "value": "<string>" }
# # - purpose: record/update a safe backend record (no raw SQL)

# # 4) search_products
# # - args: {"query": "<string>", "limit": <int>}
# # - purpose: searches available products by name and returns a list of matching items
# # - use when: the user refers to a product by name (e.g., "keyboard", "monitor") and no product_id is known 
# # """


# # # ---------- Prompt ----------
# # def build_planner_prompt(user_message: str, user_id: str | None) -> str:
# #     return f"""You are the planning module for SentinelFlow, a SAFE agent-based system.
# # Your job: output a JSON object that matches the AgentPlan schema EXACTLY.

# # Rules:
# # - Only plan tool calls using the provided tool catalog.
# # - Do NOT execute anything. Only plan.
# # - Purchases are always high risk and MUST set requires_confirmation=true.
# # - If user asks to buy by name, call search_products first
# # - If user_id is missing and a tool needs it, ask the user for user_id instead of guessing.
# # - If product_id is missing for purchase, ask the user to provide product_id.
# # - Keep steps minimal and correct.

# # TOOL CATALOG:
# # {tool_catalog_for_prompt()}

# # Context:
# # - user_id (may be null): {user_id}

# # User message:
# # {user_message}
# # """


# # # ---------- OpenAI call with Structured Outputs ----------
# # def llm_plan(user_message: str, user_id: str | None) -> AgentPlan:
# #     """
# #     Returns a validated AgentPlan.
# #     If anything goes wrong, falls back to simple_planner().
# #     """
# #     if settings.planner_mode.lower() != "llm":
# #         return simple_planner(user_message, user_id=user_id)

# #     if not settings.openai_api_key:
# #         logger.warning("OPENAI_API_KEY missing; falling back to heuristic planner.")
# #         return simple_planner(user_message, user_id=user_id)

# #     try:
# #         # OpenAI SDK usage (Responses API)
# #         from openai import OpenAI  # imported lazily so tests don't require it
# #         client = OpenAI(api_key=settings.openai_api_key)

# #         prompt = build_planner_prompt(user_message, user_id)

# #         # Structured Outputs: request schema-adherent JSON for AgentPlan
# #         # (Structured Outputs is recommended over plain JSON mode) :contentReference[oaicite:3]{index=3}
# #         resp = client.responses.create(
# #             model=settings.openai_model,
# #             input=prompt,
# #             response_format={
# #                 "type": "json_schema",
# #                 "json_schema": {
# #                     "name": "agent_plan",
# #                     "schema": AgentPlan.model_json_schema(),
# #                     "strict": True,
# #                 },
# #             },
# #         )

# #         # Responses API provides output_text convenience for text; here we expect JSON text
# #         raw = getattr(resp, "output_text", None)
# #         if not raw:
# #             # fallback: try to find JSON inside resp object
# #             raw = json.dumps(resp.model_dump(), ensure_ascii=False)

# #         # First parse JSON, then validate against Pydantic schema
# #         data: Any
# #         try:
# #             data = json.loads(raw)
# #         except Exception:
# #             # Sometimes output may include whitespace; attempt extraction
# #             raw_str = str(raw).strip()
# #             data = json.loads(raw_str)

# #         return AgentPlan.model_validate(data)

# #     except Exception as e:
# #         logger.exception("LLM planner failed; falling back to heuristic. Error=%s", e)
# #         return simple_planner(user_message, user_id=user_id)

# from __future__ import annotations

# import json
# import logging
# from typing import Any

# from app.agent.types import AgentPlan
# from app.agent.planner import simple_planner
# from app.core.config import settings

# logger = logging.getLogger(__name__)


# def tool_catalog_for_prompt() -> str:
#     return """You can plan using ONLY these tools:

# 1) check_balance
# - args: { "user_id": "<string>" }

# 2) search_products
# - args: { "query": "<string>", "limit": <int> }

# 3) execute_purchase
# - args: { "user_id": "<string>", "product_id": "<string>", "qty": <int> }

# 4) update_database
# - args: { "table": "<users|accounts|products|transactions>", "key": "<string>", "value": "<string>" }
# """

# def build_planner_prompt(user_message: str, user_id: str | None) -> dict:
#     """
#     Build a structured input block for Responses API with JSON Schema enforcement.
#     """
#     return {
#         "role": "user",
#         "content": [
#             {
#                 "type": "text",
#                 "text": f"""
# You are the planning module for SentinelFlow.

# Rules:
# - Output JSON that EXACTLY matches the AgentPlan schema.
# - Do NOT execute tools.
# - Purchases MUST set requires_confirmation=true.
# - If user_id is missing and required, ask for it.
# - If product_id is missing for purchase, call search_products first.

# USER_ID: {user_id}

# TOOL CATALOG:
# {tool_catalog_for_prompt()}

# USER MESSAGE:
# {user_message}
# """.strip(),
#             },
#             {
#                 "type": "json_schema",
#                 "name": "agent_plan",
#                 "schema": AgentPlan.model_json_schema(),
#                 "strict": True,
#             },
#         ],
#     }


# def llm_plan(user_message: str, user_id: str | None) -> AgentPlan:
#     """
#     LLM planner using OpenAI Responses API + Structured Outputs.
#     Falls back safely to heuristic planner on ANY failure.
#     """
#     if settings.planner_mode.lower() != "llm":
#         return simple_planner(user_message, user_id=user_id)

#     if not settings.openai_api_key:
#         logger.warning("OPENAI_API_KEY missing; using heuristic planner.")
#         return simple_planner(user_message, user_id=user_id)

#     try:
#         from openai import OpenAI

#         client = OpenAI(api_key=settings.openai_api_key)

#         resp = client.responses.create(
#             model=settings.openai_model,
#             input=[
#                 build_planner_prompt(user_message, user_id),
#             ],
#         )

#         # Extract structured output
#         # The SDK guarantees schema-valid JSON if strict=true
#         output = resp.output_parsed

#         if not output:
#             raise ValueError("No structured output returned by LLM planner")

#         return AgentPlan.model_validate(output)

#     except Exception as e:
#         logger.exception("LLM planner failed; falling back to heuristic. Error=%s", e)
#         return simple_planner(user_message, user_id=user_id)



def _allow_null(schema: dict) -> dict:
    """Wrap a schema to allow null values."""
    if schema.get("type") == "null":
        return schema
    if "anyOf" in schema and any(isinstance(s, dict) and s.get("type") == "null" for s in schema["anyOf"]):
        return schema
    return {"anyOf": [schema, {"type": "null"}]}


def _sanitize_refs_and_defaults(node: Any) -> Any:
    """
    OpenAI strict validator dislikes:
      - 'default' in schemas (especially alongside $ref)
      - any sibling keywords alongside '$ref'
    This recursively:
      - removes 'default' everywhere
      - if a dict has '$ref' and other keys, keeps only '$ref'
    """
    if isinstance(node, list):
        return [_sanitize_refs_and_defaults(x) for x in node]

    if not isinstance(node, dict):
        return node

    # Recurse first
    out = {}
    for k, v in node.items():
        if k == "default":
            continue
        out[k] = _sanitize_refs_and_defaults(v)

    # If $ref exists, it must be alone
    if "$ref" in out:
        return {"$ref": out["$ref"]}

    return out


def openai_strictify_json_schema(pydantic_schema: dict) -> dict:
    """
    Produce an OpenAI-Structured-Outputs-compatible strict JSON schema from Pydantic's schema.

    Enforces:
      1) additionalProperties: false on every object schema
      2) required: includes ALL keys in properties on every object schema
      3) fields that were optional in the original schema are made nullable (anyOf[..., null])
      4) removes 'default' everywhere and removes sibling keywords next to '$ref'
    """
    schema = deepcopy(pydantic_schema)

    # 1) Fix $ref + default and remove defaults everywhere
    schema = _sanitize_refs_and_defaults(schema)

    def walk(node: Any) -> Any:
        if isinstance(node, list):
            return [walk(x) for x in node]
        if not isinstance(node, dict):
            return node

        # Recurse first
        for k, v in list(node.items()):
            node[k] = walk(v)

        # Object schema detection
        is_object = node.get("type") == "object" or "properties" in node
        if is_object:
            props = node.get("properties") or {}
            original_required = set(node.get("required") or [])

            # OpenAI strict: required must include EVERY property key
            node["required"] = list(props.keys())

            # Any property not originally required must allow null
            for prop_name, prop_schema in list(props.items()):
                if prop_name not in original_required:
                    if isinstance(prop_schema, dict):
                        props[prop_name] = _allow_null(prop_schema)
                    else:
                        props[prop_name] = _allow_null({"type": "string"})

            node["properties"] = props
            node["additionalProperties"] = False

        return node

    return walk(schema)




def tool_catalog_for_prompt() -> str:
    return """You can plan using ONLY these tools:

1) check_balance
- args: { "user_id": "<string>" }

2) search_products
- args: { "query": "<string>", "limit": <int> }

3) execute_purchase
- args: { "user_id": "<string>", "product_id": "<string>", "qty": <int> }

4) update_database
- args: { "table": "<users|accounts|products|transactions>", "key": "<string>", "value": "<string>" }
"""


def build_planner_instructions(user_message: str, user_id: str | None) -> str:
    return f"""You are the planning module for SentinelFlow.

Return a JSON object that EXACTLY matches the AgentPlan schema.

Hard Rules (follow exactly):
- Do NOT execute tools. Only plan.
- Only plan tool calls from the tool catalog below.
- For search_products tool_call, arguments MUST include:
  - query: a non-empty string extracted from the user's request (e.g., "keyboard")
  - limit: integer (default 5)
- NEVER output an empty arguments object for any tool.
- If the user expresses intent to buy/purchase/order AND product_id is not explicitly provided:
  - You MUST add a tool_call step for search_products with arguments: {{"query": "<product name from user message>", "limit": 5}}
  - Then you MUST add an ask_user step asking the user to pick an option number (1-5) and qty if missing.
  - You MUST NOT ask the user for product_id directly in this case.
- Purchases MUST set requires_confirmation=true.
- If user_id is missing and required, ask for it (do not guess).
- If qty is missing, assume qty=1 in the tool_call arguments.
- If USER_ID is provided (not null), you MUST include it in arguments for any tool that requires user_id (check_balance, execute_purchase).
- NEVER output an empty arguments object for any tool.


USER_ID: {user_id}

TOOL CATALOG:
{tool_catalog_for_prompt()}

USER MESSAGE:
{user_message}
""".strip()




def _extract_json_object(text: str) -> dict[str, Any]:
    """
    Extract the first JSON object from a string.
    Handles cases where model returns extra text around JSON.
    """
    text = text.strip()

    # Fast path: whole string is JSON
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)

    # Otherwise, find the first {...} block (best effort)
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError("No JSON object found in model output.")
    return json.loads(m.group(0))


def llm_plan(user_message: str, user_id: str | None) -> AgentPlan:
    if settings.planner_mode.lower() != "llm":
        return simple_planner(user_message, user_id=user_id)

    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY missing; using heuristic planner.")
        return simple_planner(user_message, user_id=user_id)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)

        schema = openai_strictify_json_schema(AgentPlan.model_json_schema())

        response = client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": "You are a careful planner that outputs only schema-valid JSON."},
                {"role": "user", "content": build_planner_instructions(user_message, user_id)},
            ],
            # Strongly reduce formatting errors
            temperature=0,
            top_p=1,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "agent_plan",
                    "strict": True,
                    "schema": schema,
                }
            },
        )

        # 1) If SDK parsed it, use it
        parsed = getattr(response, "output_parsed", None)
        if parsed is not None:
            return AgentPlan.model_validate(parsed)

        # 2) Otherwise, parse JSON ourselves from output text
        # Prefer response.output_text if available
        raw_text = getattr(response, "output_text", None)
        if not raw_text:
            # fallback: read from response.output structure
            raw_text = response.output[0].content[0].text  # type: ignore[attr-defined]

        data = _extract_json_object(raw_text)
        return AgentPlan.model_validate(data)

    except Exception as e:
        logger.exception("LLM planner failed; falling back to heuristic. Error=%s", e)
        return simple_planner(user_message, user_id=user_id)
