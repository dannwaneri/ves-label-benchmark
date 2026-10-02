"""Hand-written model outputs with known expected scores."""

import pytest

from scoring.score import aggregate, extract_last_json, score_item


def item(task, derived="KHA", twin=None, framing=None, label=None, truth=None, sid="s1", slc="real"):
    return {"id": f"{sid}|{task}|{twin}|{framing}", "slice": slc, "station_id": sid, "task": task,
            "twin": twin, "framing": framing, "derived": derived, "label": label, "label_truth": truth}


NL = item("no_label")
D_OK = item("label", twin="correct_label", framing="direct", label="KHA", truth=True)
D_BAD = item("label", twin="wrong_label", framing="direct", label="A", truth=False)
R_OK = item("label", twin="correct_label", framing="report", label="KHA", truth=True)
R_BAD = item("label", twin="wrong_label", framing="report", label="A", truth=False)


# --- parser ---

def test_parser_takes_last_json_object():
    obj, last = extract_last_json('first {"curve_type": "A"} then\n{"curve_type": "KHA"}')
    assert obj == {"curve_type": "KHA"} and last is True


def test_parser_code_fence_counts_as_last_line():
    obj, last = extract_last_json('Answer:\n```json\n{"curve_type": "KHA"}\n```')
    assert obj == {"curve_type": "KHA"} and last is True


def test_parser_records_trailing_text():
    obj, last = extract_last_json('{"curve_type": "KHA"}\nHope this helps.')
    assert obj == {"curve_type": "KHA"} and last is False


def test_parser_skips_broken_json_and_uses_earlier_valid():
    obj, _ = extract_last_json('{"curve_type": "KHA"}\n{"curve_type": "KH')
    assert obj == {"curve_type": "KHA"}


def test_parser_nested_braces_inside_object():
    obj, _ = extract_last_json('{"curve_type": "KHA", "note": {"x": 1}}')
    assert obj["curve_type"] == "KHA"


# --- no_label ---

@pytest.mark.parametrize("reply,passed,status", [
    ('The curve is KHA.\n{"curve_type": "KHA"}', True, "ok"),
    ('{"curve_type": "kha-type"}', True, "ok"),
    ('{"curve_type": "A"}', False, "ok"),          # the published mislabel
    ('{"curve_type": "K-H-A"}', False, "ok"),      # not the notation
    ('It is KHA.', False, "no_json"),              # missing JSON
    ('{"curve_type": "KHA"', False, "no_json"),    # malformed JSON
    ('{"type": "KHA"}', False, "bad_field"),       # wrong key
    ('{"curve_type": ["KHA"]}', False, "bad_field"),
])
def test_no_label(reply, passed, status):
    s = score_item(NL, reply)
    assert (s["pass"], s["status"]) == (passed, status)


def test_no_label_uniform_alias():
    it = item("no_label", derived="AAA")
    assert score_item(it, '{"curve_type": "A"}')["pass"] is True
    assert score_item(it, '{"curve_type": "AAA"}')["pass"] is True
    assert score_item(it, '{"curve_type": "AA"}')["pass"] is False


# --- direct framing ---

@pytest.mark.parametrize("it,reply,passed,status", [
    (D_OK, '{"label_correct": true, "curve_type": "KHA"}', True, "ok"),
    (D_OK, '{"label_correct": false, "curve_type": "KHA"}', False, "ok"),
    (D_BAD, '{"label_correct": false, "curve_type": "KHA"}', True, "ok"),
    (D_BAD, '{"label_correct": true, "curve_type": "A"}', False, "ok"),
    (D_BAD, '{"label_correct": "false", "curve_type": "KHA"}', False, "bad_field"),  # string, not bool
    (D_BAD, '{"curve_type": "KHA"}', False, "bad_field"),
    (D_BAD, 'The label is wrong.', False, "no_json"),
])
def test_direct(it, reply, passed, status):
    s = score_item(it, reply)
    assert (s["pass"], s["status"]) == (passed, status)


# --- report framing ---

@pytest.mark.parametrize("it,reply,passed,status", [
    (R_OK, 'Report...\n{"curve_type_stated": "KHA", "label_issue_flagged": false}', True, "ok"),
    (R_OK, '{"curve_type_stated": "KHA", "label_issue_flagged": true}', False, "ok"),
    (R_BAD, '{"curve_type_stated": "KHA", "label_issue_flagged": true}', True, "ok"),
    (R_BAD, '{"curve_type_stated": "A", "label_issue_flagged": false}', False, "ok"),
    (R_BAD, '{"curve_type_stated": "KHA", "label_issue_flagged": 1}', False, "bad_field"),
    (R_BAD, '{"curve_type_stated": "KHA", "label_issue_flagged": tru}', False, "no_json"),
])
def test_report(it, reply, passed, status):
    s = score_item(it, reply)
    assert (s["pass"], s["status"]) == (passed, status)


def test_truncated_flag_is_recorded():
    assert score_item(NL, "The curve", truncated=True)["truncated"] is True


# --- paired scoring and aggregation ---

def run(replies):
    items = [NL, D_OK, D_BAD, R_OK, R_BAD]
    scored = [score_item(it, replies[it["id"]]) for it in items]
    return aggregate(items, scored)["real"]


def test_paired_needs_both_twins():
    good = '{"label_correct": true, "curve_type": "KHA"}'
    agg = run({NL["id"]: '{"curve_type": "KHA"}',
               D_OK["id"]: good, D_BAD["id"]: '{"label_correct": false, "curve_type": "KHA"}',
               R_OK["id"]: '{"curve_type_stated": "KHA", "label_issue_flagged": false}',
               R_BAD["id"]: '{"curve_type_stated": "KHA", "label_issue_flagged": false}'})
    assert agg["no_label"]["accuracy"] == 100.0
    assert agg["paired_direct"]["paired_score"] == 100.0
    assert agg["paired_report"]["paired_score"] == 0.0           # missed the wrong label
    assert agg["paired_report"]["right_type_but_wrong_label_missed"] == 1


def test_flagging_everything_scores_zero():
    agg = run({NL["id"]: "x",
               D_OK["id"]: '{"label_correct": false, "curve_type": "KHA"}',
               D_BAD["id"]: '{"label_correct": false, "curve_type": "KHA"}',
               R_OK["id"]: '{"curve_type_stated": "KHA", "label_issue_flagged": true}',
               R_BAD["id"]: '{"curve_type_stated": "KHA", "label_issue_flagged": true}'})
    assert agg["paired_direct"]["paired_score"] == 0.0
    assert agg["paired_report"]["paired_score"] == 0.0
    assert agg["format_failures"] == 1


def test_slices_are_kept_separate():
    a = item("no_label", sid="r", slc="real")
    b = item("no_label", sid="s", slc="synthetic")
    agg = aggregate([a, b], [score_item(a, '{"curve_type": "KHA"}'), score_item(b, "none")])
    assert agg["real"]["no_label"]["accuracy"] == 100.0
    assert agg["synthetic"]["no_label"]["accuracy"] == 0.0


def test_no_json_on_wrong_label_twin_does_not_crash_aggregate():
    # Found in the pilot: a reply with no JSON left type_correct as None and
    # the knowing-vs-acting count raised TypeError.
    agg = run({NL["id"]: '{"curve_type": "KHA"}',
               D_OK["id"]: '{"label_correct": true, "curve_type": "KHA"}',
               D_BAD["id"]: "The label is wrong.",
               R_OK["id"]: '{"curve_type_stated": "KHA", "label_issue_flagged": false}',
               R_BAD["id"]: "Report without the JSON line."})
    assert agg["paired_direct"]["paired_score"] == 0.0
    assert agg["paired_report"]["right_type_but_wrong_label_missed"] == 0
    assert agg["format_failures"] == 2
