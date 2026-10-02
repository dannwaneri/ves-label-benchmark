"""Baselines run through the real scorer on the real items.

Expected numbers are computed here independently from the item fields,
not from the scorer, so a scorer bug shows up as a mismatch.
"""

import pytest

from items.build_items import build
from scoring.baselines import run_baseline
from scoring.score import aggregate


@pytest.fixture(scope="module")
def items():
    return build()["items"]


def agg(name, items):
    used, scored = run_baseline(name, items)
    assert all(s["status"] == "ok" for s in scored)
    return aggregate(used, scored)


def test_oracle_is_perfect(items):
    a = agg("oracle", items)
    for slc in ("real", "synthetic"):
        assert a[slc]["no_label"]["accuracy"] == 100.0
        assert a[slc]["paired_direct"]["paired_score"] == 100.0
        assert a[slc]["paired_report"]["paired_score"] == 100.0


@pytest.mark.parametrize("name", ["always_trust_label", "always_flag"])
def test_trust_and_flag_score_zero_paired(items, name):
    a = agg(name, items)
    for slc in ("real", "synthetic"):
        assert a[slc]["paired_direct"]["paired_score"] == 0.0
        assert a[slc]["paired_report"]["paired_score"] == 0.0
        assert "no_label" not in a[slc] or a[slc]["no_label"]["n"] == 0


def test_always_trust_catches_no_wrong_label(items):
    a = agg("always_trust_label", items)
    assert a["real"]["paired_direct"]["correct_label_accepted"] == 100.0
    assert a["real"]["paired_direct"]["wrong_label_caught"] == 0.0


def test_always_A_matches_independent_count(items):
    a = agg("always_A", items)
    for slc in ("real", "synthetic"):
        nl = [it for it in items if it["slice"] == slc and it["task"] == "no_label"]
        expect = sum(set(it["derived"]) == {"A"} for it in nl)
        assert a[slc]["no_label"]["pass"] == expect
        # Paired pass needs: correct label is "A"-equivalent AND wrong label is not "A".
        stations = {it["station_id"] for it in items if it["slice"] == slc and it["task"] == "label"}
        exp_pairs = 0
        for sid in stations:
            tw = {it["twin"]: it for it in items if it["station_id"] == sid and it["framing"] == "direct"}
            if tw["correct_label"]["label"] == "A" and tw["wrong_label"]["label"] != "A":
                exp_pairs += 1
        assert a[slc]["paired_direct"]["pass"] == exp_pairs
        assert a[slc]["paired_report"]["pass"] == exp_pairs
