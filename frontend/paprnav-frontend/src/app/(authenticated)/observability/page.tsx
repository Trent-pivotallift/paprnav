"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { Activity, MessageSquare, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/PageHeader";
import {
  createFeedback,
  listObservability,
  ObservabilityListResponse,
  updateFeedbackStatus,
} from "@/lib/api";

export default function ObservabilityPage() {
  const [data, setData] = useState<ObservabilityListResponse>({ events: [], workflowEvents: [], feedback: [] });
  const [filters, setFilters] = useState({ aircraftId: "", eventType: "", subjectType: "", status: "" });
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [feedbackSubject, setFeedbackSubject] = useState("demo");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value.trim()));
      const response = await listObservability(params);
      setData(response);
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load product observability.");
    }
  }, [filters]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadData();
    }, 0);
    return () => window.clearTimeout(timeoutId);
  }, [loadData]);

  async function handleFeedback(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    try {
      await createFeedback({
        subjectType: feedbackSubject,
        feedbackType: "demo_note",
        message: feedbackMessage,
        severity: "medium",
      });
      setFeedbackMessage("");
      setMessage("Feedback captured.");
      await loadData();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create feedback.");
    }
  }

  async function triageFeedback(feedbackId: string, status: string) {
    await updateFeedbackStatus(feedbackId, status);
    await loadData();
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <PageHeader title="Product Observability" description="Recent product events, workflow state, and demo/support feedback" />

      {error ? <p className="mt-6 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
      {message ? <p className="mt-6 rounded-md border p-3 text-sm">{message}</p> : null}

      <Card className="mt-8">
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-5">
          <Input placeholder="Aircraft ID" value={filters.aircraftId} onChange={(event) => setFilters((current) => ({ ...current, aircraftId: event.target.value }))} />
          <Input placeholder="Event type" value={filters.eventType} onChange={(event) => setFilters((current) => ({ ...current, eventType: event.target.value }))} />
          <Input placeholder="Subject type" value={filters.subjectType} onChange={(event) => setFilters((current) => ({ ...current, subjectType: event.target.value }))} />
          <Input placeholder="Status" value={filters.status} onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))} />
          <Button type="button" onClick={loadData}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </CardContent>
      </Card>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Activity className="h-5 w-5" />
              Workflow Timeline
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.workflowEvents.length ? data.workflowEvents.map((event) => (
              <div key={event.id} className="rounded-md border p-3 text-sm">
                <p className="font-medium">{event.workflowType} · {event.newStatus}</p>
                <p className="text-muted-foreground">{event.workflowId} · {new Date(event.createdAt).toLocaleString()}</p>
                {event.reason ? <p className="mt-1">{event.reason}</p> : null}
              </div>
            )) : <p className="text-sm text-muted-foreground">No workflow events yet.</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Product Events</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.events.length ? data.events.map((event) => (
              <div key={event.id} className="rounded-md border p-3 text-sm">
                <p className="font-medium">{event.eventType}</p>
                <p className="text-muted-foreground">{event.subjectType} {event.subjectId ?? ""} · {new Date(event.eventTime).toLocaleString()}</p>
                <pre className="mt-2 overflow-auto rounded bg-muted/40 p-2 text-xs">{JSON.stringify(event.properties, null, 2)}</pre>
              </div>
            )) : <p className="text-sm text-muted-foreground">No product events yet.</p>}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <MessageSquare className="h-5 w-5" />
            Feedback
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <form className="grid gap-3 md:grid-cols-[220px_1fr_auto]" onSubmit={handleFeedback}>
            <div className="space-y-2">
              <Label htmlFor="feedback-subject">Subject</Label>
              <Input id="feedback-subject" value={feedbackSubject} onChange={(event) => setFeedbackSubject(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="feedback-message">Message</Label>
              <Textarea id="feedback-message" value={feedbackMessage} onChange={(event) => setFeedbackMessage(event.target.value)} required />
            </div>
            <div className="flex items-end">
              <Button type="submit">Capture</Button>
            </div>
          </form>
          {data.feedback.length ? data.feedback.map((item) => (
            <div key={item.id} className="rounded-md border p-3 text-sm">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="font-medium">{item.feedbackType} · {item.severity}</p>
                  <p>{item.message}</p>
                  <p className="text-muted-foreground">{item.subjectType} {item.subjectId ?? ""}</p>
                </div>
                <div className="flex gap-2">
                  <Button type="button" size="sm" variant="outline" onClick={() => triageFeedback(item.id, "triaged")}>Triaged</Button>
                  <Button type="button" size="sm" variant="ghost" onClick={() => triageFeedback(item.id, "closed")}>Closed</Button>
                </div>
              </div>
            </div>
          )) : <p className="text-sm text-muted-foreground">No feedback yet.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
