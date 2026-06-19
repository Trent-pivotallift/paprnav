"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { CheckCircle2, ExternalLink, FileWarning, RefreshCw, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/PageHeader";
import {
  ADExtractionReview,
  decideAdExtractionReview,
  listAdExtractionReviews,
} from "@/lib/api";

function prettyJson(value: Record<string, unknown>) {
  return JSON.stringify(value, null, 2);
}

export default function AirworthinessDirectivesPage() {
  const [reviews, setReviews] = useState<ADExtractionReview[]>([]);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const pendingCount = useMemo(() => reviews.filter((review) => review.status === "pending").length, [reviews]);

  const loadReviews = useCallback(async () => {
    setError(null);
    try {
      const response = await listAdExtractionReviews();
      setReviews(response.reviews);
      setDrafts(
        response.reviews.reduce<Record<string, string>>((current, review) => {
          current[review.id] = prettyJson(review.decisionOutput ?? review.proposedOutput);
          return current;
        }, {}),
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load AD extraction reviews.");
    }
  }, []);

  useEffect(() => {
    void loadReviews();
  }, [loadReviews]);

  async function submitDecision(review: ADExtractionReview, decision: "approved" | "edited" | "rejected") {
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      let output: Record<string, unknown> | undefined;
      if (decision !== "rejected") {
        output = JSON.parse(drafts[review.id] || prettyJson(review.proposedOutput)) as Record<string, unknown>;
      }
      const response = await decideAdExtractionReview(review.id, {
        decision,
        output,
        notes: notes[review.id] || null,
      });
      setMessage(`Review ${response.review.status}.`);
      await loadReviews();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save AD review decision.");
    } finally {
      setIsSaving(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <PageHeader title="Airworthiness Directives" description={`${pendingCount} AD extraction review${pendingCount === 1 ? "" : "s"} pending`} />

      {error ? <p className="mt-6 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
      {message ? (
        <p className="mt-6 flex items-center gap-2 rounded-md border bg-card p-3 text-sm text-green-700 dark:text-green-400">
          <CheckCircle2 className="h-4 w-4" />
          {message}
        </p>
      ) : null}

      <div className="mt-8 space-y-6">
        {reviews.length ? (
          reviews.map((review) => (
            <Card key={review.id}>
              <CardHeader>
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <CardTitle className="text-lg">{review.directive.title}</CardTitle>
                    <p className="mt-1 text-sm text-muted-foreground">
                      FR {review.directive.federalRegisterDocumentNumber} · confidence {(review.extraction.confidence * 100).toFixed(0)}% · {review.status}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    {review.directive.htmlUrl ? (
                      <Button asChild size="sm" variant="outline">
                        <a href={review.directive.htmlUrl} target="_blank" rel="noreferrer">
                          <ExternalLink className="mr-2 h-4 w-4" />
                          HTML
                        </a>
                      </Button>
                    ) : null}
                    {review.directive.pdfUrl ? (
                      <Button asChild size="sm" variant="outline">
                        <a href={review.directive.pdfUrl} target="_blank" rel="noreferrer">
                          <FileWarning className="mr-2 h-4 w-4" />
                          PDF
                        </a>
                      </Button>
                    ) : null}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <form className="space-y-4" onSubmit={handleSubmit}>
                  <div className="grid gap-4 lg:grid-cols-2">
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Source Text</p>
                      <div className="max-h-80 overflow-auto rounded-md border bg-muted/30 p-3 text-sm whitespace-pre-wrap">
                        {review.sourceText || "No source text retained."}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Structured Extraction</p>
                      <Textarea
                        className="min-h-80 font-mono text-xs"
                        value={drafts[review.id] ?? ""}
                        onChange={(event) => setDrafts((current) => ({ ...current, [review.id]: event.target.value }))}
                        disabled={review.status !== "pending"}
                      />
                    </div>
                  </div>
                  <Textarea
                    placeholder="Review notes"
                    value={notes[review.id] ?? ""}
                    onChange={(event) => setNotes((current) => ({ ...current, [review.id]: event.target.value }))}
                    disabled={review.status !== "pending"}
                  />
                  <div className="flex flex-wrap gap-2">
                    <Button type="button" onClick={() => submitDecision(review, "approved")} disabled={isSaving || review.status !== "pending"}>
                      <CheckCircle2 className="mr-2 h-4 w-4" />
                      Approve
                    </Button>
                    <Button type="button" variant="outline" onClick={() => submitDecision(review, "edited")} disabled={isSaving || review.status !== "pending"}>
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Save Edit
                    </Button>
                    <Button type="button" variant="destructive" onClick={() => submitDecision(review, "rejected")} disabled={isSaving || review.status !== "pending"}>
                      <XCircle className="mr-2 h-4 w-4" />
                      Reject
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          ))
        ) : (
          <Card>
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              No AD extraction reviews are queued.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
