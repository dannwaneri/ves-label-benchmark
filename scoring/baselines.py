"""Rule baselines with no model. Each returns a reply string for an item, in
the same format a model must use, so it goes through the same parser and
scorer. Returns None where the rule does not apply (reported as n/a).

always_trust_label: accepts every label; states the label as the type.
always_A:           says the curve is A; accepts a label only if it is "A".
always_flag:        rejects every label.
oracle:             the classifier itself; must score 100% (scorer sanity check).
"""

import json

from scoring.answers import label_is_correct, normalize_type


def _reply(obj):
    return "Baseline answer.\n" + json.dumps(obj)


def always_trust_label(item):
    if item["task"] == "no_label":
        return None
    if item["framing"] == "direct":
        return _reply({"label_correct": True, "curve_type": item["label"]})
    return _reply({"curve_type_stated": item["label"], "label_issue_flagged": False})


def always_A(item):
    if item["task"] == "no_label":
        return _reply({"curve_type": "A"})
    says_a = normalize_type(item["label"]) == "A"
    if item["framing"] == "direct":
        return _reply({"label_correct": says_a, "curve_type": "A"})
    return _reply({"curve_type_stated": "A", "label_issue_flagged": not says_a})


def always_flag(item):
    if item["task"] == "no_label":
        return None
    if item["framing"] == "direct":
        return _reply({"label_correct": False, "curve_type": item["derived"]})
    return _reply({"curve_type_stated": item["derived"], "label_issue_flagged": True})


def oracle(item):
    d = item["derived"]
    if item["task"] == "no_label":
        return _reply({"curve_type": d})
    ok = label_is_correct(item["label"], d)
    if item["framing"] == "direct":
        return _reply({"label_correct": ok, "curve_type": d})
    return _reply({"curve_type_stated": d, "label_issue_flagged": not ok})


BASELINES = {"always_trust_label": always_trust_label, "always_A": always_A,
             "always_flag": always_flag, "oracle": oracle}


def run_baseline(name, items):
    """Returns (items_scored, scored) restricted to items the rule applies to."""
    from scoring.score import score_item
    fn = BASELINES[name]
    used, scored = [], []
    for it in items:
        reply = fn(it)
        if reply is None:
            continue
        used.append(it)
        scored.append(score_item(it, reply))
    return used, scored
