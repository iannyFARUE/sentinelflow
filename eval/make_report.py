from __future__ import annotations

import json
from pathlib import Path

def load(p: str) -> dict:
    return json.loads(Path(p).read_text())

def main():
    llm = load("eval_report_llm.json")
    heu = load("eval_report_heuristic.json")

    lines = []
    lines.append("# Evaluation Report\n")
    lines.append("## Summary\n")
    lines.append(f"- LLM pass rate: **{llm['pass_rate']:.2%}** (p95 latency: {llm['latency_p95_s']})")
    lines.append(f"- Heuristic pass rate: **{heu['pass_rate']:.2%}** (p95 latency: {heu['latency_p95_s']})\n")

    def failures(rep: dict):
        out = []
        for r in rep["results"]:
            if not r["ok"]:
                out.append(r)
        return out

    lines.append("## Failures (LLM)\n")
    for f in failures(llm):
        lines.append(f"- {f['case_id']}")
        for t in f["turns"]:
            if t["why"]:
                lines.append(f"  - turn {t['turn']}: {t['why']} | response='{t['response_message'][:120]}'")
    if not failures(llm):
        lines.append("- None ✅")

    lines.append("\n## Failures (Heuristic)\n")
    for f in failures(heu):
        lines.append(f"- {f['case_id']}")
        for t in f["turns"]:
            if t["why"]:
                lines.append(f"  - turn {t['turn']}: {t['why']} | response='{t['response_message'][:120]}'")
    if not failures(heu):
        lines.append("- None ✅")

    Path("EVAL_REPORT.md").write_text("\n".join(lines))

if __name__ == "__main__":
    main()
