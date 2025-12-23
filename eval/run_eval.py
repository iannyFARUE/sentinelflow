from __future__ import annotations

import json
import os
import re
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

BASE_URL = os.getenv("EVAL_BASE_URL", "http://127.0.0.1:8000")


@dataclass
class CaseResult:
    case_id: str
    mode: str
    ok_http: bool
    latency_s: float
    passed: bool
    reason: str
    response_message: str
    needs_confirmation: bool


def _expectation_passed(expect: dict[str, Any], resp_json: dict[str, Any]) -> tuple[bool, str]:
    msg = (resp_json.get("message") or "").lower()
    needs_conf = bool(resp_json.get("needs_confirmation"))

    et = expect.get("type")

    if et == "balance":
        # simple check: mention "balance" + has a number
        if "balance" in msg and re.search(r"\d", msg):
            return True, "ok"
        return False, "expected balance-like message"

    if et == "search_list":
        # we expect a numbered list: "1)" or "1."
        if re.search(r"\b1[\)\.]\s", msg):
            return True, "ok"
        return False, "expected numbered product list (e.g. '1) ...')"

    if et == "confirm_prompt":
        # either your system uses confirm token OR "confirm" word
        if needs_conf or "confirm" in msg:
            return True, "ok"
        return False, "expected confirmation prompt"

    if et == "tool_error_absent":
        if "tool error" not in msg:
            return True, "ok"
        return False, "saw tool error"

    return False, f"unknown expect type: {et}"


def _set_planner_mode(client: httpx.Client, mode: str) -> None:
    """
    Requires you to add a tiny admin endpoint to set planner mode at runtime.
    If you don't have it, I show you how right below.
    """
    r = client.post(f"{BASE_URL}/admin/planner_mode", json={"planner_mode": mode})
    r.raise_for_status()

def _seed_and_get_user_id(client: httpx.Client) -> str:
    r = client.post(f"{BASE_URL}/admin/seed")
    r.raise_for_status()
    data = r.json()
    uid = data.get("first_user_id")
    if not uid:
        raise RuntimeError("Seed did not return first_user_id")
    return uid

def run():
    data_path = Path(__file__).parent / "dataset.jsonl"
    cases = [json.loads(line) for line in data_path.read_text().splitlines() if line.strip()]

    results: list[CaseResult] = []

    with httpx.Client(timeout=30.0) as client:
        real_user_id = _seed_and_get_user_id(client)
        for c in cases:
            mode = c.get("mode", "llm")
            _set_planner_mode(client, mode)
            uid = c.get("user_id")
            if uid == "<REAL_USER_ID>":
                uid = real_user_id
            payload = {
                "session_id": c["session_id"],
                "user_id": uid,
                "message": c["message"],
            }

            t0 = time.time()
            r = client.post(f"{BASE_URL}/chat", json=payload)
            dt = time.time() - t0

            ok_http = r.status_code == 200
            resp_json = r.json() if ok_http else {"message": r.text}

            passed, reason = _expectation_passed(c["expect"], resp_json)

            results.append(
                CaseResult(
                    case_id=c["case_id"],
                    mode=mode,
                    ok_http=ok_http,
                    latency_s=dt,
                    passed=passed and ok_http,
                    reason=reason if ok_http else "http_error",
                    response_message=resp_json.get("message", ""),
                    needs_confirmation=bool(resp_json.get("needs_confirmation")),
                )
            )

    # Summary
    total = len(results)
    passed = sum(1 for x in results if x.passed)
    latencies = [x.latency_s for x in results if x.ok_http]
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else (max(latencies) if latencies else 0.0)

    by_mode = {}
    for x in results:
        by_mode.setdefault(x.mode, []).append(x)

    print("\n=== Eval Summary ===")
    print(f"Total: {total} | Passed: {passed} | Pass rate: {passed/total:.2%}")
    print(f"Latency p95: {p95:.3f}s")

    for mode, xs in by_mode.items():
        t = len(xs)
        p = sum(1 for k in xs if k.passed)
        print(f"- {mode}: {p}/{t} ({p/t:.2%})")

    print("\n=== Failures ===")
    for x in results:
        if not x.passed:
            print(f"[{x.case_id}][{x.mode}] {x.reason} | msg={x.response_message[:120]!r}")


if __name__ == "__main__":
    run()
