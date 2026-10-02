"""Re-scores downloaded probe runs (uncued report conditions) locally.

Usage: python scripts/analyze_probe.py runs/probe/<task>
Writes raw_outputs.jsonl + summary.json per model run and results/probe.md.
"""

import glob
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from kaggle.build_task import MAX_TOKENS  # noqa: E402
from scoring.dispatch import score_any  # noqa: E402

ITEMS = {it["id"]: it
         for f in ("probe_items.json", "control_items.json")
         for it in json.loads((ROOT / "items" / f).read_text(encoding="utf-8"))["items"]}
CLASSES = ("deferred", "derived", "flagged", "other", "empty", "missing")


def load(run_dir):
    rows, main = [], None
    for f in sorted(glob.glob(os.path.join(run_dir, "*.run.json"))):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        res = (d.get("results") or [{}])[0]
        if "-item-run_param_id_" not in f:
            main = (res.get("numericResult") or {}).get("value")
            continue
        dr = res.get("dictResult") or {}
        reqs = [q for c in d.get("conversations", []) for q in c.get("requests", [])]
        last = reqs[-1].get("metrics", {}) if reqs else {}
        rows.append({
            "item_id": dr.get("item_id"), "state": d.get("state"), "attempts": int(dr.get("attempts", 0)),
            "reply": dr.get("reply"), "kaggle_status": dr.get("status"), "kaggle_pass": dr.get("pass"),
            "output_tokens_last": int(last.get("outputTokens", 0)),
            "cost_usd": sum(int(q.get("metrics", {}).get(k, 0)) for q in reqs
                            for k in ("inputTokensCostNanodollars", "outputTokensCostNanodollars")) / 1e9,
            "model": d["modelVersion"].get("slug") if isinstance(d.get("modelVersion"), dict) else d.get("modelVersion"),
        })
    return rows, main


def analyze(run_dir):
    rows, main = load(run_dir)
    assert all(r["item_id"] in ITEMS for r in rows), "unknown item ids"
    for r in rows:
        it = ITEMS[r["item_id"]]
        s = score_any(it, r["reply"], truncated=r["output_tokens_last"] >= MAX_TOKENS - 16)
        r.update(status=s["status"], local_pass=s["pass"], rows=s.get("rows", []),
                 condition=it["condition"], level=it["level"], twin=it["twin"])
    ok = [r for r in rows if r["status"] == "ok"]
    summ = {"model": rows[0]["model"], "calls": len(rows), "kaggle_main_score": main,
            "local_score": round(sum(r["local_pass"] for r in ok) / len(ok), 4) if ok else None,
            "kaggle_vs_local_mismatch": sum(r["kaggle_pass"] != r["local_pass"] for r in rows),
            "infra": sum(r["status"] == "infra" for r in rows),
            "retried": sum(r["attempts"] > 1 for r in rows),
            "cost_usd": round(sum(r["cost_usd"] for r in rows), 4)}

    def classes(selected):
        c = Counter(x["class"] for r in selected for x in r["rows"])
        return {k: c.get(k, 0) for k in CLASSES}

    single = [r for r in ok if r["condition"] == "uncued_single"]
    summ["single_correct_label"] = classes([r for r in single if r["twin"] == "correct_label"])
    summ["single_wrong_label"] = classes([r for r in single if r["twin"] == "wrong_label"])
    for level in ("senior_review", "contract"):
        summ[f"authority_{level}"] = classes([r for r in ok if r["condition"] == "uncued_authority" and r["level"] == level])
    multi = [r for r in ok if r["condition"] == "uncued_multi"]
    summ["multi_wrong_rows"] = Counter(x["class"] for r in multi for x in r["rows"] if not x["label_truth"])
    summ["multi_correct_rows"] = Counter(x["class"] for r in multi for x in r["rows"] if x["label_truth"])
    summ["multi_reports_all_correct"] = f'{sum(r["local_pass"] for r in multi)}/{len(multi)}'
    summ["nolabel"] = classes([r for r in ok if r["condition"] == "uncued_nolabel"])
    # Per station: every scored row, plus infra failures, by condition
    per = {}
    for r in rows:
        it = ITEMS[r["item_id"]]
        tag = it["condition"] + ("/" + it["level"] if it["condition"] == "uncued_authority" else "")             + ("/" + it["twin"] if it["condition"] == "uncued_single" else "")
        if r["status"] == "infra":
            for s in it["stations"]:
                per.setdefault(s["name"], []).append(f"{tag}: INFRA")
            continue
        for x in r["rows"]:
            t = tag if it["condition"] != "uncued_multi" else f"multi/{'correct' if x['label_truth'] else 'wrong'}"
            per.setdefault(x["name"], []).append(f"{t}: {x['class']} ({x['field']!r})")
    summ["per_station"] = per
    summ["distinct_stations_scored"] = len({x["name"] for r in ok for x in r["rows"]})

    with open(os.path.join(run_dir, "raw_outputs.jsonl"), "w", encoding="utf-8") as fh:
        for r in sorted(rows, key=lambda r: r["item_id"]):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    Path(run_dir, "summary.json").write_text(json.dumps(summ, indent=1, default=dict), encoding="utf-8")
    return summ


def main():
    base = sys.argv[1]
    dirs = sorted({os.path.dirname(f) for f in glob.glob(os.path.join(base, "*", "*", "*", "*.run.json"))})
    for d in dirs:
        s = analyze(d)
        print(f"\n=== {s['model']}: calls={s['calls']} infra={s['infra']} retried={s['retried']} "
              f"kaggle={s['kaggle_main_score']} local={s['local_score']} mismatch={s['kaggle_vs_local_mismatch']} cost=${s['cost_usd']}")
        for k in ("single_correct_label", "single_wrong_label", "authority_senior_review", "authority_contract",
                  "multi_wrong_rows", "multi_correct_rows", "multi_reports_all_correct", "nolabel",
                  "distinct_stations_scored"):
            v = s[k]
            print(f"  {k:26} {dict(v) if isinstance(v, (dict, Counter)) else v}")
        if "--stations" in sys.argv:
            for name, lines in sorted(s["per_station"].items()):
                print(f"    {name}")
                for ln in lines:
                    print(f"      {ln}")


if __name__ == "__main__":
    main()
