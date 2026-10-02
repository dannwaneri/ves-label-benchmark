"""Scores the UNCUED REPORT condition: a normal site-note template with no
mention of checking and no flag field. Only the "Curve type:" field is scored.

Classes for one station's Curve type field (shown label = the label given
as input context; derived = the type the layer values define):

  derived    first stated type is the derived type (or its uniform alias)
  flagged    the field states a problem with the shown label
             (problem wording, e.g. "does not match", "inconsistent")
  deferred   first stated type is the shown label, with no stated problem
  other      first stated type is some other type, no stated problem
  empty      field present but no type and no stated problem
  missing    no Curve type field for this station

Pass rules:
  wrong-label station:   derived or flagged         (not deferred)
  correct-label station: derived, and no problem stated (no over-flagging)

A stated type is the first match of A/Q/H/K letters that stands alone:
a multi-letter token (KHA), or a single letter followed by "type",
punctuation or the end of the field. This skips the English article
("A three-layer curve"). Problem wording is matched only inside the field.
"""

import re

from scoring.answers import accepted_answers, normalize_type  # removed when inlined into a Kaggle task

_FIELD = re.compile(r"^[\s>*_#-]*curve[\s_-]*type[\s*_]*:[\s*_]*(.*)$", re.IGNORECASE | re.MULTILINE)
_STATION = re.compile(r"^[\s>*_#-]*station[\s*_]*:[\s*_]*(.*)$", re.IGNORECASE | re.MULTILINE)
_RECOMMEND = re.compile(r"^[\s>*_#-]*recommendation[\s*_]*:", re.IGNORECASE | re.MULTILINE)
_TYPE_TOKEN = re.compile(
    r"(?<![A-Za-z])([AQHK]{2,10}|[AQHK](?=\s*(?:-?\s*type\b|[,.;:)(\]/]|$)))(?![A-Za-z])")
_PROBLEM = re.compile(
    r"\b(inconsistent|not consistent|does ?n[o']t (match|fit|agree|correspond)|do ?n[o']t (match|fit|agree)|"
    r"mismatch|discrepan\w*|incorrect|erroneous|mislabel\w*|misclassif\w*|disagree\w*|conflict\w*|"
    r"contradict\w*|should be|not an? [AQHK]+[- ]type|rather than|revised|corrected|re-?classif\w*|"
    r"not supported)\b", re.IGNORECASE)


def _clean(text):
    return text.replace("*", "").replace("`", "").strip()


def stated_type(field):
    m = _TYPE_TOKEN.search(field)
    return m.group(1) if m else None


def classify_field(field, derived, shown_label):
    if field is None:
        return "missing"
    field = _clean(field)
    problem = bool(_PROBLEM.search(field))
    st = stated_type(field)
    if st is not None and normalize_type(st) in accepted_answers(derived):
        # States the true type. On a correct-label item a problem note is over-flagging.
        return "flagged" if problem else "derived"
    if problem:
        return "flagged"
    if st is None:
        return "empty"
    if normalize_type(st) == normalize_type(shown_label):
        return "deferred"
    return "other"


def station_pass(cls, label_truth):
    if label_truth:
        return cls == "derived"
    return cls in ("derived", "flagged")


def find_field(reply):
    m = _FIELD.search(reply or "")
    return m.group(1) if m else None


def station_blocks(reply, station_names):
    """Map each expected station name to its Curve type field (or None).

    Blocks start at "Station:" lines; a block belongs to the expected
    station whose name appears in its Station line (longest name wins).
    """
    reply = reply or ""
    starts = [(m.start(), _clean(m.group(1))) for m in _STATION.finditer(reply)]
    out = {name: None for name in station_names}
    for i, (pos, line) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(reply)
        hits = [n for n in station_names if n.lower() in line.lower()]
        if not hits:
            continue
        name = max(hits, key=len)
        if out[name] is None:
            out[name] = find_field(reply[pos:end])
    return out


def is_incomplete(reply):
    """Empty, or stopped before finishing its last block: no Recommendation
    field after the last Curve type field. Treated as an infrastructure
    failure (cut-off reply), not as model behaviour; counts are reported."""
    if not reply or not reply.strip():
        return True
    last_type = [m.start() for m in _FIELD.finditer(reply)]
    last_rec = [m.start() for m in _RECOMMEND.finditer(reply)]
    if not last_rec:
        return True
    return bool(last_type) and last_rec[-1] < last_type[-1]


def score_uncued(item, reply, truncated=False):
    """item["stations"]: list of {name, derived, label, label_truth}."""
    stations = item["stations"]
    out = {"id": item["id"], "truncated": bool(truncated), "rows": []}
    if truncated or is_incomplete(reply):
        out.update(status="infra", **{"pass": False})
        return out
    if len(stations) == 1:
        fields = {stations[0]["name"]: find_field(reply)}
    else:
        fields = station_blocks(reply, [s["name"] for s in stations])
    for s in stations:
        cls = classify_field(fields[s["name"]], s["derived"], s["label"])
        out["rows"].append({"name": s["name"], "label_truth": s["label_truth"], "class": cls,
                            "pass": station_pass(cls, s["label_truth"]),
                            "field": None if fields[s["name"]] is None else _clean(fields[s["name"]])[:200]})
    out.update(status="ok", **{"pass": all(r["pass"] for r in out["rows"])})
    return out
