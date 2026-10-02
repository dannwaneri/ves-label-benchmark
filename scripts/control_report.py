"""Builds results/control.md from the analyzed control, check and probe runs.
Run scripts/analyze_probe.py on each run directory first."""

import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def summaries(rel):
    out = {}
    for f in glob.glob(str(ROOT / rel / "*" / "*" / "*" / "summary.json")):
        s = json.loads(Path(f).read_text(encoding="utf-8"))
        out[s["model"]] = s
    return out


CTRL = summaries("runs/control/control-ves-nolabel")
CHK = summaries("runs/check/check-strong-uncued")
PRB = summaries("runs/probe/probe-ves-uncued")
MODELS = [("google/gemini-3.7-flash", "Gemini 3.7 Flash"),
          ("anthropic/claude-sonnet-5@default", "Claude Sonnet 5"),
          ("google/gemma-4-26b-a4b", "Gemma 4 26B")]
WRONG = {"Choba-LawnTennisField": "A", "Kor-road": "AK", "Odufor": "A", "Opiro": "A", "Egwi": "HAA"}


def first(lines, prefix):
    return next((l.split(": ", 1)[1] for l in lines if l.startswith(prefix)), None)


def fmt(x):
    if x is None or x.startswith("INFRA"):
        return "-"
    cls, field = x.split(" ", 1)
    field = field.strip("()'")
    return {"derived": "ok", "other": f"wrong ({field})", "deferred": f"copied ({field})",
            "flagged": f"flagged ({field})", "empty": "empty"}.get(cls, cls)


def main():
    L = ["# Control probe: uncued site note, layers only, NO label", "",
         "Task `control-ves-nolabel` (private), run 2026-10-02, 1 repeat, 10 distinct real stations.",
         "Same uncued template as the probe; no label, no notation, no checking cue.",
         "Strong-model check `check-strong-uncued`: Sonnet 5 completed 5/5 items (Kor-road, Choba, Odufor",
         "included); the pre-declared rule was 5/5, so Sonnet 5 replaces Opus 5 here.",
         "No claim is made about the cause of the Opus 5 empty replies.", "",
         "## Control: can the model classify without a label? (10 distinct stations)", "",
         "| Model | Derived type stated | Other type | Empty/missing | Infra | Cost |", "|---|---|---|---|---|---|"]
    for m, n in MODELS:
        s = CTRL[m]
        c = s["nolabel"]
        L.append(f'| {n} | {c["derived"]}/10 | {c["other"]}/10 | {c["empty"] + c["missing"]}/10 | '
                 f'{s["infra"]} | ${s["cost_usd"]} |')
    L += ["", "## Same station: no label (control) vs wrong label on file (uncued single, plain level)", "",
          "`ok` = stated the derived type; `wrong (X)` = stated another type; `copied (X)` = repeated the "
          "wrong label; `-` = not run.", "",
          "| Station | Wrong label shown | Model | Control (no label) | With wrong label |", "|---|---|---|---|---|"]
    for st in WRONG:
        for m, n in MODELS:
            c = first(CTRL[m]["per_station"].get(st, []), "uncued_nolabel")
            w = None
            for src in (CHK.get(m), PRB.get(m)):
                if src and w is None:
                    w = first(src["per_station"].get(st, []), "uncued_single/wrong_label")
            L.append(f"| {st} | {WRONG[st]} | {n} | {fmt(c)} | {fmt(w)} |")
    L += ["", "## Correct-label items in the uncued set", "",
          "When the label on file is correct, copying it and deriving it give the same answer; "
          "these rows can only show over-flagging.", "",
          "| Model | Source | Correct-label rows kept | Over-flagged |", "|---|---|---|---|"]
    for m, n, src, name in [("google/gemma-4-26b-a4b", "Gemma 4 26B", PRB, "probe (5 single + 60 multi rows)"),
                            ("anthropic/claude-opus-5@default", "Claude Opus 5", PRB, "probe, complete replies only"),
                            ("anthropic/claude-sonnet-5@default", "Claude Sonnet 5", CHK, "check (2 single)"),
                            ("google/gemini-3.7-flash", "Gemini 3.7 Flash", CHK, "check (2 single)")]:
        s = src[m]
        sc, mc = s["single_correct_label"], s["multi_correct_rows"]
        kept = sc["derived"] + mc.get("derived", 0)
        over = sc["flagged"] + mc.get("flagged", 0)
        tot = sum(sc.values()) + sum(mc.values())
        L.append(f"| {n} | {name} | {kept}/{tot} | {over} |")
    L += ["", "## Caveats", "",
          "- 1 repeat. 10 distinct stations in the control; 3 (Flash, Sonnet) or 5 (Gemma) stations in the",
          "  station-by-station comparison.",
          "- Real slice only; no synthetic items in this round.",
          "- The probe (with labels) and the control (without) are separate runs at different times.", "",
          "Raw outputs: `runs/control/`, `runs/check/`, `runs/probe/` (raw_outputs.jsonl per model run)."]
    out = "\n".join(L) + "\n"
    (ROOT / "results" / "control.md").write_text(out, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
