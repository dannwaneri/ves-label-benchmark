import pytest

from scoring.answers import accepted_answers, is_correct_type, label_is_correct, normalize_type
from scoring.curve_type import label_matches as js_label_matches


# --- rule 2: exact full string; one alias for uniform curves only ---

@pytest.mark.parametrize("derived,answer", [
    ("HA", "HA"), ("KHA", "KHA"), ("AKQH", "AKQH"),   # full string
    ("AAA", "AAA"), ("AAA", "A"),                    # uniform: full or alias
    ("QQ", "QQ"), ("QQ", "Q"),
    ("A", "A"),
])
def test_accepted(derived, answer):
    assert is_correct_type(answer, derived)


@pytest.mark.parametrize("derived,answer", [
    ("HA", "H"), ("HA", "A"),            # no collapsing for mixed curves
    ("KHA", "A"), ("KHA", "KH"),         # Choba published label; truncation
    ("AK", "A"), ("KH", "A"),            # Odufor, Opiro published labels
    ("AAA", "AA"), ("AAA", "AAAA"),      # wrong length is not an alias
    ("QQ", "A"), ("HA", "AH"),
])
def test_rejected(derived, answer):
    assert not is_correct_type(answer, derived)


def test_accepted_answers_sets():
    assert accepted_answers("AAA") == {"AAA", "A"}
    assert accepted_answers("QQ") == {"QQ", "Q"}
    assert accepted_answers("HAK") == {"HAK"}


def test_derived_with_question_mark_is_rejected():
    with pytest.raises(ValueError):
        accepted_answers("A?")


def test_differs_from_js_checklabel_on_full_uniform_label():
    # Documented difference: the JS collapses only the derived string.
    layers = [{"layerIndex": i, "resistivityOhmM": r} for i, r in enumerate([9, 5, 3, 1])]
    assert js_label_matches(layers, "QQ") is False
    assert label_is_correct("QQ", "QQ") is True


@pytest.mark.parametrize("raw,norm", [
    ("HA", "HA"), (" ha ", "HA"), ("HA-type", "HA"), ("HA type", "HA"), ("a-TYPE", "A"),
])
def test_normalize_ok(raw, norm):
    assert normalize_type(raw) == norm


@pytest.mark.parametrize("raw", ["H-A", "HA or KA", "A (AAA)", "", "type", "HX", None, 5])
def test_normalize_rejects(raw):
    assert normalize_type(raw) is None
