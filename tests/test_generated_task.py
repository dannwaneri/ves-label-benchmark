"""The generated Kaggle task file:
- the copied scorer scores exactly like the repo scorer (all item kinds);
- the whole file runs end to end against a stub kaggle_benchmarks module,
  which checks fresh chats, the single retry, and infra exclusion."""

import contextlib
import json
import sys
import types
from pathlib import Path

import pandas as pd
import pytest

from kaggle.build_task import SCORER_END, SCORER_START, build
from scoring.baselines import BASELINES
from scoring.dispatch import score_any

ROOT = Path(__file__).resolve().parent.parent
ITEMS = json.loads((ROOT / "items" / "items.json").read_text(encoding="utf-8"))["items"]
PROBE = json.loads((ROOT / "items" / "probe_items.json").read_text(encoding="utf-8"))["items"]


@pytest.fixture(scope="module")
def inlined():
    code = build("test-task", ITEMS, repeats=2)
    block = code.split(SCORER_START, 1)[1].split(SCORER_END, 1)[0]
    ns = {}
    exec(compile(block, "<inlined-scorer>", "exec"), ns)
    return ns


def test_generated_file_compiles():
    compile(build("test-task", ITEMS + PROBE, repeats=2), "<generated>", "exec")


def test_items_round_trip():
    code = build("test-task", PROBE)
    embedded = json.loads(code.split("ITEMS = json.loads(r'''", 1)[1].split("''')", 1)[0])
    assert embedded == PROBE


@pytest.mark.parametrize("name", list(BASELINES) + ["garbage", "empty"])
def test_inlined_scorer_matches_repo_json_items(inlined, name):
    fn = BASELINES.get(name, lambda it: "" if name == "empty" else '{"curve_type": 5} x {"label_correct": "yes"')
    for it in ITEMS:
        reply = fn(it)
        if reply is None:
            continue
        assert score_any(it, reply) == inlined["score_any"](it, reply)


UNCUED_REPLIES = [
    "", "Station: X\nCurve type: KHA\nAquifer", "Station: X\nCurve type: A-type\nAquifer depth: 9\nRecommendation: go",
    "**Curve type:** HK (does not match the file)\nRecommendation: go",
]


@pytest.mark.parametrize("reply", UNCUED_REPLIES)
def test_inlined_scorer_matches_repo_uncued_items(inlined, reply):
    for it in PROBE:
        assert score_any(it, reply) == inlined["score_any"](it, reply)


# ---------------------------------------------------------------- end-to-end with a stub kbench

class _Runs:
    def __init__(self, results):
        self._results = results
        self.errored_runs = []

    @property
    def completed_runs(self):
        return self

    def as_dataframe(self):
        return pd.DataFrame({"result": self._results})


def _stub_kbench(script, log):
    """script: prompt -> list of replies returned on successive calls."""
    kb = types.ModuleType("kaggle_benchmarks")
    calls = {}

    class LLM:
        def prompt(self, text, extra_api_params=None):
            assert extra_api_params == {"max_tokens": 16000}
            assert kb._open_chats == 1, "prompt must run inside a fresh chat"
            n = calls.get(text, 0)
            calls[text] = n + 1
            log.append(text)
            replies = script[text]
            return replies[min(n, len(replies) - 1)]

    @contextlib.contextmanager
    def new(name):
        kb._open_chats += 1
        yield
        kb._open_chats -= 1

    def task(name=None, store_task=True):
        def deco(fn):
            def evaluate(llm, evaluation_data, **kw):
                return _Runs([fn(llm[0], **row) for row in evaluation_data.to_dict("records")])

            def run(llm):
                kb.result = fn(llm)
            fn.evaluate, fn.run = evaluate, run
            return fn
        return deco

    kb._open_chats = 0
    kb.chats = types.SimpleNamespace(new=new)
    kb.task = task
    kb.llm = LLM()
    return kb


def test_end_to_end_retry_and_infra_exclusion(monkeypatch, capsys):
    a, b, c = PROBE[0], PROBE[1], PROBE[2]  # Choba correct, Choba wrong, Odufor correct
    good = lambda it: (f"Station: {it['stations'][0]['name']}\nCurve type: {it['stations'][0]['derived']}\n"
                       "Aquifer depth: 10-20 m\nRecommendation: drill")
    script = {
        a["prompt"]: [good(a)],                                   # fine first time
        b["prompt"]: ["**Site Note — Station Choba", good(b)],    # cut off, then fine on retry
        c["prompt"]: ["", ""],                                    # empty twice -> infra
    }
    log = []
    monkeypatch.setitem(sys.modules, "kaggle_benchmarks", _stub_kbench(script, log))
    ns = {}
    exec(compile(build("e2e", [a, b, c]), "<generated>", "exec"), ns)
    out = capsys.readouterr().out
    assert sys.modules["kaggle_benchmarks"].result == 1.0          # 2 scored items, both pass
    assert [log.count(it["prompt"]) for it in (a, b, c)] == [1, 2, 2]  # one retry at most
    assert "infra_failures=1" in out
    results = [json.loads(ln[len("ITEM_RESULT "):]) for ln in out.splitlines() if ln.startswith("ITEM_RESULT ")]
    by_id = {r["item_id"]: r for r in results}
    assert by_id[b["id"]]["attempts"] == 2 and by_id[b["id"]]["replies"][0].startswith("**Site Note")
    assert by_id[c["id"]]["status"] == "infra"
