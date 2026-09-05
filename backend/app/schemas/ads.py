from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


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


class ADDirectiveApplicabilityTargetResponse(BaseModel):
    groupKey: Optional[str]
    productType: str
    productSubtype: Optional[str]
    manufacturer: Optional[str]
    model: Optional[str]
    sourceManufacturer: Optional[str]
    sourceModel: Optional[str]


class AirworthinessDirectiveResponse(BaseModel):
    id: str
    discoveryRecordId: Optional[str]
    adNumber: Optional[str]
    officialAdNumber: Optional[str]
    title: str
    status: str
    extractionStatus: str
    reviewStatus: str
    federalRegisterDocumentNumber: Optional[str]
    publicationDate: Optional[date]
    htmlUrl: Optional[str]
    pdfUrl: Optional[str]
    applicabilityTargets: list[ADDirectiveApplicabilityTargetResponse] = []


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


class ADSourceDocumentResponse(BaseModel):
    id: str
    sourceSystem: str
    sourceType: str
    sourceIdentifier: str
    parentSourceIdentifier: Optional[str]
    sourceUrl: Optional[str]
    contentUrl: str
    mediaType: Optional[str]
    contentHash: str
    storageBytes: int
    capturedAt: datetime
    publicationDate: Optional[date]
    parserName: Optional[str]
    parserVersion: Optional[str]
    relevantPageStart: Optional[int] = None
    relevantPageEnd: Optional[int] = None
    relevantPageNumbers: list[int] = Field(default_factory=list)
    relevantPagesContiguous: bool = False
    navigationUrl: str


class ADSourcePageEvidenceResponse(BaseModel):
    sourceDocumentId: str
    directiveId: str
    sourceContentHash: str
    pageNumber: int
    pageTextVersionId: str
    pageTextHash: str
    pageText: str
    renditionId: str
    renditionHash: str
    renditionMediaType: str
    renditionWidthPx: int
    renditionHeightPx: int


class ADSourcePageMaterializeRequest(BaseModel):
    directiveId: str
    expectedSourceContentHash: str = Field(min_length=64, max_length=64)


class ADEvidenceFragmentCreateRequest(BaseModel):
    directiveId: str
    pageNumber: int = Field(ge=1)
    expectedSourceContentHash: str = Field(min_length=64, max_length=64)
    expectedPageTextHash: str = Field(min_length=64, max_length=64)
    characterStart: int = Field(ge=0)
    characterEnd: int = Field(gt=0)
    reason: str = Field(min_length=1, max_length=2000)
    paragraphLocator: Optional[str] = Field(default=None, max_length=255)
    tableLocator: Optional[str] = Field(default=None, max_length=255)
    rowLocator: Optional[str] = Field(default=None, max_length=255)
    noteLocator: Optional[str] = Field(default=None, max_length=255)


class ADEvidenceFragmentResponse(BaseModel):
    id: str
    directiveId: str
    sourceDocumentId: str
    sourceContentHash: str
    pageTextVersionId: str
    pageStart: int
    pageEnd: int
    characterStart: int
    characterEnd: int
    paragraphLocator: Optional[str]
    tableLocator: Optional[str]
    rowLocator: Optional[str]
    noteLocator: Optional[str]
    exactText: str
    fragmentHash: str
    createdByUserId: str
    createdAt: datetime
    created: bool


class ADV4SubmissionRelationshipAuditResponse(BaseModel):
    relationshipKey: str
    relationType: str
    predecessorProposalId: str
    reason: str
    evidenceKeys: list[str]
    relationshipHash: str
    createdAt: datetime


class ADV4SubmissionAuditResponse(BaseModel):
    submissionId: str
    actorUserId: str
    authorizingMembershipId: str
    organizationId: str
    actorRole: str
    actorStatus: str
    authPolicyName: str
    authPolicyVersion: str
    authClaimsHash: str
    endpointAction: str
    idempotencyKey: str
    requestHash: str
    rawTransportHash: str
    relationships: list[ADV4SubmissionRelationshipAuditResponse]
    createdAt: datetime


class ADV4CandidateResponse(BaseModel):
    proposalId: str
    submissionId: str
    directiveId: str
    schemaVersion: str
    canonicalizationVersion: str
    validatorVersion: str
    canonicalHash: str
    evidenceBindingHash: str
    bindingCount: int
    gate: str
    contentReused: bool = False
    idempotentRetry: bool = False
    canonicalProposal: dict[str, Any]
    submissions: list[ADV4SubmissionAuditResponse] = Field(default_factory=list)
    submissionCount: int
    submissionLimit: int
    submissionOffset: int
    createdAt: datetime


class ADV4CandidateListResponse(BaseModel):
    candidates: list[ADV4CandidateResponse]
    count: int
    total: int
    limit: int
    offset: int


class ADProposalProvenanceResponse(BaseModel):
    stagingDecisionId: str
    actorUserId: Optional[str]
    stagedAt: datetime
    stagingMode: str


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
    sourcePages: list[dict[str, Any]]
    sourceDocuments: list[ADSourceDocumentResponse]
    requirementCount: int
    unresolvedRequirementCount: int
    evidenceStatus: str
    evidenceMessage: str
    canApprove: bool
    approvalBlockers: list[str]
    proposalProvenance: Optional[ADProposalProvenanceResponse]


class ADExtractionReviewListResponse(BaseModel):
    reviews: list[ADExtractionReviewResponse]
    currentOffset: int
    totalCount: int
    pendingCount: int
    reviewedCount: int
    verifiedCount: int
    quarantinedCount: int
    approvalReadyCount: int


class ADReviewDecisionRequest(BaseModel):
    decision: str
    output: Optional[dict[str, Any]] = None
    notes: Optional[str] = None


class ADReviewDecisionResponse(BaseModel):
    review: ADExtractionReviewResponse


class ADMatchEvidenceResponse(BaseModel):
    id: str
    logbookEntryId: str
    entryDate: Optional[date]
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


class ADDueStateResponse(BaseModel):
    id: str
    requirementId: str
    status: str
    dueDate: Optional[date]
    dueMetric: Optional[str]
    dueValue: Optional[str]
    triggerStates: list[dict[str, Any]]
    unresolvedReasons: list[str]
    algorithmVersion: str
    inputHash: str


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
    dueState: Optional[ADDueStateResponse]
    dueStates: list[ADDueStateResponse]
    algorithmName: str
    algorithmVersion: str
    inputHash: str
    evidence: list[ADMatchEvidenceResponse]
    adjudication: Optional[ADMatchAdjudicationResponse]


class ADCoverageTargetStatusResponse(BaseModel):
    productType: str
    make: Optional[str]
    model: Optional[str]
    status: str


class ADMatchResultListResponse(BaseModel):
    matches: list[ADMatchResultResponse]
    matcherStatus: str
    algorithmName: str
    algorithmVersion: str
    reprocessingRequired: bool
    coverageStatus: str
    coverageWarnings: list[str]
    coverageTargets: list[ADCoverageTargetStatusResponse]


class ADMatchAdjudicationDecisionRequest(BaseModel):
    decision: str
    notes: Optional[str] = None
    futureImprovementTags: list[str] = []


class ADMatchAdjudicationDecisionResponse(BaseModel):
    match: ADMatchResultResponse
