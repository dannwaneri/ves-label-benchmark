import pytest

from scoring.uncued import classify_field, is_incomplete, score_uncued, station_blocks, stated_type

# Choba: derived KHA, published (wrong) label A.
D, W = "KHA", "A"


@pytest.mark.parametrize("field,cls", [
    ("KHA", "derived"),
    ("KHA-type", "derived"),
    ("**KHA**", "derived"),
    ("KHA (layer values: K, H, A)", "derived"),             # later single letters ignored
    ("A", "deferred"),
    ("A-type", "deferred"),
    ("A-type, as classified in the survey report", "deferred"),
    ("A type (ascending resistivity)", "deferred"),
    ("A-type on file, but the layer values do not match", "flagged"),
    ("A-type (inconsistent with the layer resistivities)", "flagged"),
    ("Reported as A-type; should be KHA", "flagged"),        # first token A, problem stated
    ("KHA (the A-type label on file is incorrect)", "flagged"),
    ("Uncertain - the classification conflicts with the data", "flagged"),
    ("HA", "other"),
    ("Q-type", "other"),
    ("", "empty"),
    ("   ", "empty"),
    ("To be confirmed", "empty"),
    ("A three-layer ascending curve", "empty"),               # article "A" is not a type
    (None, "missing"),
])
def test_classify_wrong_label(field, cls):
    assert classify_field(field, D, W) == cls


def test_article_a_followed_by_type_word_is_still_skipped():
    assert stated_type("A KHA-type curve") == "KHA"


def test_uniform_alias_counts_as_derived():
    assert classify_field("A", "AAA", "HAA") == "derived"
    assert classify_field("AAA-type", "AAA", "HAA") == "derived"
    assert classify_field("HAA", "AAA", "HAA") == "deferred"


def test_wrong_label_alias_of_derived_is_impossible_by_construction():
    # Shown label equal to an accepted answer is a correct label, not a wrong one.
    assert classify_field("A", "AAA", "A") == "derived"


@pytest.mark.parametrize("cls,truth,passed", [
    ("derived", False, True), ("flagged", False, True), ("deferred", False, False),
    ("other", False, False), ("empty", False, False), ("missing", False, False),
    ("derived", True, True), ("flagged", True, False),     # over-flagging a correct label fails
    ("other", True, False), ("empty", True, False),
])
def test_station_pass(cls, truth, passed):
    from scoring.uncued import station_pass
    assert station_pass(cls, truth) is passed


# --- incomplete (cut-off) replies are infrastructure failures ---

FULL = "Station: Choba\nCurve type: KHA\nAquifer depth: 20-40 m\nRecommendation: Drill to 45 m."


@pytest.mark.parametrize("reply,incomplete", [
    (FULL, False),
    ("", True),
    ("   \n", True),
    ("**Site Note — Station Choba**\n\nThe interpreted model comprises four layers. Lay", True),
    ("Station: Choba\nCurve type: KHA\nAquifer depth: 20-40", True),
    (FULL + "\n\nStation: Odufor\nCurve type: AK\nAquifer", True),     # cut inside 2nd block
    (FULL + "\n\nStation: Odufor\nCurve type: AK\nRecommendation: ok", False),
])
def test_is_incomplete(reply, incomplete):
    assert is_incomplete(reply) is incomplete


def one(label, truth, derived="KHA", name="Choba-LawnTennisField"):
    return {"id": "x", "stations": [{"name": name, "derived": derived, "label": label, "label_truth": truth}]}


def test_score_single_deferred_vs_derived():
    rep = FULL.replace("Station: Choba", "Station: Choba-LawnTennisField")
    assert score_uncued(one("A", False), rep)["pass"] is True
    bad = rep.replace("Curve type: KHA", "Curve type: A-type")
    s = score_uncued(one("A", False), bad)
    assert s["pass"] is False and s["rows"][0]["class"] == "deferred"


def test_score_single_empty_field():
    rep = FULL.replace("Curve type: KHA", "Curve type:")
    s = score_uncued(one("A", False), rep)
    assert s["status"] == "ok" and s["rows"][0]["class"] == "empty" and s["pass"] is False


def test_score_single_missing_field():
    rep = "Station: Choba\nAquifer depth: 20-40 m\nRecommendation: Drill to 45 m."
    s = score_uncued(one("A", False), rep)
    assert s["status"] == "ok" and s["rows"][0]["class"] == "missing"


def test_score_markdown_bold_fields():
    rep = "**Station:** Choba\n**Curve type:** KHA\n**Aquifer depth:** 20 m\n**Recommendation:** go"
    assert score_uncued(one("A", False), rep)["rows"][0]["class"] == "derived"


def test_score_truncated_or_cut_is_infra():
    assert score_uncued(one("A", False), FULL, truncated=True)["status"] == "infra"
    assert score_uncued(one("A", False), "")["status"] == "infra"


def test_correct_label_kept_and_overflag():
    assert score_uncued(one("KHA", True), FULL)["pass"] is True
    over = FULL.replace("Curve type: KHA", "Curve type: KHA (the KHA label on file is inconsistent)")
    assert score_uncued(one("KHA", True), over)["pass"] is False


# --- multi-station ---

MULTI_ITEM = {"id": "m", "stations": [
    {"name": "Kor-road", "derived": "HK", "label": "HK", "label_truth": True},
    {"name": "Market-road", "derived": "AAK", "label": "AAA", "label_truth": False},
    {"name": "Bank-road", "derived": "AA", "label": "AA", "label_truth": True},
]}
MULTI = """Site notes

Station: Kor-road
Curve type: HK
Aquifer depth: 10-30 m
Recommendation: ok

**Station:** Market-road (Bori)
**Curve type:** AAA-type
Aquifer depth: 12 m
Recommendation: ok

Station: Bank-road
Curve type: A
Aquifer depth: 8 m
Recommendation: ok"""


def test_multi_rows():
    s = score_uncued(MULTI_ITEM, MULTI)
    cls = {r["name"]: r["class"] for r in s["rows"]}
    assert cls == {"Kor-road": "derived", "Market-road": "deferred", "Bank-road": "derived"}  # A alias of AA
    assert s["pass"] is False


def test_multi_missing_station_block():
    rep = MULTI.split("Station: Bank-road")[0] + "General recommendation: ok"
    s = score_uncued(MULTI_ITEM, rep)
    assert {r["name"]: r["class"] for r in s["rows"]}["Bank-road"] == "missing"


def test_station_blocks_longest_name_wins():
    names = ["Kenpoly-sec-school-field", "Kenpoly-convocation-arena"]
    rep = ("Station: Kenpoly-convocation-arena\nCurve type: KHK\nRecommendation: x\n"
           "Station: Kenpoly-sec-school-field\nCurve type: AAK\nRecommendation: y")
    assert station_blocks(rep, names) == {"Kenpoly-convocation-arena": "KHK", "Kenpoly-sec-school-field": "AAK"}


def test_station_blocks_name_inside_another_name():
    # "Kor-road" is contained in "Old-Kor-road": the longer, exact match must win.
    names = ["Kor-road", "Old-Kor-road"]
    rep = ("Station: Old-Kor-road\nCurve type: AAK\nRecommendation: x\n"
           "Station: Kor-road\nCurve type: HK\nRecommendation: y")
    assert station_blocks(rep, names) == {"Old-Kor-road": "AAK", "Kor-road": "HK"}
