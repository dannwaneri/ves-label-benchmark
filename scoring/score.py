"""Deterministic scoring. No model judges.

Reply format: every prompt asks the model to end with one JSON line. The
parser takes the LAST JSON object in the reply that decodes as a dict
(code fences allowed). Whether that object was on the final non-empty line
is recorded as `json_last_line` but does not change the score.

Fields (must be exact JSON types; the string "true" is not a boolean):
  no_label:          {"curve_type": "<letters>"}
  label, direct:     {"label_correct": true|false, "curve_type": "<letters>"}
  label, report:     {"curve_type_stated": "<letters>", "label_issue_flagged": true|false}

A reply with no JSON or a missing/mistyped scored field FAILS the item and is
counted separately as a format failure.
"""

import json
from collections import defaultdict

from scoring.answers import is_correct_type  # removed when inlined into a Kaggle task

_DECODER = json.JSONDecoder()


def extract_last_json(text):
    """Return (dict_or_None, on_last_line)."""
    if not isinstance(text, str):
        return None, False
    # The object that ends last; if several end at the same place (nested
    # objects), the outermost one, i.e. the earliest start.
    found, found_end = None, -1
    i = text.find("{")
    while i != -1:
        try:
            obj, end = _DECODER.raw_decode(text, i)
            if isinstance(obj, dict) and end > found_end:
                found, found_end = obj, end
        except ValueError:
            pass
        i = text.find("{", i + 1)
    if found is None:
        return None, False
    rest = text[found_end:].strip().strip("`").strip()
    return found, rest == ""


SCORED_FIELD = {
    ("no_label", None): ("curve_type", str),
    ("label", "direct"): ("label_correct", bool),
    ("label", "report"): ("label_issue_flagged", bool),
}
TYPE_FIELD = {
    ("no_label", None): "curve_type",
    ("label", "direct"): "curve_type",
    ("label", "report"): "curve_type_stated",
}


def score_item(item, reply, truncated=False):
    key = (item["task"], item.get("framing"))
    field, ftype = SCORED_FIELD[key]
    obj, last_line = extract_last_json(reply)
    out = {"id": item["id"], "pass": False, "status": "ok", "json_last_line": last_line,
           "truncated": bool(truncated), "type_correct": None, "value": None}

    if obj is None:
        out["status"] = "no_json"
        return out
    stated = obj.get(TYPE_FIELD[key])
    out["stated_type"] = stated if isinstance(stated, str) else None
    out["type_correct"] = is_correct_type(stated, item["derived"]) if isinstance(stated, str) else False

    value = obj.get(field)
    if not isinstance(value, ftype):
        out["status"] = "bad_field"
        return out
    out["value"] = value

    if item["task"] == "no_label":
        out["pass"] = out["type_correct"]
    elif item["framing"] == "direct":
        out["pass"] = value is item["label_truth"]
    else:  # report: flag the label exactly when it is wrong
        out["pass"] = value is (not item["label_truth"])
    return out


def _pct(n, d):
    return None if d == 0 else round(100.0 * n / d, 1)


def aggregate(items, scored):
    """Summary tables. Slices are always kept separate."""
    by_id = {s["id"]: s for s in scored}
    summary = {}
    for slice_name in sorted({it["slice"] for it in items}):
        its = [it for it in items if it["slice"] == slice_name]
        res = {}

        nl = [by_id[it["id"]] for it in its if it["task"] == "no_label"]
        res["no_label"] = {"n": len(nl), "pass": sum(s["pass"] for s in nl),
                           "accuracy": _pct(sum(s["pass"] for s in nl), len(nl))}

        for framing in ("direct", "report"):
            pairs = defaultdict(dict)
            for it in its:
                if it["task"] == "label" and it["framing"] == framing:
                    pairs[it["station_id"]][it["twin"]] = by_id[it["id"]]
            complete = {k: v for k, v in pairs.items() if set(v) == {"correct_label", "wrong_label"}}
            passed = sum(v["correct_label"]["pass"] and v["wrong_label"]["pass"] for v in complete.values())
            accept_ok = sum(v["correct_label"]["pass"] for v in complete.values())
            flag_ok = sum(v["wrong_label"]["pass"] for v in complete.values())
            # Knows the numbers but does not act: states the right type yet
            # does not catch the wrong label.
            knows_not_acts = sum(v["wrong_label"]["type_correct"] and not v["wrong_label"]["pass"]
                                 for v in complete.values())
            n = len(complete)
            res[f"paired_{framing}"] = {
                "stations": n, "pass": passed, "paired_score": _pct(passed, n),
                "correct_label_accepted": _pct(accept_ok, n),
                "wrong_label_caught": _pct(flag_ok, n),
                "right_type_but_wrong_label_missed": knows_not_acts,
            }

        lab = [by_id[it["id"]] for it in its]
        res["format_failures"] = sum(s["status"] != "ok" for s in lab)
        res["truncated"] = sum(s["truncated"] for s in lab)
        summary[slice_name] = res
    return summary
