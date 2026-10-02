"""Scores the rule baselines on items/items.json -> results/baselines.md"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scoring.baselines import BASELINES, run_baseline  # noqa: E402
from scoring.score import aggregate  # noqa: E402

items = json.loads((ROOT / "items" / "items.json").read_text(encoding="utf-8"))["items"]
lines = ["| Baseline | Slice | no_label acc. | Paired direct | Paired report | Wrong label caught (direct) | Correct label accepted (direct) |",
         "|---|---|---|---|---|---|---|"]
for name in BASELINES:
    used, scored = run_baseline(name, items)
    a = aggregate(used, scored)
    for slc in ("real", "synthetic"):
        r = a[slc]
        nl = f'{r["no_label"]["accuracy"]}% ({r["no_label"]["pass"]}/{r["no_label"]["n"]})' if r["no_label"]["n"] else "n/a"
        pd, pr = r["paired_direct"], r["paired_report"]
        lines.append(f'| {name} | {slc} | {nl} | {pd["paired_score"]}% ({pd["pass"]}/{pd["stations"]}) | '
                     f'{pr["paired_score"]}% ({pr["pass"]}/{pr["stations"]}) | {pd["wrong_label_caught"]}% | {pd["correct_label_accepted"]}% |')
out = "\n".join(lines)
(ROOT / "results" / "baselines.md").write_text(out + "\n", encoding="utf-8")
print(out)
