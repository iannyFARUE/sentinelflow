from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas.tool_io import UpdateDatabaseIn, UpdateDatabaseOut
from app.tools.registry import ToolResult


def update_database_tool(db: Session, args: dict) -> ToolResult:
    # demo-safe generic: validate but do not allow arbitrary SQL
    inp = UpdateDatabaseIn.model_validate(args)

    # For portfolio: restrict to known, safe ops
    allowed_tables = {"users", "accounts", "products", "transactions"}
    if inp.table not in allowed_tables:
        return ToolResult(ok=False, error="table_not_allowed")

    # In a real version you'd implement specific updates. Here we just record intent.
    out = UpdateDatabaseOut(status=f"queued_update:{inp.table}:{inp.key}")
    return ToolResult(ok=True, output=out.model_dump(mode="json"))
