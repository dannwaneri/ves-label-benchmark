import json
from pathlib import Path

from items.build_control import build
from kaggle.build_task import SCORER_END, SCORER_START, build as build_task
from scoring.dispatch import score_any

FILE = Path(__file__).resolve().parent.parent / "items" / "control_items.json"
ITEMS = build()["items"]


def test_committed_file_matches_fresh_build():
    assert json.loads(FILE.read_text(encoding="utf-8"))["items"] == json.loads(json.dumps(ITEMS))


def test_ten_distinct_stations_no_label_no_cue():
    assert len({it["stations"][0]["station_id"] for it in ITEMS}) == 10
    for it in ITEMS:
        p = it["prompt"].lower()
        for w in ("-type", "classif", "label", "check", "notation", "paper", "on file"):
            assert w not in p, (it["id"], w)
        assert it["stations"][0]["label"] is None


def reply(field):
    return f"Station: X\nCurve type: {field}\nAquifer depth: 1 m\nRecommendation: go"


def test_scoring_without_a_label():
    choba = next(it for it in ITEMS if "choba" in it["id"])
    assert score_any(choba, reply("KHA"))["rows"][0]["class"] == "derived"
    assert score_any(choba, reply("KHA"))["pass"] is True
    s = score_any(choba, reply("A-type"))
    assert s["rows"][0]["class"] == "other" and s["pass"] is False   # no label -> never "deferred"
    assert score_any(choba, reply(""))["rows"][0]["class"] == "empty"
    assert score_any(choba, "")["status"] == "infra"


def test_inlined_scorer_matches_on_control_items():
    code = build_task("t", ITEMS)
    ns = {}
    exec(compile(code.split(SCORER_START, 1)[1].split(SCORER_END, 1)[0], "<s>", "exec"), ns)
    for it in ITEMS:
        for r in (reply("KHA"), reply("A"), reply(""), "", "Station: X\nCurve type: HK"):
            assert score_any(it, r) == ns["score_any"](it, r)
