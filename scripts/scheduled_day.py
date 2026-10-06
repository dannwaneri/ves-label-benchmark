"""One scheduled day: push a new task (Flash runs automatically), then run
more models on it. Every step has guards; a failed guard stops the day.
Never retries a step (run-once marker per step). Logs to
runs/scheduled/scheduled.log.

Steps:
  1. push <task> (skipped if the task already exists), wait until created
  2. for each model, in order: run, if it has no run yet and the daily
     quota remaining >= its threshold

Usage:
  python scripts/scheduled_day.py --task ves-synthetic-a \
      --not-before 2026-10-06T03:30 --min-start 9.5 \
      --model claude-sonnet-5-default:5.2 --model gemma-4-26b-a4b-it:1.0 [--dry-run]
"""

import argparse
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scheduled_run import LOG_DIR, ROOT, daily_quota, kaggle, log  # noqa: E402


def task_state(task):
    rc, out = kaggle("b", "t", "status", task)
    if rc != 0:
        return None, out
    m = re.search(r"^Status:\s*(\S+)", out, re.MULTILINE)
    return (m.group(1) if m else "?"), out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--not-before", required=True, help="UTC, e.g. 2026-10-06T03:30")
    ap.add_argument("--min-start", type=float, required=True, help="daily remaining needed to start the day")
    ap.add_argument("--model", action="append", default=[], help="slug:min_remaining, in run order")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    tag = f"day {a.task}" + (" [dry-run]" if a.dry_run else "")
    try:
        not_before = datetime.fromisoformat(a.not_before).replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) < not_before:
            return log(f"SKIP {tag}: before not-before {not_before:%Y-%m-%d %H:%M} UTC")
        remaining, refill = daily_quota()
        if refill is not None and refill.replace(tzinfo=timezone.utc) - timedelta(hours=24) < not_before:
            return log(f"SKIP {tag}: not a fresh quota window (remaining ${remaining:.2f})")
        if remaining < a.min_start:
            return log(f"SKIP {tag}: remaining ${remaining:.2f} < ${a.min_start:.2f}")

        # Step 1: push (once)
        state, _ = task_state(a.task)
        push_marker = LOG_DIR / f"{a.task}__push.started"
        if state is None:
            if push_marker.exists():
                return log(f"STOP {tag}: push was started before but the task does not exist")
            if a.dry_run:
                log(f"DRY-RUN {tag}: would push {a.task} (remaining ${remaining:.2f})")
            else:
                push_marker.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
                src = ROOT / "kaggle" / "generated" / f"{a.task}.py"
                # The push waits for the default-model run to finish: allow far more than
                # the 10-minute default (bug on 2026-10-06: push timed out at 10 min).
                rc, out = kaggle("b", "t", "push", a.task, "-f", str(src), "--wait", "5400", timeout=6000)
                log(f"{'PUSHED' if rc == 0 else 'PUSH FAILED'} {tag}: {out.strip()[-200:]}")
                if rc != 0:
                    return
        if not a.dry_run:
            for _ in range(60):  # up to 30 min more for creation to finish
                state, _ = task_state(a.task)
                if state != "Running":
                    break
                time.sleep(30)
            if state != "Completed":
                return log(f"STOP {tag}: task state is {state}, not Completed; no model runs started")

        # Step 2: models, in order
        for spec in a.model:
            slug, need = spec.rsplit(":", 1)
            need = float(need)
            marker = LOG_DIR / f"{a.task}__{slug}.started"
            rc, out = kaggle("b", "t", "status", a.task, "-m", slug)
            if marker.exists() or any(ln.strip().startswith(slug) for ln in out.splitlines()):
                log(f"SKIP {tag} / {slug}: already has a run")
                continue
            remaining, _ = daily_quota()
            if remaining < need:
                log(f"STOP {tag} / {slug}: remaining ${remaining:.2f} < ${need:.2f}; later models not started")
                return
            if a.dry_run:
                log(f"DRY-RUN {tag} / {slug}: would start (remaining ${remaining:.2f})")
                continue
            marker.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
            rc, out = kaggle("b", "t", "run", a.task, "-m", slug)
            log(f"{'STARTED' if rc == 0 else 'START FAILED'} {tag} / {slug} (remaining ${remaining:.2f}): "
                f"{out.strip()[-160:]}")
            time.sleep(60)  # let the run register its spend before the next quota check
    except Exception as e:  # noqa: BLE001 - logged; never retried
        log(f"ERROR {tag}: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
