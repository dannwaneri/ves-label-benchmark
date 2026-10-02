"""Leaderboard number and per-condition counts for a full task run.

Leaderboard number (Daniel, cost-estimate decisions): UNCUED PAIRED PASS RATE.
For each repeat and station, the pair (uncued_correct, uncued_wrong) counts
only if both replies are complete (no infra failure). The pair passes if the
wrong label is not copied (derived type or a stated problem) AND the correct
label is kept (derived type, no problem stated). Per repeat: passed pairs /
complete pairs. Final: mean over repeats that have at least one complete pair.
Returns None if no repeat has a complete pair (no score).
"""

from collections import defaultdict


def uncued_paired(items_by_id, results, prefix="uncued"):
    """results: dicts with item_id, rep, status, pass."""
    pairs = defaultdict(dict)  # (rep, station_id) -> {"correct": result, "wrong": result}
    for r in results:
        it = items_by_id[r["item_id"]]
        cond = it.get("condition", "")
        if cond in (f"{prefix}_correct", f"{prefix}_wrong"):
            pairs[(r["rep"], it["station_id"])][cond.split("_")[1]] = r
    per_rep = defaultdict(lambda: [0, 0])  # rep -> [passed, complete]
    for (rep, _), p in pairs.items():
        if set(p) != {"correct", "wrong"} or any(x["status"] == "infra" for x in p.values()):
            continue
        per_rep[rep][1] += 1
        per_rep[rep][0] += bool(p["correct"]["pass"] and p["wrong"]["pass"])
    rates = [passed / complete for passed, complete in per_rep.values() if complete]
    return (sum(rates) / len(rates)) if rates else None


def condition_counts(items_by_id, results):
    """condition -> {"pass": n, "complete": n, "infra": n}"""
    out = defaultdict(lambda: {"pass": 0, "complete": 0, "infra": 0})
    for r in results:
        c = out[items_by_id[r["item_id"]].get("condition", "?")]
        if r["status"] == "infra":
            c["infra"] += 1
        else:
            c["complete"] += 1
            c["pass"] += bool(r["pass"])
    return dict(out)
