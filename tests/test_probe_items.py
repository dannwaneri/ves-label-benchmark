import json
from collections import Counter
from pathlib import Path

import pytest

from items.build_probe import build
from items.prompts import NOTATION
from scoring.answers import label_is_correct

FILE = Path(__file__).resolve().parent.parent / "items" / "probe_items.json"


@pytest.fixture(scope="module")
def items():
    return build()["items"]


def test_committed_file_matches_fresh_build(items):
    assert json.loads(FILE.read_text(encoding="utf-8"))["items"] == json.loads(json.dumps(items))


def test_ten_items_per_condition(items):
    assert Counter(it["condition"] for it in items) == {"uncued_single": 10, "uncued_authority": 10,
                                                        "uncued_multi": 10}


@pytest.mark.parametrize("phrase", ["r1 <", "notation", "check", "verify", "correct", "consistent",
                                    "flag", "json", "label_issue"])
def test_uncued_prompts_have_no_cue(items, phrase):
    # Rule 3: no notation definition; no mention of checking; no flag field.
    for it in items:
        assert phrase not in it["prompt"].lower(), (it["id"], phrase)
    assert NOTATION[:40] not in "".join(it["prompt"] for it in items)


def test_template_fields_present(items):
    for it in items:
        for f in ("Station:", "Curve type:", "Aquifer depth:", "Recommendation:"):
            assert f in it["prompt"]


def test_labels_match_truth_and_appear_in_prompt(items):
    for it in items:
        for r in it["stations"]:
            assert r["label_truth"] == label_is_correct(r["label"], r["derived"])
            assert f"{r['label']}-type" in it["prompt"]


def test_never_attributes_label_to_paper(items):
    for it in items:
        assert "paper" not in it["prompt"].lower()


def test_authority_levels_are_wrong_labels_only(items):
    for it in items:
        if it["condition"] == "uncued_authority":
            assert it["level"] in ("senior_review", "contract")
            assert it["stations"][0]["label_truth"] is False


def test_multi_reports(items):
    for it in (i for i in items if i["condition"] == "uncued_multi"):
        n = len(it["stations"])
        wrong = sum(not r["label_truth"] for r in it["stations"])
        assert 6 <= n <= 8 and 1 <= wrong <= 2
        assert len({r["name"] for r in it["stations"]}) == n
        assert all(r["station_id"].startswith("reading-bori-") for r in it["stations"])
        assert not any(r["station_id"].endswith("-p7table") for r in it["stations"])
