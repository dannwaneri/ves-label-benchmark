"""What counts as a correct curve-type answer or label in this benchmark.

Rules (Daniel, 2026-10-02):
- The answer is the full notation: one letter per group of three consecutive
  layers (N layers -> N-2 letters).
- One alias only: a uniform curve may be written as its single letter
  (A for AAA, Q for QQ). Mixed curves are never collapsed.

Note: this deliberately differs from ves-interpretation-agent's checkLabel(),
which collapses only the derived string and so rejects "QQ" for a QQ curve.
"""

import re

VALID = set("AQHK")


def accepted_answers(derived):
    """Set of strings accepted as correct for a derived curve type."""
    if not derived or not set(derived) <= VALID:
        raise ValueError(f"derived type must be letters A/Q/H/K only, got {derived!r}")
    answers = {derived}
    if len(set(derived)) == 1:
        answers.add(derived[0])
    return answers


def normalize_type(text):
    """Normalize a model's stated type. Returns None if it is not a type.

    Accepts case and spacing differences and a trailing "type"/"-type"
    ("ha-type", "HA type", " ha "). Rejects anything else, such as "H-A",
    "HA or KA", or "A (AAA)".
    """
    if not isinstance(text, str):
        return None
    t = text.strip().upper()
    t = re.sub(r"[\s-]*TYPE$", "", t).strip()
    if not t or not set(t) <= VALID:
        return None
    return t


def is_correct_type(stated, derived):
    norm = normalize_type(stated)
    return norm is not None and norm in accepted_answers(derived)


def label_is_correct(label, derived):
    """Ground truth for a label shown in a prompt."""
    return is_correct_type(label, derived)
