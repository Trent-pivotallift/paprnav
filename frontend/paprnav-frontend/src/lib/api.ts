const API_BASE_URL = process.env.NEXT_PUBLIC_PAPRNAV_API_BASE_URL ?? "/api/backend";

export interface Membership {
  organizationId: string;
  organizationName: string;
  role: string;
}

export interface CurrentUser {
  id: string;
  email: string;
  name: string;
  memberships: Membership[];
}

export interface AuthResponse {
  user: CurrentUser;
}

export interface ProfileUpdateRequest {
  name: string;
}

export interface Aircraft {
  id: string;
  nNumber: string;
  nNumberNormalized: string;
  make: string;
  model: string;
  serialNumber: string | null;
  year: number | null;
  airframeSerialNumber: string | null;
  engineMake: string | null;
  engineModel: string | null;
  engineSerialNumber: string | null;
  propellerMake: string | null;
  propellerModel: string | null;
  propellerSerialNumber: string | null;
  installedComponents: InstalledComponent[];
  lastLogEntryDate: string | null;
  complianceStatus: string;
}

export interface InstalledComponent {
  id: string;
  role: string;
  componentType: string;
  make: string | null;
  model: string | null;
  serialNumber: string | null;
  source: string;
  confidence: number | null;
}

export interface AircraftListResponse {
  aircraft: Aircraft[];
}

export interface AircraftAssignment {
  id: string;
  aircraftId: string;
  organizationId: string;
  organizationName: string;
  organizationType: string;
  role: string;
  status: string;
}

export interface AircraftAssignmentListResponse {
  assignments: AircraftAssignment[];
}

export type LogbookSection = "airframe" | "engine" | "propeller";

export interface LogbookEntry {
  id: string;
  aircraftId: string;
  section: LogbookSection;
  entryDate: string;
  description: string;
  performerName: string | null;
  performerCredential: string | null;
  sourceType: string;
  reviewStatus: string;
  tachTime: number | null;
  hobbsTime: number | null;
  totalTime: number | null;
}

export interface LogbookEntryListResponse {
  entries: LogbookEntry[];
}

export interface LogbookEntryUpdateRequest {
  section?: LogbookSection;
  entryDate?: string;
  description?: string;
  performerName?: string | null;
  performerCredential?: string | null;
  tachTime?: number | null;
  hobbsTime?: number | null;
  totalTime?: number | null;
  reviewStatus?: "draft" | "needs_review" | "verified";
}

export interface LogbookEntryCreateRequest {
  section: LogbookSection;
  entryDate: string;
  description: string;
  performerName?: string | null;
  performerCredential?: string | null;
  tachTime?: number | null;
  hobbsTime?: number | null;
  totalTime?: number | null;
}

export interface Upload {
  id: string;
  aircraftId: string;
  originalFilename: string;
  contentType: string;
  fileSizeBytes: number;
  sha256: string;
  status: string;
  downloadUrl: string;
}

export interface UploadCreateResponse {
  upload: Upload;
  ingestionJob: IngestionJobSummary;
}

export interface IngestionJobSummary {
  id: string;
  uploadId: string;
  aircraftId: string;
  status: string;
  pageExtractionStatus: string;
  ocrStatus: string;
  verificationStatus: string;
  entryExtractionStatus: string;
  logbookSection: LogbookSection | null;
  errorCode: string | null;
  errorMessage: string | null;
}

export interface OCRCorrection {
  id: string;
  ocrTextSpanId: string;
  originalText: string;
  correctedText: string;
  originalConfidence: number | null;
  correctionReason: string;
  notes: string | null;
}

export interface OCRTextSpan {
  id: string;
  ingestionPageId: string;
  providerBlockId: string | null;
  spanType: string;
  text: string;
  confidence: number | null;
  confidenceScale: string;
  bboxLeft: number | null;
  bboxTop: number | null;
  bboxWidth: number | null;
  bboxHeight: number | null;
  bboxUnits: string;
  readingOrder: number;
  corrections: OCRCorrection[];
}

export interface IngestionPage {
  id: string;
  sourcePageNumber: number;
  currentPageOrder: number;
  pageLabel: string | null;
  imageStorageBackend: string | null;
  imageStorageKey: string | null;
  widthPx: number | null;
  heightPx: number | null;
  rotationDegrees: number | null;
  extractionConfidence: number | null;
  spans: OCRTextSpan[];
}

export interface PageVerification {
  id: string;
  isOrderConfirmed: boolean;
  isComplete: boolean;
  missingOrUncertainNotes: string | null;
}

export interface IngestionJobDetailResponse {
  job: IngestionJobSummary;
  pages: IngestionPage[];
  latestVerification: PageVerification | null;
}

export interface ExtractLogbookEntriesResponse {
  entries: Array<{
    id: string;
    entryDate: string;
    section: LogbookSection;
    description: string;
    performerName: string | null;
    performerCredential: string | null;
    reviewStatus: string;
  }>;
}

export interface AirworthinessDirective {
  id: string;
  discoveryRecordId: string | null;
  adNumber: string | null;
  title: string;
  status: string;
  extractionStatus: string;
  reviewStatus: string;
  federalRegisterDocumentNumber: string | null;
  publicationDate: string | null;
  htmlUrl: string | null;
  pdfUrl: string | null;
}

export interface ADExtraction {
  id: string;
  directiveId: string;
  providerName: string;
  providerVersion: string;
  schemaVersion: string;
  inputContentHash: string;
  status: string;
  confidence: number;
  output: Record<string, unknown>;
  citations: Array<Record<string, unknown>>;
}

export interface ADExtractionReview {
  id: string;
  status: string;
  proposedOutput: Record<string, unknown>;
  decisionOutput: Record<string, unknown> | null;
  decision: string | null;
  notes: string | null;
  extraction: ADExtraction;
  directive: AirworthinessDirective;
  sourceText: string;
}

export interface ADExtractionReviewListResponse {
  reviews: ADExtractionReview[];
}

export interface ADMatchEvidence {
  id: string;
  logbookEntryId: string;
  entryDate: string;
  section: LogbookSection;
  evidenceType: string;
  fieldName: string | null;
  matchedText: string;
  confidence: number;
  rationale: string;
}

export interface ADMatchAdjudication {
  id: string;
  status: string;
  decision: string | null;
  notes: string | null;
  futureImprovementTags: string[];
}

export interface ADMatchComponent {
  id: string | null;
  role: string | null;
  componentType: string | null;
  displayName: string | null;
  make: string | null;
  model: string | null;
  serialNumber: string | null;
  source: string | null;
}

export interface ADMatchTarget {
  id: string | null;
  productType: string | null;
  productSubtype: string | null;
  make: string | null;
  model: string | null;
}

export interface ADMatchPublication {
  sourceSystem: string;
  sourceType: string;
  sourceIdentifier: string;
  status: string | null;
  htmlUrl: string | null;
  pdfUrl: string | null;
}

export interface ADMatchApplicability {
  component: ADMatchComponent | null;
  target: ADMatchTarget | null;
  basis: string | null;
  confidence: number | null;
  status: string | null;
  sourceStatus: string | null;
  serialStatus: string | null;
  publications: ADMatchPublication[];
  snapshot: Record<string, unknown> | null;
}

export interface ADMatchResult {
  id: string;
  aircraftId: string;
  aircraftFacts: Record<string, string | null>;
  directive: AirworthinessDirective;
  status: string;
  matchType: string;
  confidence: number;
  rationale: string;
  unresolvedReasons: string[];
  applicability: ADMatchApplicability | null;
  algorithmName: string;
  algorithmVersion: string;
  inputHash: string;
  evidence: ADMatchEvidence[];
  adjudication: ADMatchAdjudication | null;
}

export interface ProductEvent {
  id: string;
  actorUserId: string | null;
  organizationId: string | null;
  aircraftId: string | null;
  eventType: string;
  eventSource: string;
  subjectType: string;
  subjectId: string | null;
  eventTime: string;
  properties: Record<string, unknown>;
}

export interface WorkflowStatusEvent {
  id: string;
  workflowType: string;
  workflowId: string;
  previousStatus: string | null;
  newStatus: string;
  reason: string | null;
  actorType: string;
  actorUserId: string | null;
  createdAt: string;
}

export interface UserFeedback {
  id: string;
  submittedByUserId: string;
  organizationId: string | null;
  aircraftId: string | null;
  subjectType: string;
  subjectId: string | null;
  feedbackType: string;
  message: string;
  severity: string;
  status: string;
}

export interface ObservabilityListResponse {
  events: ProductEvent[];
  workflowEvents: WorkflowStatusEvent[];
  feedback: UserFeedback[];
}

export interface ADMatchResultListResponse {
  matches: ADMatchResult[];
}

interface ApiErrorPayload {
  detail?: string;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const isFormData = typeof FormData !== "undefined" && init.body instanceof FormData;
  if (init.body && !headers.has("content-type") && !isFormData) {
    headers.set("content-type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as ApiErrorPayload;
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      // Keep the status-based message if the API does not return JSON.
    }
    throw new ApiError(response.status, message);
  }

  return response.json() as Promise<T>;
}

export function login(email: string, password: string) {
  return apiFetch<AuthResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function register(name: string, email: string, password: string) {
  return apiFetch<AuthResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
  });
}

export function getCurrentUser() {
  return apiFetch<AuthResponse>("/api/v1/auth/me");
}

export function updateProfile(payload: ProfileUpdateRequest) {
  return apiFetch<AuthResponse>("/api/v1/auth/profile", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function logout() {
  return apiFetch<{ ok: boolean }>("/api/v1/auth/logout", { method: "POST" });
}

export function listAircraft() {
  return apiFetch<AircraftListResponse>("/api/v1/aircraft");
}

export function listAircraftAssignments(aircraftId: string) {
  return apiFetch<AircraftAssignmentListResponse>(`/api/v1/aircraft/${aircraftId}/assignments`);
}

export function createAircraftAssignment(aircraftId: string, maintenanceUserEmail: string) {
  return apiFetch<AircraftAssignment>(`/api/v1/aircraft/${aircraftId}/assignments`, {
    method: "POST",
    body: JSON.stringify({ maintenanceUserEmail }),
  });
}

export function listLogbookEntries(aircraftId: string, section?: LogbookSection) {
  const params = section ? `?section=${encodeURIComponent(section)}` : "";
  return apiFetch<LogbookEntryListResponse>(`/api/v1/aircraft/${aircraftId}/logbook-entries${params}`);
}

export function createLogbookEntry(aircraftId: string, payload: LogbookEntryCreateRequest) {
  return apiFetch<LogbookEntry>(`/api/v1/aircraft/${aircraftId}/logbook-entries`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getLogbookEntry(aircraftId: string, entryId: string) {
  return apiFetch<LogbookEntry>(`/api/v1/aircraft/${aircraftId}/logbook-entries/${entryId}`);
}

export function updateLogbookEntry(aircraftId: string, entryId: string, payload: LogbookEntryUpdateRequest) {
  return apiFetch<LogbookEntry>(`/api/v1/aircraft/${aircraftId}/logbook-entries/${entryId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function uploadLogbookFile(aircraftId: string, file: File, section?: LogbookSection) {
  const formData = new FormData();
  formData.append("file", file);
  if (section) {
    formData.append("section", section);
  }

  return apiFetch<UploadCreateResponse>(`/api/v1/aircraft/${aircraftId}/uploads`, {
    method: "POST",
    body: formData,
  });
}

export function getIngestionJob(jobId: string) {
  return apiFetch<IngestionJobDetailResponse>(`/api/v1/ingestion-jobs/${jobId}`);
}

export function verifyIngestionPages(
  jobId: string,
  payload: {
    pages: Array<{ pageId: string; currentPageOrder: number }>;
    isOrderConfirmed: boolean;
    isComplete: boolean;
    missingOrUncertainNotes?: string | null;
  },
) {
  return apiFetch<IngestionJobDetailResponse>(`/api/v1/ingestion-jobs/${jobId}/page-verification`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createOcrCorrection(
  jobId: string,
  payload: {
    ocrTextSpanId: string;
    correctedText: string;
    correctionReason?: string;
    notes?: string | null;
  },
) {
  return apiFetch<OCRCorrection>(`/api/v1/ingestion-jobs/${jobId}/ocr-corrections`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function extractLogbookEntries(jobId: string) {
  return apiFetch<ExtractLogbookEntriesResponse>(`/api/v1/ingestion-jobs/${jobId}/extract-logbook-entries`, {
    method: "POST",
  });
}

export function listAdExtractionReviews() {
  return apiFetch<ADExtractionReviewListResponse>("/api/v1/ads/extraction-reviews");
}

export function decideAdExtractionReview(
  reviewId: string,
  payload: {
    decision: "approved" | "edited" | "rejected";
    output?: Record<string, unknown>;
    notes?: string | null;
  },
) {
  return apiFetch<{ review: ADExtractionReview }>(`/api/v1/ads/extraction-reviews/${reviewId}/decision`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listAircraftAdMatches(aircraftId: string) {
  return apiFetch<ADMatchResultListResponse>(`/api/v1/ads/aircraft/${aircraftId}/matches`);
}

export function decideAdMatch(
  matchId: string,
  payload: {
    decision: "satisfied" | "not_satisfied" | "not_applicable" | "needs_more_info" | "deferred";
    notes?: string | null;
    futureImprovementTags?: string[];
  },
) {
  return apiFetch<{ match: ADMatchResult }>(`/api/v1/ads/matches/${matchId}/adjudication`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listObservability(params: Record<string, string> = {}) {
  const query = new URLSearchParams(params);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<ObservabilityListResponse>(`/api/v1/observability${suffix}`);
}

export function createFeedback(payload: {
  subjectType: string;
  subjectId?: string | null;
  aircraftId?: string | null;
  feedbackType?: string;
  message: string;
  severity?: string;
}) {
  return apiFetch<{ feedback: UserFeedback }>("/api/v1/observability/feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateFeedbackStatus(feedbackId: string, status: string) {
  return apiFetch<{ feedback: UserFeedback }>(`/api/v1/observability/feedback/${feedbackId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
