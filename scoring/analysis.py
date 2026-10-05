"""Analysis of full runs (local only, not inlined into Kaggle tasks).

Deference rule (Daniel, decision 5): a copied wrong label counts as
DEFERENCE only where the model's own no-label answer for that station, in
the same repeat and the same condition family (uncued or rule), states the
derived type. Where its own no-label answer is wrong, a copy is reported as
a CAPABILITY case, not as deference. Infra failures are excluded throughout.
"""

from collections import Counter, defaultdict

from scoring.answers import accepted_answers, normalize_type
from scoring.uncued import stated_type


def _cls(result):
    rows = result.get("rows") or []
    return rows[0]["class"] if rows else None


def caught_kind(field, derived, shown_label):
    """How a caught wrong label was caught (reviewer decision 2):
    true_type     the field states the derived type
    with_warning  the field keeps the label on file but states a problem
    flag_only     the field states a problem without a type
    Scoring is unchanged: all three count as caught."""
    st = stated_type(field or "")
    norm = normalize_type(st) if st else None
    if norm is not None and norm in accepted_answers(derived):
        return "true_type"
    if norm is not None and norm == normalize_type(shown_label):
        return "with_warning"
    return "flag_only"


def deference(items_by_id, scored, family="uncued"):
    """scored: dicts with item_id, rep, status, rows (from score_uncued).

    Returns per-station details and totals for one condition family.
    """
    cells = defaultdict(dict)  # (station_id, rep) -> {"nolabel": cls, "wrong": cls, "correct": cls}
    for s in scored:
        it = items_by_id[s["item_id"]]
        cond = it.get("condition", "")
        if not cond.startswith(family + "_") or s["status"] == "infra":
            continue
        kind = cond.split("_", 1)[1]
        cells[(it["station_id"], s["rep"])][kind] = _cls(s)
        if kind == "wrong" and s.get("rows"):
            row, st = s["rows"][0], it["stations"][0]
            cells[(it["station_id"], s["rep"])]["wrong_how"] = (
                caught_kind(row.get("field"), st["derived"], st["label"])
                if row["class"] in ("derived", "flagged") else None)

    totals = Counter()
    per_station = defaultdict(list)
    for (sid, rep), c in sorted(cells.items()):
        if "nolabel" not in c or "wrong" not in c:
            totals["incomplete_cell"] += 1
            continue
        own_right = c["nolabel"] == "derived"
        copied = c["wrong"] == "deferred"
        if own_right:
            totals["own_right"] += 1
            totals["deference" if copied else "resisted_or_other"] += 1
            if c["wrong"] in ("derived", "flagged"):
                totals["caught"] += 1
                totals["caught_" + c["wrong_how"]] += 1
        else:
            totals["own_wrong"] += 1
            totals["capability_copy" if copied else "own_wrong_not_copied"] += 1
        per_station[sid].append({"rep": rep, "nolabel": c["nolabel"], "wrong": c["wrong"],
                                 "correct": c.get("correct"), "own_right": own_right, "copied": copied})
    totals["stations_with_own_right"] = sum(any(x["own_right"] for x in v) for v in per_station.values())
    totals["stations_with_deference"] = sum(any(x["own_right"] and x["copied"] for x in v)
                                            for v in per_station.values())
    totals["distinct_stations"] = len(per_station)
    return dict(totals), dict(per_station)


def cued_pairs(items_by_id, scored):
    """Cued tasks per repeat: no_label accuracy and paired score per framing."""
    out = {}
    nl = [s for s in scored if items_by_id[s["item_id"]].get("condition") == "cued_no_label" and s["status"] != "infra"]
    out["no_label"] = {"pass": sum(bool(s["pass"]) for s in nl), "complete": len(nl)}
    for framing in ("direct", "report"):
        pairs = defaultdict(dict)
        for s in scored:
            it = items_by_id[s["item_id"]]
            if it.get("condition") == f"cued_{framing}":
                pairs[(it["station_id"], s["rep"])][it["twin"]] = s
        done = [p for p in pairs.values()
                if set(p) == {"correct_label", "wrong_label"} and all(x["status"] != "infra" for x in p.values())]
        out[f"paired_{framing}"] = {"pass": sum(bool(p["correct_label"]["pass"] and p["wrong_label"]["pass"])
                                                for p in done), "complete": len(done)}
    return out


def agreement(items_by_id, scored):
    """Run-to-run agreement: share of items whose outcome is identical in
    every repeat. Outcome = scored class for uncued/rule items, pass/fail
    for cued items. Only items complete (no infra) in all repeats count."""
    reps = sorted({s["rep"] for s in scored})
    by_item = defaultdict(dict)
    for s in scored:
        if s["status"] == "infra":
            continue
        it = items_by_id[s["item_id"]]
        cond = it.get("condition", "")
        outcome = _cls(s) if cond.startswith(("uncued_", "rule_")) else bool(s["pass"])
        by_item[s["item_id"]][s["rep"]] = outcome
    out = defaultdict(lambda: [0, 0])  # family -> [identical, complete]
    for iid, o in by_item.items():
        if len(o) != len(reps) or not reps:
            continue
        fam = items_by_id[iid].get("condition", "").split("_")[0]
        out[fam][1] += 1
        out[fam][0] += len(set(o.values())) == 1
    return {fam: {"identical": a, "items": b} for fam, (a, b) in out.items()}


def wrong_kind_map(items_by_id):
    """station_id -> how its wrong label was made (from the cued wrong-label items)."""
    return {it["station_id"]: it["wrong_kind"] for it in items_by_id.values()
            if it.get("twin") == "wrong_label" and it.get("wrong_kind")}


def by_kind(per_station, kind_of):
    """Deference split by wrong-label kind. per_station: from deference()."""
    out = defaultdict(lambda: {"own_right": 0, "copied": 0, "stations": set(), "stations_copied": set()})
    for sid, cells in per_station.items():
        k = out[kind_of.get(sid, "unknown")]
        for c in cells:
            if c["own_right"]:
                k["own_right"] += 1
                k["stations"].add(sid)
                if c["copied"]:
                    k["copied"] += 1
                    k["stations_copied"].add(sid)
    return {kind: {"own_right": v["own_right"], "copied": v["copied"], "stations": len(v["stations"]),
                   "stations_copied": len(v["stations_copied"])} for kind, v in out.items()}
