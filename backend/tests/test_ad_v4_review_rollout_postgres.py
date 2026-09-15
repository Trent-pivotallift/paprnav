"""Migration rollback gates for the immutable Slice-4 review foundation.

Run this module against its own freshly migrated disposable database.  The
tests intentionally leave immutable review history behind in the final case.
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from test_ad_v4_review_case_migration_postgres import Records


URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not URL, reason="PAPRNAV_TEST_POSTGRES_URL required")


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = URL or ""
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def _version(engine) -> str:
    with engine.connect() as connection:
        return connection.scalar(text("SELECT version_num FROM alembic_version"))


def test_00_empty_disabled_review_schema_downgrades_and_reupgrades() -> None:
    engine = create_engine(URL, pool_pre_ping=True)
    try:
        assert _version(engine) == "20260913_0029"
        down = _alembic("downgrade", "20260911_0028")
        assert down.returncode == 0, down.stdout + down.stderr
        assert _version(engine) == "20260911_0028"
        with engine.connect() as connection:
            frozen_0028 = {
                function: connection.scalar(text(
                    f"SELECT pg_get_functiondef('{function}()'::regprocedure)"
                ))
                for function in (
                    "paprnav_v4_validate_submission",
                    "paprnav_v4_validate_app_request",
                )
            }
            assert connection.scalar(text(
                "SELECT to_regprocedure('paprnav_v4_review_case_authoritative_bytes(text)')"
            )) is None
        up = _alembic("upgrade", "head")
        assert up.returncode == 0, up.stdout + up.stderr
        assert _version(engine) == "20260913_0029"
        with engine.connect() as connection:
            gates = dict(connection.execute(text(
                "SELECT gate_key,enabled FROM ad_v4_feature_gates "
                "WHERE gate_key IN ('reviewer4_draft_enabled','reviewer4_decision_enabled')"
            )).all())
        assert gates == {
            "reviewer4_draft_enabled": False,
            "reviewer4_decision_enabled": False,
        }
        second_down = _alembic("downgrade", "20260911_0028")
        assert second_down.returncode == 0, second_down.stdout + second_down.stderr
        assert _version(engine) == "20260911_0028"
        with engine.connect() as connection:
            assert {
                function: connection.scalar(text(
                    f"SELECT pg_get_functiondef('{function}()'::regprocedure)"
                ))
                for function in frozen_0028
            } == frozen_0028
            assert connection.scalar(text(
                "SELECT to_regprocedure('paprnav_v4_review_case_authoritative_bytes(text)')"
            )) is None
        second_up = _alembic("upgrade", "head")
        assert second_up.returncode == 0, second_up.stdout + second_up.stderr
        assert _version(engine) == "20260913_0029"
    finally:
        engine.dispose()


@pytest.mark.parametrize("gate", ["reviewer4_draft_enabled", "reviewer4_decision_enabled"])
def test_01_enabled_review_gate_refuses_downgrade_without_schema_loss(gate: str) -> None:
    engine = create_engine(URL, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            connection.execute(text(
                "SELECT paprnav_set_v4_feature_gate(:gate,true,'review-rollout-test')"
            ), {"gate": gate})
        down = _alembic("downgrade", "20260911_0028")
        assert down.returncode != 0
        assert "Revision 0029 reviewer gates are enabled" in down.stdout + down.stderr
        assert _version(engine) == "20260913_0029"
        with engine.begin() as connection:
            connection.execute(text(
                "SELECT paprnav_set_v4_feature_gate(:gate,false,'review-rollout-test')"
            ), {"gate": gate})
    finally:
        engine.dispose()


def test_99_immutable_review_history_refuses_downgrade_without_row_loss() -> None:
    engine = create_engine(URL, pool_pre_ping=True)
    try:
        with Session(engine) as db:
            records = Records(db)
            records.create()
            for gate in ("reviewer4_draft_enabled", "reviewer4_decision_enabled"):
                db.execute(text(
                    "SELECT paprnav_set_v4_feature_gate(:gate,false,'review-rollout-test')"
                ), {"gate": gate})
            db.commit()
            case_id = records.case
        down = _alembic("downgrade", "20260911_0028")
        assert down.returncode != 0
        assert "Revision 0029 contains immutable review history" in down.stdout + down.stderr
        assert _version(engine) == "20260913_0029"
        with engine.connect() as connection:
            assert connection.scalar(text(
                "SELECT count(*) FROM ad_v4_review_cases WHERE id=:case_id"
            ), {"case_id": case_id}) == 1
    finally:
        engine.dispose()
