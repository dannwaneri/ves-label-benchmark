"""Checks a layer table for internal depth arithmetic.

Port of ves-interpretation-agent/agent/depthArithmetic.js. Each layer's
cumulative depth should equal the previous layer's cumulative depth plus this
layer's thickness. A mismatch says the two printed numbers disagree; it does
NOT say which one is wrong.

Tolerance 0.5 m: largest known rounding drift on a clean station is 0.300 m
(Bori Court-road); smallest known real inconsistency is 0.795 m (Etche Akpoku).
"""

from decimal import ROUND_HALF_UP, Decimal

TOLERANCE_M = 0.5


def _is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _round4(x):
    # JS: Number(x.toFixed(4)). toFixed rounds the exact binary value and
    # breaks ties away from zero; Python's format would break ties to even.
    return float(Decimal(x).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def sort_layers_by_index(layers):
    return sorted(layers, key=lambda l: l.get("layerIndex") if l.get("layerIndex") is not None else 0)


def check_depth_arithmetic(reading):
    layers = sort_layers_by_index(reading.get("layers") or [])
    for i in range(1, len(layers)):
        prev, cur = layers[i - 1], layers[i]
        if not (
            _is_number(prev.get("cumulativeDepthM"))
            and _is_number(cur.get("cumulativeDepthM"))
            and _is_number(cur.get("thicknessM"))
        ):
            continue
        implied_depth = prev["cumulativeDepthM"] + cur["thicknessM"]
        implied_thickness = cur["cumulativeDepthM"] - prev["cumulativeDepthM"]
        diff = abs(implied_depth - cur["cumulativeDepthM"])
        if diff > TOLERANCE_M:
            return {
                "station": reading.get("station"),
                "matches": False,
                "layerIndex": cur.get("layerIndex"),
                "priorCumulativeDepthM": prev["cumulativeDepthM"],
                "printedThicknessM": cur["thicknessM"],
                "printedCumulativeDepthM": cur["cumulativeDepthM"],
                "impliedDepthIfThicknessCorrect": _round4(implied_depth),
                "impliedThicknessIfDepthCorrect": _round4(implied_thickness),
            }
    return {"station": reading.get("station"), "matches": True}
