"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { CheckCircle, ChevronLeft, FileText, Plane, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/PageHeader";
import {
  Aircraft,
  AircraftCreateRequest,
  createAircraft,
  IngestionJobSummary,
  LogbookSection,
  uploadLogbookFile,
  Upload as StoredUpload,
} from "@/lib/api";

const SECTION_OPTIONS: Array<{ value: LogbookSection; label: string }> = [
  { value: "airframe", label: "Airframe" },
  { value: "engine", label: "Engine" },
  { value: "propeller", label: "Propeller" },
];

const FIELD_LABELS: Array<{ key: keyof AircraftCreateRequest; label: string; required?: boolean; type?: string }> = [
  { key: "nNumber", label: "N-number", required: true },
  { key: "make", label: "Aircraft make", required: true },
  { key: "model", label: "Aircraft model", required: true },
  { key: "serialNumber", label: "Aircraft serial number" },
  { key: "year", label: "Year", type: "number" },
  { key: "engineMake", label: "Engine make" },
  { key: "engineModel", label: "Engine model" },
  { key: "engineSerialNumber", label: "Engine serial number" },
  { key: "propellerMake", label: "Propeller make" },
  { key: "propellerModel", label: "Propeller model" },
  { key: "propellerSerialNumber", label: "Propeller serial number" },
];

function emptyForm(): Record<keyof AircraftCreateRequest, string> {
  return {
    nNumber: "",
    make: "",
    model: "",
    serialNumber: "",
    year: "",
    airframeSerialNumber: "",
    engineMake: "",
    engineModel: "",
    engineSerialNumber: "",
    propellerMake: "",
    propellerModel: "",
    propellerSerialNumber: "",
  };
}

function toPayload(form: Record<keyof AircraftCreateRequest, string>): AircraftCreateRequest {
  return {
    nNumber: form.nNumber,
    make: form.make,
    model: form.model,
    serialNumber: form.serialNumber || null,
    year: form.year ? Number(form.year) : null,
    airframeSerialNumber: form.airframeSerialNumber || form.serialNumber || null,
    engineMake: form.engineMake || null,
    engineModel: form.engineModel || null,
    engineSerialNumber: form.engineSerialNumber || null,
    propellerMake: form.propellerMake || null,
    propellerModel: form.propellerModel || null,
    propellerSerialNumber: form.propellerSerialNumber || null,
  };
}

export default function PilotOnboardingPage() {
  const router = useRouter();
  const [form, setForm] = useState(emptyForm());
  const [aircraft, setAircraft] = useState<Aircraft | null>(null);
  const [section, setSection] = useState<LogbookSection>("airframe");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [pilotConsentAccepted, setPilotConsentAccepted] = useState(false);
  const [storedUpload, setStoredUpload] = useState<StoredUpload | null>(null);
  const [ingestionJob, setIngestionJob] = useState<IngestionJobSummary | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateField(key: keyof AircraftCreateRequest, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleCreateAircraft(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    try {
      const created = await createAircraft(toPayload(form));
      setAircraft(created);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create aircraft.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleUpload() {
    if (!aircraft || !selectedFile || !pilotConsentAccepted) {
      return;
    }
    setIsUploading(true);
    setError(null);
    try {
      const response = await uploadLogbookFile(aircraft.id, selectedFile, section, { pilotConsentAccepted });
      setStoredUpload(response.upload);
      setIngestionJob(response.ingestionJob);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to upload logbook.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="container mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6">
        <Link href="/logbook" className="inline-flex items-center text-sm text-muted-foreground hover:text-primary">
          <ChevronLeft className="mr-1 h-4 w-4" />
          Back to Dashboard
        </Link>
      </div>

      <PageHeader title="Pilot Intake" description="Create the aircraft account and receive the first maintenance log" />

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Plane className="h-5 w-5" />
              Aircraft account
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4 sm:grid-cols-2" onSubmit={handleCreateAircraft}>
              {FIELD_LABELS.map((field) => (
                <div key={field.key} className={field.key === "nNumber" ? "sm:col-span-2" : ""}>
                  <Label htmlFor={field.key}>{field.label}</Label>
                  <Input
                    id={field.key}
                    type={field.type ?? "text"}
                    value={form[field.key]}
                    required={field.required}
                    onChange={(event) => updateField(field.key, event.target.value)}
                    disabled={Boolean(aircraft)}
                  />
                </div>
              ))}

              <div className="sm:col-span-2">
                <Button type="submit" disabled={isSaving || Boolean(aircraft)}>
                  {isSaving ? "Creating..." : aircraft ? "Aircraft Created" : "Create Aircraft"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Cost tags</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {aircraft ? (
                <>
                  <div>
                    <p className="text-muted-foreground">CustomerAccount</p>
                    <p className="font-mono">{aircraft.customerAccountTag}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Aircraft</p>
                    <p className="font-mono">{aircraft.aircraftCostTag}</p>
                  </div>
                </>
              ) : (
                <p className="text-muted-foreground">Tags are generated after aircraft creation.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <FileText className="h-5 w-5" />
                First logbook upload
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="section">Logbook</Label>
                <select
                  id="section"
                  className="mt-2 h-10 w-full rounded-md border bg-background px-3 text-sm"
                  value={section}
                  onChange={(event) => setSection(event.target.value as LogbookSection)}
                  disabled={!aircraft || Boolean(storedUpload)}
                >
                  {SECTION_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <Label htmlFor="logbook-file">Maintenance log file</Label>
                <Input
                  id="logbook-file"
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  disabled={!aircraft || Boolean(storedUpload)}
                  onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                />
              </div>

              <label className="flex gap-3 rounded-md border p-3 text-sm">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4"
                  checked={pilotConsentAccepted}
                  disabled={!aircraft || Boolean(storedUpload)}
                  onChange={(event) => setPilotConsentAccepted(event.target.checked)}
                />
                <span>
                  I have permission to upload this logbook and associate initial OCR processing with this
                  customer account for pilot cost tracking.
                </span>
              </label>

              <Button
                type="button"
                disabled={!aircraft || !selectedFile || !pilotConsentAccepted || isUploading || Boolean(storedUpload)}
                onClick={handleUpload}
                className="w-full"
              >
                <Upload className="mr-2 h-4 w-4" />
                {isUploading ? "Uploading..." : "Upload and Queue OCR"}
              </Button>

              {storedUpload ? (
                <div className="rounded-md bg-green-50 p-3 text-sm text-green-700 dark:bg-green-950 dark:text-green-300">
                  <div className="flex items-center gap-2 font-medium">
                    <CheckCircle className="h-4 w-4" />
                    Logbook received
                  </div>
                  <p className="mt-2">Billable account: {storedUpload.initialOcrBillableToTag}</p>
                  <div className="mt-3 flex gap-4">
                    {ingestionJob ? (
                      <Link className="underline underline-offset-4" href={`/logbook/${aircraft?.nNumberNormalized}/ingestion/${ingestionJob.id}`}>
                        Review OCR
                      </Link>
                    ) : null}
                    <Link className="underline underline-offset-4" href={`/logbook/${aircraft?.nNumberNormalized}`}>
                      Open aircraft
                    </Link>
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>
      </div>

      {error ? <p className="mt-6 text-sm text-destructive">{error}</p> : null}

      {aircraft && !storedUpload ? (
        <div className="mt-6">
          <Button variant="outline" onClick={() => router.push(`/logbook/${aircraft.nNumberNormalized}`)}>
            Continue without upload
          </Button>
        </div>
      ) : null}
    </div>
  );
}
