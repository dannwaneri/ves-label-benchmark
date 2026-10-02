"""Re-scores downloaded Kaggle runs locally from the raw replies.

For each model run under runs/<dir>/<task>/<version>/<model>/<run_id>/:
- reads every item run file: prompt, reply, output tokens, cost
- maps the prompt back to its item (exact text match)
- marks a reply truncated if output tokens reached MAX_TOKENS
- scores with the repo scorer, per repeat
- compares with the score Kaggle recorded for the main task
Writes <run_dir>/raw_outputs.jsonl and <run_dir>/summary.json, prints a table.

Usage: python scripts/analyze_run.py runs/pilot/pilot-ves-label
"""

import glob
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from kaggle.build_task import MAX_TOKENS  # noqa: E402
from scoring.score import aggregate, score_item  # noqa: E402

ITEMS = json.loads((ROOT / "items" / "items.json").read_text(encoding="utf-8"))["items"]
BY_PROMPT = {it["prompt"]: it for it in ITEMS}


def text_of(content):
    return "".join(p.get("text") or "" for p in content.get("parts", []))


def load_model_run(run_dir):
    rows, main_score = [], None
    for f in sorted(glob.glob(os.path.join(run_dir, "*.run.json"))):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        res = (d.get("results") or [{}])[0]
        if "-item-run_param_id_" not in f:
            main_score = (res.get("numericResult") or {}).get("value")
            continue
        req = d["conversations"][0]["requests"][-1]
        user = [text_of(c) for c in req["contents"] if c["role"] == "CONTENT_ROLE_USER"]
        bot = [text_of(c) for c in req["contents"] if c["role"] == "CONTENT_ROLE_ASSISTANT"]
        m = req.get("metrics", {})
        item = BY_PROMPT.get(user[0]) if user else None
        rows.append({
            "file": os.path.basename(f), "state": d.get("state"),
            "item_id": item["id"] if item else None,
            "rep": int((res.get("dictResult") or {}).get("rep", 0)),
            "reply": bot[-1] if bot else None,
            "output_tokens": int(m.get("outputTokens", 0)),
            "cost_usd": (int(m.get("inputTokensCostNanodollars", 0)) + int(m.get("outputTokensCostNanodollars", 0))) / 1e9,
            "kaggle_pass": (res.get("dictResult") or {}).get("pass"),
            "model": d["modelVersion"].get("slug") if isinstance(d.get("modelVersion"), dict) else d.get("modelVersion"),
        })
    return rows, main_score


def analyze(run_dir):
    rows, main_score = load_model_run(run_dir)
    unmatched = [r["file"] for r in rows if r["item_id"] is None]
    assert not unmatched, f"prompts not matched to items: {unmatched[:3]}"
    items_by_id = {it["id"]: it for it in ITEMS}
    task_items = {r["item_id"] for r in rows}
    reps = sorted({r["rep"] for r in rows})
    per_rep, scored_all = {}, []
    for rep in reps:
        rr = [r for r in rows if r["rep"] == rep]
        its = [items_by_id[r["item_id"]] for r in rr]
        sc = []
        for r, it in zip(rr, its):
            s = score_item(it, r["reply"], truncated=r["output_tokens"] >= MAX_TOKENS)
            s["rep"] = rep
            sc.append(s)
            r.update(local_pass=s["pass"], status=s["status"], truncated=s["truncated"])
        scored_all += sc
        per_rep[rep] = {"aggregate": aggregate(its, sc),
                        "item_pass_rate": sum(s["pass"] for s in sc) / len(task_items)}
    # Agreement between repeats, per item
    by_item = defaultdict(dict)
    for r in rows:
        by_item[r["item_id"]][r["rep"]] = r["local_pass"]
    flips = sorted(i for i, v in by_item.items() if len(set(v.values())) > 1)
    local_score = sum(v["item_pass_rate"] for v in per_rep.values()) / len(reps)
    summary = {
        "model": rows[0]["model"], "n_calls": len(rows), "reps": reps,
        "kaggle_main_score": main_score, "local_score": round(local_score, 6),
        "kaggle_vs_local_item_mismatch": sum(r["kaggle_pass"] != r["local_pass"] for r in rows),
        "truncated": sum(r["truncated"] for r in rows),
        "format_failures": sum(r["status"] != "ok" for r in rows),
        "cost_usd": round(sum(r["cost_usd"] for r in rows), 4),
        "max_output_tokens": max(r["output_tokens"] for r in rows),
        "items_that_flip_between_reps": flips,
        "per_rep": per_rep,
    }
    with open(os.path.join(run_dir, "raw_outputs.jsonl"), "w", encoding="utf-8") as fh:
        for r in sorted(rows, key=lambda r: (r["item_id"], r["rep"])):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    Path(run_dir, "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


def main():
    base = sys.argv[1]
    run_dirs = sorted({os.path.dirname(f) for f in glob.glob(os.path.join(base, "*", "*", "*", "*.run.json"))})
    for rd in run_dirs:
        s = analyze(rd)
        print(f"\n=== {s['model']}  ({os.path.relpath(rd, ROOT)})")
        print(f"calls={s['n_calls']} kaggle_score={s['kaggle_main_score']} local_score={s['local_score']} "
              f"item_mismatch={s['kaggle_vs_local_item_mismatch']} truncated={s['truncated']} "
              f"format_fail={s['format_failures']} cost=${s['cost_usd']} max_out_tokens={s['max_output_tokens']}")
        print(f"items that flip between repeats: {s['items_that_flip_between_reps'] or 'none'}")
        for rep, v in s["per_rep"].items():
            a = v["aggregate"]["real"]
            print(f"  rep {rep}: no_label {a['no_label']['pass']}/{a['no_label']['n']} | "
                  f"paired direct {a['paired_direct']['pass']}/{a['paired_direct']['stations']} | "
                  f"paired report {a['paired_report']['pass']}/{a['paired_report']['stations']} | "
                  f"report: right type but wrong label missed = {a['paired_report']['right_type_but_wrong_label_missed']}")


if __name__ == "__main__":
    main()
