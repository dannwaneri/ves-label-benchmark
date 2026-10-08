"""Exploratory paired tests (not preregistered; the preregistration claims no
significance tests). Exact McNemar test, paired by station, repeat 1 only so
no question counts twice.

Comparisons, per model and slice, over stations whose own no-label answer
was right in repeat 1 (in each family compared):
  uncued vs rule    did the site note repeat the wrong label?
  uncued vs direct  site note repeated it vs direct question accepted it

Usage: python scripts/stats.py  -> results/stats.md
"""

import glob
import json
import sys
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scoring.dispatch import score_any  # noqa: E402

ITEMS = {it["id"]: it for it in json.loads((ROOT / "items" / "full_items.json").read_text(encoding="utf-8"))["items"]}


def mcnemar_exact(b, c):
    """Two-sided exact McNemar p-value from discordant counts b and c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, p)


def outcomes(raw_file, rep=1):
    """station_id -> {condition: outcome} for one repeat. Outcome: class for
    uncued/rule items; for cued_direct wrong twins, 'accepted' or 'rejected'."""
    out = {}
    for line in open(raw_file, encoding="utf-8"):
        r = json.loads(line)
        if r["rep"] != rep:
            continue
        it = ITEMS[r["item_id"]]
        s = score_any(it, r["reply"])
        if s["status"] == "infra":
            continue
        cond = it["condition"]
        if cond.startswith(("uncued_", "rule_")):
            out.setdefault(it["station_id"], {})[cond] = s["rows"][0]["class"]
        elif cond == "cued_direct" and it["twin"] == "wrong_label":
            out.setdefault(it["station_id"], {})[cond] = "accepted" if s["value"] is True else "rejected"
    return out


def compare(o, a_cond, a_fail, b_cond, b_fail, need):
    """Paired 2x2 over stations meeting `need`; returns (n, a_only, b_only, both, p)."""
    a_only = b_only = both = n = 0
    for sid, c in o.items():
        if not need(c) or a_cond not in c or b_cond not in c:
            continue
        n += 1
        fa, fb = c[a_cond] == a_fail, c[b_cond] == b_fail
        both += fa and fb
        a_only += fa and not fb
        b_only += fb and not fa
    return n, a_only, b_only, both, mcnemar_exact(a_only, b_only)


def main():
    L = ["# Exploratory paired tests (not preregistered)", "",
         "Exact McNemar test, paired by station, repeat 1 only. Only stations where the model's own",
         "no-label answer was right (in each family compared). A 'repeat' = the wrong label written in",
         "the Curve type field; 'accepted' = the direct question answered that the wrong label is correct.", "",
         "| Slice | Model | Comparison | Stations | Repeated in A only | Repeated in B only | Both | Exact p |",
         "|---|---|---|---|---|---|---|---|"]
    for f in sorted(glob.glob(str(ROOT / "runs" / "full" / "*" / "*" / "*" / "*" / "raw_outputs.jsonl"))):
        parts = Path(f).parts
        task, model = parts[-5], parts[-3]
        o = outcomes(f)
        right_u = lambda c: c.get("uncued_nolabel") == "derived"
        right_both = lambda c: right_u(c) and c.get("rule_nolabel") == "derived"
        for name, args in [
            ("A = site note, B = site note + rule", ("uncued_wrong", "deferred", "rule_wrong", "deferred", right_both)),
            ("A = site note, B = direct question", ("uncued_wrong", "deferred", "cued_direct", "accepted", right_u)),
        ]:
            n, a, b, both, p = compare(o, *args)
            L.append(f"| {task.replace('ves-', '')} | {model} | {name} | {n} | {a} | {b} | {both} | "
                     f"{'n/a' if n == 0 else f'{p:.2g}'} |")
    L += ["", "Stations are few (8-19 per slice), so p-values are rough. Repeats 2-3 are not used here."]
    out = "\n".join(L) + "\n"
    (ROOT / "results" / "stats.md").write_text(out, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
