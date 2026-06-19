"use client";

import React, { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { CheckCircle2, ChevronLeft, FileText, Wand2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/PageHeader";
import {
  createOcrCorrection,
  extractLogbookEntries,
  getIngestionJob,
  IngestionJobDetailResponse,
  OCRTextSpan,
  verifyIngestionPages,
} from "@/lib/api";

function normalizeNNumber(nNumber: string) {
  return nNumber.replace(/[-\s]/g, "").toUpperCase();
}

function effectiveText(span: OCRTextSpan) {
  return span.corrections.at(-1)?.correctedText ?? span.text;
}

export default function IngestionReviewPage() {
  const params = useParams();
  const nNumber = normalizeNNumber(params.nNumber as string);
  const jobId = params.jobId as string;
  const [detail, setDetail] = useState<IngestionJobDetailResponse | null>(null);
  const [notes, setNotes] = useState("");
  const [corrections, setCorrections] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const lowConfidenceSpans = useMemo(
    () =>
      detail?.pages
        .flatMap((page) => page.spans)
        .filter((span) => (span.confidence ?? 100) < 80) ?? [],
    [detail],
  );

  const loadJob = useCallback(async () => {
    setError(null);
    try {
      const response = await getIngestionJob(jobId);
      setDetail(response);
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
        <div className="mt-8 space-y-6">
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
              <CardTitle className="text-lg">Low-Confidence OCR</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
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
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Structured Entry Extraction</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-muted-foreground">
                Creates logbook entries with OCR evidence links after page verification.
              </p>
              <Button type="button" onClick={handleExtractEntries} disabled={isSaving || detail.job.verificationStatus !== "verified"}>
                <Wand2 className="mr-2 h-4 w-4" />
                Extract Entries
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
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
