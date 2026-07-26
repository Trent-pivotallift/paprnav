from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class IngestionJobSummary(BaseModel):
    id: str
    uploadId: str
    uploadDownloadUrl: str
    aircraftId: str
    status: str
    pageExtractionStatus: str
    ocrStatus: str
    verificationStatus: str
    entryExtractionStatus: str
    logbookSection: Optional[str]
    errorCode: Optional[str]
    errorMessage: Optional[str]
    documentInspection: Optional[dict] = None


class OCRCorrectionResponse(BaseModel):
    id: str
    ocrTextSpanId: str
    correctionOrder: int
    originalText: str
    correctedText: str
    originalConfidence: Optional[float]
    correctionReason: str
    notes: Optional[str]


class OCRTextSpanResponse(BaseModel):
    id: str
    ingestionPageId: str
    providerBlockId: Optional[str]
    spanType: str
    text: str
    confidence: Optional[float]
    confidenceScale: str
    bboxLeft: Optional[float]
    bboxTop: Optional[float]
    bboxWidth: Optional[float]
    bboxHeight: Optional[float]
    bboxUnits: str
    readingOrder: int
    corrections: list[OCRCorrectionResponse] = []


class LogicalPageRegionResponse(BaseModel):
    id: str
    regionKey: str
    regionType: str
    bboxLeft: float
    bboxTop: float
    bboxWidth: float
    bboxHeight: float
    bboxUnits: str
    readingOrder: int
    classification: Optional[dict] = None


class IngestionPageResponse(BaseModel):
    id: str
    sourcePageNumber: int
    currentPageOrder: int
    pageLabel: Optional[str]
    imageStorageBackend: Optional[str]
    imageStorageKey: Optional[str]
    imageDownloadUrl: Optional[str]
    widthPx: Optional[int]
    heightPx: Optional[int]
    rotationDegrees: Optional[float]
    extractionConfidence: Optional[float]
    inspectionStatus: Optional[str] = None
    sourcePageFingerprint: Optional[str] = None
    canonicalImageSha256: Optional[str] = None
    renderProfile: Optional[str] = None
    renderMetadata: Optional[dict] = None
    pageClassification: Optional[dict] = None
    nativeTextEvaluation: Optional[dict] = None
    extractionPlan: Optional[dict] = None
    stageResults: Optional[dict] = None
    logicalRegions: list[LogicalPageRegionResponse] = []
    spans: list[OCRTextSpanResponse] = []


class LogbookEntryEvidenceResponse(BaseModel):
    id: str
    fieldName: Optional[str]
    evidenceType: str
    confidence: Optional[float]
    span: Optional[OCRTextSpanResponse]
    reviewMetadata: Optional[dict] = None


class CandidateRegionResponse(BaseModel):
    pageId: str
    bboxLeft: float
    bboxTop: float
    bboxWidth: float
    bboxHeight: float
    bboxUnits: str = "ratio"


class ExtractedLogbookEntryCandidateResponse(BaseModel):
    id: str
    entryDate: Optional[date]
    section: str
    description: str
    performerName: Optional[str]
    performerCredential: Optional[str]
    tachTime: Optional[float]
    hobbsTime: Optional[float]
    totalTime: Optional[float]
    reviewStatus: str
    validationStatus: Optional[str] = None
    validationResults: Optional[dict] = None
    region: Optional[CandidateRegionResponse] = None
    evidence: list[LogbookEntryEvidenceResponse] = []


class PageVerificationResponse(BaseModel):
    id: str
    isOrderConfirmed: bool
    isComplete: bool
    missingOrUncertainNotes: Optional[str]


class IngestionJobDetailResponse(BaseModel):
    job: IngestionJobSummary
    pages: list[IngestionPageResponse]
    latestVerification: Optional[PageVerificationResponse]
    extractedEntries: list[ExtractedLogbookEntryCandidateResponse] = []


class PageOrderUpdate(BaseModel):
    pageId: str
    currentPageOrder: int = Field(ge=1)


class PageVerificationRequest(BaseModel):
    pages: list[PageOrderUpdate]
    isOrderConfirmed: bool
    isComplete: bool
    missingOrUncertainNotes: Optional[str] = None


class OCRCorrectionRequest(BaseModel):
    ocrTextSpanId: str
    correctedText: str = Field(min_length=1)
    correctionReason: str = Field(default="low_confidence", min_length=1, max_length=64)
    notes: Optional[str] = None


class ExtractedLogbookEntryResponse(BaseModel):
    id: str
    entryDate: Optional[date]
    section: str
    description: str
    performerName: Optional[str]
    performerCredential: Optional[str]
    tachTime: Optional[float]
    hobbsTime: Optional[float]
    totalTime: Optional[float]
    reviewStatus: str


class ExtractLogbookEntriesResponse(BaseModel):
    entries: list[ExtractedLogbookEntryResponse]


class IngestionReviewMetricsResponse(BaseModel):
    ingestionJobId: str
    extractedEntryCount: int
    reviewedEntryCount: int
    verifiedEntryCount: int
    verificationRate: float
    medianReviewSeconds: Optional[float]
    meanEditedFieldCount: Optional[float]
    acceptedFieldAccuracy: Optional[float]
    acceptedFieldCount: int
    decidedFieldCount: int
    unresolvedFieldCount: int
    nullFieldCount: int
