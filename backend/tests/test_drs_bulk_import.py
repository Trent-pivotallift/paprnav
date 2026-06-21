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
from app.services.drs_bulk_import import import_drs_bulk_rows


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

