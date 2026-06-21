from datetime import date
from typing import Any, Optional

from pydantic import BaseModel


class ADDiscoveryRecordResponse(BaseModel):
    id: str
    federalRegisterDocumentNumber: str
    title: str
    documentType: Optional[str]
    publicationDate: Optional[date]
    htmlUrl: Optional[str]
    pdfUrl: Optional[str]
    classification: str
    classificationConfidence: float
    classificationReason: str
    contentHash: str


class AirworthinessDirectiveResponse(BaseModel):
    id: str
    discoveryRecordId: Optional[str]
    adNumber: Optional[str]
    title: str
    status: str
    extractionStatus: str
    reviewStatus: str
    federalRegisterDocumentNumber: Optional[str]
    publicationDate: Optional[date]
    htmlUrl: Optional[str]
    pdfUrl: Optional[str]


class ADExtractionResponse(BaseModel):
    id: str
    directiveId: str
    providerName: str
    providerVersion: str
    schemaVersion: str
    inputContentHash: str
    status: str
    confidence: float
    output: dict[str, Any]
    citations: list[dict[str, Any]]


class ADExtractionReviewResponse(BaseModel):
    id: str
    status: str
    proposedOutput: dict[str, Any]
    decisionOutput: Optional[dict[str, Any]]
    decision: Optional[str]
    notes: Optional[str]
    extraction: ADExtractionResponse
    directive: AirworthinessDirectiveResponse
    sourceText: str


class ADExtractionReviewListResponse(BaseModel):
    reviews: list[ADExtractionReviewResponse]


class ADReviewDecisionRequest(BaseModel):
    decision: str
    output: Optional[dict[str, Any]] = None
    notes: Optional[str] = None


class ADReviewDecisionResponse(BaseModel):
    review: ADExtractionReviewResponse


class ADMatchEvidenceResponse(BaseModel):
    id: str
    logbookEntryId: str
    entryDate: date
    section: str
    evidenceType: str
    fieldName: Optional[str]
    matchedText: str
    confidence: float
    rationale: str


class ADMatchAdjudicationResponse(BaseModel):
    id: str
    status: str
    decision: Optional[str]
    notes: Optional[str]
    futureImprovementTags: list[str]


class ADMatchComponentResponse(BaseModel):
    id: Optional[str]
    role: Optional[str]
    componentType: Optional[str]
    displayName: Optional[str]
    make: Optional[str]
    model: Optional[str]
    serialNumber: Optional[str]
    source: Optional[str]


class ADMatchTargetResponse(BaseModel):
    id: Optional[str]
    productType: Optional[str]
    productSubtype: Optional[str]
    make: Optional[str]
    model: Optional[str]


class ADMatchPublicationResponse(BaseModel):
    sourceSystem: str
    sourceType: str
    sourceIdentifier: str
    status: Optional[str]
    htmlUrl: Optional[str]
    pdfUrl: Optional[str]


class ADMatchApplicabilityResponse(BaseModel):
    component: Optional[ADMatchComponentResponse]
    target: Optional[ADMatchTargetResponse]
    basis: Optional[str]
    confidence: Optional[float]
    status: Optional[str]
    sourceStatus: Optional[str]
    serialStatus: Optional[str]
    publications: list[ADMatchPublicationResponse]
    snapshot: Optional[dict[str, Any]]


class ADMatchResultResponse(BaseModel):
    id: str
    aircraftId: str
    aircraftFacts: dict[str, Optional[str]]
    directive: AirworthinessDirectiveResponse
    status: str
    matchType: str
    confidence: float
    rationale: str
    unresolvedReasons: list[str]
    applicability: Optional[ADMatchApplicabilityResponse]
    algorithmName: str
    algorithmVersion: str
    inputHash: str
    evidence: list[ADMatchEvidenceResponse]
    adjudication: Optional[ADMatchAdjudicationResponse]


class ADMatchResultListResponse(BaseModel):
    matches: list[ADMatchResultResponse]


class ADMatchAdjudicationDecisionRequest(BaseModel):
    decision: str
    notes: Optional[str] = None
    futureImprovementTags: list[str] = []


class ADMatchAdjudicationDecisionResponse(BaseModel):
    match: ADMatchResultResponse
