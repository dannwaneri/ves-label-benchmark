import json
import re
import sys
from collections import Counter
from pathlib import Path

import pytest

from items.build_full import build
from items.prompts import NOTATION
from kaggle.build_task import build as build_task

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "items" / "full_items.json"
SRC = json.loads((ROOT / "items" / "items.json").read_text(encoding="utf-8"))
ITEMS = build()["items"]
EXCLUDED = {"reading-etche-akpoku", "reading-etche-ndashi", "reading-etche-umuokom"}
CUE_WORDS = ("check", "verify", "correct", "consistent", "flag", "json", "paper", "published")


def test_committed_file_matches_fresh_build():
    assert json.loads(FILE.read_text(encoding="utf-8"))["items"] == json.loads(json.dumps(ITEMS))


def test_task_sizes_match_cost_estimate():
    assert Counter(it["task_name"] for it in ITEMS) == {"ves-real": 218, "ves-synthetic-a": 176,
                                                        "ves-synthetic-b": 176}


def test_each_station_in_exactly_one_task_and_slices_separate():
    task_of = {}
    for it in ITEMS:
        assert task_of.setdefault(it["station_id"], it["task_name"]) == it["task_name"]
        assert (it["slice"] == "real") == (it["task_name"] == "ves-real")
    assert len(task_of) == 54


def test_every_station_gets_every_condition():
    conds = {}
    for it in ITEMS:
        conds.setdefault(it["station_id"], Counter())[it["condition"]] += 1
    for sid, c in conds.items():
        if sid in EXCLUDED:
            assert c == {"uncued_nolabel": 1, "rule_nolabel": 1, "cued_no_label": 1}
        else:
            assert c == {"uncued_nolabel": 1, "uncued_correct": 1, "uncued_wrong": 1, "rule_nolabel": 1,
                         "rule_correct": 1, "rule_wrong": 1, "cued_no_label": 1, "cued_direct": 2,
                         "cued_report": 2}, sid


def test_uncued_has_no_notation_and_no_cue():
    for it in ITEMS:
        if it["condition"].startswith("uncued_"):
            p = it["prompt"].lower()
            assert NOTATION[:40].lower() not in p and "r1 <" not in p
            for w in CUE_WORDS:
                assert w not in p, (it["id"], w)


def test_rule_has_notation_once_and_no_cue_outside_it():
    for it in ITEMS:
        if it["condition"].startswith("rule_"):
            assert it["prompt"].count(NOTATION) == 1
            rest = it["prompt"].replace(NOTATION, "").lower()
            for w in CUE_WORDS:
                assert w not in rest, (it["id"], w)


def test_uncued_and_rule_differ_only_by_the_reference_note():
    by = {it["id"]: it for it in ITEMS}
    for it in ITEMS:
        if it["condition"].startswith("rule_"):
            twin = by[it["id"].replace("|rule_", "|uncued_")]
            assert it["prompt"] == twin["prompt"] + "\n\nReference note: " + NOTATION


def test_labels_are_the_label_task_labels():
    want = {(it["station_id"], it["twin"].split("_")[0]): it["label"]
            for it in SRC["items"] if it["task"] == "label" and it["framing"] == "direct"}
    for it in ITEMS:
        kind = it["condition"].split("_", 1)[1]
        if it["condition"].split("_")[0] in ("uncued", "rule") and kind in ("correct", "wrong"):
            row = it["stations"][0]
            assert row["label"] == want[(it["station_id"], kind)]
            assert row["label_truth"] is (kind == "correct")
            assert f"as {row['label']}-type." in it["prompt"]


def test_synthetic_tables_fixed_precision():
    for it in ITEMS:
        if it["synthetic"] and it["condition"].endswith("nolabel") and it["condition"].startswith("uncued"):
            rho = [ln.split(" | ")[1] for ln in it["prompt"].splitlines() if re.match(r"^\d+ \| ", ln)]
            assert rho and all(re.fullmatch(r"\d+\.\d", v) for v in rho)


# ---------------------------------------------------------------- paired score end to end (stub kbench)

def test_paired_score_end_to_end(monkeypatch, capsys):
    from tests.test_generated_task import _stub_kbench
    sub = [it for it in ITEMS if it["station_id"] in ("reading-etche-odufor", "reading-bori-kor-road")
           and it["condition"] in ("uncued_correct", "uncued_wrong", "uncued_nolabel")]

    def note(it, field):
        return f"Station: {it['stations'][0]['name']}\nCurve type: {field}\nAquifer depth: 5 m\nRecommendation: go"

    script = {}
    for it in sub:
        row = it["stations"][0]
        if it["station_id"] == "reading-etche-odufor":
            field = row["derived"]                         # never copies
        else:
            field = row["label"] or row["derived"]         # Kor-road: copies whatever is on file
        script[it["prompt"]] = [note(it, field)]
    monkeypatch.setitem(sys.modules, "kaggle_benchmarks", _stub_kbench(script, []))
    exec(compile(build_task("e2e", sub, repeats=2, score="uncued_paired"), "<generated>", "exec"), {})
    out = capsys.readouterr().out
    assert sys.modules["kaggle_benchmarks"].result == pytest.approx(0.5)   # Odufor passes, Kor-road copies
    assert "UNCUED_PAIRED 0.5" in out and "COUNTS " in out


def test_no_complete_pair_records_no_score(monkeypatch, capsys):
    from tests.test_generated_task import _stub_kbench
    sub = [it for it in ITEMS if it["station_id"] == "reading-etche-odufor"
           and it["condition"] in ("uncued_correct", "uncued_wrong", "uncued_nolabel")]
    ok = (f"Station: Odufor\nCurve type: AK\nAquifer depth: 5 m\nRecommendation: go")
    script = {it["prompt"]: ([ok] if it["condition"] == "uncued_nolabel" else ["", ""]) for it in sub}
    monkeypatch.setitem(sys.modules, "kaggle_benchmarks", _stub_kbench(script, []))
    with pytest.raises(RuntimeError, match="no complete uncued pairs"):
        exec(compile(build_task("e2e", sub, score="uncued_paired"), "<generated>", "exec"), {})
