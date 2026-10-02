"""Checks on the built items: exclusions, slices, twins, rule 4."""

import json
from pathlib import Path

import pytest

from items.build_items import (EXCLUDED_DUPLICATES, EXCLUDED_FROM_LABEL_TASKS, MIN_GAP,
                               REAL_MISLABELS, build)
from scoring.answers import label_is_correct
from scoring.curve_type import derive_curve_type
from scoring.depth_check import check_depth_arithmetic

ITEMS_FILE = Path(__file__).resolve().parent.parent / "items" / "items.json"


@pytest.fixture(scope="module")
def data():
    return build()


def test_committed_items_file_matches_a_fresh_build(data):
    assert json.loads(ITEMS_FILE.read_text(encoding="utf-8")) == json.loads(json.dumps(data))


def test_build_is_deterministic(data):
    assert build() == data


# --- rule 3: p7table duplicates excluded everywhere ---

def test_p7table_duplicates_excluded(data):
    ids = {it["station_id"] for it in data["items"]}
    assert not ids & EXCLUDED_DUPLICATES
    real = [s for s in data["stations"] if not s["station_id"].startswith("synthetic")]
    assert len(real) == 22
    assert {"BMGS-bori-field", "Kenpoly-sec-school-field"} <= {s["station"] for s in real}


# --- rule 1: 6-layer Etche KH curves only in no_label, with full notation ---

@pytest.mark.parametrize("sid,derived", [("reading-etche-akpoku", "AKHA"),
                                         ("reading-etche-ndashi", "AKQH"),
                                         ("reading-etche-umuokom", "AKQH")])
def test_convention_labels_excluded_from_label_tasks(data, sid, derived):
    its = [it for it in data["items"] if it["station_id"] == sid]
    assert [it["task"] for it in its] == ["no_label"]
    assert its[0]["derived"] == derived
    assert "KH-type" not in its[0]["prompt"]


def test_only_three_real_published_mislabels(data):
    pub = {it["station_id"] for it in data["items"] if it["wrong_kind"] == "published_mislabel"}
    assert pub == REAL_MISLABELS
    for it in data["items"]:
        if it["wrong_kind"] == "published_mislabel":
            assert it["label"] == "A"


def test_excluded_set_is_exactly_the_three():
    assert EXCLUDED_FROM_LABEL_TASKS == {"reading-etche-akpoku", "reading-etche-ndashi",
                                        "reading-etche-umuokom"}


# --- twins and slices ---

def test_every_label_station_has_both_twins_in_both_framings(data):
    from collections import defaultdict
    seen = defaultdict(set)
    for it in data["items"]:
        if it["task"] == "label":
            seen[it["station_id"]].add((it["twin"], it["framing"]))
    full = {(t, f) for t in ("correct_label", "wrong_label") for f in ("direct", "report")}
    assert all(v == full for v in seen.values())
    assert len(seen) == 19 + 32


def test_label_truth_matches_rules(data):
    for it in data["items"]:
        if it["task"] == "label":
            assert it["label_truth"] == label_is_correct(it["label"], it["derived"])
            assert it["label_truth"] == (it["twin"] == "correct_label")
            assert f"as {it['label']}-type" in it["prompt"]


def test_synthetic_flag(data):
    for it in data["items"]:
        assert it["synthetic"] == (it["slice"] == "synthetic")
        assert it["synthetic"] == it["station_id"].startswith("synthetic")


def test_both_alias_forms_are_shown_as_correct_labels(data):
    shown = {(it["derived"], it["label"]) for it in data["items"]
             if it["twin"] == "correct_label" and it["slice"] == "synthetic"}
    assert any(len(d) > 1 and set(d) == {"A"} and l == "A" for d, l in shown)
    assert any(len(d) > 1 and set(d) == {"Q"} and l == "Q" for d, l in shown)
    assert any(len(d) > 1 and len(set(d)) == 1 and l == d for d, l in shown)


# --- rule 4: synthetic values ---

def synthetic(data):
    return [s for s in data["stations"] if s["station_id"].startswith("synthetic")]


def test_synthetic_min_gap_and_never_equal(data):
    for s in synthetic(data):
        r = [l["resistivityOhmM"] for l in s["layers"]]
        for a, b in zip(r, r[1:]):
            assert a != b
            assert abs(b - a) / min(a, b) >= MIN_GAP, (s["station_id"], a, b)


def test_synthetic_has_near_equal_and_4_to_6_layers(data):
    syn = synthetic(data)
    near = [s for s in syn if min(abs(b - a) / min(a, b) for a, b in
                                  zip(*(lambda r: (r, r[1:]))([l["resistivityOhmM"] for l in s["layers"]]))) < 0.05]
    assert len(near) >= 8
    assert {len(s["layers"]) for s in syn} >= {4, 5}


def test_printed_values_give_the_same_type(data):
    # Fixed precision: parse the printed table back and re-derive.
    by_station = {s["station_id"]: s for s in data["stations"]}
    for it in data["items"]:
        if it["task"] != "no_label":
            continue
        rows = [ln for ln in it["prompt"].splitlines() if ln[:1].isdigit() and " | " in ln]
        printed = [float(ln.split(" | ")[1]) for ln in rows]
        assert printed == [l["resistivityOhmM"] for l in by_station[it["station_id"]]["layers"]]
        assert derive_curve_type([{"resistivityOhmM": v} for v in printed]) == it["derived"]
        if it["synthetic"]:
            assert all(len(ln.split(" | ")[1].split(".")[1]) == 1 for ln in rows)


def test_synthetic_depth_tables_are_consistent(data):
    for s in synthetic(data):
        layers = [dict(l, layerIndex=i) for i, l in enumerate(s["layers"])]
        assert check_depth_arithmetic({"layers": layers})["matches"]


def test_no_prompt_attributes_labels_to_a_paper(data):
    # Decision 1 (post-probe): neutral wording in all prompts; constructed
    # labels must never be attributed to the real papers.
    for it in data["items"]:
        assert "paper" not in it["prompt"].lower(), it["id"]
        assert "published" not in it["prompt"].lower(), it["id"]
        if it["task"] == "label":
            assert "The survey interpretation on file classifies this station's curve as" in it["prompt"]
