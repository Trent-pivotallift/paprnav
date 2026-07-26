import subprocess
import zipfile

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import (
    ADPublication,
    ADReconciliationIssue,
    ADSourceSnapshot,
    ADTargetApplicability,
    AirworthinessDirective,
    ApplicabilityTarget,
)
from app.services import drs_bulk_import
from app.services.drs_bulk_import import import_drs_bulk_rows, import_drs_bulk_zip
from app.services.ad_reconciliation import run_ad_reconciliation


def test_import_drs_bulk_rows_creates_pre_1994_directive_and_applicability(db_session: Session) -> None:
    stats = import_drs_bulk_rows(
        db_session,
        [
            {
                "adNumber": "93-01-01",
                "Subject": "Airworthiness Directives; Cessna 172 Airplanes",
                "ProductType": "Aircraft",
                "Make": "Cessna",
                "Model": "172R | 172S",
                "Status": "Current",
                "PublicationDate": "01/08/1993",
                "Identifier": "DRS-93-01-01",
            },
            {
                "adNumber": "2026-99-01",
                "Subject": "Airworthiness Directives; Missing applicability",
                "Status": "Current",
                "Identifier": "DRS-2026-99-01",
            },
        ],
        source_url="https://drs.faa.gov/browse/ADFREAD/doctypeDetails",
        filename="ADFinalRulesEmergencyADs_fixture.accdb",
        content_hash="a" * 64,
    )
    db_session.commit()

    assert stats["rows_seen"] == 2
    assert stats["directives_upserted"] == 2
    assert stats["applicabilities_upserted"] == 2
    assert stats["issues"] == 1

    snapshot = db_session.scalar(select(ADSourceSnapshot).where(ADSourceSnapshot.source_system == "drs"))
    assert snapshot is not None
    assert snapshot.parser_name == "drs_bulk_importer"
    assert snapshot.parser_version == "0.2.0"

    directive = db_session.scalar(select(AirworthinessDirective).where(AirworthinessDirective.ad_number == "1993-01-01"))
    assert directive is not None
    assert directive.discovery_record_id is None

    publication = db_session.scalar(select(ADPublication).where(ADPublication.directive_id == directive.id))
    assert publication is not None
    assert publication.source_system == "drs"
    assert publication.publication_date.isoformat() == "1993-01-08"

    targets = db_session.scalars(select(ApplicabilityTarget).where(ApplicabilityTarget.make == "Cessna")).all()
    assert {target.model for target in targets} == {"172R", "172S"}
    assert db_session.scalar(select(ADTargetApplicability).where(ADTargetApplicability.directive_id == directive.id)) is not None

    issue = db_session.scalar(select(ADReconciliationIssue).where(ADReconciliationIssue.issue_type == "drs_row_missing_applicability"))
    assert issue is not None
    assert issue.severity == "medium"


def test_import_drs_bulk_zip_falls_back_with_degraded_snapshot_when_access_parser_unavailable(
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(drs_bulk_import.shutil, "which", lambda _command: None)
    zip_path = tmp_path / "ADFinalRulesEmergencyADs.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("ADFinalRulesEmergencyADs.accdb", "binary text AD 2026-01-02 with no table export")

    stats = import_drs_bulk_zip(db_session, zip_path, source_url="https://drs.faa.gov/bulk")
    db_session.commit()

    assert stats["rows_seen"] == 1
    assert stats["directives_upserted"] == 1
    assert stats["publications_upserted"] == 1
    assert stats["applicabilities_upserted"] == 0
    assert stats["issues"] == 2

    snapshot = db_session.scalar(select(ADSourceSnapshot).where(ADSourceSnapshot.source_type == "bulk_zip"))
    assert snapshot is not None
    assert snapshot.status == "partial"
    assert snapshot.row_count == 1
    assert snapshot.metadata_json["accessParsing"] == "mdbtools_unavailable"
    assert snapshot.metadata_json["fallback"] == "binary_ad_number_scan"

    source_issue = db_session.scalar(
        select(ADReconciliationIssue).where(ADReconciliationIssue.issue_type == "drs_access_table_parse_unavailable")
    )
    assert source_issue is not None
    assert source_issue.source_snapshot_id == snapshot.id
    assert source_issue.severity == "high"

    directive = db_session.scalar(select(AirworthinessDirective).where(AirworthinessDirective.ad_number == "2026-01-02"))
    assert directive is not None
    assert db_session.scalar(
        select(ADReconciliationIssue).where(
            ADReconciliationIssue.directive_id == directive.id,
            ADReconciliationIssue.issue_type == "drs_zip_applicability_unparsed",
        )
    ) is not None

    run_ad_reconciliation(db_session)
    degraded_issue = db_session.scalar(
        select(ADReconciliationIssue).where(
            ADReconciliationIssue.source_snapshot_id == snapshot.id,
            ADReconciliationIssue.issue_type == "drs_source_degraded",
        )
    )
    assert degraded_issue is not None
    assert degraded_issue.severity == "medium"


def test_import_drs_bulk_zip_uses_mdbtools_exported_access_rows(
    db_session: Session,
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(drs_bulk_import.shutil, "which", lambda command: f"/usr/bin/{command}")

    def fake_run(command, check, capture_output, text, timeout):
        _ = check
        _ = capture_output
        _ = text
        _ = timeout
        if command[0] == "mdb-tables":
            return subprocess.CompletedProcess(command, 0, stdout="ADTable\nNotes\n", stderr="")
        if command[0] == "mdb-export" and command[-1] == "ADTable":
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    "ADNumber,Subject,ProductType,Make,Model,Status,PublicationDate,Identifier\n"
                    "2026-02-03,Airworthiness Directives; Cessna 172R Airplanes,Aircraft,Cessna,172R,Current,2026-02-04,DRS-2026-02-03\n"
                ),
                stderr="",
            )
        if command[0] == "mdb-export" and command[-1] == "Notes":
            return subprocess.CompletedProcess(command, 0, stdout="Note\nnot an AD row\n", stderr="")
        raise AssertionError(f"Unexpected command {command}")

    monkeypatch.setattr(drs_bulk_import.subprocess, "run", fake_run)
    zip_path = tmp_path / "ADFinalRulesEmergencyADs.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("ADFinalRulesEmergencyADs.accdb", b"fake access bytes")

    stats = import_drs_bulk_zip(db_session, zip_path, source_url="https://drs.faa.gov/bulk")
    db_session.commit()

    assert stats["rows_seen"] == 1
    assert stats["directives_upserted"] == 1
    assert stats["publications_upserted"] == 1
    assert stats["applicabilities_upserted"] == 1
    assert stats["issues"] == 0

    snapshot = db_session.scalar(select(ADSourceSnapshot).where(ADSourceSnapshot.source_type == "bulk_access"))
    assert snapshot is not None
    assert snapshot.status == "complete"
    assert snapshot.row_count == 1
    assert snapshot.metadata_json["accessParsing"] == "mdbtools"
    assert snapshot.table_inventory["accessTables"]["ADFinalRulesEmergencyADs.accdb"]["rowCounts"]["ADTable"] == 1

    directive = db_session.scalar(select(AirworthinessDirective).where(AirworthinessDirective.ad_number == "2026-02-03"))
    assert directive is not None
    publication = db_session.scalar(select(ADPublication).where(ADPublication.directive_id == directive.id))
    assert publication is not None
    assert publication.source_snapshot_id == snapshot.id
    assert publication.metadata_json["sourceAccessTable"] == "ADTable"
    assert db_session.scalar(select(ADTargetApplicability).where(ADTargetApplicability.directive_id == directive.id)) is not None
