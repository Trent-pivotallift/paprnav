import re
from typing import Optional

from app.models.core import Aircraft, Organization, Upload

TAG_SAFE_PATTERN = re.compile(r"[^A-Za-z0-9_.:/=+\-@]+")


def normalize_tag_value(value: str, *, fallback: str) -> str:
    cleaned = TAG_SAFE_PATTERN.sub("-", value.strip())
    cleaned = cleaned.strip("-")
    return cleaned[:128] or fallback


def organization_account_tag(organization: Organization) -> str:
    return organization.customer_account_tag or f"acct-{organization.id}"


def aircraft_cost_tag(aircraft: Aircraft) -> str:
    return aircraft.cost_allocation_tag or f"aircraft-{aircraft.id}"


def ensure_organization_account_tag(organization: Organization) -> str:
    if not organization.customer_account_tag:
        organization.customer_account_tag = normalize_tag_value(f"acct-{organization.id}", fallback=organization.id)
    return organization.customer_account_tag


def ensure_aircraft_cost_tag(aircraft: Aircraft) -> str:
    if not aircraft.cost_allocation_tag:
        aircraft.cost_allocation_tag = normalize_tag_value(f"aircraft-{aircraft.id}", fallback=aircraft.id)
    return aircraft.cost_allocation_tag


def upload_cost_tags(*, organization: Organization, aircraft: Aircraft, upload_id: str, stage: str = "initial-ocr") -> dict[str, str]:
    account_tag = ensure_organization_account_tag(organization)
    aircraft_tag = ensure_aircraft_cost_tag(aircraft)
    return {
        "Project": "paprnav",
        "Environment": "pilot",
        "Application": "paprnav",
        "CustomerAccount": account_tag,
        "Aircraft": aircraft_tag,
        "Upload": normalize_tag_value(f"upload-{upload_id}", fallback=upload_id),
        "BillableAccount": account_tag,
        "BillingStage": normalize_tag_value(stage, fallback="ocr"),
    }


def upload_billable_account_tag(upload: Upload) -> Optional[str]:
    if upload.initial_ocr_billable_to_tag:
        return upload.initial_ocr_billable_to_tag
    if upload.cost_allocation_tags:
        return upload.cost_allocation_tags.get("BillableAccount")
    return None
