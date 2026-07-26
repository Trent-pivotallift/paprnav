"use client";

import React, { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AlertTriangle, CheckCircle2, ChevronLeft, FileText, MapPinned, Maximize2, Wand2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/PageHeader";
import {
  CandidateRegion,
  createOcrCorrection,
  ExtractedLogbookEntryCandidate,
  extractLogbookEntries,
  getIngestionJob,
  getIngestionReviewMetrics,
  IngestionJobDetailResponse,
  IngestionReviewMetrics,
  LogbookEntryEvidence,
  OCRTextSpan,
  updateLogbookEntry,
  verifyIngestionPages,
} from "@/lib/api";

function normalizeNNumber(nNumber: string) {
  return nNumber.replace(/[-\s]/g, "").toUpperCase();
}

function effectiveText(span: OCRTextSpan) {
  return span.corrections.at(-1)?.correctedText ?? span.text;
}

function backendProxyPath(path: string) {
  return `/api/backend${path.startsWith("/") ? path : `/${path}`}`;
}

function uploadPreviewPath(detail: IngestionJobDetailResponse) {
  return backendProxyPath(detail.job.uploadDownloadUrl ?? `/api/v1/uploads/${detail.job.uploadId}/download`);
}

function formatBbox(span: OCRTextSpan) {
  const values = [span.bboxLeft, span.bboxTop, span.bboxWidth, span.bboxHeight];
  if (values.some((value) => value === null)) {
    return "No region";
  }
  return values.map((value) => value?.toFixed(3)).join(", ");
}

function hasDrawableRegion(span: OCRTextSpan | null) {
  return Boolean(
    span &&
      span.bboxLeft !== null &&
      span.bboxTop !== null &&
      span.bboxWidth !== null &&
      span.bboxHeight !== null &&
      span.bboxUnits === "ratio",
  );
}

function evidenceLabel(evidence: LogbookEntryEvidence) {
  return `${evidence.fieldName ?? "field"} · ${evidence.evidenceType}`;
}

type CandidateEditDraft = {
  entryDate?: string;
  tachTime?: string;
  hobbsTime?: string;
  totalTime?: string;
  performerName?: string;
  performerCredential?: string;
  description?: string;
};

function candidateDisplayValue(entry: ExtractedLogbookEntryCandidate, draft: CandidateEditDraft, fieldName: keyof CandidateEditDraft) {
  if (draft[fieldName] !== undefined) {
    return draft[fieldName] ?? "";
  }
  if (fieldName === "entryDate") {
    return entry.entryDate ?? "";
  }
  if (fieldName === "description") {
    return entry.description;
  }
  const value = entry[fieldName];
  return value === null ? "" : String(value);
}

function candidateFieldIsDirty(entry: ExtractedLogbookEntryCandidate, draft: CandidateEditDraft, fieldName: keyof CandidateEditDraft) {
  if (draft[fieldName] === undefined) {
    return false;
  }
  return candidateDisplayValue(entry, draft, fieldName) !== candidateDisplayValue(entry, {}, fieldName);
}

function candidateIsDirty(entry: ExtractedLogbookEntryCandidate, draft: CandidateEditDraft) {
  return (["entryDate", "tachTime", "hobbsTime", "totalTime", "performerName", "performerCredential", "description"] as const).some((fieldName) =>
    candidateFieldIsDirty(entry, draft, fieldName),
  );
}

function parseOptionalCandidateNumber(value: string, label: string) {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const numericValue = Number(trimmed);
  if (!Number.isFinite(numericValue) || numericValue < 0) {
    throw new Error(`Enter a valid non-negative ${label.toLowerCase()} value.`);
  }
  return numericValue;
}

export default function IngestionReviewPage() {
  const params = useParams();
  const nNumber = normalizeNNumber(params.nNumber as string);
  const jobId = params.jobId as string;
  const [detail, setDetail] = useState<IngestionJobDetailResponse | null>(null);
  const [reviewMetrics, setReviewMetrics] = useState<IngestionReviewMetrics | null>(null);
  const [notes, setNotes] = useState("");
  const [corrections, setCorrections] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [activeEvidenceId, setActiveEvidenceId] = useState<string | null>(null);
  const [isEvidenceExpanded, setIsEvidenceExpanded] = useState(false);
  const [candidateEdits, setCandidateEdits] = useState<Record<string, CandidateEditDraft>>({});
  const candidateReviewStartedAt = useRef<Record<string, number>>({});

  const lowConfidenceSpans = useMemo(
    () =>
      detail?.pages
        .flatMap((page) => page.spans)
        .filter((span) => span.spanType.toUpperCase() === "LINE" && (span.confidence ?? 100) < 80) ?? [],
    [detail],
  );
  const extractedEntries = useMemo(() => detail?.extractedEntries ?? [], [detail?.extractedEntries]);
  useEffect(() => {
    const startedAt = Date.now();
    for (const entry of extractedEntries) {
      candidateReviewStartedAt.current[entry.id] ??= startedAt;
    }
  }, [extractedEntries]);
  const evidenceOptions = useMemo(
    () => extractedEntries.flatMap((entry, entryIndex) => entry.evidence.map((evidence) => ({ entryIndex, entry, evidence }))),
    [extractedEntries],
  );
  const activeEvidence =
    evidenceOptions.find((item) => item.evidence.id === activeEvidenceId) ?? evidenceOptions.find((item) => hasDrawableRegion(item.evidence.span));
  const activePage =
    detail?.pages.find((page) => page.id === (activeEvidence?.evidence.span?.ingestionPageId ?? activeEvidence?.entry.region?.pageId)) ??
    detail?.pages[0] ??
    null;

  const loadJob = useCallback(async () => {
    setError(null);
    try {
      const [response, metrics] = await Promise.all([
        getIngestionJob(jobId),
        getIngestionReviewMetrics(jobId),
      ]);
      setDetail(response);
      setReviewMetrics(metrics);
      setNotes(response.latestVerification?.missingOrUncertainNotes ?? "");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load ingestion job.");
    }
  }, [jobId]);

  useEffect(() => {
    void loadJob();
  }, [loadJob]);

  async function handleVerifyPages(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail) {
      return;
    }
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      const response = await verifyIngestionPages(jobId, {
        pages: detail.pages.map((page) => ({ pageId: page.id, currentPageOrder: page.currentPageOrder })),
        isOrderConfirmed: true,
        isComplete: true,
        missingOrUncertainNotes: notes || null,
      });
      setDetail(response);
      setMessage("Page order and completeness saved.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save page verification.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleCorrection(span: OCRTextSpan) {
    const correctedText = corrections[span.id]?.trim();
    if (!correctedText) {
      setError("Enter corrected text before saving.");
      return;
    }
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      await createOcrCorrection(jobId, {
        ocrTextSpanId: span.id,
        correctedText,
        correctionReason: "low_confidence",
      });
      setCorrections((current) => ({ ...current, [span.id]: "" }));
      setMessage("Correction saved.");
      await loadJob();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save correction.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleExtractEntries() {
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      const response = await extractLogbookEntries(jobId);
      setMessage(`Created ${response.entries.length} structured logbook entr${response.entries.length === 1 ? "y" : "ies"}.`);
      await loadJob();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to extract structured entries.");
    } finally {
      setIsSaving(false);
    }
  }

  function updateCandidateEdit(entryId: string, fieldName: keyof CandidateEditDraft, value: string) {
    setCandidateEdits((current) => ({
      ...current,
      [entryId]: {
        ...current[entryId],
        [fieldName]: value,
      },
    }));
  }

  async function handleCandidateSave(
    entry: ExtractedLogbookEntryCandidate,
    reviewStatus: "needs_review" | "verified",
  ) {
    if (!detail) {
      return;
    }
    const draft = candidateEdits[entry.id] ?? {};
    const entryDate = candidateDisplayValue(entry, draft, "entryDate").trim();
    const description = candidateDisplayValue(entry, draft, "description").trim();
    if (!description) {
      setError("Description is required before saving a candidate.");
      return;
    }
    let tachTime: number | null;
    let hobbsTime: number | null;
    let totalTime: number | null;
    try {
      tachTime = parseOptionalCandidateNumber(candidateDisplayValue(entry, draft, "tachTime"), "Tach");
      hobbsTime = parseOptionalCandidateNumber(candidateDisplayValue(entry, draft, "hobbsTime"), "Hobbs");
      totalTime = parseOptionalCandidateNumber(candidateDisplayValue(entry, draft, "totalTime"), "Total");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Enter valid numeric values before saving.");
      return;
    }
    if (reviewStatus === "verified" && !entryDate) {
      setError("A date is required before verifying a candidate. Leave it blank and save for review if the source is uncertain.");
      return;
    }
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      await updateLogbookEntry(detail.job.aircraftId, entry.id, {
        entryDate: entryDate || null,
        description,
        performerName: candidateDisplayValue(entry, draft, "performerName").trim() || null,
        performerCredential: candidateDisplayValue(entry, draft, "performerCredential").trim() || null,
        tachTime,
        hobbsTime,
        totalTime,
        reviewStatus,
        reviewElapsedSeconds: Math.max(
          0,
          (Date.now() - (candidateReviewStartedAt.current[entry.id] ?? Date.now())) / 1000,
        ),
      });
      candidateReviewStartedAt.current[entry.id] = Date.now();
      setCandidateEdits((current) => ({
        ...current,
        [entry.id]: {},
      }));
      setMessage(reviewStatus === "verified" ? "Candidate verified." : "Candidate edits saved for review.");
      await loadJob();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save candidate edits.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <Link href={`/logbook/${nNumber}`} className="inline-flex items-center text-sm text-muted-foreground hover:text-primary">
          <ChevronLeft className="mr-1 h-4 w-4" />
          Back to logbook
        </Link>
      </div>

      <PageHeader title="OCR Review" description={`${nNumber} upload ingestion and human review`} />

      {error ? <p className="mt-6 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
      {message ? (
        <p className="mt-6 flex items-center gap-2 rounded-md border bg-card p-3 text-sm text-green-700 dark:text-green-400">
          <CheckCircle2 className="h-4 w-4" />
          {message}
        </p>
      ) : null}

      {!detail ? (
        <Card className="mt-8">
          <CardContent className="py-10 text-center text-sm text-muted-foreground">Loading ingestion job...</CardContent>
        </Card>
      ) : (
        <div className="mt-8 grid gap-6 xl:grid-cols-[minmax(360px,0.95fr)_minmax(0,1.25fr)]">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Scanned Document</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-hidden rounded-md border bg-muted">
                  <iframe
                    title="Scanned logbook document"
                    src={uploadPreviewPath(detail)}
                    className="h-[72vh] min-h-[520px] w-full bg-background"
                  />
                </div>
                <EvidenceOverlay
                  page={activePage}
                  evidence={activeEvidence?.evidence ?? null}
                  region={activeEvidence?.entry.region ?? null}
                  entryIndex={activeEvidence?.entryIndex ?? null}
                  documentSrc={uploadPreviewPath(detail)}
                  isExpanded={isEvidenceExpanded}
                  onExpandChange={setIsEvidenceExpanded}
                />
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Job Status</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 text-sm sm:grid-cols-4">
                <Status label="Job" value={detail.job.status} />
                <Status label="OCR" value={detail.job.ocrStatus} />
                <Status label="Page review" value={detail.job.verificationStatus} />
                <Status label="Entry extraction" value={detail.job.entryExtractionStatus} />
              </CardContent>
            </Card>

            {reviewMetrics && reviewMetrics.extractedEntryCount > 0 ? (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Review Metrics</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-3 text-sm sm:grid-cols-3">
                  <Status
                    label="Verified"
                    value={`${reviewMetrics.verifiedEntryCount}/${reviewMetrics.extractedEntryCount}`}
                  />
                  <Status
                    label="Verification rate"
                    value={`${Math.round(reviewMetrics.verificationRate * 100)}%`}
                  />
                  <Status
                    label="Median review"
                    value={
                      reviewMetrics.medianReviewSeconds === null
                        ? "not measured"
                        : `${reviewMetrics.medianReviewSeconds.toFixed(1)} sec`
                    }
                  />
                  <Status
                    label="Mean edits"
                    value={
                      reviewMetrics.meanEditedFieldCount === null
                        ? "not measured"
                        : reviewMetrics.meanEditedFieldCount.toFixed(1)
                    }
                  />
                  <Status
                    label="Accepted-field accuracy"
                    value={
                      reviewMetrics.acceptedFieldAccuracy === null
                        ? "not measured"
                        : `${Math.round(reviewMetrics.acceptedFieldAccuracy * 100)}%`
                    }
                  />
                  <Status
                    label="Unresolved/null"
                    value={`${reviewMetrics.unresolvedFieldCount}/${reviewMetrics.nullFieldCount}`}
                  />
                </CardContent>
              </Card>
            ) : null}

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Pages</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-4" onSubmit={handleVerifyPages}>
                  {detail.pages.length ? (
                    detail.pages.map((page) => (
                      <div key={page.id} className="rounded-md border p-4">
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                          <div className="flex items-center gap-2">
                            <FileText className="h-5 w-5 text-muted-foreground" />
                            <div>
                              <p className="font-medium">{page.pageLabel ?? `Page ${page.sourcePageNumber}`}</p>
                              <p className="text-xs text-muted-foreground">
                                Source page {page.sourcePageNumber} · order {page.currentPageOrder}
                              </p>
                            </div>
                          </div>
                          <Input
                            className="w-28"
                            type="number"
                            min={1}
                            value={page.currentPageOrder}
                            onChange={(event) => {
                              const nextOrder = Number(event.target.value);
                              setDetail((current) =>
                                current
                                  ? {
                                      ...current,
                                      pages: current.pages.map((item) =>
                                        item.id === page.id ? { ...item, currentPageOrder: nextOrder } : item,
                                      ),
                                    }
                                  : current,
                              );
                            }}
                          />
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">Run the local OCR worker to extract page placeholders.</p>
                  )}
                  <div className="space-y-2">
                    <Label htmlFor="verification-notes">Missing or uncertain pages</Label>
                    <Textarea id="verification-notes" value={notes} onChange={(event) => setNotes(event.target.value)} />
                  </div>
                  <Button type="submit" disabled={isSaving || detail.pages.length === 0}>
                    Confirm Order And Completeness
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Structured Entry Extraction</CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm text-muted-foreground">
                    Creates review candidates with OCR evidence links after page verification.
                  </p>
                  <Button type="button" onClick={handleExtractEntries} disabled={isSaving || detail.job.verificationStatus !== "verified"}>
                    <Wand2 className="mr-2 h-4 w-4" />
                    Extract Entries
                  </Button>
                </div>

                {extractedEntries.length ? (
                  <div className="space-y-4">
                    {extractedEntries.map((entry, index) => {
                      const draft = candidateEdits[entry.id] ?? {};
                      const isDirty = candidateIsDirty(entry, draft);
                      return (
                      <div key={entry.id} className={`rounded-md border p-4 ${isDirty ? "border-amber-300 bg-amber-50/40 dark:border-amber-900 dark:bg-amber-950/20" : ""}`}>
                        <div className="flex flex-col gap-2 border-b pb-3 sm:flex-row sm:items-start sm:justify-between">
                          <div>
                            <p className="text-sm font-semibold">Candidate {index + 1}</p>
                            <p className="text-xs text-muted-foreground">{entry.section} · {entry.reviewStatus.replaceAll("_", " ")}</p>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {isDirty ? (
                              <span className="inline-flex items-center gap-1 rounded-md border border-amber-300 bg-amber-50 px-2 py-1 text-xs text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-300">
                                Edited
                              </span>
                            ) : null}
                            {entry.reviewStatus === "needs_review" ? (
                              <span className="inline-flex items-center gap-1 rounded-md border border-amber-300 bg-amber-50 px-2 py-1 text-xs text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-300">
                                <AlertTriangle className="h-3.5 w-3.5" />
                                Review required
                              </span>
                            ) : null}
                          </div>
                        </div>

                        <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2 xl:grid-cols-4">
                          <CandidateTextField
                            id={`candidate-${entry.id}-date`}
                            label="Date"
                            type="date"
                            value={candidateDisplayValue(entry, draft, "entryDate")}
                            placeholder="Unknown"
                            isDirty={candidateFieldIsDirty(entry, draft, "entryDate")}
                            onValueChange={(value) => updateCandidateEdit(entry.id, "entryDate", value)}
                            disabled={isSaving}
                          />
                          <CandidateTextField
                            id={`candidate-${entry.id}-tach`}
                            label="Tach"
                            type="number"
                            value={candidateDisplayValue(entry, draft, "tachTime")}
                            placeholder="Needs review"
                            isDirty={candidateFieldIsDirty(entry, draft, "tachTime")}
                            onValueChange={(value) => updateCandidateEdit(entry.id, "tachTime", value)}
                            disabled={isSaving}
                          />
                          <CandidateTextField
                            id={`candidate-${entry.id}-hobbs`}
                            label="Hobbs"
                            type="number"
                            value={candidateDisplayValue(entry, draft, "hobbsTime")}
                            placeholder="Not recorded"
                            isDirty={candidateFieldIsDirty(entry, draft, "hobbsTime")}
                            onValueChange={(value) => updateCandidateEdit(entry.id, "hobbsTime", value)}
                            disabled={isSaving}
                          />
                          <CandidateTextField
                            id={`candidate-${entry.id}-total`}
                            label="Total"
                            type="number"
                            value={candidateDisplayValue(entry, draft, "totalTime")}
                            placeholder="Needs review"
                            isDirty={candidateFieldIsDirty(entry, draft, "totalTime")}
                            onValueChange={(value) => updateCandidateEdit(entry.id, "totalTime", value)}
                            disabled={isSaving}
                          />
                        </div>

                        <div className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
                          <CandidateTextField
                            id={`candidate-${entry.id}-performer`}
                            label="Performer or facility"
                            type="text"
                            value={candidateDisplayValue(entry, draft, "performerName")}
                            placeholder="Not extracted"
                            isDirty={candidateFieldIsDirty(entry, draft, "performerName")}
                            onValueChange={(value) => updateCandidateEdit(entry.id, "performerName", value)}
                            disabled={isSaving}
                          />
                          <CandidateTextField
                            id={`candidate-${entry.id}-credential`}
                            label="Certificate or work order"
                            type="text"
                            value={candidateDisplayValue(entry, draft, "performerCredential")}
                            placeholder="Not extracted"
                            isDirty={candidateFieldIsDirty(entry, draft, "performerCredential")}
                            onValueChange={(value) => updateCandidateEdit(entry.id, "performerCredential", value)}
                            disabled={isSaving}
                          />
                        </div>

                        <div className="mt-4 space-y-2">
                          <Label htmlFor={`candidate-${entry.id}-description`} className="text-xs font-medium text-muted-foreground">
                            Extracted text
                          </Label>
                          <Textarea
                            id={`candidate-${entry.id}-description`}
                            value={candidateDisplayValue(entry, draft, "description")}
                            onChange={(event) => updateCandidateEdit(entry.id, "description", event.target.value)}
                            className={`min-h-32 text-sm leading-6 ${candidateFieldIsDirty(entry, draft, "description") ? "border-amber-400 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-950/20" : ""}`}
                            disabled={isSaving}
                          />
                          <div className="flex flex-wrap justify-end gap-2">
                            <Button
                              type="button"
                              variant="outline"
                              onClick={() => handleCandidateSave(entry, "needs_review")}
                              disabled={isSaving || !isDirty}
                            >
                              Save for Review
                            </Button>
                            <Button
                              type="button"
                              onClick={() => handleCandidateSave(entry, "verified")}
                              disabled={
                                isSaving ||
                                !candidateDisplayValue(entry, draft, "entryDate").trim() ||
                                (!isDirty && entry.reviewStatus === "verified")
                              }
                              title={
                                candidateDisplayValue(entry, draft, "entryDate").trim()
                                  ? "Save this candidate as human verified"
                                  : "Enter a source-supported date before verification"
                              }
                            >
                              <CheckCircle2 className="mr-2 h-4 w-4" />
                              Verify Entry
                            </Button>
                          </div>
                        </div>

                        <div className="mt-4 space-y-2">
                          <p className="text-xs font-medium text-muted-foreground">Evidence regions</p>
                          <div className="space-y-2">
                            {entry.evidence.length ? (
                              entry.evidence.map((evidence) => (
                                <button
                                  key={evidence.id}
                                  type="button"
                                  onClick={() => setActiveEvidenceId(evidence.id)}
                                  className={`w-full rounded-md border p-3 text-left transition ${
                                    activeEvidence?.evidence.id === evidence.id
                                      ? "border-primary bg-primary/5 ring-1 ring-primary"
                                      : "hover:border-primary/60 hover:bg-muted/40"
                                  }`}
                                >
                                  <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                                    <p className="text-sm font-medium">{evidenceLabel(evidence)}</p>
                                    {evidence.span ? (
                                      <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                                        <MapPinned className="h-3.5 w-3.5" />
                                        {formatBbox(evidence.span)}
                                      </span>
                                    ) : null}
                                  </div>
                                  {evidence.span ? (
                                    <p className="mt-2 text-sm text-muted-foreground">{effectiveText(evidence.span)}</p>
                                  ) : null}
                                </button>
                              ))
                            ) : (
                              <p className="text-sm text-muted-foreground">No evidence links available for this candidate.</p>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No structured candidates have been extracted yet.</p>
                )}
              </CardContent>
            </Card>

            <details className="rounded-md border bg-card p-4">
              <summary className="cursor-pointer text-sm font-semibold">Raw OCR correction queue</summary>
              <div className="mt-4 space-y-4">
                <p className="text-sm text-muted-foreground">
                  Use this only for raw OCR token fixes. Structured entry review should happen against the scanned evidence above.
                </p>
                {lowConfidenceSpans.length ? (
                  lowConfidenceSpans.map((span) => (
                    <div key={span.id} className="space-y-3 rounded-md border p-4">
                      <div>
                        <p className="text-sm font-medium">{effectiveText(span)}</p>
                        <p className="text-xs text-muted-foreground">
                          Confidence {span.confidence ?? "unknown"} / 100 · bbox {span.bboxUnits}
                        </p>
                      </div>
                      <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
                        <Input
                          value={corrections[span.id] ?? ""}
                          onChange={(event) => setCorrections((current) => ({ ...current, [span.id]: event.target.value }))}
                          placeholder="Corrected OCR text"
                        />
                        <Button type="button" variant="outline" onClick={() => handleCorrection(span)} disabled={isSaving}>
                          Save Correction
                        </Button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No low-confidence spans are available yet.</p>
                )}
              </div>
            </details>
          </div>
        </div>
      )}
    </div>
  );
}

function EvidenceOverlay({
  page,
  evidence,
  region,
  entryIndex,
  documentSrc,
  isExpanded,
  onExpandChange,
}: {
  page: IngestionJobDetailResponse["pages"][number] | null;
  evidence: LogbookEntryEvidence | null;
  region: CandidateRegion | null;
  entryIndex: number | null;
  documentSrc: string;
  isExpanded: boolean;
  onExpandChange: (expanded: boolean) => void;
}) {
  const span = evidence?.span ?? null;
  const canDraw = hasDrawableRegion(span);
  const drawableRegion = canDraw
    ? {
        left: span!.bboxLeft!,
        top: span!.bboxTop!,
        width: span!.bboxWidth!,
        height: span!.bboxHeight!,
        label: effectiveText(span!),
      }
    : region
      ? {
          left: region.bboxLeft,
          top: region.bboxTop,
          width: region.bboxWidth,
          height: region.bboxHeight,
          label: "Candidate region",
        }
      : null;
  const width = page?.widthPx && page.widthPx > 0 ? page.widthPx : 100;
  const height = page?.heightPx && page.heightPx > 0 ? page.heightPx : 100;
  const aspectRatio = `${width} / ${height}`;
  const pageNumber = page?.sourcePageNumber ?? 1;
  const pageImageSrc = page?.imageDownloadUrl ? backendProxyPath(page.imageDownloadUrl) : null;
  const pdfUnderlaySrc = `${documentSrc}#page=${pageNumber}&toolbar=0&navpanes=0&scrollbar=0&view=Fit`;
  const imageRatio = width / height;
  const compactHeight = 320;
  const compactWidth = Math.max(760, Math.round(compactHeight * imageRatio));

  function renderOverlayContent(expanded: boolean) {
    return (
      <>
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold">Evidence highlight</p>
          <p className="text-xs text-muted-foreground">
            {evidence
              ? `Candidate ${entryIndex !== null ? entryIndex + 1 : ""} ${evidenceLabel(evidence)}`
              : "Select an evidence row to locate it on the page."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {page ? <p className="text-xs text-muted-foreground">{page.pageLabel ?? `Page ${page.sourcePageNumber}`}</p> : null}
          <Button type="button" size={expanded ? "default" : "sm"} variant="outline" onClick={() => onExpandChange(!expanded)}>
            {expanded ? <X className="mr-2 h-4 w-4" /> : <Maximize2 className="mr-2 h-4 w-4" />}
            {expanded ? "Close" : "Expand"}
          </Button>
        </div>
      </div>

      <div className={`mx-auto w-full ${expanded ? "max-w-[min(92vw,1180px)]" : "max-w-[760px]"}`}>
        <div className={`overflow-auto rounded-md border bg-muted/40 ${expanded ? "max-h-[74vh]" : "max-h-[360px]"}`}>
          <div
            className="relative"
            style={
              expanded
                ? { aspectRatio, height: "70vh", minWidth: "100%", width: `calc(70vh * ${imageRatio})` }
                : { height: compactHeight, minWidth: "100%", width: compactWidth }
            }
          >
            {pageImageSrc ? (
              <img
                alt={`Evidence page ${pageNumber} underlay`}
                src={pageImageSrc}
                className="absolute inset-0 h-full w-full object-fill"
              />
            ) : (
              <iframe
                title={`Evidence page ${pageNumber} underlay`}
                src={pdfUnderlaySrc}
                className="absolute inset-0 h-full w-full bg-background"
                tabIndex={-1}
              />
            )}
            <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(14,165,233,0.16)_1px,transparent_1px),linear-gradient(to_bottom,rgba(14,165,233,0.16)_1px,transparent_1px)] bg-[size:10%_10%]" />
            {drawableRegion ? (
              <div
                className="pointer-events-none absolute rounded-sm border-2 border-amber-500 bg-amber-300/30 shadow-[0_0_0_9999px_rgba(15,23,42,0.18)]"
                style={{
                  left: `${drawableRegion.left * 100}%`,
                  top: `${drawableRegion.top * 100}%`,
                  width: `${drawableRegion.width * 100}%`,
                  height: `${drawableRegion.height * 100}%`,
                }}
              />
            ) : null}
          </div>
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        {drawableRegion
          ? drawableRegion.label
          : "No drawable bounding box is available for this evidence item yet."}
      </p>
      </>
    );
  }

  return (
    <>
      <div className="mt-4 space-y-3 rounded-md border bg-background p-4">{renderOverlayContent(false)}</div>
      {isExpanded ? (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-background/95 p-4 backdrop-blur-sm sm:p-8">
          <div className="mx-auto max-w-7xl space-y-4 rounded-md border bg-background p-4 shadow-lg sm:p-6">{renderOverlayContent(true)}</div>
        </div>
      ) : null}
    </>
  );
}

function CandidateTextField({
  id,
  label,
  type,
  value,
  placeholder,
  isDirty,
  onValueChange,
  disabled,
}: {
  id: string;
  label: string;
  type: "date" | "number" | "text";
  value: string;
  placeholder?: string;
  isDirty: boolean;
  onValueChange: (value: string) => void;
  disabled: boolean;
}) {
  return (
    <div className={`rounded-md border p-3 ${isDirty ? "border-amber-400 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-950/20" : ""}`}>
      <Label htmlFor={id} className="text-xs text-muted-foreground">
        {label}
      </Label>
      <Input
        id={id}
        type={type}
        min={type === "number" ? 0 : undefined}
        step={type === "number" ? "any" : undefined}
        inputMode={type === "number" ? "decimal" : undefined}
        value={value}
        onChange={(event) => onValueChange(event.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="mt-2"
      />
      {type === "number" ? (
        <p className="mt-2 text-xs text-muted-foreground">
          Blank saves as not recorded. Enter 0 only if the log actually records zero.
        </p>
      ) : null}
      {type === "date" ? <p className="mt-2 text-xs text-muted-foreground">Blank saves as unknown until review.</p> : null}
    </div>
  );
}

function Status({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-medium">{value.replaceAll("_", " ")}</p>
    </div>
  );
}
