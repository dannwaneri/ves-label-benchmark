"""Writes a BLIND draft of the held-out stations for Daniel to complete.

- Layer values come from an unseeded system random source, so nobody
  (including Claude, who wrote this script) can reproduce them.
- The script prints only the output path. Claude does not open the file
  until Daniel has filled it in and frozen it (sha256 sent in chat).
- expected_type, correct_label and wrong_label are left EMPTY: Daniel works
  them out by hand. Those hand answers are the check on the classifier.

Design (rule 4 and the brief): 8 stations, 4-6 layers, neighbours differ by
at least 2% (never equal), two stations with a near-equal pair (2-5%),
one decimal for resistivity, depth = previous depth + thickness.

Usage: python scripts/draft_heldout.py   (refuses to overwrite)
"""

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
rng = random.SystemRandom()

N_LAYERS = [4, 4, 5, 5, 5, 6, 6, 6]
NEAR_EQUAL = {2, 6}          # station indexes that get one near-equal pair
UNIFORM = {4}                # one station that is all-rising or all-falling


def station(i):
    n = N_LAYERS[i]
    if i in UNIFORM:
        d = rng.choice("ud")
        signs = d * (n - 1)
    else:
        while True:
            signs = "".join(rng.choice("ud") for _ in range(n - 1))
            if len(set(signs)) > 1:
                break
    near = rng.randrange(n - 1) if i in NEAR_EQUAL else None
    for _ in range(10000):
        r = [10 ** rng.uniform(1.3, 3.3)]
        for k in range(n - 1):
            mag = rng.uniform(1.02, 1.05) if k == near else 10 ** rng.uniform(0.08, 0.8)
            r.append(r[-1] * mag if signs[k] == "u" else r[-1] / mag)
        r = [round(x, 1) for x in r]
        ok = min(r) >= 5.0 and all(a != b and abs(b - a) / min(a, b) >= 0.02 for a, b in zip(r, r[1:])) \
            and "".join("u" if b > a else "d" for a, b in zip(r, r[1:])) == signs
        if ok:
            break
    else:
        raise RuntimeError("generation failed")
    layers, depth = [], 0.0
    for k in range(n):
        if k == n - 1:
            layers.append({"resistivityOhmM": r[k], "thicknessM": None, "cumulativeDepthM": None})
        else:
            t = round(10 ** rng.uniform(-0.3, 1.5), 2)
            depth = round(depth + t, 2)
            layers.append({"resistivityOhmM": r[k], "thicknessM": t, "cumulativeDepthM": depth})
    return {"name": f"H-{i + 1:02d}", "layers": layers,
            "expected_type": "", "correct_label": "", "wrong_label": ""}


def main():
    now = datetime.now(timezone(timedelta(hours=1)))
    out = ROOT / "data" / "heldout" / f"heldout_{now:%Y%m%d-%H%M}.json"
    if out.exists():
        sys.exit(f"refusing to overwrite {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    data = {"frozen_at": "", "site": "survey area H",
            "instructions": "Fill expected_type, correct_label, wrong_label for every station by hand. "
                            "Then set frozen_at, save, and send the path + SHA256 hash.",
            "stations": [station(i) for i in range(len(N_LAYERS))]}
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
