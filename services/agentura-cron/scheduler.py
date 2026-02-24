"""Agentura Cron Scheduler — Periodic skill execution.

Reads schedule from schedule.yaml and executes skills on cron intervals.
Uses APScheduler for lightweight, in-process scheduling.

Usage:
    python scheduler.py                     # default schedule.yaml
    python scheduler.py --config my.yaml    # custom config
    python scheduler.py --dry-run           # show schedule without executing
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import httpx
import yaml
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Mutable config — set once in main() before scheduler starts
_config = {"executor_url": "http://localhost:3001"}


def load_schedule(path: str = "schedule.yaml") -> list[dict]:
    with open(path) as f:
        config = yaml.safe_load(f)
    return config.get("schedules", [])


def execute_skill(domain: str, skill: str, input_data: dict | None = None):
    """Fire a skill execution via the API."""
    url = f"{_config['executor_url']}/api/v1/skills/{domain}/{skill}/execute"
    payload = {"input_data": input_data or {}, "dry_run": False}

    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] Executing {domain}/{skill}...", flush=True)

    try:
        resp = httpx.post(url, json=payload, timeout=30.0)
        resp.raise_for_status()
        result = resp.json()
        success = result.get("success", False)
        latency = result.get("latency_ms", 0)
        print(
            f"[{ts}]   {'OK' if success else 'FAIL'} — "
            f"{latency:.0f}ms — {result.get('model_used', 'unknown')}",
            flush=True,
        )
    except httpx.HTTPStatusError as e:
        print(f"[{ts}]   ERROR {e.response.status_code}: {e.response.text[:200]}", flush=True)
    except Exception as e:
        print(f"[{ts}]   ERROR: {e}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Agentura Cron Scheduler")
    parser.add_argument("--config", default="schedule.yaml", help="Schedule config file")
    parser.add_argument("--dry-run", action="store_true", help="Show schedule without executing")
    parser.add_argument("--executor-url", default="http://localhost:3001", help="Executor API URL")
    args = parser.parse_args()

    _config["executor_url"] = args.executor_url

    config_path = Path(__file__).parent / args.config
    if not config_path.exists():
        print(f"Schedule file not found: {config_path}")
        sys.exit(1)

    schedules = load_schedule(str(config_path))
    if not schedules:
        print("No schedules defined.")
        sys.exit(0)

    scheduler = BlockingScheduler()

    print("Agentura Cron Scheduler")
    print("=" * 50)

    for entry in schedules:
        skill_path = entry["skill"]
        cron_expr = entry["cron"]
        domain, skill = skill_path.split("/")
        input_data = entry.get("input_data", {})
        description = entry.get("description", skill_path)

        trigger = CronTrigger.from_crontab(cron_expr)

        if args.dry_run:
            print(f"  {cron_expr:<20} {skill_path:<30} {description}")
        else:
            scheduler.add_job(
                execute_skill,
                trigger=trigger,
                args=[domain, skill, input_data],
                id=skill_path,
                name=description,
            )
            print(f"  Scheduled: {skill_path} ({cron_expr}) — {description}")

    if args.dry_run:
        print("\nDry run — no jobs started.")
        return

    print(f"\n{len(schedules)} jobs scheduled. Press Ctrl+C to stop.\n")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nScheduler stopped.")


if __name__ == "__main__":
    main()
