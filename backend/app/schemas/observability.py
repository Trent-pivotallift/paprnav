from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ProductEventResponse(BaseModel):
    id: str
    actorUserId: Optional[str]
    organizationId: Optional[str]
    aircraftId: Optional[str]
    eventType: str
    eventSource: str
    subjectType: str
    subjectId: Optional[str]
    eventTime: datetime
    properties: dict[str, Any]


class WorkflowStatusEventResponse(BaseModel):
    id: str
    workflowType: str
    workflowId: str
    previousStatus: Optional[str]
    newStatus: str
    reason: Optional[str]
    actorType: str
    actorUserId: Optional[str]
    createdAt: datetime


class UserFeedbackResponse(BaseModel):
    id: str
    submittedByUserId: str
    organizationId: Optional[str]
    aircraftId: Optional[str]
    subjectType: str
    subjectId: Optional[str]
    feedbackType: str
    message: str
    severity: str
    status: str


class ObservabilityListResponse(BaseModel):
    events: list[ProductEventResponse]
    workflowEvents: list[WorkflowStatusEventResponse]
    feedback: list[UserFeedbackResponse]


class UserFeedbackCreateRequest(BaseModel):
    subjectType: str = Field(min_length=1, max_length=128)
    subjectId: Optional[str] = Field(default=None, max_length=128)
    aircraftId: Optional[str] = Field(default=None, max_length=36)
    feedbackType: str = Field(default="demo_note", max_length=64)
    message: str = Field(min_length=1, max_length=2000)
    severity: str = Field(default="medium", max_length=32)


class UserFeedbackUpdateRequest(BaseModel):
    status: str = Field(max_length=32)


class UserFeedbackCreateResponse(BaseModel):
    feedback: UserFeedbackResponse


class PilotAchievementRecentResponse(BaseModel):
    id: str
    eventType: str
    subjectType: str
    subjectId: str
    actorUserId: Optional[str]
    organizationId: Optional[str]
    aircraftId: Optional[str]
    eventTime: datetime


class PilotAchievementSummaryResponse(BaseModel):
    taxonomyVersion: str
    identityCount: int
    counts: dict[str, int]
    recent: list[PilotAchievementRecentResponse]


class PilotFailureRecentResponse(BaseModel):
    id: str
    workflowType: str
    workflowId: str
    category: str
    createdAt: datetime


class PilotFailureSummaryResponse(BaseModel):
    count: int
    counts: dict[str, int]
    recent: list[PilotFailureRecentResponse]


class PilotFeedbackRecentResponse(BaseModel):
    id: str
    feedbackType: str
    severity: str
    status: str
    organizationId: Optional[str]
    aircraftId: Optional[str]
    createdAt: datetime


class PilotFeedbackSummaryResponse(BaseModel):
    count: int
    typeCounts: dict[str, int]
    severityCounts: dict[str, int]
    statusCounts: dict[str, int]
    recent: list[PilotFeedbackRecentResponse]


class PilotOCRSummaryResponse(BaseModel):
    recordedRunsOnly: bool
    paidAttemptCoverageComplete: bool
    reconciliationCompletenessAvailable: bool
    missingRowVisibilityAvailable: bool
    attributionBasis: str
    historicalTagsReattributed: bool
    recordedRunCount: int
    lifecycleCounts: dict[str, int]
    pricingCounts: dict[str, int]
    attributionCounts: dict[str, int]
    billingCounts: dict[str, int]
    reconciliationRequiredRunCount: int
    knownEstimateRunCount: int
    unknownAmountRunCount: int
    knownPartialEstimateUsd: Optional[float]
    completedPricedEstimateUsd: Optional[float]
    estimateIsPartial: bool


class PilotSummaryResponse(BaseModel):
    generatedAt: datetime
    dateFrom: Optional[datetime]
    dateTo: Optional[datetime]
    actorUserId: Optional[str]
    achievements: PilotAchievementSummaryResponse
    failures: PilotFailureSummaryResponse
    feedback: PilotFeedbackSummaryResponse
    ocr: PilotOCRSummaryResponse
