"""Tools-only evaluation of the question bank (no language model).

For each question in eval/questions.yaml, run the tool call a good assistant would make and check
whether an expected place is among the top 5 results. Questions marked expect_unknown are listed
with their data gap: the assistant must answer "not known" there.

Output: eval/results/tools_baseline.md (and a one-line summary on stdout).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from atlas.assistant.tools import TOOLS

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "eval/questions.yaml"
OUT = ROOT / "eval/results/tools_baseline.md"


def names(result) -> list[str]:
    if result is None:
        return []
    if isinstance(result, dict):  # get_place
        return [result["name"]]
    return [r.get("place") or r.get("name") for r in result]


def main() -> None:
    qs = yaml.safe_load(QUESTIONS.read_text())
    rows, hits, answerable = [], 0, 0
    for q in qs:
        call = q["call"]
        result = TOOLS[call["tool"]](**call["args"])
        if q.get("expect_fields"):  # area tools: check numbers instead of names
            answerable += 1
            ok = all(
                (len(result.get(k) or []) if isinstance(result.get(k), list) else (result.get(k) or 0))
                >= need
                for k, need in q["expect_fields"].items()
            )
            hits += ok
            top = [
                f"{k}={result.get(k) if not isinstance(result.get(k), list) else len(result[k])}"
                for k in q["expect_fields"]
            ]
            rows.append((q, "hit" if ok else "MISS", top))
            continue
        got = names(result)
        top = list(dict.fromkeys(got))[:5]
        if q.get("expect_unknown"):
            verdict = "unknown (gap)"
        else:
            answerable += 1
            ok = any(any(e == n or e in n for n in top) for e in q["expect_any"])
            hits += ok
            verdict = "hit" if ok else "MISS"
        rows.append((q, verdict, top))
    rate = hits / answerable if answerable else 0
    lines = [
        "# Question bank: tools-only baseline",
        "",
        f"Run {date.today().isoformat()} with `scripts/eval_tools.py` (no language model). "
        f"**Hit rate at 5: {hits}/{answerable} = {rate:.0%}** of answerable questions; "
        f"{len(qs) - answerable} questions need data we do not have (listed below).",
        "",
        "Caveat: the expected places were written after looking at our data, so this is a regression "
        "baseline (it catches breakage when data or tools change), not an independent quality score. "
        "A real score needs expected answers written by people who know these places.",
        "",
        "| id | category | verdict | top results |",
        "|---|---|---|---|",
    ]
    for q, verdict, top in rows:
        lines.append(f"| {q['id']} | {q['category']} | {verdict} | {'; '.join(top) or '(none)'} |")
    lines += ["", '## Data gaps (the assistant must say "not known")', ""]
    lines += [f"- **{q['question']}** {q['gap']}" for q, v, _ in rows if v.startswith("unknown")]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print(f"hit@5 {hits}/{answerable} ({rate:.0%}); {len(qs) - answerable} gaps -> {OUT.relative_to(ROOT)}")
    for q, verdict, top in rows:
        if verdict == "MISS":
            print(f"  MISS {q['id']}: got {top}")


if __name__ == "__main__":
    main()
