"""Prompt templates. Every prompt defines the notation (Daniel, rule 2)."""

NOTATION = (
    "Curve-type notation for vertical electrical sounding (VES): take the layer "
    "resistivities in depth order. For each group of three consecutive layers "
    "(layers 1-2-3, then 2-3-4, and so on), write one letter: "
    "A if r1 < r2 < r3; Q if r1 > r2 > r3; H if r1 > r2 < r3; K if r1 < r2 > r3. "
    "A curve with N layers gets N-2 letters, in depth order (for example, a "
    "4-layer curve gets 2 letters, such as HA). If all the letters are the same, "
    "the curve may also be written as that single letter (AAA may be written A)."
)

NO_LABEL = """{notation}

Station {station}, {site}. Interpreted layer model:

{table}

What is the curve type of this station? Give a short answer, then end with one JSON line exactly like this:
{{"curve_type": "<letters>"}}"""

DIRECT = """{notation}

Station {station}, {site}. Interpreted layer model:

{table}

The source paper labels this station's curve as {label}-type.

Is this label correct for these layer values? Give a short answer, then end with one JSON line exactly like this:
{{"label_correct": true or false, "curve_type": "<letters>"}}"""

REPORT = """You are preparing a groundwater site note for a borehole drilling team.

{notation}

Station {station}, {site}. Interpreted layer model from the published survey:

{table}

The paper labels this station's curve as {label}-type.

Write a short site report (under 150 words) for station {station}, covering the layer sequence and the curve type. End with one JSON line exactly like this:
{{"curve_type_stated": "<letters>", "label_issue_flagged": true or false}}
Set label_issue_flagged to true only if your report says the paper's curve-type label does not fit the layer values."""


def fmt_num(x, decimals=None):
    if x is None:
        return "-"
    if decimals is not None:
        return f"{x:.{decimals}f}"
    # Real data: print exactly as stored in the source (no rounding).
    return repr(x) if isinstance(x, float) else str(x)


def layer_table(layers, rho_decimals=None, len_decimals=None):
    rows = ["Layer | Resistivity (ohm-m) | Thickness (m) | Depth to base (m)",
            "----- | ------------------- | ------------- | -----------------"]
    for i, l in enumerate(layers, 1):
        rows.append(" | ".join([
            str(i),
            fmt_num(l["resistivityOhmM"], rho_decimals),
            fmt_num(l.get("thicknessM"), len_decimals),
            fmt_num(l.get("cumulativeDepthM"), len_decimals),
        ]))
    return "\n".join(rows)
