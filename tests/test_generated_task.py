"""The scorer copied into a generated Kaggle task must score exactly like the
repo scorer, on every item, for every baseline's replies."""

import json
from pathlib import Path

import pytest

from kaggle.build_task import SCORER_END, SCORER_START, build
from scoring.baselines import BASELINES
from scoring.score import aggregate, score_item

ITEMS = json.loads((Path(__file__).resolve().parent.parent / "items" / "items.json")
                   .read_text(encoding="utf-8"))["items"]


@pytest.fixture(scope="module")
def code():
    return build("test-task", ITEMS, repeats=2)


@pytest.fixture(scope="module")
def inlined(code):
    block = code.split(SCORER_START, 1)[1].split(SCORER_END, 1)[0]
    ns = {}
    exec(compile(block, "<inlined-scorer>", "exec"), ns)
    return ns


def test_generated_file_compiles(code):
    compile(code, "<generated>", "exec")


def test_items_round_trip(code):
    embedded = json.loads(code.split("ITEMS = json.loads(r'''", 1)[1].split("''')", 1)[0])
    assert [it["prompt"] for it in embedded] == [it["prompt"] for it in ITEMS]


@pytest.mark.parametrize("name", list(BASELINES) + ["garbage"])
def test_inlined_scorer_matches_repo(inlined, name):
    fn = BASELINES.get(name, lambda it: '{"curve_type": 5} trailing {"label_correct": "yes"')
    items, repo, copy = [], [], []
    for it in ITEMS:
        reply = fn(it)
        if reply is None:
            continue
        items.append(it)
        repo.append(score_item(it, reply))
        copy.append(inlined["score_item"](it, reply))
    assert repo == copy
    assert aggregate(items, repo) == inlined["aggregate"](items, copy)
