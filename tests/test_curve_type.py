import json
from pathlib import Path

import pytest

from scoring.curve_type import check_label, derive_curve_type, label_matches

EXPORT = Path(__file__).resolve().parent.parent / "data" / "source" / "sanity_production_2026-10-02.json"


def layers(*rho):
    return [{"layerIndex": i + 1, "resistivityOhmM": r} for i, r in enumerate(rho)]


# --- ported from ves-interpretation-agent/agent/curveType.test.js ---

def test_a_type():
    assert derive_curve_type(layers(1, 2, 3)) == "A"


def test_q_type():
    assert derive_curve_type(layers(3, 2, 1)) == "Q"


def test_h_type():
    assert derive_curve_type(layers(5, 2, 4)) == "H"


def test_k_type():
    assert derive_curve_type(layers(2, 5, 3)) == "K"


def test_four_layers_give_two_letters():
    assert derive_curve_type(layers(5, 2, 4, 6)) == "HA"


def test_equal_adjacent_values_are_undecidable():
    assert derive_curve_type(layers(3, 3, 5)) == "?"


def test_fewer_than_three_layers_raises():
    with pytest.raises(ValueError):
        derive_curve_type(layers(1, 2))


@pytest.mark.parametrize("station,rho,derived,matches", [
    ("Choba-LawnTennisField", (91.2, 380.2, 43.25, 474.3, 597.1), "KHA", False),
    ("Egwi", (295.88, 798.6, 864.62, 1810.2, 5634.2), "AAA", True),
    ("Odufor", (20.32, 851.16, 2511.9, 1345), "AK", False),
    ("Opiro", (54.639, 9147.8, 1119.9, 2566.8), "KH", False),
])
def test_real_a_labels(station, rho, derived, matches):
    res = check_label({"station": station, "curveTypePublished": "A", "layers": layers(*rho)})
    assert res["derived"] == derived
    assert res["matches"] is matches


# --- new for the benchmark ---

def test_near_equal_values_still_decide():
    # 1000 vs 1000.001: strict comparison, no rounding.
    assert derive_curve_type(layers(1000, 1000.001, 999.999)) == "K"


def test_order_comes_from_layer_index_not_list_order():
    shuffled = [{"layerIndex": 3, "resistivityOhmM": 4},
                {"layerIndex": 1, "resistivityOhmM": 5},
                {"layerIndex": 2, "resistivityOhmM": 2}]
    assert check_label({"layers": shuffled, "curveTypePublished": "H"})["matches"] is True


def test_label_is_trimmed_and_uppercased():
    assert label_matches(layers(5, 2, 4, 6), "  ha ") is True


def test_uniform_long_curve_matches_single_letter_and_full_string():
    assert label_matches(layers(5, 4, 3, 2), "Q") is True
    assert label_matches(layers(5, 4, 3, 2), "QQ") is False  # JS collapses derived only


def test_mixed_curve_never_matches_one_letter():
    for letter in "AQHK":
        assert label_matches(layers(5, 2, 4, 6), letter) is False


def test_empty_label_never_matches():
    assert label_matches(layers(1, 2, 3), "") is False


# Every real station: derived type and label result, as produced by the
# ORIGINAL JS on 2026-10-02 (see crosscheck/run_crosscheck.py output).
REAL = {
    "reading-bori-bank-road": ("AA", None),
    "reading-bori-bmgs-bori-field": ("KQHA", None),
    "reading-bori-bmgs-bori-field-p7table": ("KHK", None),
    "reading-bori-bori-police-station": ("HA", None),
    "reading-bori-court-road": ("AKH", None),
    "reading-bori-gokana-street": ("HAA", None),
    "reading-bori-kenpoly-convocation-arena": ("KHK", None),
    "reading-bori-kenpoly-sec-school-field": ("KHK", None),
    "reading-bori-kenpoly-sec-school-field-p7table": ("KQHA", None),
    "reading-bori-kogam-street": ("HAA", None),
    "reading-bori-kor-road": ("HK", None),
    "reading-bori-maakoro-street": ("KHKH", None),
    "reading-bori-market-road": ("AAK", None),
    "reading-bori-monokpo-street": ("HAA", None),
    "reading-bori-tigidam-street": ("KHA", None),
    "reading-choba-choba-lawntennisfield": ("KHA", False),
    "reading-etche-akpoku": ("AKHA", False),
    "reading-etche-egwi": ("AAA", True),
    "reading-etche-ndashi": ("AKQH", False),
    "reading-etche-odufor": ("AK", False),
    "reading-etche-okehi": ("KH", True),
    "reading-etche-opiro": ("KH", False),
    "reading-etche-ulakwo": ("AA", True),
    "reading-etche-umuokom": ("AKQH", False),
}


def test_every_real_station():
    docs = json.loads(EXPORT.read_text(encoding="utf-8"))["result"]
    readings = {d["_id"]: d for d in docs if d["_type"] == "vesReading"}
    assert set(readings) == set(REAL)
    for _id, (derived, matches) in REAL.items():
        res = check_label(readings[_id])
        assert res["derived"] == derived, _id
        if matches is not None:
            assert res["matches"] is matches, _id
