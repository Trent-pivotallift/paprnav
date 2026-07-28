from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.core import User
from app.schemas.admin import ADCostAdminSummaryResponse, OCRBillingSummaryResponse
from app.services.ad_coverage import summarize_ad_costs
from app.services.ocr_billing import summarize_ocr_billing

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def ensure_platform_admin(user: User) -> None:
    is_platform_admin = any(
        membership.status == "active" and membership.role == "platform_admin"
        for membership in user.memberships
    )
    if not is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform administrator access required",
        )


@router.get("/ad-costs", response_model=ADCostAdminSummaryResponse)
def get_ad_cost_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ADCostAdminSummaryResponse:
    ensure_platform_admin(current_user)
    return ADCostAdminSummaryResponse.model_validate(summarize_ad_costs(db))


@router.get("/ocr-billing", response_model=OCRBillingSummaryResponse)
def get_ocr_billing_summary(
    date_from: Optional[datetime] = Query(default=None, alias="dateFrom"),
    date_to: Optional[datetime] = Query(default=None, alias="dateTo"),
    account_tag: Optional[str] = Query(default=None, alias="accountTag"),
    aircraft_tag: Optional[str] = Query(default=None, alias="aircraftTag"),
    billing_status: Optional[
        Literal["chargeable", "not_billable", "credited", "disputed"]
    ] = Query(default=None, alias="billingStatus"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OCRBillingSummaryResponse:
    ensure_platform_admin(current_user)
    date_from = _normalized_datetime(date_from)
    date_to = _normalized_datetime(date_to)
    account_tag = _normalized_filter(account_tag)
    aircraft_tag = _normalized_filter(aircraft_tag)
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="dateFrom must be earlier than or equal to dateTo",
        )
    return OCRBillingSummaryResponse.model_validate(
        summarize_ocr_billing(
            db,
            date_from=date_from,
            date_to=date_to,
            account_tag=account_tag,
            aircraft_tag=aircraft_tag,
            billing_status=billing_status,
        )
    )


def _normalized_datetime(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _normalized_filter(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
