"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/PageHeader";
import { Aircraft, getLogbookEntry, listAircraft, LogbookEntry, updateLogbookEntry } from "@/lib/api";

function normalizeNNumber(nNumber: string) {
  return nNumber.replace(/[-\s]/g, "").toUpperCase();
}

function toFormState(entry: LogbookEntry) {
  return {
    entryDate: entry.entryDate,
    description: entry.description,
    performerName: entry.performerName ?? "",
    performerCredential: entry.performerCredential ?? "",
    tachTime: entry.tachTime?.toString() ?? "",
    hobbsTime: entry.hobbsTime?.toString() ?? "",
    totalTime: entry.totalTime?.toString() ?? "",
  };
}

function optionalNumber(value: string) {
  return value.trim() ? Number(value) : null;
}

export default function LogbookEntryDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const nNumber = params.nNumber as string;
  const entryId = params.entryId as string;
  const logbookType = searchParams.get("logbook") || "airframe";
  const [aircraft, setAircraft] = useState<Aircraft | null>(null);
  const [entry, setEntry] = useState<LogbookEntry | null>(null);
  const [formState, setFormState] = useState({
    entryDate: "",
    description: "",
    performerName: "",
    performerCredential: "",
    tachTime: "",
    hobbsTime: "",
    totalTime: "",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormState((prev) => ({ ...prev, [name]: value }));
  };

  const loadEntry = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setSaveMessage(null);
    try {
      const aircraftResponse = await listAircraft();
      const selectedAircraft = aircraftResponse.aircraft.find(
        (item) => item.nNumberNormalized === normalizeNNumber(nNumber),
      );
      if (!selectedAircraft) {
        throw new Error("Aircraft not found.");
      }

      const logbookEntry = await getLogbookEntry(selectedAircraft.id, entryId);
      setAircraft(selectedAircraft);
      setEntry(logbookEntry);
      setFormState(toFormState(logbookEntry));
    } catch (caught) {
      setAircraft(null);
      setEntry(null);
      setError(caught instanceof Error ? caught.message : "Unable to load logbook entry.");
    } finally {
      setIsLoading(false);
    }
  }, [entryId, nNumber]);

  async function handleSave() {
    if (!aircraft || !entry) {
      return;
    }

    setIsSaving(true);
    setError(null);
    setSaveMessage(null);
    try {
      const updatedEntry = await updateLogbookEntry(aircraft.id, entry.id, {
        entryDate: formState.entryDate,
        description: formState.description,
        performerName: formState.performerName || null,
        performerCredential: formState.performerCredential || null,
        tachTime: optionalNumber(formState.tachTime),
        hobbsTime: optionalNumber(formState.hobbsTime),
        totalTime: optionalNumber(formState.totalTime),
      });
      setEntry(updatedEntry);
      setFormState(toFormState(updatedEntry));
      setSaveMessage("Changes saved.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save changes.");
    } finally {
      setIsSaving(false);
    }
  };

  useEffect(() => {
    void loadEntry();
  }, [loadEntry]);

  return (
    <div className="container mx-auto px-4 py-8">
      <PageHeader
        title={entry ? `Log Entry: ${entry.entryDate}` : "Log Entry"}
        description={
          aircraft ? `Editing ${aircraft.nNumber} ${logbookType} logbook entry` : `Editing entry #${entryId}`
        }
        backLinkHref={`/logbook/${nNumber}?logbook=${logbookType}`}
        backLinkLabel="Back to Logbook"
      />

      {isLoading ? (
        <Card className="mt-8 animate-pulse">
          <CardContent className="space-y-4 p-6">
            <div className="h-5 w-1/3 rounded bg-muted" />
            <div className="h-32 w-full rounded bg-muted" />
          </CardContent>
        </Card>
      ) : error && !entry ? (
        <Card className="mt-8">
          <CardContent className="flex flex-col items-center justify-center gap-4 py-12 text-center">
            <p className="text-sm text-destructive">{error}</p>
            <Button variant="outline" onClick={loadEntry}>
              Retry
            </Button>
          </CardContent>
        </Card>
      ) : (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
        {/* Scanned Logbook Page */}
        <Card>
          <CardHeader>
            <CardTitle>Original Scan</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg aspect-video bg-muted flex items-center justify-center p-4">
              <p className="text-muted-foreground text-center">
                (Placeholder: Image of scanned log page with <span className="bg-yellow-200/50 text-yellow-900 px-1 rounded-sm">highlighted text</span> matching editable fields)
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Digitized Data (Editable) */}
        <Card>
          <CardHeader>
            <CardTitle>Digitized Data (Editable)</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="entryDate">Date</Label>
                <Input
                  type="date"
                  id="entryDate"
                  name="entryDate"
                  value={formState.entryDate}
                  onChange={handleChange}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  name="description"
                  rows={6}
                  value={formState.description}
                  onChange={handleChange}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="performerName">Performer</Label>
                <Input
                  type="text"
                  id="performerName"
                  name="performerName"
                  value={formState.performerName}
                  onChange={handleChange}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="performerCredential">Certificate / Credential</Label>
                <Input
                  type="text"
                  id="performerCredential"
                  name="performerCredential"
                  value={formState.performerCredential}
                  onChange={handleChange}
                />
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="tachTime">Tach</Label>
                  <Input
                    type="number"
                    id="tachTime"
                    name="tachTime"
                    min="0"
                    step="0.1"
                    value={formState.tachTime}
                    onChange={handleChange}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="hobbsTime">Hobbs</Label>
                  <Input
                    type="number"
                    id="hobbsTime"
                    name="hobbsTime"
                    min="0"
                    step="0.1"
                    value={formState.hobbsTime}
                    onChange={handleChange}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="totalTime">Total</Label>
                  <Input
                    type="number"
                    id="totalTime"
                    name="totalTime"
                    min="0"
                    step="0.1"
                    value={formState.totalTime}
                    onChange={handleChange}
                  />
                </div>
              </div>

              {error ? <p className="text-sm text-destructive">{error}</p> : null}
              {saveMessage ? <p className="text-sm text-muted-foreground">{saveMessage}</p> : null}

              <div className="flex justify-end space-x-3">
                <Button variant="outline" type="button" onClick={loadEntry}>
                  Cancel
                </Button>
                <Button type="button" onClick={handleSave} disabled={isSaving}>
                  {isSaving ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
      )}
    </div>
  );
}
