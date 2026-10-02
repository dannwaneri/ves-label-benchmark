"""Checks a held-out file's FORMAT without revealing its contents.

Prints only station names, field names and pass/fail messages: never layer
values, types or labels. It does NOT compare answers with the classifier
(that happens only after the file is frozen).

Usage: python scripts/check_heldout.py data/heldout/heldout_<stamp>.json
"""

import json
import re
import sys

LETTERS = re.compile(r"^[AQHK]+$")


def main(path):
    d = json.load(open(path, encoding="utf-8"))
    problems = []
    if not d.get("frozen_at"):
        problems.append("frozen_at is empty")
    for s in d["stations"]:
        name, L = s.get("name", "?"), s.get("layers", [])
        if len(L) < 3:
            problems.append(f"{name}: fewer than 3 layers")
        r = [l["resistivityOhmM"] for l in L]
        for i, (a, b) in enumerate(zip(r, r[1:]), 1):
            if a == b or abs(b - a) / min(a, b) < 0.02:
                problems.append(f"{name}: layers {i}-{i + 1} differ by less than 2%")
        prev = 0.0
        for i, l in enumerate(L[:-1], 1):
            if l["thicknessM"] is None or l["cumulativeDepthM"] is None:
                problems.append(f"{name}: layer {i} missing thickness or depth")
                continue
            if abs(prev + l["thicknessM"] - l["cumulativeDepthM"]) > 0.011:
                problems.append(f"{name}: layer {i} depth != previous depth + thickness")
            prev = l["cumulativeDepthM"]
        for f in ("expected_type", "correct_label", "wrong_label"):
            v = (s.get(f) or "").strip().upper()
            if not LETTERS.match(v):
                problems.append(f"{name}: {f} is empty or not letters A/Q/H/K")
        exp = (s.get("expected_type") or "").strip().upper()
        if LETTERS.match(exp) and len(exp) != len(L) - 2:
            problems.append(f"{name}: expected_type should have {len(L) - 2} letters (layers - 2)")
        if (s.get("correct_label") or "").strip().upper() == (s.get("wrong_label") or "").strip().upper() != "":
            problems.append(f"{name}: correct_label and wrong_label are the same")
    print(f"{len(d['stations'])} stations checked")
    print("\n".join(problems) if problems else "OK: format valid. Freeze it now (hash) and send path + hash.")


if __name__ == "__main__":
    main(sys.argv[1])
