"""Derives a VES curve type from layer resistivities, in depth order.

Port of ves-interpretation-agent/agent/curveType.js. Behaviour must match the
JS exactly; crosscheck/run_crosscheck.py checks this on every real station and
on generated inputs.

Letter for each group of three consecutive layers:
    A: r1 < r2 < r3    Q: r1 > r2 > r3    H: r1 > r2 < r3    K: r1 < r2 > r3
Equal adjacent values give "?". A 4-layer curve gives 2 letters (e.g. "HA").
"""

from functools import cmp_to_key


def letter_for(r1, r2, r3):
    if r1 == r2 or r2 == r3:
        return "?"
    if r1 < r2 < r3:
        return "A"
    if r1 > r2 > r3:
        return "Q"
    if r1 > r2 and r2 < r3:
        return "H"
    if r1 < r2 and r2 > r3:
        return "K"
    return "?"


def derive_curve_type(layers):
    if not isinstance(layers, list) or len(layers) < 3:
        raise ValueError("derive_curve_type requires at least 3 layers, in depth order")
    r = [layer["resistivityOhmM"] for layer in layers]
    return "".join(letter_for(r[i], r[i + 1], r[i + 2]) for i in range(len(r) - 2))


def _is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _depth_cmp(a, b):
    # Same comparator as the JS: layerIndex when both have one, else depth.
    ai, bi = a.get("layerIndex"), b.get("layerIndex")
    if _is_number(ai) and _is_number(bi):
        return ai - bi
    ad = a.get("cumulativeDepthM")
    bd = b.get("cumulativeDepthM")
    return (0 if ad is None else ad) - (0 if bd is None else bd)


def sort_layers_by_depth(layers):
    return sorted(layers, key=cmp_to_key(_depth_cmp))


def collapse_if_uniform(letters):
    # "AAA" (5 strictly rising layers) is a single-type curve, so it matches
    # the single-letter label "A". A mixed string never matches one letter.
    return letters[0] if len(set(letters)) == 1 else letters


def check_label(reading):
    layers = sort_layers_by_depth(reading.get("layers") or [])
    derived = derive_curve_type(layers)
    published = (reading.get("curveTypePublished") or "").strip().upper()
    return {
        "station": reading.get("station"),
        "derived": derived,
        "published": published,
        "matches": len(published) > 0 and collapse_if_uniform(derived) == published,
    }


def label_matches(layers, label):
    """True if `label` is correct for these layers (depth-ordered)."""
    return check_label({"layers": layers, "curveTypePublished": label})["matches"]
