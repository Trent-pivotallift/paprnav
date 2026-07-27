from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.core import (
    ADCostLedgerEntry,
    ADCoverageSet,
    ADCoverageSubscription,
    ADPublication,
    ADSourceSnapshot,
    ADTargetApplicability,
    Aircraft,
    ApplicabilityTarget,
    InstalledComponent,
)
from app.services.ad_applicability import get_or_create_target
from app.services.ad_costs import record_ad_cost_entry


@dataclass
class CoverageResolutionStats:
    aircraft_id: str
    components_seen: int = 0
    components_skipped: int = 0
    coverage_sets_created: int = 0
    coverage_sets_reused: int = 0
    associations_created: int = 0
    associations_reused: int = 0
    associations_deactivated: int = 0
    source_snapshots_reused: int = 0
    source_downloads_requested: int = 0

    def to_dict(self) -> dict[str, int | str]:
        return asdict(self)


def resolve_aircraft_ad_coverage(db: Session, aircraft_id: str) -> dict[str, int | str]:
    aircraft = db.scalar(
        select(Aircraft)
        .where(Aircraft.id == aircraft_id)
        .options(selectinload(Aircraft.installed_components))
    )
    if aircraft is None:
        raise ValueError(f"Aircraft {aircraft_id} not found")

    now = datetime.now(timezone.utc)
    snapshot = latest_reusable_drs_snapshot(db)
    stats = CoverageResolutionStats(aircraft_id=aircraft.id)
    active_coverage_ids: set[str] = set()

    for component in active_identity_components(aircraft):
        stats.components_seen += 1
        if not component.make and not component.model:
            stats.components_skipped += 1
            continue

        target = get_or_create_target(
            db,
            product_type=product_type_for_component(component),
            product_subtype=None,
            make=component.make,
            model=component.model,
        )
        coverage = db.scalar(
            select(ADCoverageSet).where(ADCoverageSet.target_id == target.id)
        )
        created = coverage is None
        if coverage is None:
            coverage = ADCoverageSet(
                target_id=target.id,
                first_triggered_by_aircraft_id=aircraft.id,
                first_triggered_by_organization_id=aircraft.owner_organization_id,
                status="awaiting_source_snapshot",
                coverage_version="unversioned",
                last_built_at=now,
                last_resolved_at=now,
                metadata_json={"creationReason": "aircraft_identity_onboarding"},
            )
            db.add(coverage)
            db.flush()
            stats.coverage_sets_created += 1
        else:
            stats.coverage_sets_reused += 1

        refresh_coverage_set(db, coverage, target=target, snapshot=snapshot, resolved_at=now)
        if snapshot is not None:
            stats.source_snapshots_reused += 1
        active_coverage_ids.add(coverage.id)

        subscription = db.scalar(
            select(ADCoverageSubscription).where(
                ADCoverageSubscription.coverage_set_id == coverage.id,
                ADCoverageSubscription.aircraft_id == aircraft.id,
            )
        )
        if subscription is None:
            subscription = ADCoverageSubscription(
                coverage_set_id=coverage.id,
                aircraft_id=aircraft.id,
                organization_id=aircraft.owner_organization_id,
                status="active",
                triggered_creation=created,
                last_resolved_at=now,
            )
            db.add(subscription)
            db.flush()
            stats.associations_created += 1
        else:
            subscription.organization_id = aircraft.owner_organization_id
            subscription.status = "active"
            subscription.last_resolved_at = now
            stats.associations_reused += 1

        record_ad_cost_entry(
            db,
            idempotency_key=f"coverage-link:{coverage.id}:{aircraft.id}",
            scope_type="aircraft",
            cost_category="coverage_association",
            usage_quantity=1,
            usage_unit="coverage_link",
            source_snapshot_id=coverage.current_source_snapshot_id,
            coverage_set_id=coverage.id,
            aircraft_id=aircraft.id,
            organization_id=aircraft.owner_organization_id,
            attribution_status="informational_unallocated",
            metadata={
                "triggeredCreation": subscription.triggered_creation,
                "billingActive": False,
            },
        )

    existing_subscriptions = db.scalars(
        select(ADCoverageSubscription).where(
            ADCoverageSubscription.aircraft_id == aircraft.id,
            ADCoverageSubscription.status == "active",
        )
    ).all()
    for subscription in existing_subscriptions:
        if subscription.coverage_set_id not in active_coverage_ids:
            subscription.status = "inactive_identity_changed"
            subscription.last_resolved_at = now
            stats.associations_deactivated += 1

    db.flush()
    return stats.to_dict()


def refresh_coverage_sets_for_snapshot(db: Session, snapshot: ADSourceSnapshot) -> int:
    coverages = db.scalars(select(ADCoverageSet)).all()
    refreshed = 0
    now = datetime.now(timezone.utc)
    for coverage in coverages:
        target = db.get(ApplicabilityTarget, coverage.target_id)
        if target is None:
            continue
        refresh_coverage_set(db, coverage, target=target, snapshot=snapshot, resolved_at=now)
        refreshed += 1
    db.flush()
    return refreshed


def refresh_coverage_set(
    db: Session,
    coverage: ADCoverageSet,
    *,
    target: ApplicabilityTarget,
    snapshot: ADSourceSnapshot | None,
    resolved_at: datetime,
) -> None:
    directive_count = db.scalar(
        select(func.count(distinct(ADTargetApplicability.directive_id))).where(
            ADTargetApplicability.target_id == target.id,
            ADTargetApplicability.status == "current",
        )
    ) or 0
    publication_rows = db.scalars(
        select(ADPublication)
        .join(
            ADTargetApplicability,
            ADTargetApplicability.source_publication_id == ADPublication.id,
        )
        .where(ADTargetApplicability.target_id == target.id)
        .distinct()
    ).all()
    logical_storage_bytes = sum(
        len(
            json.dumps(
                {
                    "sourceIdentifier": publication.source_identifier,
                    "title": publication.title,
                    "metadata": publication.metadata_json,
                },
                sort_keys=True,
                default=str,
            ).encode("utf-8")
        )
        for publication in publication_rows
    )

    previous_snapshot_id = coverage.current_source_snapshot_id
    coverage.current_source_snapshot_id = snapshot.id if snapshot else None
    coverage.directive_count = int(directive_count)
    coverage.source_document_count = len(publication_rows)
    coverage.derived_storage_bytes = logical_storage_bytes
    coverage.last_resolved_at = resolved_at
    if snapshot is None:
        coverage.status = "awaiting_source_snapshot"
        coverage.coverage_version = "unversioned"
    elif snapshot.status != "complete":
        coverage.status = "degraded_source"
        coverage.coverage_version = coverage_version(snapshot, target)
    elif directive_count == 0:
        coverage.status = "pending_applicability"
        coverage.coverage_version = coverage_version(snapshot, target)
    else:
        coverage.status = "current"
        coverage.coverage_version = coverage_version(snapshot, target)

    if previous_snapshot_id != coverage.current_source_snapshot_id:
        coverage.last_built_at = resolved_at
    coverage.metadata_json = {
        **(coverage.metadata_json or {}),
        "storageMeasurement": "estimated_logical_bytes",
        "physicalSourceStorageShared": True,
        "billingActive": False,
    }

    record_ad_cost_entry(
        db,
        idempotency_key=f"coverage-materialization:{coverage.id}:{coverage.coverage_version}",
        scope_type="coverage_set",
        cost_category="derived_index_storage",
        usage_quantity=logical_storage_bytes,
        usage_unit="estimated_logical_byte",
        source_snapshot_id=coverage.current_source_snapshot_id,
        coverage_set_id=coverage.id,
        organization_id=coverage.first_triggered_by_organization_id,
        actual_cost_usd=0,
        allocated_cost_usd=0,
        attribution_status="informational_unallocated",
        metadata={
            "directiveCount": coverage.directive_count,
            "sourceDocumentCount": coverage.source_document_count,
            "billingActive": False,
        },
    )


def latest_reusable_drs_snapshot(db: Session) -> ADSourceSnapshot | None:
    complete = db.scalar(
        select(ADSourceSnapshot)
        .where(
            ADSourceSnapshot.source_system == "drs",
            ADSourceSnapshot.status == "complete",
        )
        .order_by(ADSourceSnapshot.captured_at.desc(), ADSourceSnapshot.created_at.desc())
        .limit(1)
    )
    if complete is not None:
        return complete
    return db.scalar(
        select(ADSourceSnapshot)
        .where(
            ADSourceSnapshot.source_system == "drs",
            ADSourceSnapshot.status == "partial",
        )
        .order_by(ADSourceSnapshot.captured_at.desc(), ADSourceSnapshot.created_at.desc())
        .limit(1)
    )


def coverage_version(snapshot: ADSourceSnapshot, target: ApplicabilityTarget) -> str:
    digest = hashlib.sha256(
        f"{snapshot.content_hash}|{target.normalized_key}".encode("utf-8")
    ).hexdigest()
    return digest[:24]


def active_identity_components(aircraft: Aircraft) -> list[InstalledComponent]:
    return [
        component
        for component in aircraft.installed_components
        if component.removed_at is None
    ]


def product_type_for_component(component: InstalledComponent) -> str:
    component_type = (component.component_type or component.role or "").lower()
    if "engine" in component_type:
        return "Engine"
    if "propeller" in component_type:
        return "Propeller"
    if "rotorcraft" in component_type or "helicopter" in component_type:
        return "Rotorcraft"
    if "appliance" in component_type or "equipment" in component_type:
        return "Appliance"
    return "Aircraft"


def summarize_ad_costs(db: Session) -> dict:
    snapshots = db.scalars(
        select(ADSourceSnapshot)
        .where(ADSourceSnapshot.source_system == "drs")
        .order_by(ADSourceSnapshot.captured_at.desc(), ADSourceSnapshot.created_at.desc())
    ).all()
    coverages = db.scalars(
        select(ADCoverageSet)
        .options(
            selectinload(ADCoverageSet.target),
            selectinload(ADCoverageSet.current_source_snapshot),
            selectinload(ADCoverageSet.subscriptions).selectinload(ADCoverageSubscription.aircraft),
            selectinload(ADCoverageSet.subscriptions).selectinload(ADCoverageSubscription.organization),
            selectinload(ADCoverageSet.cost_entries),
        )
        .order_by(ADCoverageSet.created_at)
    ).all()
    all_costs = db.scalars(select(ADCostLedgerEntry)).all()

    return {
        "generatedAt": datetime.now(timezone.utc),
        "allocationPolicyStatus": "not_active",
        "allocationPolicyVersion": None,
        "billingActive": False,
        "totals": {
            "sharedSourceStorageBytes": sum(snapshot.storage_bytes or 0 for snapshot in snapshots),
            "derivedLogicalStorageBytes": sum(coverage.derived_storage_bytes for coverage in coverages),
            "actualCostUsd": sum((entry.actual_cost_usd for entry in all_costs), start=0),
            "allocatedCostUsd": sum((entry.allocated_cost_usd for entry in all_costs), start=0),
            "coverageSetCount": len(coverages),
            "clientCount": len(
                {
                    subscription.organization_id
                    for coverage in coverages
                    for subscription in coverage.subscriptions
                    if subscription.status == "active"
                }
            ),
            "aircraftCount": len(
                {
                    subscription.aircraft_id
                    for coverage in coverages
                    for subscription in coverage.subscriptions
                    if subscription.status == "active"
                }
            ),
        },
        "sourceSnapshots": [
            {
                "id": snapshot.id,
                "contentHash": snapshot.content_hash,
                "filename": snapshot.filename,
                "status": snapshot.status,
                "capturedAt": snapshot.captured_at,
                "storageBytes": snapshot.storage_bytes or 0,
                "rowCount": snapshot.row_count,
            }
            for snapshot in snapshots
        ],
        "coverages": [
            serialize_coverage_summary(coverage)
            for coverage in coverages
        ],
    }


def serialize_coverage_summary(coverage: ADCoverageSet) -> dict:
    active_subscriptions = [
        subscription
        for subscription in coverage.subscriptions
        if subscription.status == "active"
    ]
    return {
        "id": coverage.id,
        "status": coverage.status,
        "coverageVersion": coverage.coverage_version,
        "productType": coverage.target.product_type,
        "productSubtype": coverage.target.product_subtype,
        "make": coverage.target.make,
        "model": coverage.target.model,
        "directiveCount": coverage.directive_count,
        "sourceDocumentCount": coverage.source_document_count,
        "derivedLogicalStorageBytes": coverage.derived_storage_bytes,
        "sourceSnapshotId": coverage.current_source_snapshot_id,
        "sourceContentHash": (
            coverage.current_source_snapshot.content_hash
            if coverage.current_source_snapshot
            else None
        ),
        "lastBuiltAt": coverage.last_built_at,
        "lastResolvedAt": coverage.last_resolved_at,
        "actualCostUsd": sum(
            (entry.actual_cost_usd for entry in coverage.cost_entries),
            start=0,
        ),
        "allocatedCostUsd": sum(
            (entry.allocated_cost_usd for entry in coverage.cost_entries),
            start=0,
        ),
        "clients": [
            {
                "organizationId": subscription.organization_id,
                "organizationName": subscription.organization.name,
                "aircraftId": subscription.aircraft_id,
                "nNumber": subscription.aircraft.n_number_normalized,
                "triggeredCreation": subscription.triggered_creation,
                "linkedAt": subscription.linked_at,
            }
            for subscription in sorted(
                active_subscriptions,
                key=lambda item: (
                    item.organization.name,
                    item.aircraft.n_number_normalized,
                ),
            )
        ],
    }
