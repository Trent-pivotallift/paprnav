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
  lastLogEntryDate: string | null;
  complianceStatus: string;
}

export interface AircraftListResponse {
  aircraft: Aircraft[];
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

export function logout() {
  return apiFetch<{ ok: boolean }>("/api/v1/auth/logout", { method: "POST" });
}

export function listAircraft() {
  return apiFetch<AircraftListResponse>("/api/v1/aircraft");
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
