from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.core import (
    ADCostLedgerEntry,
    ADCoverageSet,
    ADCoverageSubscription,
    ADSourceSnapshot,
)
from app.services.ad_costs import record_ad_cost_entry
from app.services.ad_coverage import (
    resolve_aircraft_ad_coverage,
    summarize_aircraft_coverage_status,
)
from app.services.drs_bulk_import import import_drs_bulk_rows
from tests.conftest import (
    add_membership,
    create_aircraft,
    create_organization,
    create_user,
    login,
)


DRS_ROWS = [
    {
        "adNumber": "2026-01-01",
        "Subject": "Airworthiness Directives; Cessna 172R Airplanes",
        "ProductType": "Aircraft",
        "Make": "Cessna",
        "Model": "172R",
        "Status": "Current",
        "Identifier": "DRS-2026-01-01",
    },
    {
        "adNumber": "2026-01-02",
        "Subject": "Airworthiness Directives; Lycoming IO-360-L2A Engines",
        "ProductType": "Engine",
        "Make": "Lycoming",
        "Model": "IO-360-L2A",
        "Status": "Current",
        "Identifier": "DRS-2026-01-02",
    },
    {
        "adNumber": "2026-01-03",
        "Subject": "Airworthiness Directives; McCauley 1A170 Propellers",
        "ProductType": "Propeller",
        "Make": "McCauley",
        "Model": "1A170",
        "Status": "Current",
        "Identifier": "DRS-2026-01-03",
    },
]


def test_second_client_reuses_coverage_without_duplicate_source_download(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    first_aircraft = demo_data["aircraft"]
    first_owner = demo_data["owner_user"]
    import_drs_bulk_rows(
        db_session,
        DRS_ROWS,
        filename="ADFinalRulesEmergencyADs_fixture.accdb",
        content_hash="c" * 64,
    )

    first_stats = resolve_aircraft_ad_coverage(db_session, first_aircraft.id)
    assert first_stats["coverage_sets_created"] == 3
    assert first_stats["coverage_sets_reused"] == 0
    assert first_stats["associations_created"] == 3
    assert first_stats["source_snapshots_reused"] == 3

    second_owner = create_user(db_session, "second.owner@paprnav.local", "Second Owner")
    second_org = create_organization(db_session, "Second Owner Hangar", "owner")
    add_membership(db_session, second_org, second_owner, "owner_admin")
    second_aircraft = create_aircraft(
        db_session,
        second_org,
        second_owner,
        n_number="N456CD",
    )
    db_session.commit()

    second_stats = resolve_aircraft_ad_coverage(db_session, second_aircraft.id)
    db_session.commit()

    assert second_stats["coverage_sets_created"] == 0
    assert second_stats["coverage_sets_reused"] == 3
    assert second_stats["associations_created"] == 3
    assert second_stats["source_snapshots_reused"] == 3
    assert db_session.scalar(select(func.count()).select_from(ADSourceSnapshot)) == 1
    assert db_session.scalar(select(func.count()).select_from(ADCoverageSet)) == 3
    assert db_session.scalar(select(func.count()).select_from(ADCoverageSubscription)) == 6

    first_trigger_subscriptions = db_session.scalars(
        select(ADCoverageSubscription).where(
            ADCoverageSubscription.aircraft_id == first_aircraft.id,
            ADCoverageSubscription.triggered_creation.is_(True),
        )
    ).all()
    second_trigger_subscriptions = db_session.scalars(
        select(ADCoverageSubscription).where(
            ADCoverageSubscription.aircraft_id == second_aircraft.id,
            ADCoverageSubscription.triggered_creation.is_(True),
        )
    ).all()
    assert len(first_trigger_subscriptions) == 3
    assert second_trigger_subscriptions == []

    source_storage_entries = db_session.scalars(
        select(ADCostLedgerEntry).where(
            ADCostLedgerEntry.scope_type == "shared_source",
            ADCostLedgerEntry.cost_category == "source_storage",
        )
    ).all()
    assert len(source_storage_entries) == 1
    assert source_storage_entries[0].organization_id is None
    assert source_storage_entries[0].attribution_status == "platform_shared_unallocated"
    assert first_owner.id


def test_incomplete_component_identity_prevents_current_coverage(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    aircraft = demo_data["aircraft"]
    import_drs_bulk_rows(
        db_session,
        DRS_ROWS,
        filename="ADFinalRulesEmergencyADs_incomplete_identity.accdb",
        content_hash="d" * 64,
    )
    engine = next(
        component
        for component in aircraft.installed_components
        if component.role == "engine"
    )
    engine.model = None
    db_session.flush()

    resolve_aircraft_ad_coverage(db_session, aircraft.id)
    summary = summarize_aircraft_coverage_status(db_session, aircraft.id)

    assert summary["coverageStatus"] == "degraded"
    assert any(
        "identity must be completed" in warning
        for warning in summary["coverageWarnings"]
    )


def test_stale_snapshot_prevents_current_coverage(
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    aircraft = demo_data["aircraft"]
    import_drs_bulk_rows(
        db_session,
        DRS_ROWS,
        filename="ADFinalRulesEmergencyADs_stale.accdb",
        content_hash="e" * 64,
    )
    snapshot = db_session.scalar(select(ADSourceSnapshot))
    assert snapshot is not None
    snapshot.captured_at = datetime.now(timezone.utc) - timedelta(days=8)
    db_session.flush()

    resolve_aircraft_ad_coverage(db_session, aircraft.id)
    summary = summarize_aircraft_coverage_status(db_session, aircraft.id)

    assert summary["coverageStatus"] == "degraded"
    assert any(
        target["status"] == "stale_source"
        for target in summary["coverageTargets"]
    )
    assert any(
        "snapshot is stale" in warning
        for warning in summary["coverageWarnings"]
    )


def test_admin_ad_cost_summary_is_platform_only_and_separates_allocation(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    aircraft = demo_data["aircraft"]
    import_drs_bulk_rows(
        db_session,
        DRS_ROWS[:1],
        filename="ADFinalRulesEmergencyADs_fixture.accdb",
        content_hash="d" * 64,
    )
    resolve_aircraft_ad_coverage(db_session, aircraft.id)
    coverage = db_session.scalar(
        select(ADCoverageSet).where(ADCoverageSet.status == "current")
    )
    assert coverage is not None
    record_ad_cost_entry(
        db_session,
        idempotency_key="test-coverage-processing-cost",
        scope_type="coverage_set",
        cost_category="source_processing",
        usage_quantity=1,
        usage_unit="run",
        actual_cost_usd=Decimal("1.25"),
        allocated_cost_usd=Decimal("0"),
        attribution_status="informational_unallocated",
        coverage_set_id=coverage.id,
        organization_id=aircraft.owner_organization_id,
    )

    admin_user = create_user(db_session, "platform.admin@paprnav.local", "Platform Admin")
    admin_org = create_organization(db_session, "Paprnav Operations", "platform")
    add_membership(db_session, admin_org, admin_user, "platform_admin")
    db_session.commit()

    login(client, "owner.test@paprnav.local")
    forbidden = client.get("/api/v1/admin/ad-costs")
    assert forbidden.status_code == 403

    client.post("/api/v1/auth/logout")
    login(client, "platform.admin@paprnav.local")
    response = client.get("/api/v1/admin/ad-costs")
    assert response.status_code == 200
    payload = response.json()
    assert payload["billingActive"] is False
    assert payload["allocationPolicyStatus"] == "not_active"
    assert Decimal(payload["totals"]["actualCostUsd"]) == Decimal("1.25000000")
    assert Decimal(payload["totals"]["allocatedCostUsd"]) == Decimal("0E-8")
    assert payload["totals"]["coverageSetCount"] == 3
    current = next(item for item in payload["coverages"] if item["status"] == "current")
    assert current["make"] == "Cessna"
    assert current["model"] == "172R"
    assert current["clients"][0]["nNumber"] == "N123AB"
    assert current["clients"][0]["triggeredCreation"] is True
