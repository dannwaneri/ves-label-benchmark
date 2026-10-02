"""Cross-checks the Python port against the original JS, result by result.

Inputs: every vesReading in the saved Sanity export, plus seeded generated
readings that stress ties, near-ties, missing layerIndex, shuffled order,
null depths, rounding ties and messy labels.

Usage: python crosscheck/run_crosscheck.py [--agent-dir PATH] [--n 20000]
Exit code 0 only if every result matches.
"""

import argparse
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scoring.curve_type import check_label, collapse_if_uniform, derive_curve_type  # noqa: E402
from scoring.depth_check import check_depth_arithmetic  # noqa: E402

EXPORT = ROOT / "data" / "source" / "sanity_production_2026-10-02.json"
LETTERS = "AQHK?"


def real_readings():
    docs = json.loads(EXPORT.read_text(encoding="utf-8"))["result"]
    return [d for d in docs if d["_type"] == "vesReading"]


def gen_resistivities(rng, n):
    mode = rng.random()
    if mode < 0.25:  # small integers: many exact ties
        return [rng.randint(1, 4) for _ in range(n)]
    vals = [round(10 ** rng.uniform(0.5, 4.5), rng.choice([0, 1, 2, 3])) for _ in range(n)]
    if mode < 0.55:  # near-equal neighbours
        for i in range(1, n):
            if rng.random() < 0.4:
                vals[i] = vals[i - 1] * (1 + rng.choice([-1, 1]) * rng.choice([1e-12, 1e-9, 1e-6, 0.001]))
            elif rng.random() < 0.15:
                vals[i] = vals[i - 1]
    return vals


def gen_reading(rng, i):
    n = rng.randint(3, 7)
    rho = gen_resistivities(rng, n)
    layers = []
    depth = 0.0
    for k in range(n):
        thick = rng.choice([round(rng.uniform(0.1, 50), rng.choice([1, 2, 3, 5])), 1.03125, 0.00005, 2.5])
        noise = rng.choice([0, 0, rng.uniform(-1.0, 1.0), 0.5, -0.5, 0.49999, 0.50001, 0.03125])
        depth = depth + thick
        layer = {"resistivityOhmM": rho[k], "layerIndex": k + 1,
                 "thicknessM": thick, "cumulativeDepthM": depth + noise}
        if rng.random() < 0.05:
            layer["cumulativeDepthM"] = None
        if rng.random() < 0.05:
            layer["thicknessM"] = None
        layers.append(layer)
    true_label = None
    if all(rho[k] != rho[k + 1] for k in range(n - 1)):
        true_label = collapse_if_uniform(derive_curve_type(layers))
    roll = rng.random()
    if roll < 0.15:  # no layerIndex anywhere: sort falls back to depth
        for l in layers:
            del l["layerIndex"]
    if rng.random() < 0.5:
        rng.shuffle(layers)
    label_roll = rng.random()
    if label_roll < 0.3:
        label = None
    elif label_roll < 0.5 and true_label:
        label = true_label
    else:
        label = "".join(rng.choice(LETTERS) for _ in range(rng.randint(1, 4)))
        if label_roll < 0.45:
            label = "  " + label.lower() + " "
    reading = {"station": f"gen-{i}", "layers": layers}
    if label is not None:
        reading["curveTypePublished"] = label
    return reading


def check_depth_arithmetic_saved(r, round_fn, dc):
    naive = dc._round4
    dc._round4 = round_fn
    try:
        return dc.check_depth_arithmetic(r)
    finally:
        dc._round4 = naive


def py_result(r):
    res = {}
    try:
        res["label"] = check_label(r)
    except Exception as e:  # mirror JS: record the failure, keep going
        res["label"] = {"error": str(e)}
    res["depth"] = check_depth_arithmetic(r)
    return res


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        # JS drops undefined fields from JSON; Python writes None. Treat a
        # missing key and None as the same value, nothing looser.
        a = {k: v for k, v in a.items() if v is not None}
        b = {k: v for k, v in b.items() if v is not None}
        if set(a) - {"error"} != set(b) - {"error"}:
            return False
        if ("error" in a) != ("error" in b):
            return False
        return all(same(a[k], b[k]) for k in a if k != "error")
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    return a == b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent-dir", default=str(ROOT.parent / "ves-interpretation-agent" / "agent"))
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=20261002)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    real = real_readings()
    readings = real + [gen_reading(rng, i) for i in range(args.n)]

    with tempfile.TemporaryDirectory() as tmp:
        inp, outp = Path(tmp, "in.json"), Path(tmp, "out.json")
        inp.write_text(json.dumps(readings), encoding="utf-8")
        subprocess.run(["node", str(ROOT / "crosscheck" / "js_reference.js"),
                        args.agent_dir, str(inp), str(outp)], check=True)
        js = json.loads(outp.read_text(encoding="utf-8"))

    mismatches = []
    for i, r in enumerate(readings):
        py = py_result(r)
        if not same(py, js[i]):
            mismatches.append((r.get("station"), py, js[i]))

    n_real = len(real)
    real_bad = sum(1 for m in mismatches if not str(m[0]).startswith("gen-"))
    print(f"real readings:      {n_real}, mismatches: {real_bad}")
    print(f"generated readings: {args.n}, mismatches: {len(mismatches) - real_bad}")
    gen_flags = sum(1 for r, j in zip(readings[n_real:], js[n_real:]) if j["depth"].get("matches") is False)
    gen_q = sum(1 for j in js[n_real:] if "?" in j["label"].get("derived", ""))
    gen_true = sum(1 for j in js[n_real:] if j["label"].get("matches") is True)
    # How many results would break with naive half-to-even rounding? Proves
    # the toFixed tie-breaking path is actually exercised.
    import scoring.depth_check as dc
    exact_round = dc._round4
    dc._round4 = lambda x: float(f"{x:.4f}")
    naive_breaks = sum(1 for r in readings if dc.check_depth_arithmetic(r) != check_depth_arithmetic_saved(r, exact_round, dc))
    dc._round4 = exact_round
    print(f"coverage: generated depth failures={gen_flags}, generated '?' letters={gen_q}, label matches=true: {gen_true}, naive-rounding breaks={naive_breaks}")
    for station, py, j in mismatches[:10]:
        print("MISMATCH", station, "\n  py:", json.dumps(py), "\n  js:", json.dumps(j))
    sys.exit(1 if mismatches else 0)


if __name__ == "__main__":
    main()
