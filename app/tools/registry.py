from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Any

from sqlalchemy.orm import Session

from app.db.models import AuditLog, ToolCallStatus


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    output: dict | None = None
    error: str | None = None


ToolFn = Callable[[Session, dict], ToolResult]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolFn] = {}

    def register(self, name: str, fn: ToolFn) -> None:
        self._tools[name] = fn

    def get(self, name: str) -> ToolFn:
        if name not in self._tools:
            raise KeyError(f"Tool not registered: {name}")
        return self._tools[name]

    def run_with_audit(self, *, db: Session, trace_id: str, tool_name: str, args: dict) -> ToolResult:
        fn = self.get(tool_name)
        input_json = json.dumps(args, ensure_ascii=False)
        try:
            result = fn(db, args)
            status = ToolCallStatus.ok if result.ok else ToolCallStatus.error
            db.add(
                AuditLog(
                    trace_id=trace_id,
                    tool_name=tool_name,
                    status=status,
                    input_json=input_json,
                    output_json=json.dumps(result.output, ensure_ascii=False) if result.output else None,
                    error_message=result.error,
                )
            )
            db.commit()
            return result
        except Exception as e:  # safety net: audit unexpected exceptions
            db.add(
                AuditLog(
                    trace_id=trace_id,
                    tool_name=tool_name,
                    status=ToolCallStatus.error,
                    input_json=input_json,
                    output_json=None,
                    error_message=str(e),
                )
            )
            db.commit()
            return ToolResult(ok=False, output=None, error=str(e))
