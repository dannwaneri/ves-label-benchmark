import json
from pathlib import Path

from scoring.depth_check import TOLERANCE_M, check_depth_arithmetic

EXPORT = Path(__file__).resolve().parent.parent / "data" / "source" / "sanity_production_2026-10-02.json"


def reading(*rows, station="Test"):
    return {"station": station, "layers": [
        {"layerIndex": i + 1, "cumulativeDepthM": d, "thicknessM": t} for i, (d, t) in enumerate(rows)]}


# --- ported from ves-interpretation-agent/agent/depthArithmetic.test.js ---

def test_consistent_depths_match():
    assert check_depth_arithmetic(reading((2, 2), (5, 3), (10, 5)))["matches"] is True


def test_tiny_noise_tolerated():
    assert check_depth_arithmetic(reading((2.535, 2.535), (18.37, 15.83)))["matches"] is True


def test_court_road_rounding_not_flagged():
    r = reading((2.56, 2.56), (12.9, 10.4), (62.9, 49.9), (114, 51.4), station="Court-road")
    assert check_depth_arithmetic(r)["matches"] is True


def test_egwi_layer4():
    r = reading((0.9, 0.9), (3.2, 2.3), (6.2935, 3.0935), (37.25, 37.957), station="Egwi")
    res = check_depth_arithmetic(r)
    assert res["matches"] is False
    assert res["layerIndex"] == 4
    assert res["printedCumulativeDepthM"] == 37.25
    assert res["printedThicknessM"] == 37.957
    assert res["impliedDepthIfThicknessCorrect"] == 44.2505
    assert res["impliedThicknessIfDepthCorrect"] == 30.9565


def test_ulakwo_layer2():
    r = reading((0.12415, 0.124), (9.665, 8.25), (47.738, 27.074), (None, None))
    assert check_depth_arithmetic(r)["matches"] is False


def test_okehi_layer3():
    r = reading((0.29506, 0.29506), (0.81449, 0.51943), (39.13, 35.32), (None, None))
    res = check_depth_arithmetic(r)
    assert res["matches"] is False and res["layerIndex"] == 3


def test_akpoku_layer2_small_inconsistency():
    r = reading((0.36897, 0.36897), (0.45729, 0.8832), (4.1889, 3.7316), (33.027, 28.838), (81.135, 48.108))
    res = check_depth_arithmetic(r)
    assert res["matches"] is False and res["layerIndex"] == 2


def test_ndashi_layer5():
    r = reading((0.49701, 0.49701), (2.0866, 1.5896), (6.6232, 4.5367), (24.217, 17.594), (30.85, 16.33))
    res = check_depth_arithmetic(r)
    assert res["matches"] is False and res["layerIndex"] == 5


def test_umuokom_layer5():
    r = reading((0.60549, 0.60549), (0.93718, 0.33169), (5.2477, 4.3105), (35.724, 30.476), (36.766, 10.418))
    res = check_depth_arithmetic(r)
    assert res["matches"] is False and res["layerIndex"] == 5


# --- new for the benchmark ---

def test_tolerance_is_half_metre():
    assert TOLERANCE_M == 0.5
    assert check_depth_arithmetic(reading((1, 1), (3.49, 2)))["matches"] is True   # diff 0.49
    assert check_depth_arithmetic(reading((1, 1), (3.51, 2)))["matches"] is False  # diff 0.51


def test_rounding_ties_go_away_from_zero_like_js_tofixed():
    # implied depth 1 + 0.03125 = 1.03125 exactly in binary: JS toFixed(4) -> 1.0313
    res = check_depth_arithmetic(reading((1, 1), (5, 0.03125)))
    assert res["impliedDepthIfThicknessCorrect"] == 1.0313


# Every real station, as produced by the ORIGINAL JS on 2026-10-02.
FAILING = {
    "reading-etche-akpoku": 2,
    "reading-etche-egwi": 4,
    "reading-etche-ndashi": 5,
    "reading-etche-okehi": 3,
    "reading-etche-ulakwo": 2,
    "reading-etche-umuokom": 5,
}


def test_every_real_station():
    docs = json.loads(EXPORT.read_text(encoding="utf-8"))["result"]
    readings = [d for d in docs if d["_type"] == "vesReading"]
    assert len(readings) == 24
    for r in readings:
        res = check_depth_arithmetic(r)
        if r["_id"] in FAILING:
            assert res["matches"] is False, r["_id"]
            assert res["layerIndex"] == FAILING[r["_id"]], r["_id"]
        else:
            assert res["matches"] is True, r["_id"]
