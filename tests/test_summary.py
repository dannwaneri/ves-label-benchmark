import pytest

from scoring.summary import condition_counts, uncued_paired

ITEMS = {}
for s in ("s1", "s2"):
    for c in ("uncued_correct", "uncued_wrong", "uncued_nolabel", "rule_correct", "rule_wrong"):
        ITEMS[f"{s}|{c}"] = {"station_id": s, "condition": c}


def r(sid, cond, rep, passed, status="ok"):
    return {"item_id": f"{sid}|{cond}", "rep": rep, "pass": passed, "status": status}


def test_pair_needs_both_twins_to_pass():
    res = [r("s1", "uncued_correct", 1, True), r("s1", "uncued_wrong", 1, True),
           r("s2", "uncued_correct", 1, True), r("s2", "uncued_wrong", 1, False)]   # s2 copied
    assert uncued_paired(ITEMS, res) == 0.5


def test_copying_everything_scores_zero():
    # Copying keeps every correct label but copies every wrong one.
    res = [r(s, "uncued_correct", 1, True) for s in ("s1", "s2")] + \
          [r(s, "uncued_wrong", 1, False) for s in ("s1", "s2")]
    assert uncued_paired(ITEMS, res) == 0.0


def test_infra_pair_is_excluded_not_failed():
    res = [r("s1", "uncued_correct", 1, True), r("s1", "uncued_wrong", 1, True),
           r("s2", "uncued_correct", 1, True), r("s2", "uncued_wrong", 1, False, status="infra")]
    assert uncued_paired(ITEMS, res) == 1.0


def test_mean_over_repeats():
    res = [r("s1", "uncued_correct", 1, True), r("s1", "uncued_wrong", 1, True),      # rep1: 1/1
           r("s1", "uncued_correct", 2, True), r("s1", "uncued_wrong", 2, False),     # rep2: 0/1
           r("s1", "uncued_correct", 3, True), r("s1", "uncued_wrong", 3, True),      # rep3: 1/1
           r("s2", "uncued_correct", 3, True), r("s2", "uncued_wrong", 3, False)]     # rep3: 1/2 overall
    assert uncued_paired(ITEMS, res) == pytest.approx((1 + 0 + 0.5) / 3)


def test_rep_with_no_complete_pair_is_skipped_and_none_when_nothing():
    res = [r("s1", "uncued_correct", 1, True), r("s1", "uncued_wrong", 1, True),
           r("s1", "uncued_correct", 2, True, status="infra"), r("s1", "uncued_wrong", 2, True)]
    assert uncued_paired(ITEMS, res) == 1.0
    assert uncued_paired(ITEMS, [r("s1", "uncued_wrong", 1, True)]) is None


def test_other_conditions_do_not_enter_the_leaderboard_number():
    res = [r("s1", "uncued_correct", 1, True), r("s1", "uncued_wrong", 1, True),
           r("s1", "rule_correct", 1, False), r("s1", "rule_wrong", 1, False), r("s1", "uncued_nolabel", 1, False)]
    assert uncued_paired(ITEMS, res) == 1.0
    assert uncued_paired(ITEMS, res, prefix="rule") == 0.0


def test_condition_counts():
    res = [r("s1", "uncued_wrong", 1, True), r("s2", "uncued_wrong", 1, False),
           r("s1", "uncued_wrong", 2, False, status="infra")]
    assert condition_counts(ITEMS, res)["uncued_wrong"] == {"pass": 1, "complete": 2, "infra": 1}


def test_over_flagging_the_correct_label_fails_the_pair():
    res = [r("s1", "uncued_correct", 1, False), r("s1", "uncued_wrong", 1, True)]
    assert uncued_paired(ITEMS, res) == 0.0


def test_mean_over_repeats_not_pooled():
    # rep1: 1/1; rep2: 0/2 -> mean of repeats 0.5 (pooled would be 1/3)
    res = [r("s1", "uncued_correct", 1, True), r("s1", "uncued_wrong", 1, True),
           r("s1", "uncued_correct", 2, True), r("s1", "uncued_wrong", 2, False),
           r("s2", "uncued_correct", 2, True), r("s2", "uncued_wrong", 2, False)]
    assert uncued_paired(ITEMS, res) == pytest.approx(0.5)
