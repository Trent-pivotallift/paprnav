"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { AlertTriangle, ArrowLeft, CheckCircle2, ExternalLink, FileWarning, RefreshCw, ShieldAlert, XCircle } from "lucide-react";
import { useAuth } from "@/components/AuthProvider";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { ADExtractionReview, adSourceDocumentContentUrl, decideAdExtractionReview, listAdExtractionReviews } from "@/lib/api";

function prettyJson(value: Record<string, unknown>) { return JSON.stringify(value, null, 2); }

export default function ADExtractionReviewsPage() {
  const { user } = useAuth();
  const isAdmin = user?.memberships.some((membership) => membership.role === "platform_admin") ?? false;
  const [reviews, setReviews] = useState<ADExtractionReview[]>([]);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [progress, setProgress] = useState({ total: 0, pending: 0, reviewed: 0, verified: 0, quarantined: 0, approvalReady: 0 });
  const [reviewOffset, setReviewOffset] = useState(0);
  const [targetReviewId, setTargetReviewId] = useState<string | null>(null);
  const [queryReady, setQueryReady] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setTargetReviewId(new URLSearchParams(window.location.search).get("reviewId"));
    setQueryReady(true);
  }, []);

  const loadReviews = useCallback(async () => {
    if (!isAdmin || !queryReady) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await listAdExtractionReviews(reviewOffset, 1, targetReviewId);
      setReviews(response.reviews);
      setReviewOffset(response.currentOffset);
      setProgress({ total: response.totalCount, pending: response.pendingCount, reviewed: response.reviewedCount, verified: response.verifiedCount, quarantined: response.quarantinedCount, approvalReady: response.approvalReadyCount });
      setDrafts(response.reviews.reduce<Record<string, string>>((current, review) => {
        current[review.id] = prettyJson(review.decisionOutput ?? review.proposedOutput);
        return current;
      }, {}));
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Unable to load AD extraction reviews."); }
    finally { setIsLoading(false); }
  }, [isAdmin, queryReady, reviewOffset, targetReviewId]);

  useEffect(() => { void loadReviews(); }, [loadReviews]);

  async function submitDecision(review: ADExtractionReview, decision: "approved" | "edited" | "rejected") {
    setIsSaving(true); setError(null); setMessage(null);
    try {
      const output = decision === "rejected" ? undefined : JSON.parse(drafts[review.id] || prettyJson(review.proposedOutput)) as Record<string, unknown>;
      const response = await decideAdExtractionReview(review.id, { decision, output, notes: notes[review.id] || null });
      setMessage(`Review ${response.review.status}.`);
      await loadReviews();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Unable to save AD review decision."); }
    finally { setIsSaving(false); }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); }

  function moveToReview(offset: number) {
    setTargetReviewId(null);
    window.history.replaceState({}, "", "/logbook/ads/reviews");
    setReviewOffset(offset);
  }

  if (!isAdmin) {
    return <div className="container mx-auto px-4 py-8"><PageHeader title="Admin extraction review" description="Downloaded source and machine extraction review is restricted to Paprnav administrators." /><Card className="mt-6"><CardContent className="py-10 text-center"><ShieldAlert className="mx-auto h-8 w-8 text-muted-foreground" /><p className="mt-3 font-medium">Administrator access required</p><p className="mt-1 text-sm text-muted-foreground">Maintenance shops use the released AD catalog and aircraft-specific compliance views.</p><Button asChild className="mt-4"><Link href="/logbook/ads">Return to AD research</Link></Button></CardContent></Card></div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <Button asChild variant="ghost" className="mb-3 -ml-3"><Link href="/logbook/ads"><ArrowLeft className="mr-2 h-4 w-4" />AD currency & research</Link></Button>
      <PageHeader title="Admin extraction review" description={isLoading ? "Loading and re-verifying the selected review's retained source…" : `${progress.verified} source-indexed out of ${progress.total} · ${progress.approvalReady} approval candidates · ${progress.quarantined} source-quarantined · ${progress.pending} decisions pending`} />
      <p className="mt-2 max-w-3xl text-sm text-muted-foreground">Compare the bounded official source section with the proposed structure. Queue totals use cached provenance for triage; opening a record re-verifies its exact PDF bytes and extracted text. Missing or identity-unverified evidence is quarantined and cannot be approved.</p>

      <div className="mt-4 flex items-center justify-between gap-3">
        <Button type="button" variant="outline" onClick={() => moveToReview(Math.max(0, reviewOffset - 1))} disabled={reviewOffset === 0 || isSaving}>Previous review</Button>
        <span className="text-sm text-muted-foreground">{progress.total ? reviewOffset + 1 : 0} of {progress.total}</span>
        <Button type="button" variant="outline" onClick={() => moveToReview(Math.min(progress.total - 1, reviewOffset + 1))} disabled={reviewOffset >= progress.total - 1 || isSaving}>Next review</Button>
      </div>

      {error ? <p className="mt-6 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
      {message ? <p className="mt-6 flex items-center gap-2 rounded-md border bg-card p-3 text-sm text-green-700 dark:text-green-400"><CheckCircle2 className="h-4 w-4" />{message}</p> : null}

      <div className="mt-8 space-y-6">
        {reviews.map((review) => (
          <Card key={review.id}>
            <CardHeader>
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <CardTitle className="text-lg">AD {review.directive.officialAdNumber ?? "Unnumbered"} · {review.directive.title}</CardTitle>
                  <p className="mt-1 text-sm text-muted-foreground">{review.directive.adNumber !== review.directive.officialAdNumber ? `Normalized ID ${review.directive.adNumber} · ` : ""}confidence {(review.extraction.confidence * 100).toFixed(0)}% · {review.status}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{review.requirementCount} requirements · {review.unresolvedRequirementCount} unresolved · {review.sourcePages.length} bounded source pages</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {review.directive.htmlUrl ? <Button asChild size="sm" variant="outline"><a href={review.directive.htmlUrl} target="_blank" rel="noreferrer"><ExternalLink className="mr-2 h-4 w-4" />Publisher HTML</a></Button> : null}
                  {review.sourceDocuments.map((source) => <Button asChild key={source.id} size="sm" variant="outline"><a href={adSourceDocumentContentUrl(source.id, source.relevantPageStart)} target="_blank" rel="noreferrer"><FileWarning className="mr-2 h-4 w-4" />PDF {source.sourceIdentifier}{source.relevantPageStart ? ` · ${source.relevantPagesContiguous ? `p. ${source.relevantPageStart}${source.relevantPageEnd !== source.relevantPageStart ? `–${source.relevantPageEnd}` : ""}` : `pp. ${source.relevantPageNumbers.join(", ")}`}` : ""}</a></Button>)}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {review.proposalProvenance ? <div className="mb-4 rounded-md border border-blue-600/30 bg-blue-600/10 p-3 text-sm text-blue-900 dark:text-blue-200"><p className="font-medium">Administrator-staged calibration draft</p><p>This is not raw model output. It was staged in {review.proposalProvenance.stagingMode.replaceAll("_", " ")} mode by administrator {review.proposalProvenance.actorUserId ?? "unknown"} at {new Date(review.proposalProvenance.stagedAt).toLocaleString()} (audit decision {review.proposalProvenance.stagingDecisionId}). Review every field against the retained source before publishing.</p></div> : null}
              <div className={`mb-4 flex gap-3 rounded-md border p-3 text-sm ${review.canApprove ? "border-green-600/30 bg-green-600/10 text-green-800 dark:text-green-300" : "border-amber-600/30 bg-amber-600/10 text-amber-900 dark:text-amber-200"}`}>
                {review.canApprove ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" /> : <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />}<div><p className="font-medium">{review.canApprove ? "Ready for admin decision" : review.evidenceStatus === "verified" ? "Extraction incomplete — approval blocked" : "Source evidence quarantined — approval blocked"}</p>{review.approvalBlockers.length ? <ul className="mt-1 list-disc space-y-1 pl-5">{review.approvalBlockers.map((blocker) => <li key={blocker}>{blocker}</li>)}</ul> : <p>{review.evidenceMessage}</p>}</div>
              </div>
              <form className="space-y-4" onSubmit={handleSubmit}>
                <div className="rounded-md border bg-muted/20 p-3 text-sm">
                  <p className="font-medium">Source attribution</p>
                  {review.sourceDocuments.length ? <div className="mt-2 space-y-2">{review.sourceDocuments.map((source) => <div key={source.id}><p>{source.sourceSystem.replaceAll("_", " ")} · {source.sourceType.replaceAll("_", " ")} · {source.sourceIdentifier}</p><p className="text-xs text-muted-foreground">Retained {new Date(source.capturedAt).toLocaleString()} · SHA-256 {source.contentHash.slice(0, 16)}… · {(source.storageBytes / 1024 / 1024).toFixed(1)} MB{source.parserName ? ` · ${source.parserName} ${source.parserVersion ?? ""}` : ""}</p></div>)}</div> : <p className="mt-1 text-muted-foreground">No retained evidence document is attributable to this extraction.</p>}
                </div>
                <details className="rounded-md border p-3 text-sm">
                  <summary className="cursor-pointer font-medium">How to complete the structured JSON</summary>
                  <div className="mt-2 space-y-2 text-muted-foreground">
                    <p><code>applicabilityGroups</code> is the authoritative applicability structure. Keep the official manufacturer in <code>sourceName</code> and each model in a separate <code>sourceDesignation</code>. Never combine manufacturer and model in one string or list them as unrelated sibling values.</p>
                    <p>Use <code>normalizedName</code> and <code>normalizedDesignation</code> only for a conservative canonical identity; otherwise use <code>null</code>. Preserve serial scope, installed-equipment conditions, exceptions, and a page citation in the group.</p>
                    <p>Every safety-relevant value must be visible verbatim in its cited excerpt: manufacturer, model, serial values and range endpoints, equipment or applicability conditions, compliance action, timing, terminating action, and AMOC authority or submission instructions. Do not infer or paraphrase a value that the retained page does not state.</p>
                    <p><code>requirements</code> is a JSON list. Add one object for each independently testable one-time, recurring, conditional, or alternative obligation.</p>
                    <p>Put the source-faithful instruction—not a paraphrase—in each requirement&apos;s <code>actionText</code>. List the exact <code>applicabilityGroupKeys</code> it governs. The server derives <code>affectedProducts</code> and <code>complianceActions</code>; do not use those compatibility summaries as source data.</p>
                    <p>Every requirement needs at least one citation using the exact retained <code>sourceDocumentId</code>, one-based <code>pageNumber</code>, and a supporting excerpt displayed on the left.</p>
                    <p>Each threshold or trigger must repeat its exact timing clause in <code>sourceText</code>. Preserve <code>anchorKind</code>: effective date, last compliance, installation, or manufacture are not interchangeable.</p>
                    <p>Choose <code>combinationLogic</code> from the rule text: <code>whichever_first</code> uses the earliest limit, <code>whichever_later</code> uses the latest limit, and <code>alternative</code> remains blocked for explicit adjudication instead of being flattened to <code>all</code>.</p>
                    <p>Use <code>amocProvisions</code> for the AD&apos;s alternative-method-of-compliance paragraph and approving authority. Do not encode that paragraph as an <code>alternative</code> compliance requirement.</p>
                    <p>Keep each independently due obligation as a separate requirement object even when two obligations apply to the same applicability group. The matcher calculates and retains one due state per requirement.</p>
                    <pre className="overflow-x-auto rounded bg-background p-3 text-xs text-foreground">{`"applicabilityGroups": [{
  "groupKey": "paragraph-c-cessna-150a",
  "productType": "aircraft",
  "productSubtype": "small_airplane",
  "manufacturer": {
    "sourceName": "Cessna Aircraft Company",
    "normalizedName": "Textron Aviation Inc."
  },
  "modelApplicability": {
    "kind": "listed",
    "models": [{
      "sourceDesignation": "150A",
      "normalizedDesignation": "150A",
      "aliases": []
    }],
    "sourceText": "Model 150A airplanes"
  },
  "serialNumberApplicability": {
    "kind": "all", "values": [], "ranges": [],
    "excludedValues": [], "sourceText": "all serial numbers"
  },
  "equipmentCombinationLogic": "all",
  "equipmentConditions": [],
  "conditions": [],
  "citations": [{
    "sourceDocumentId": "copy from the page heading",
    "pageNumber": 1,
    "text": "copy the applicability source excerpt"
  }],
  "confidence": 0.9,
  "uncertaintyReasons": []
}],
"requirements": [
  {
    "requirementKey": "paragraph-g-inspection",
    "applicabilityGroupKeys": ["paragraph-c-cessna-150a"],
    "requirementType": "conditional",
    "actionText": "Copy the complete regulatory instruction from the cited source.",
    "initialThresholds": [],
    "recurringTriggers": [],
    "combinationLogic": "all",
    "conditions": ["Use the source's exact applicability condition."],
    "terminatingAction": null,
    "citations": [{
      "sourceDocumentId": "copy from the page heading",
      "pageNumber": 1,
      "text": "copy the supporting source excerpt"
    }],
    "confidence": 0.9,
    "uncertaintyReasons": []
  }
]`}</pre>
                  </div>
                </details>
                <div className="grid gap-4 lg:grid-cols-2">
                  <div className="space-y-2"><p className="text-sm font-medium">Bounded official source section</p><div className="max-h-[32rem] space-y-4 overflow-auto rounded-md border bg-muted/30 p-3 text-sm">{review.sourcePages.length ? review.sourcePages.map((page) => <section key={`${page.sourceDocumentId}-${page.pageNumber}`}><p className="mb-1 text-xs font-semibold text-muted-foreground">Page {page.pageNumber} · {page.sourceDocumentId}</p><p className="whitespace-pre-wrap">{page.text}</p></section>) : <p className="text-muted-foreground">No retained source section. The record is visible for remediation only and is not reviewable.</p>}</div></div>
                  <div className="space-y-2"><p className="text-sm font-medium">Proposed structured extraction</p><Textarea className="min-h-[32rem] font-mono text-xs" value={drafts[review.id] ?? ""} onChange={(event) => setDrafts((current) => ({ ...current, [review.id]: event.target.value }))} disabled={review.status !== "pending" || review.evidenceStatus !== "verified" || review.extraction.schemaVersion !== "ad_extraction_v3"} /></div>
                </div>
                <Textarea placeholder="Review notes or source-remediation reason" value={notes[review.id] ?? ""} onChange={(event) => setNotes((current) => ({ ...current, [review.id]: event.target.value }))} disabled={review.status !== "pending"} />
                <p className="text-xs text-muted-foreground">Approval records your identity, publishes the reviewed directive, materializes supported requirements, and replays affected aircraft compliance state.</p>
                <div className="flex flex-wrap gap-2"><Button type="button" onClick={() => submitDecision(review, "approved")} disabled={isSaving || !review.canApprove}><CheckCircle2 className="mr-2 h-4 w-4" />Approve &amp; publish</Button><Button type="button" variant="outline" onClick={() => submitDecision(review, "edited")} disabled={isSaving || review.status !== "pending" || review.evidenceStatus !== "verified" || review.extraction.schemaVersion !== "ad_extraction_v3"}><RefreshCw className="mr-2 h-4 w-4" />Edit, validate &amp; publish</Button><Button type="button" variant="destructive" onClick={() => submitDecision(review, "rejected")} disabled={isSaving || review.status !== "pending"}><XCircle className="mr-2 h-4 w-4" />Reject / send to remediation</Button></div>
              </form>
            </CardContent>
          </Card>
        ))}
        {isLoading && !reviews.length ? <Card><CardContent className="flex items-center justify-center gap-2 py-10 text-sm text-muted-foreground"><RefreshCw className="h-4 w-4 animate-spin" />Re-verifying retained PDF bytes and source text…</CardContent></Card> : null}
        {!isLoading && !reviews.length ? <Card><CardContent className="py-10 text-center text-sm text-muted-foreground">{targetReviewId ? `Review ${targetReviewId} was not found in the current queue.` : "No AD extraction reviews are queued."}</CardContent></Card> : null}
      </div>
    </div>
  );
}
