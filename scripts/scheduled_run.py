"""Starts ONE Kaggle benchmark run, only if every guard passes. For use from a
Windows scheduled task. Never retries, never waits for the run, logs everything.

Guards (all must pass, else it logs SKIP and exits):
  1. now (UTC) >= --not-before
  2. a marker file for this task+model does not exist (run once only)
  3. the model has no run yet on this task (kaggle b t status)
  4. Kaggle daily quota: remaining >= --min-remaining, and the open window
     (if any) did not start before --not-before (a fresh window)

Usage:
  python scripts/scheduled_run.py --task ves-real --model claude-sonnet-5-default \
      --not-before 2026-10-05T03:10 --min-remaining 8.5 [--dry-run]
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "runs" / "scheduled"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def log(msg):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC  {msg}"
    print(line)
    with open(LOG_DIR / "scheduled.log", "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def kaggle(*args, timeout=600):
    # cwd=home: the repo's own kaggle/ folder would shadow the kaggle package.
    p = subprocess.run([sys.executable, "-m", "kaggle", *args], capture_output=True, text=True,
                       env=ENV, encoding="utf-8", errors="replace", timeout=timeout, cwd=str(Path.home()))
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def daily_quota():
    from kaggle.api.kaggle_api_extended import KaggleApi
    from kagglesdk.models.types.model_proxy_api_service import ApiGetModelProxyQuotasRequest
    api = KaggleApi()
    api.authenticate()
    with api.build_kaggle_client() as k:
        r = k.models.model_proxy_api_client.get_model_proxy_quotas(ApiGetModelProxyQuotasRequest())
    for b in r.quota_balances:
        if "DAILY" in str(b.refill_period):
            return b.total_quota_allowed - b.quota_used, b.refill_time
    raise RuntimeError("no daily quota returned")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--not-before", required=True, help="UTC, e.g. 2026-10-05T03:10")
    ap.add_argument("--min-remaining", type=float, required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    tag = f"{a.task} / {a.model}" + (" [dry-run]" if a.dry_run else "")
    try:
        not_before = datetime.fromisoformat(a.not_before).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if now < not_before:
            return log(f"SKIP {tag}: now is before not-before {not_before:%Y-%m-%d %H:%M} UTC")
        marker = LOG_DIR / f"{a.task}__{a.model}.started"
        if marker.exists():
            return log(f"SKIP {tag}: already started once ({marker.name})")
        rc, out = kaggle("b", "t", "status", a.task, "-m", a.model)
        if rc != 0:
            return log(f"SKIP {tag}: status check failed: {out.strip()[:300]}")
        if any(ln.strip().startswith(a.model) for ln in out.splitlines()):
            return log(f"SKIP {tag}: model already has a run on this task")
        remaining, refill = daily_quota()
        if refill is not None:
            window_start = refill.replace(tzinfo=timezone.utc) - timedelta(hours=24)
            if window_start < not_before:
                return log(f"SKIP {tag}: current window started {window_start:%Y-%m-%d %H:%M} UTC, "
                           f"before not-before (not a fresh window); remaining ${remaining:.2f}")
        if remaining < a.min_remaining:
            return log(f"SKIP {tag}: daily remaining ${remaining:.2f} < ${a.min_remaining:.2f}")
        if a.dry_run:
            return log(f"DRY-RUN {tag}: all guards passed (remaining ${remaining:.2f}); would start the run now")
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(now.isoformat(), encoding="utf-8")
        rc, out = kaggle("b", "t", "run", a.task, "-m", a.model)
        log(f"{'STARTED' if rc == 0 else 'START FAILED'} {tag} (remaining before ${remaining:.2f}): "
            f"{out.strip()[-300:]}")
    except Exception as e:  # noqa: BLE001 - logged; never retried
        log(f"ERROR {tag}: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
