from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import ADV4CandidateCorrectionSemanticBinding, User
from app.services.ad_v4_applicability import materialize_applicability
from app.services.ad_v4_candidates import VALIDATOR_VERSION_V2
from test_ad_v4_applicability_postgres import _enable, _store
from test_ad_v4_obligation_persistence_postgres import _persist_complete_graph


POSTGRES_URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
BASE = "9ad410b7c4021244ac36a6fab44b1dd021f5d05c"
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="PAPRNAV_TEST_POSTGRES_URL required",
)


def _run_old_reader(
    old_root: Path, *, app_projection_id: str, expect_failure: bool,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = POSTGRES_URL or ""
    environment["PYTHONPATH"] = str(old_root / "backend")
    environment["APP_PROJECTION_ID"] = app_projection_id
    environment["EXPECT_FAILURE"] = "1" if expect_failure else "0"
    script = """
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models.core import ADV4CandidateAppProjection
from app.services.ad_v4_applicability import reconstruct_applicability

engine = create_engine(os.environ['DATABASE_URL'], pool_pre_ping=True)
with Session(engine) as db:
    projection = db.get(ADV4CandidateAppProjection, os.environ['APP_PROJECTION_ID'])
    if projection is None:
        raise RuntimeError('old reader lost the Slice-3A projection')
    try:
        reconstruct_applicability(db, projection)
    except Exception:
        if os.environ['EXPECT_FAILURE'] != '1':
            raise
    else:
        if os.environ['EXPECT_FAILURE'] == '1':
            raise RuntimeError('old reader accepted a committed Slice-3B binding')
engine.dispose()
"""
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=old_root,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_exact_old_reader_only_accepts_upgraded_empty_slice3b_boundary(tmp_path):
    assert POSTGRES_URL
    repository_root = Path(__file__).resolve().parents[2]
    archive = tmp_path / "old-reader.tar"
    old_root = tmp_path / "old-reader"
    old_root.mkdir()
    subprocess.run(
        ["git", "archive", "--format=tar", f"--output={archive}", BASE],
        cwd=repository_root,
        check=True,
        timeout=30,
    )
    subprocess.run(
        ["tar", "-xf", archive, "-C", old_root],
        check=True,
        timeout=30,
    )

    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    try:
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            assert db.scalar(select(func.count()).select_from(
                ADV4CandidateCorrectionSemanticBinding,
            ).where(
                ADV4CandidateCorrectionSemanticBinding.binding_slice == "slice_3b",
            )) == 0
            user_id, membership_id, directive_id, proposal_id = _store(
                db,
                validator_version=VALIDATOR_VERSION_V2,
                suffix="old-reader-empty",
                ad_number="2097-00-01",
            )
            app_projection = materialize_applicability(
                db,
                directive_id=directive_id,
                proposal_id=proposal_id,
                actor=db.get(User, user_id),
                membership_id=membership_id,
                idempotency_key="old-reader-empty",
            ).projection
            db.commit()
            empty_result = _run_old_reader(
                old_root,
                app_projection_id=app_projection.id,
                expect_failure=False,
            )
            assert empty_result.returncode == 0, empty_result.stdout + empty_result.stderr

            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'old-reader-boundary-test')"
            ))
            db.commit()
            obligation_projection = _persist_complete_graph(
                db, with_correction=True,
            )
            assert db.scalar(select(func.count()).select_from(
                ADV4CandidateCorrectionSemanticBinding,
            ).where(
                ADV4CandidateCorrectionSemanticBinding.binding_slice == "slice_3b",
            )) > 0
            occupied_result = _run_old_reader(
                old_root,
                app_projection_id=obligation_projection.app_projection_id,
                expect_failure=True,
            )
            assert occupied_result.returncode == 0, (
                occupied_result.stdout + occupied_result.stderr
            )

        rollout = (
            repository_root
            / "backend/app/contracts/ad_v4_slice3b_rollout.md"
        ).read_text(encoding="utf-8")
        assert BASE in rollout
        assert "zero Slice-3B correction bindings" in rollout
        assert "deploying that binary is prohibited" in rollout
    finally:
        get_settings.cache_clear()
        engine.dispose()
