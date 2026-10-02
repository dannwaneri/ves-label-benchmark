"""Full item set (Daniel, decisions after the control probe and cost estimate).

Every station, real and synthetic, gets:
  uncued_nolabel, uncued_correct, uncued_wrong   site-note template, no notation
  rule_nolabel,   rule_correct,   rule_wrong     same, plus the notation as a reference note
  cued_no_label, cued_direct x2, cued_report x2  the earlier JSON tasks, neutral wording
Stations excluded from label tasks (rule 1) get only the three no-label items.
Correct and wrong labels are the same as in items/items.json.

Tasks (Kaggle daily cap split): ves-real (22 stations), ves-synthetic-a
(synthetic 01-16), ves-synthetic-b (17-32). Each task holds every condition.

Usage: python items/build_full.py -> items/full_items.json
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from items.build_probe import LABEL_SENTENCE, ROLE, TEMPLATE  # noqa: E402
from items.prompts import NOTATION, layer_table  # noqa: E402
from scoring.answers import label_is_correct  # noqa: E402

SRC = ROOT / "items" / "items.json"
OUT = ROOT / "items" / "full_items.json"

UNCUED = """{role}

Station {station} ({site}). Interpreted VES layer model:

{table}
{label_block}
Write the site note using exactly this template:

{template}"""

RULE_NOTE = "\n\nReference note: " + NOTATION

CUED_CONDITION = {("no_label", None): "cued_no_label", ("label", "direct"): "cued_direct",
                  ("label", "report"): "cued_report"}


def task_for(station_id):
    if not station_id.startswith("synthetic-"):
        return "ves-real"
    return "ves-synthetic-a" if int(station_id.split("-")[1]) <= 16 else "ves-synthetic-b"


def table_for(st):
    if st["station_id"].startswith("synthetic-"):
        return layer_table(st["layers"], rho_decimals=1, len_decimals=2)
    return layer_table(st["layers"])


def build():
    src = json.loads(SRC.read_text(encoding="utf-8"))
    labels, cued = {}, []
    for it in src["items"]:
        if it["task"] == "label" and it["framing"] == "direct":
            labels.setdefault(it["station_id"], {})[it["twin"]] = it["label"]
        cued.append(it)
    items = []
    for st in src["stations"]:
        sid = st["station_id"]
        table = table_for(st)
        variants = [("nolabel", None)]
        if sid in labels:
            variants += [("correct", labels[sid]["correct_label"]), ("wrong", labels[sid]["wrong_label"])]
        for prefix, note in (("uncued", ""), ("rule", RULE_NOTE)):
            for kind, label in variants:
                label_block = "\n" + LABEL_SENTENCE["plain"].format(label=label) + "\n" if label else ""
                truth = None if label is None else label_is_correct(label, st["derived"])
                items.append({
                    "id": f"{sid}|{prefix}_{kind}", "condition": f"{prefix}_{kind}", "task_name": task_for(sid),
                    "station_id": sid, "slice": "synthetic" if sid.startswith("synthetic-") else "real",
                    "synthetic": sid.startswith("synthetic-"),
                    "stations": [{"name": st["station"], "station_id": sid, "derived": st["derived"],
                                  "label": label, "label_truth": truth}],
                    "prompt": UNCUED.format(role=ROLE, station=st["station"], site=st["site"], table=table,
                                            label_block=label_block, template=TEMPLATE + note)})
    for it in cued:
        items.append(dict(it, condition=CUED_CONDITION[(it["task"], it["framing"])],
                          task_name=task_for(it["station_id"])))
    return {"source": SRC.name, "items": items}


if __name__ == "__main__":
    data = build()
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    from collections import Counter
    for t, n in sorted(Counter(it["task_name"] for it in data["items"]).items()):
        print(t, n)
    print(dict(Counter(it["condition"] for it in data["items"])))
