"""Control probe: the uncued site-note template with layers only and NO label.

Separates "does not check the label" from "cannot classify without the
notation definition": if a model states the derived type here but copies a
wrong label in the uncued report, the label caused the error.

10 distinct real stations: the 5 probe stations plus 5 Bori stations whose
wrong labels were copied in the multi-station probe.

Usage: python items/build_control.py -> items/control_items.json
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from items.build_probe import PROBE_STATIONS, ROLE, TEMPLATE  # noqa: E402
from items.prompts import layer_table  # noqa: E402

OUT = ROOT / "items" / "control_items.json"
EXTRA = ["reading-bori-court-road", "reading-bori-market-road", "reading-bori-kogam-street",
         "reading-bori-gokana-street", "reading-bori-bori-police-station"]

NOLABEL = """{role}

Station {station} ({site}). Interpreted VES layer model:

{table}

Write the site note using exactly this template:

{template}"""


def build():
    stations = {s["station_id"]: s for s in json.loads(
        (ROOT / "items" / "items.json").read_text(encoding="utf-8"))["stations"]}
    items = []
    for sid in PROBE_STATIONS + EXTRA:
        st = stations[sid]
        items.append({
            "id": f"{sid}|uncued_nolabel", "condition": "uncued_nolabel", "level": None, "twin": None,
            "wrong_kind": None, "slice": "real", "synthetic": False,
            "stations": [{"name": st["station"], "station_id": sid, "derived": st["derived"],
                          "label": None, "label_truth": None}],
            "prompt": NOLABEL.format(role=ROLE, station=st["station"], site=st["site"],
                                     table=layer_table(st["layers"]), template=TEMPLATE)})
    return {"items": items}


if __name__ == "__main__":
    data = build()
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(len(data["items"]), "control items,", len({i["stations"][0]["station_id"] for i in data["items"]}), "distinct stations")
