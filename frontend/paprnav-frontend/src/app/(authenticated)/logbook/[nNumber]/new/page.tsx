"use client";

import React, { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/PageHeader";
import { Aircraft, createLogbookEntry, listAircraft, LogbookSection } from "@/lib/api";

function normalizeNNumber(nNumber: string) {
  return nNumber.replace(/[-\s]/g, "").toUpperCase();
}

function getSection(value: string | null): LogbookSection {
  if (value === "engine" || value === "propeller") {
    return value;
  }
  return "airframe";
}

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

function optionalNumber(value: string) {
  return value.trim() ? Number(value) : null;
}

export default function NewLogbookEntryPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const nNumber = params.nNumber as string;
  const displayNNumber = normalizeNNumber(nNumber);
  const initialSection = getSection(searchParams.get("logbook"));

  const [aircraft, setAircraft] = useState<Aircraft | null>(null);
  const [section, setSection] = useState<LogbookSection>(initialSection);
  const [entryDate, setEntryDate] = useState(todayIsoDate());
  const [description, setDescription] = useState("");
  const [performerName, setPerformerName] = useState("");
  const [performerCredential, setPerformerCredential] = useState("");
  const [notes, setNotes] = useState("");
  const [tachTime, setTachTime] = useState("");
  const [hobbsTime, setHobbsTime] = useState("");
  const [totalTime, setTotalTime] = useState("");
  const [isLoadingAircraft, setIsLoadingAircraft] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAircraft = useCallback(async () => {
    setIsLoadingAircraft(true);
    setError(null);
    try {
      const aircraftResponse = await listAircraft();
      const selectedAircraft = aircraftResponse.aircraft.find(
        (item) => item.nNumberNormalized === displayNNumber,
      );
      if (!selectedAircraft) {
        throw new Error("Aircraft not found.");
      }
      setAircraft(selectedAircraft);
    } catch (caught) {
      setAircraft(null);
      setError(caught instanceof Error ? caught.message : "Unable to load aircraft.");
    } finally {
      setIsLoadingAircraft(false);
    }
  }, [displayNNumber]);

  useEffect(() => {
    void loadAircraft();
  }, [loadAircraft]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!aircraft) {
      setError("Aircraft is required before creating an entry.");
      return;
    }
    if (!entryDate) {
      setError("Entry date is required.");
      return;
    }
    if (!description.trim()) {
      setError("Description is required.");
      return;
    }

    setIsSubmitting(true);
    try {
      const combinedDescription = notes.trim()
        ? `${description.trim()}\n\nNotes: ${notes.trim()}`
        : description.trim();
      const entry = await createLogbookEntry(aircraft.id, {
        section,
        entryDate,
        description: combinedDescription,
        performerName: performerName.trim() || null,
        performerCredential: performerCredential.trim() || null,
        tachTime: optionalNumber(tachTime),
        hobbsTime: optionalNumber(hobbsTime),
        totalTime: optionalNumber(totalTime),
      });
      router.push(`/logbook/${displayNNumber}/entry/${entry.id}?logbook=${entry.section}`);
      router.refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create logbook entry.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="container mx-auto max-w-3xl px-4 py-8">
      <PageHeader
        title="Add Manual Entry"
        description={
          aircraft
            ? `${aircraft.nNumber} ${aircraft.make} ${aircraft.model}`
            : `Aircraft ${displayNNumber}`
        }
        backLinkHref={`/logbook/${displayNNumber}?logbook=${section}`}
        backLinkLabel="Back to Logbook"
      />

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Entry Details</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoadingAircraft ? (
            <div className="space-y-4">
              <div className="h-5 w-1/3 animate-pulse rounded bg-muted" />
              <div className="h-32 w-full animate-pulse rounded bg-muted" />
            </div>
          ) : (
            <form className="space-y-5" onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="entryDate">Date</Label>
                  <Input
                    id="entryDate"
                    name="entryDate"
                    type="date"
                    required
                    value={entryDate}
                    onChange={(event) => setEntryDate(event.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="section">Section</Label>
                  <select
                    id="section"
                    name="section"
                    value={section}
                    onChange={(event) => setSection(getSection(event.target.value))}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  >
                    <option value="airframe">Airframe</option>
                    <option value="engine">Engine</option>
                    <option value="propeller">Propeller</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  name="description"
                  required
                  rows={5}
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                />
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="performerName">Performer</Label>
                  <Input
                    id="performerName"
                    name="performerName"
                    value={performerName}
                    onChange={(event) => setPerformerName(event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="performerCredential">Certificate / Credential</Label>
                  <Input
                    id="performerCredential"
                    name="performerCredential"
                    value={performerCredential}
                    onChange={(event) => setPerformerCredential(event.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  name="notes"
                  rows={3}
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                />
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="tachTime">Tach</Label>
                  <Input
                    id="tachTime"
                    name="tachTime"
                    type="number"
                    min="0"
                    step="0.1"
                    value={tachTime}
                    onChange={(event) => setTachTime(event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="hobbsTime">Hobbs</Label>
                  <Input
                    id="hobbsTime"
                    name="hobbsTime"
                    type="number"
                    min="0"
                    step="0.1"
                    value={hobbsTime}
                    onChange={(event) => setHobbsTime(event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="totalTime">Total</Label>
                  <Input
                    id="totalTime"
                    name="totalTime"
                    type="number"
                    min="0"
                    step="0.1"
                    value={totalTime}
                    onChange={(event) => setTotalTime(event.target.value)}
                  />
                </div>
              </div>

              {error ? <p className="text-sm text-destructive">{error}</p> : null}

              <div className="flex justify-end gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.push(`/logbook/${displayNNumber}?logbook=${section}`)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmitting || !aircraft}>
                  <Save className="mr-2 h-4 w-4" />
                  {isSubmitting ? "Saving..." : "Save Entry"}
                </Button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
