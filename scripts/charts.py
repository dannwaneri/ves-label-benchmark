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


def choba_diagram(fname="diagram_choba.png"):
    """One station, five conditions, what Gemini 3.7 Flash wrote (all 3 repeats identical,
    checked against runs/full/ves-real raw outputs before drawing)."""
    GOOD, BAD = "#0ca30c", "#d03b3b"  # status palette: always with a symbol and a word
    rows = [
        ("1  No label", "Layer values only", "KHA", True, "can classify it"),
        ("2  Asked directly", "Rule + label on file \"A\"\n+ \"Is this label correct?\"",
         "label_correct: false (KHA)", True, "caught"),
        ("3  Report with a flag", "Rule + label on file \"A\"\n+ a JSON flag field",
         "label_issue_flagged: true", True, "caught"),
        ("4  Site note + rule", "Site-note template + label \"A\"\n+ rule as a reference note",
         "Curve type: KHA", True, "caught"),
        ("5  Plain site note", "Site-note template\n+ label on file \"A\"",
         "Curve type: A-type", False, "repeated the label"),
    ]
    fig, ax = plt.subplots(figsize=(9.5, 5.0), dpi=200)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.04)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    fig.suptitle("One station, five situations: what Gemini 3.7 Flash wrote", x=0.02, ha="left",
                 fontsize=12.5, fontweight="bold", color=INK, y=0.985)
    ax.text(0, 97, "Choba (published as A-type). Layers: 91.2 < 380.2 > 43.25 < 474.3 < 597.1 ohm-m"
            "  ->  up, down, up, up  ->  K H A", fontsize=8.8, color=INK2, va="top")
    cols = [(0, "Situation"), (27, "What the model saw"), (58, "What it wrote"), (84, "Result")]
    for x, h in cols:
        ax.text(x, 88, h, fontsize=9, color=INK2, fontweight="bold", va="center")
    ax.plot([0, 100], [85, 85], color=GRID, linewidth=1)
    for i, (name, saw, wrote, ok, verdict) in enumerate(rows):
        y = 76 - i * 15.5
        ax.text(0, y, name, fontsize=9.5, color=INK, va="center", fontweight="bold")
        ax.text(27, y, saw, fontsize=8.5, color=INK, va="center", linespacing=1.4)
        ax.text(58, y, wrote, fontsize=8.8, color=INK, va="center", family="monospace")
        ax.text(84, y, ("✓ " if ok else "✗ ") + verdict, fontsize=9, va="center",
                color=GOOD if ok else BAD, fontweight="bold")
        if i < len(rows) - 1:
            ax.plot([0, 100], [y - 7.75, y - 7.75], color=GRID, linewidth=0.6)
    rule_rate = rates(summaries("ves-real")["google/gemini-3.7-flash"])["rule"][0]
    fig.text(0.02, 0.0, "One example station; same answer in all 3 repeats. Across all real stations, Flash still "
             f"repeated {rule_rate * 100:.0f}% of wrong labels in situation 4.\nSource: ves-label-benchmark, real slice.",
             fontsize=7.5, color=INK2, ha="left")
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / fname, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return OUT / fname


def slices_chart(fname="chart_slices.png"):
    """Small multiples, one panel per model: repeated-label rate per slice, site note vs + rule.
    Numbers from scripts/final_tables.py (full runs; Sonnet synthetic-b from its leaderboard run)."""
    import sys
    sys.path.insert(0, str(ROOT))
    from scripts.final_tables import full_runs, leaderboard_runs
    F, LB = full_runs(), leaderboard_runs()
    slices = ["real", "held-out", "synthetic-a", "synthetic-b"]
    models = ["Flash", "Sonnet 5", "Gemma 4"]
    names = {"Flash": "Gemini 3.7 Flash", "Sonnet 5": "Claude Sonnet 5", "Gemma 4": "Gemma 4 26B"}

    def r(t):
        return None if not t.get("own_right") else (t.get("deference", 0) / t["own_right"], t["own_right"])

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), dpi=200, sharey=True)
    fig.patch.set_facecolor(SURFACE)
    for ax, m in zip(axes, models):
        style(ax)
        for i, sl in enumerate(slices):
            y = len(slices) - 1 - i
            if (m, sl) in F:
                note, rule = r(F[(m, sl)]["deference_uncued"]), r(F[(m, sl)]["deference_rule"])
            else:
                note, rule = r(LB[(m, sl)]["uncued"]), None
            pts = [(rule, ORANGE, -0.27), (note, AQUA, 0.27)]
            xs = [v[0] * 100 for v, _, _ in pts if v]
            if len(xs) == 2:
                ax.plot(xs, [y, y], color=GRID, linewidth=2, zorder=1)
            for v, col, dy in pts:
                if not v:
                    continue
                # rule dot drawn larger and underneath, so equal values still show both marks
                big = col == ORANGE
                ax.scatter(v[0] * 100, y, s=150 if big else 60, color=col, edgecolors=SURFACE, linewidths=2,
                           zorder=2 if big else 3)
                lab = f"{v[0] * 100:.0f}%" + (f" (n={v[1]})" if v[1] < 10 else "")
                ax.annotate(lab, (v[0] * 100, y + dy), ha="center", va="center", fontsize=7.2, color=INK)
            if rule is None:
                ax.annotate("rule not run", (50, y - 0.27), ha="center", va="center", fontsize=7, color=INK2)
        ax.set_title(names[m], fontsize=10, color=INK, loc="left")
        ax.set_xlim(-8, 112)
        ax.set_xticks([0, 50, 100])
        ax.set_xticklabels(["0%", "50%", "100%"], fontsize=8)
        ax.set_ylim(-0.7, len(slices) - 0.3)
    axes[0].set_yticks(range(len(slices)))
    axes[0].set_yticklabels(list(reversed(slices)), fontsize=9, color=INK)
    handles = [plt.Line2D([], [], marker="o", linestyle="", markersize=7, color=c, label=l)
               for c, l in ((AQUA, "Plain site note"), (ORANGE, "Site note, rule as a reference note"))]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.01, 0.93), ncol=2, frameon=False, fontsize=8.5)
    fig.suptitle("In a plain site note, every model repeated the wrong label on every slice; Sonnet 5 less often on synthetic stations",
                 x=0.01, ha="left", fontsize=11.5, fontweight="bold", color=INK, y=1.04)
    fig.text(0.01, 0.955, "Share of wrong labels repeated, where the model's own no-label answer was right. 3 repeats.",
             fontsize=8.8, color=INK2, ha="left")
    fig.text(0.01, -0.06, "Gemma 4 could classify few curves without the rule, so its plain-site-note rates rest on few "
             "cases (n shown). Sonnet 5 synthetic-b: leaderboard run, site-note items only.\nAsked directly, every model "
             "caught every wrong label whenever it was asked directly. Source: ves-label-benchmark.", fontsize=7.3, color=INK2, ha="left",
             va="top")
    fig.subplots_adjust(top=0.78, wspace=0.08)
    fig.savefig(OUT / fname, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return OUT / fname


def cover(fname="cover.png"):
    """DEV cover image, 1000x420 (2x for sharpness). Numbers from final_tables (real slice)."""
    import sys
    sys.path.insert(0, str(ROOT))
    from scripts.final_tables import full_runs
    F = full_runs()
    u = F[("Flash", "real")]["deference_uncued"]
    rep = u["deference"] / u["own_right"]
    fig = plt.figure(figsize=(10, 4.2), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    fig.text(0.05, 0.80, "VES Label Check", fontsize=15, color=INK2, fontweight="bold")
    fig.text(0.05, 0.56, "Asked directly, 3 AI models caught", fontsize=27, color=INK, fontweight="bold")
    fig.text(0.05, 0.41, "every wrong label. In a site note,", fontsize=27, color=INK, fontweight="bold")
    fig.text(0.05, 0.26, "they copied it.", fontsize=27, color=INK, fontweight="bold")
    fig.text(0.05, 0.09, f"Gemini 3.7 Flash, 19 real groundwater survey stations: caught 100% when asked, "
             f"repeated {rep * 100:.0f}% in the site note.", fontsize=11, color=INK2)
    fig.add_artist(plt.Line2D([0.05, 0.13], [0.74, 0.74], color=AQUA, linewidth=4))
    fig.savefig(OUT / fname, facecolor=SURFACE)
    plt.close(fig)
    return OUT / fname


if __name__ == "__main__":
    print(ladder())
    print(choba_diagram())
    print(slices_chart())
    print(cover())
