from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.core import User
from app.schemas.admin import ADCostAdminSummaryResponse
from app.services.ad_coverage import summarize_ad_costs

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
