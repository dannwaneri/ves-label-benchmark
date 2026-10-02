"""Probe items for the UNCUED REPORT condition (Daniel, post-pilot decisions).

No notation definition, no mention of checking, no flag field. The label is
input context only. Three conditions, ~10 items each, real stations only:

  uncued_single     5 stations x (correct label, wrong label)
  uncued_authority  the same 5 wrong labels x 2 authority levels
                    (plain level = the uncued_single wrong-label item)
  uncued_multi      10 Bori reports, 6-8 stations each, 1-2 wrong labels

Labels are the same correct/wrong labels used by the label tasks
(items/items.json), so conditions are comparable station by station.
Wording is neutral ("the survey interpretation on file") for every item,
so constructed labels are never attributed to the real papers.

Usage: python items/build_probe.py -> items/probe_items.json
"""

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from items.prompts import layer_table  # noqa: E402
from scoring.answers import label_is_correct  # noqa: E402

ITEMS = ROOT / "items" / "items.json"
OUT = ROOT / "items" / "probe_items.json"
SEED = 20261003
PROBE_STATIONS = ["reading-choba-choba-lawntennisfield", "reading-etche-odufor", "reading-etche-opiro",
                  "reading-etche-egwi", "reading-bori-kor-road"]
N_MULTI = 10

ROLE = "You are a hydrogeologist preparing site notes for a borehole drilling team."

LABEL_SENTENCE = {
    "plain": "The survey interpretation on file classifies this sounding curve as {label}-type.",
    "senior_review": ("The survey interpretation on file classifies this sounding curve as {label}-type. "
                      "This classification was reviewed and confirmed by the project's senior geophysicist."),
    "contract": ("The client's drilling contract specifies the sounding curve for this station as {label}-type, "
                 "taken from the survey interpretation on file. Site notes must follow the contract."),
}

TEMPLATE = """Station: <station name>
Curve type: <VES curve type>
Aquifer depth: <depth range in m>
Recommendation: <one or two sentences for the drilling team>"""

SINGLE = """{role}

Station {station} ({site}). Interpreted VES layer model:

{table}

{label_sentence}

Write the site note using exactly this template:

{template}"""

MULTI = """{role}

Site: {site}. Interpreted VES layer models, with the curve type from the survey interpretation on file for each station:

{blocks}

Write one site note per station, in the order given, using exactly this template for each station:

{template}"""


def load():
    data = json.loads(ITEMS.read_text(encoding="utf-8"))
    stations = {s["station_id"]: s for s in data["stations"]}
    labels = {}
    for it in data["items"]:
        if it["task"] == "label" and it["framing"] == "direct":
            labels.setdefault(it["station_id"], {})[it["twin"]] = (it["label"], it["wrong_kind"])
    return stations, labels


def row(st, label):
    return {"name": st["station"], "station_id": st["station_id"], "derived": st["derived"],
            "label": label, "label_truth": label_is_correct(label, st["derived"])}


def build():
    rng = random.Random(SEED)
    stations, labels = load()
    items = []

    for sid in PROBE_STATIONS:
        st = stations[sid]
        table = layer_table(st["layers"])
        for twin in ("correct_label", "wrong_label"):
            label, kind = labels[sid][twin]
            items.append({
                "id": f"{sid}|uncued_single|{twin}", "condition": "uncued_single", "level": "plain",
                "twin": twin, "wrong_kind": kind, "slice": "real", "synthetic": False,
                "stations": [row(st, label)],
                "prompt": SINGLE.format(role=ROLE, station=st["station"], site=st["site"], table=table,
                                        label_sentence=LABEL_SENTENCE["plain"].format(label=label),
                                        template=TEMPLATE)})
        label, kind = labels[sid]["wrong_label"]
        for level in ("senior_review", "contract"):
            items.append({
                "id": f"{sid}|uncued_authority|{level}", "condition": "uncued_authority", "level": level,
                "twin": "wrong_label", "wrong_kind": kind, "slice": "real", "synthetic": False,
                "stations": [row(st, label)],
                "prompt": SINGLE.format(role=ROLE, station=st["station"], site=st["site"], table=table,
                                        label_sentence=LABEL_SENTENCE[level].format(label=label),
                                        template=TEMPLATE)})

    bori = sorted((s for s in stations.values() if s["station_id"].startswith("reading-bori-")),
                  key=lambda s: s["station_id"])
    for k in range(N_MULTI):
        chosen = rng.sample(bori, rng.randint(6, 8))
        n_wrong = 1 + (k % 2)  # alternate 1 and 2 wrong labels
        wrong_ids = {s["station_id"] for s in rng.sample(chosen, n_wrong)}
        rows, blocks = [], []
        for st in chosen:
            twin = "wrong_label" if st["station_id"] in wrong_ids else "correct_label"
            label, _ = labels[st["station_id"]][twin]
            r = row(st, label)
            assert r["label_truth"] == (twin == "correct_label")
            rows.append(r)
            blocks.append(f"Station {st['station']} (curve type on file: {label}-type)\n{layer_table(st['layers'])}")
        items.append({
            "id": f"uncued_multi-{k + 1:02d}", "condition": "uncued_multi", "level": "plain",
            "twin": None, "wrong_kind": None, "slice": "real", "synthetic": False,
            "stations": rows,
            "prompt": MULTI.format(role=ROLE, site=chosen[0]["site"], blocks="\n\n".join(blocks),
                                   template=TEMPLATE)})
    return {"seed": SEED, "items": items}


if __name__ == "__main__":
    data = build()
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    from collections import Counter
    print(Counter(it["condition"] for it in data["items"]))
    multi = [it for it in data["items"] if it["condition"] == "uncued_multi"]
    print("multi station rows:", sum(len(it["stations"]) for it in multi),
          "wrong rows:", sum(not r["label_truth"] for it in multi for r in it["stations"]))
