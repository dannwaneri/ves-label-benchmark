"""Static figures for the post (PNG). Numbers come from the analysis summaries
(runs/full/**/summary.json), never typed by hand.

Palette: dataviz reference categorical slots 1-3 (validated, light surface);
aqua is below 3:1 on the surface, so every mark carries a visible value label.

Usage: python scripts/charts.py  -> results/figures/*.png
"""

import glob
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "figures"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
NAMES = {"google/gemini-3.7-flash": "Gemini 3.7 Flash", "anthropic/claude-sonnet-5@default": "Claude Sonnet 5",
         "google/gemma-4-26b-a4b": "Gemma 4 26B"}
ORDER = ["google/gemini-3.7-flash", "anthropic/claude-sonnet-5@default", "google/gemma-4-26b-a4b"]


def summaries(task):
    out = {}
    for f in glob.glob(str(ROOT / "runs" / "full" / task / "*" / "*" / "*" / "summary.json")):
        s = json.loads(Path(f).read_text(encoding="utf-8"))
        out[s["model"]] = s
    return out


def direct_accepted(s):
    """Share of wrong-label direct questions answered 'label correct'.
    The summaries hold paired counts only; when every pair passed, every wrong
    label was rejected, so the share is exactly 0. Otherwise refuse to guess."""
    p = s["cued"]["paired_direct"]
    if not p["complete"] or p["pass"] != p["complete"]:
        raise ValueError(f"{s['model']}: direct pairs not all passed; compute accepted share from raw outputs")
    return 0.0, None


def rates(s):
    u, r = s["deference_uncued"], s["deference_rule"]
    rate = lambda t: (t.get("deference", 0) / t["own_right"], t.get("deference", 0), t["own_right"]) \
        if t.get("own_right") else (None, 0, 0)
    d, _ = direct_accepted(s)
    return {"direct": (d, None, None), "rule": rate(r), "note": rate(u)}


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK2, length=0)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def ladder(task="ves-real", fname="chart_ladder.png", title_slice="real slice"):
    S = summaries(task)
    models = [m for m in ORDER if m in S]
    fig, ax = plt.subplots(figsize=(9, 3.9), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    style(ax)
    series = [("direct", "Asked directly: \"is this label correct?\"", BLUE),
              ("rule", "Site note, rule given as a reference note", ORANGE),
              ("note", "Plain site note", AQUA)]
    for i, m in enumerate(models):
        y = len(models) - 1 - i
        R = rates(S[m])
        xs = [R[k][0] * 100 for k, _, _ in series if R[k][0] is not None]
        ax.plot([min(xs), max(xs)], [y, y], color=GRID, linewidth=2, zorder=1, solid_capstyle="round")
        for j, (k, _, col) in enumerate(series):
            v, num, den = R[k]
            if v is None:
                continue
            ax.scatter(v * 100, y, s=110, color=col, edgecolors=SURFACE, linewidths=2, zorder=3)
            label = f"{v * 100:.0f}%" + (f" ({num}/{den})" if den is not None and den < 20 else "")
            dy = 0.24 if j != 1 else -0.30  # rule labels below, others above: avoids collisions
            ax.annotate(label, (v * 100, y + dy), ha="center", va="center", fontsize=8.5, color=INK)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels([NAMES[m] for m in reversed(models)], fontsize=10, color=INK)
    ax.set_xlim(-5, 108)
    ax.set_ylim(-0.6, len(models) - 0.4)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=9)
    handles = [plt.Line2D([], [], marker="o", linestyle="", markersize=8, color=c, label=l) for _, l, c in series]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=3, frameon=False,
              fontsize=8.5, labelcolor=INK)
    fig.suptitle("Asked directly, no model accepted a wrong label. In a site note, they repeated it.",
                 x=0.02, ha="left", fontsize=12, color=INK, y=1.12, fontweight="bold")
    fig.text(0.02, 1.045, f"Share of wrong labels accepted or repeated, {title_slice}, 3 repeats",
             fontsize=9.5, color=INK2, ha="left")
    fig.text(0.02, -0.05, "Only station-repeats where the model's own no-label answer was right. Gemma 4 could "
             "classify few curves without the rule,\nso its plain-site-note rate rests on few cases. Asked directly: "
             "share of wrong labels it called correct. Source: ves-label-benchmark.",
             fontsize=7.5, color=INK2, ha="left", va="top")
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / fname, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return OUT / fname


if __name__ == "__main__":
    print(ladder())
