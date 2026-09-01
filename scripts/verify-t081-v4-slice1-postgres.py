#!/usr/bin/env python3
"""Narrow, timeout-bounded PostgreSQL verifier for T081 V4 slice 1."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
DATABASE_NAME = f"paprnav_t081_v4_slice1_{os.getpid()}_{uuid.uuid4().hex[:8]}"
DATABASE_URL = (
    "postgresql+psycopg://paprnav_user:paprnav_password@db:5432/"
    f"{DATABASE_NAME}"
)
TOTAL_TIMEOUT_SECONDS = 170
CLEANUP_RESERVE_SECONDS = 15


def run_phase(
    label: str,
    command: list[str],
    *,
    timeout_seconds: int,
    deadline: float | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    if deadline is not None:
        remaining = int(deadline - time.monotonic())
        if remaining <= 0:
            raise RuntimeError(f"{label} not started: total verifier deadline exhausted")
        timeout_seconds = min(timeout_seconds, remaining)
    print(f"[{label}] timeout={timeout_seconds}s", flush=True)
    try:
        result = subprocess.run(
            command,
            cwd=BACKEND_DIR,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{label} exceeded {timeout_seconds}s") from exc
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n", file=sys.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"{label} failed with exit code {result.returncode}")
    return result


def compose(*arguments: str) -> list[str]:
    return ["docker", "compose", *arguments]


def main() -> None:
    if not re.fullmatch(r"paprnav_t081_v4_slice1_[0-9]+_[0-9a-f]{8}", DATABASE_NAME):
        raise SystemExit(f"Refusing invalid temporary database name: {DATABASE_NAME}")

    created = False
    completed = 0
    verification_deadline = (
        time.monotonic() + TOTAL_TIMEOUT_SECONDS - CLEANUP_RESERVE_SECONDS
    )
    try:
        run_phase(
            "build-current-api", compose("build", "api"),
            timeout_seconds=45, deadline=verification_deadline,
        )
        completed += 1
        run_phase(
            "create-isolated-database",
            compose("exec", "-T", "db", "createdb", "-U", "paprnav_user", DATABASE_NAME),
            timeout_seconds=15,
            deadline=verification_deadline,
        )
        created = True
        completed += 1
        run_phase(
            "upgrade-0025",
            compose("run", "--rm", "-T", "-e", f"DATABASE_URL={DATABASE_URL}", "api", "alembic", "upgrade", "head"),
            timeout_seconds=90,
            deadline=verification_deadline,
        )
        completed += 1
        run_phase(
            "empty-downgrade-0024",
            compose("run", "--rm", "-T", "-e", f"DATABASE_URL={DATABASE_URL}", "api", "alembic", "downgrade", "20260823_0024"),
            timeout_seconds=60,
            deadline=verification_deadline,
        )
        completed += 1
        run_phase(
            "reupgrade-0025",
            compose("run", "--rm", "-T", "-e", f"DATABASE_URL={DATABASE_URL}", "api", "alembic", "upgrade", "head"),
            timeout_seconds=60,
            deadline=verification_deadline,
        )
        completed += 1
        test_result = run_phase(
            "slice1-postgresql-tests",
            compose(
                "run", "--rm", "-T",
                "-e", "PYTHONPATH=/app",
                "-e", f"PAPRNAV_TEST_POSTGRES_URL={DATABASE_URL}",
                "api", "pytest", "-q", "--maxfail=1", "tests/test_ad_evidence_postgres.py",
            ),
            timeout_seconds=90,
            deadline=verification_deadline,
        )
        if "2 passed" not in test_result.stdout:
            raise RuntimeError("slice1 PostgreSQL verifier did not report 2 passed out of 2")
        completed += 1
        current = run_phase(
            "confirm-head",
            compose("run", "--rm", "-T", "-e", f"DATABASE_URL={DATABASE_URL}", "api", "alembic", "current"),
            timeout_seconds=30,
            deadline=verification_deadline,
        )
        if "20260830_0025" not in current.stdout:
            raise RuntimeError("isolated verifier did not finish at revision 20260830_0025")
        completed += 1
    finally:
        if created:
            cleanup = run_phase(
                "drop-isolated-database",
                compose(
                    "exec", "-T", "db", "dropdb", "--if-exists", "--force",
                    "-U", "paprnav_user", DATABASE_NAME,
                ),
                timeout_seconds=CLEANUP_RESERVE_SECONDS,
                check=False,
            )
            if cleanup.returncode != 0 and sys.exc_info()[0] is None:
                raise RuntimeError("isolated verifier database cleanup failed")

    print(f"{completed} passed out of 7 phases; PostgreSQL tests 2 passed out of 2")


if __name__ == "__main__":
    main()
