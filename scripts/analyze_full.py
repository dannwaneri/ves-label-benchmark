"""Re-scores full runs locally and writes results/full.md.

Layout (from `kaggle b t download <task>` run inside runs/full/):
  runs/full/<task>/<version>/<model>/<run_id>/*.run.json
For each model run: raw_outputs.jsonl + summary.json next to the run files.

Usage: python scripts/analyze_full.py [--stations]
"""

import glob
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from kaggle.build_task import MAX_TOKENS  # noqa: E402
from scoring.analysis import agreement, by_kind, cued_pairs, deference, wrong_kind_map  # noqa: E402
from scoring.dispatch import score_any  # noqa: E402
from scoring.summary import condition_counts, uncued_paired  # noqa: E402

ITEMS = {it["id"]: it for it in json.loads((ROOT / "items" / "full_items.json").read_text(encoding="utf-8"))["items"]}
KIND_OF = wrong_kind_map(ITEMS)


def load(run_dir):
    rows, main = [], None
    for f in sorted(glob.glob(os.path.join(run_dir, "*.run.json"))):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        res = (d.get("results") or [{}])[0]
        if "-item-run_param_id_" not in f:
            # protobuf omits a zero value: numericResult {} means 0.0
            main = (res["numericResult"].get("value", 0.0) if "numericResult" in res else None)
            continue
        dr = res.get("dictResult") or {}
        reqs = [q for c in d.get("conversations", []) for q in c.get("requests", [])]
        last = reqs[-1].get("metrics", {}) if reqs else {}
        rows.append({
            "item_id": dr.get("item_id"), "rep": int(dr.get("rep", 0)), "attempts": int(dr.get("attempts", 0)),
            "reply": dr.get("reply"), "errors": dr.get("errors"), "kaggle_status": dr.get("status"),
            "kaggle_pass": dr.get("pass"), "output_tokens_last": int(last.get("outputTokens", 0)),
            "cost_usd": sum(int(q.get("metrics", {}).get(k, 0)) for q in reqs
                            for k in ("inputTokensCostNanodollars", "outputTokensCostNanodollars")) / 1e9,
            "model": d["modelVersion"].get("slug") if isinstance(d.get("modelVersion"), dict) else d.get("modelVersion"),
        })
    return rows, main


def analyze(run_dir):
    rows, main = load(run_dir)
    unknown = [r["item_id"] for r in rows if r["item_id"] not in ITEMS]
    assert not unknown, f"unknown item ids: {unknown[:3]}"
    scored = []
    for r in rows:
        s = score_any(ITEMS[r["item_id"]], r["reply"], truncated=r["output_tokens_last"] >= MAX_TOKENS - 16)
        r.update(status=s["status"], local_pass=s["pass"])
        scored.append(dict(s, item_id=r["item_id"], rep=r["rep"]))
    results = [{"item_id": r["item_id"], "rep": r["rep"], "status": r["status"], "pass": r["local_pass"]} for r in rows]
    slc = Counter(ITEMS[r["item_id"]]["slice"] for r in rows).most_common(1)[0][0]
    unc_t, unc_st = deference(ITEMS, scored, "uncued")
    rule_t, rule_st = deference(ITEMS, scored, "rule")
    summ = {
        "model": rows[0]["model"], "slice": slc, "calls": len(rows),
        "reps": sorted({r["rep"] for r in rows}),
        "infra": sum(r["status"] == "infra" for r in rows), "retried": sum(r["attempts"] > 1 for r in rows),
        "kaggle_main_score": main, "local_uncued_paired": uncued_paired(ITEMS, results),
        "local_rule_paired": uncued_paired(ITEMS, results, prefix="rule"),
        "kaggle_vs_local_item_mismatch": sum(r["kaggle_pass"] != r["local_pass"] for r in rows),
        "cost_usd": round(sum(r["cost_usd"] for r in rows), 4),
        "conditions": condition_counts(ITEMS, results), "cued": cued_pairs(ITEMS, scored),
        "deference_uncued": unc_t, "deference_rule": rule_t,
        "agreement": agreement(ITEMS, scored),
        "by_kind_uncued": by_kind(unc_st, KIND_OF), "by_kind_rule": by_kind(rule_st, KIND_OF),
        "per_station_uncued": unc_st, "per_station_rule": rule_st,
    }
    with open(os.path.join(run_dir, "raw_outputs.jsonl"), "w", encoding="utf-8") as fh:
        for r in sorted(rows, key=lambda r: (r["item_id"], r["rep"])):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    Path(run_dir, "summary.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")
    return summ


def pct(a, b):
    return "n/a" if not b else f"{100 * a / b:.0f}% ({a}/{b})"


def report(summaries, stations=False):
    L = ["# Full benchmark results", "",
         "Scored locally from raw replies (scoring/*.py); infra failures excluded and counted.",
         "Leaderboard number = uncued paired pass rate, mean over repeats.", ""]
    by_slice = defaultdict(list)
    for s in summaries:
        by_slice[s["slice"]].append(s)
    for slc in ("real", "synthetic", "heldout"):
        ss = sorted(by_slice.get(slc, []), key=lambda s: s["model"])
        if not ss:
            continue
        L += [f"## Slice: {slc}", "",
              "| Model | Calls | Infra | Uncued paired (leaderboard) | Kaggle score | Rule paired | Cued no_label | Cued direct paired | Cued report paired | Cost |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for s in ss:
            c = s["cued"]
            f = lambda x: "n/a" if x is None else f"{100 * x:.1f}%"
            L.append(f"| {s['model']} | {s['calls']} | {s['infra']} | {f(s['local_uncued_paired'])} | "
                     f"{f(s['kaggle_main_score'])} | {f(s['local_rule_paired'])} | "
                     f"{pct(c['no_label']['pass'], c['no_label']['complete'])} | "
                     f"{pct(c['paired_direct']['pass'], c['paired_direct']['complete'])} | "
                     f"{pct(c['paired_report']['pass'], c['paired_report']['complete'])} | ${s['cost_usd']} |")
        L += ["", "Label on file repeated without checking: counted only for station-repeats where the model's own",
              "no-label answer (same family, same repeat) was right. Where its own answer was wrong, a repeated label",
              "is listed as 'could not classify' and is not counted.", "",
              "| Model | Family | Station-repeats with own answer right | Repeated the label on file | Caught: true type | Caught: label kept + warning | Caught: warning only | Own answer wrong | Repeated anyway (could not classify) | Distinct stations | Stations with any repeat |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for s in ss:
            for fam in ("uncued", "rule"):
                t = s[f"deference_{fam}"]
                n = t.get("own_right", 0)
                L.append(f"| {s['model']} | {fam} | {n} | {pct(t.get('deference', 0), n)} | "
                         f"{t.get('caught_true_type', 0)} | {t.get('caught_with_warning', 0)} | {t.get('caught_flag_only', 0)} | "
                         f"{t.get('own_wrong', 0)} | {t.get('capability_copy', 0)} | {t.get('distinct_stations', 0)} | "
                         f"{t.get('stations_with_deference', 0)} |")
        L += ["", "Label on file repeated, by how the wrong label was made (only station-repeats where the model's own no-label answer was right).", "",
              "| Model | Family | Wrong-label kind | Repeated | Distinct stations (repeated / with own answer right) |",
              "|---|---|---|---|---|"]
        for s in ss:
            for fam in ("uncued", "rule"):
                for kind, v in sorted(s[f"by_kind_{fam}"].items()):
                    L.append(f"| {s['model']} | {fam} | {kind} | {pct(v['copied'], v['own_right'])} | "
                             f"{v['stations_copied']} / {v['stations']} |")
        L += ["", "Run-to-run agreement: items with the same outcome in all 3 repeats (complete in all repeats).", "",
              "| Model | Uncued | Rule | Cued |", "|---|---|---|---|"]
        for s in ss:
            g = s["agreement"]
            cell = lambda f: pct(g.get(f, {}).get("identical", 0), g.get(f, {}).get("items", 0))
            L.append(f"| {s['model']} | {cell('uncued')} | {cell('rule')} | {cell('cued')} |")
        if stations:
            L += ["", "Per station (uncued): repeat -> no-label class / wrong-label class", ""]
            for s in ss:
                L.append(f"**{s['model']}**")
                for sid, cells in sorted(s["per_station_uncued"].items()):
                    L.append(f"- {sid}: " + "; ".join(f"r{c['rep']} {c['nolabel']}/{c['wrong']}" for c in cells))
        L.append("")
    return "\n".join(L) + "\n"


def main():
    dirs = sorted({os.path.dirname(f) for f in glob.glob(str(ROOT / "runs" / "full" / "*" / "*" / "*" / "*" / "*.run.json"))})
    summaries = [analyze(d) for d in dirs]
    out = report(summaries, stations="--stations" in sys.argv)
    (ROOT / "results" / "full.md").write_text(out, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
