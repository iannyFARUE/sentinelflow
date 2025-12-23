from __future__ import annotations

import json
import time
from pathlib import Path
import httpx


BASE_URL = "http://127.0.0.1:8000"


def run():
    data_path = Path(__file__).parent / "dataset.jsonl"
    cases = [json.loads(line) for line in data_path.read_text().splitlines() if line.strip()]

    results = []
    with httpx.Client(timeout=30.0) as client:
        for c in cases:
            payload = {"session_id": c["session_id"], "user_id": c.get("user_id"), "message": c["message"]}
            t0 = time.time()
            r = client.post(f"{BASE_URL}/chat", json=payload)
            dt = time.time() - t0
            out = r.json()

            results.append(
                {
                    "case_id": c["case_id"],
                    "ok_http": r.status_code == 200,
                    "latency_s": dt,
                    "needs_confirmation": out.get("needs_confirmation", False),
                    "message": out.get("message", ""),
                }
            )

    print(json.dumps({"n": len(results), "results": results}, indent=2))


if __name__ == "__main__":
    run()
