"""Builds the benchmark items from the saved Sanity export.

Two slices, always reported separately:
- real:      stations from the three papers (Figure 2 versions for Bori).
- synthetic: generated from real layer patterns; every item has synthetic=True.

Per station: one no_label item, and (if label-eligible) a correct_label twin
and a wrong_label twin, each in two framings (direct, report).

Usage: python items/build_items.py   -> items/items.json
"""

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from items.prompts import DIRECT, NO_LABEL, NOTATION, REPORT, layer_table  # noqa: E402
from scoring.answers import label_is_correct  # noqa: E402
from scoring.curve_type import derive_curve_type, sort_layers_by_depth  # noqa: E402
from scoring.depth_check import check_depth_arithmetic  # noqa: E402

EXPORT = ROOT / "data" / "source" / "sanity_production_2026-10-02.json"
OUT = ROOT / "items" / "items.json"
SEED = 20261002
N_SYNTHETIC = 32
MIN_GAP = 0.02  # rule 4: neighbour layers differ by at least 2%

# Rule 3: Figure 2 versions only; the p.7 Table 1 rows swap two stations.
EXCLUDED_DUPLICATES = {"reading-bori-bmgs-bori-field-p7table",
                       "reading-bori-kenpoly-sec-school-field-p7table"}
# Rule 1: >4-layer curves whose published label follows a naming convention.
EXCLUDED_FROM_LABEL_TASKS = {"reading-etche-akpoku", "reading-etche-ndashi",
                             "reading-etche-umuokom"}
REAL_MISLABELS = {"reading-choba-choba-lawntennisfield", "reading-etche-odufor",
                  "reading-etche-opiro"}

SIGNS = {"A": "uu", "Q": "dd", "H": "du", "K": "ud"}
LETTER = {v: k for k, v in SIGNS.items()}


def to_signs(derived):
    return SIGNS[derived[0]][0] + "".join(SIGNS[c][1] for c in derived)


def from_signs(signs):
    return "".join(LETTER[signs[i:i + 2]] for i in range(len(signs) - 1))


def gap_ok(a, b):
    return a != b and abs(b - a) / min(a, b) >= MIN_GAP


# ---------------------------------------------------------------- labels

def wrong_label(derived, kind, rng):
    """A label that is wrong under the benchmark's rules.

    flip:   flip one up/down step -> a different but realizable full string.
    single: one letter that does not occur in the true type.
    """
    if kind == "flip":
        signs = to_signs(derived)
        options = []
        for i in range(len(signs)):
            s = signs[:i] + ("d" if signs[i] == "u" else "u") + signs[i + 1:]
            cand = from_signs(s)
            if not label_is_correct(cand, derived):
                options.append(cand)
        label = rng.choice(options)
    elif kind == "single":
        # Prefer a letter absent from the true type. A mixed curve has no
        # single-letter alias, so if all four letters occur any letter is wrong.
        absent = sorted(set("AQHK") - set(derived))
        label = rng.choice(absent or sorted(set("AQHK")))
    else:
        raise ValueError(kind)
    assert not label_is_correct(label, derived), (label, derived)
    return label


# ---------------------------------------------------------------- real slice

def real_stations():
    docs = json.loads(EXPORT.read_text(encoding="utf-8"))["result"]
    sites = {d["_id"]: d.get("name") for d in docs if d["_type"] == "surveySite"}
    out = []
    for d in sorted((d for d in docs if d["_type"] == "vesReading"), key=lambda d: d["_id"]):
        if d["_id"] in EXCLUDED_DUPLICATES:
            continue
        layers = sort_layers_by_depth(d["layers"])
        out.append({
            "station_id": d["_id"],
            "station": d["station"],
            "site": sites[d["site"]["_ref"]],
            "layers": [{k: l.get(k) for k in ("resistivityOhmM", "thicknessM", "cumulativeDepthM")}
                       for l in layers],
            "published": (d.get("curveTypePublished") or "").strip().upper() or None,
            "label_eligible": d["_id"] not in EXCLUDED_FROM_LABEL_TASKS,
            "fmt": {},
        })
    return out


def real_labels(st, rng, i):
    derived = st["derived"]
    pub = st["published"]
    if st["station_id"] in REAL_MISLABELS:
        assert pub and not label_is_correct(pub, derived)
        return derived, pub, "published_mislabel"
    correct = pub if pub and label_is_correct(pub, derived) else derived
    kind = "flip" if i % 2 == 0 else "single"
    return correct, wrong_label(derived, kind, rng), f"constructed_{kind}"


# ---------------------------------------------------------------- synthetic slice

def make_synthetic(template, rng, uniform_letter=None):
    """New station from a real layer pattern: same number of layers and
    similar magnitudes; sometimes one step flipped, sometimes a near-equal pair."""
    n = len(template["layers"])
    if uniform_letter:
        signs = SIGNS[uniform_letter][0] * (n - 1)
    else:
        signs = to_signs(template["derived"])
        if rng.random() < 0.5:
            i = rng.randrange(len(signs))
            signs = signs[:i] + ("d" if signs[i] == "u" else "u") + signs[i + 1:]
    t_rho = [l["resistivityOhmM"] for l in template["layers"]]
    near = rng.randrange(n - 1) if rng.random() < 0.6 else None

    for _ in range(1000):
        raw = [t_rho[0] * 10 ** rng.uniform(-0.3, 0.3)]
        for k in range(n - 1):
            mag = abs(t_rho[k + 1] / t_rho[k])
            mag = min(max(max(mag, 1 / mag) ** rng.uniform(0.5, 1.5), 1.03), 12.0)
            if k == near:
                mag = rng.uniform(1.02, 1.05)  # near-equal neighbours (>= 2% after rounding, checked below)
            raw.append(raw[-1] * mag if signs[k] == "u" else raw[-1] / mag)
        if min(raw) < 10:  # rescale: ratios and directions unchanged
            raw = [x * (10 / min(raw)) * rng.uniform(1, 3) for x in raw]
        r = [round(x, 1) for x in raw]
        if min(r) >= 1.0 and all(gap_ok(r[k], r[k + 1]) for k in range(n - 1)) \
                and "".join("u" if r[k + 1] > r[k] else "d" for k in range(n - 1)) == signs:
            break
    else:
        raise RuntimeError("could not generate a valid synthetic station")

    layers, depth = [], 0.0
    for k in range(n):
        if k == n - 1:
            layers.append({"resistivityOhmM": r[k], "thicknessM": None, "cumulativeDepthM": None})
            break
        t = round(10 ** rng.uniform(-0.5, 1.6), 2)
        depth = round(depth + t, 2)
        layers.append({"resistivityOhmM": r[k], "thicknessM": t, "cumulativeDepthM": depth})
    return layers


def synthetic_stations(templates, rng):
    out = []
    uniform = ["A", "Q", "A", "Q"]  # make sure the single-letter alias is tested
    for j in range(N_SYNTHETIC):
        tpl = templates[j % len(templates)]
        u = uniform[j] if j < len(uniform) else None
        layers = make_synthetic(tpl, rng, uniform_letter=u)
        out.append({
            "station_id": f"synthetic-{j + 1:02d}",
            "station": f"T-{j + 1:02d}",
            "site": "survey area T",
            "layers": layers,
            "published": None,
            "label_eligible": True,
            "template": tpl["station_id"],
            "fmt": {"rho_decimals": 1, "len_decimals": 2},
        })
    return out


def synthetic_labels(st, rng, j):
    derived = st["derived"]
    # Forced uniform stations j=0..3 are A, Q, A, Q: show the alias for the
    # first A and first Q, the full string for the second of each.
    if len(set(derived)) == 1 and (j // 2) % 2 == 0:
        correct = derived[0]  # alias form
    else:
        correct = derived
    kind = "flip" if j % 2 == 0 else "single"
    return correct, wrong_label(derived, kind, rng), f"constructed_{kind}"


# ---------------------------------------------------------------- items

def items_for(st, slice_name, correct, wrong, wrong_kind):
    table = layer_table(st["layers"], **st["fmt"])
    base = {"slice": slice_name, "synthetic": slice_name == "synthetic",
            "station_id": st["station_id"], "station": st["station"],
            "derived": st["derived"], "n_layers": len(st["layers"])}
    ctx = {"notation": NOTATION, "station": st["station"], "site": st["site"], "table": table}
    items = [dict(base, id=f"{st['station_id']}|no_label", task="no_label", twin=None,
                  framing=None, label=None, label_truth=None, wrong_kind=None,
                  prompt=NO_LABEL.format(**ctx))]
    if not st["label_eligible"]:
        return items
    for twin, label in (("correct_label", correct), ("wrong_label", wrong)):
        truth = label_is_correct(label, st["derived"])
        assert truth == (twin == "correct_label"), (st["station_id"], twin, label)
        for framing, tmpl in (("direct", DIRECT), ("report", REPORT)):
            items.append(dict(base, id=f"{st['station_id']}|{twin}|{framing}", task="label",
                              twin=twin, framing=framing, label=label, label_truth=truth,
                              wrong_kind=wrong_kind if twin == "wrong_label" else None,
                              prompt=tmpl.format(label=label, **ctx)))
    return items


def build():
    rng = random.Random(SEED)
    real = real_stations()
    for st in real:
        st["derived"] = derive_curve_type(st["layers"])
    syn = synthetic_stations(real, rng)
    for st in syn:
        st["derived"] = derive_curve_type(st["layers"])
        assert "?" not in st["derived"]
        assert check_depth_arithmetic({"layers": [dict(l, layerIndex=i) for i, l in enumerate(st["layers"])]})["matches"]

    items = []
    eligible = [st for st in real if st["label_eligible"]]
    for st in real:
        if st["label_eligible"]:
            correct, wrong, kind = real_labels(st, rng, eligible.index(st))
        else:
            correct = wrong = kind = None
        items += items_for(st, "real", correct, wrong, kind)
    for j, st in enumerate(syn):
        correct, wrong, kind = synthetic_labels(st, rng, j)
        items += items_for(st, "synthetic", correct, wrong, kind)

    stations = [{k: v for k, v in st.items() if k != "fmt"} for st in real + syn]
    return {"seed": SEED, "source": EXPORT.name, "stations": stations, "items": items}


if __name__ == "__main__":
    data = build()
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    from collections import Counter
    c = Counter((it["slice"], it["task"], it.get("framing")) for it in data["items"])
    for k in sorted(c, key=str):
        print(k, c[k])
    print("total items:", len(data["items"]))
