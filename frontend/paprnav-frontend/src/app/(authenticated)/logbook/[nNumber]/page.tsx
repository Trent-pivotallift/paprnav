"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Building2, Calendar, ChevronLeft, FileWarning, Plus, ShieldCheck, Upload, User, UserPlus } from "lucide-react";
import { useAuth } from "@/components/AuthProvider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader } from "@/components/PageHeader";
import {
  Aircraft,
  AircraftAssignment,
  ADMatchResult,
  createAircraftAssignment,
  decideAdMatch,
  listAircraftAdMatches,
  listAircraft,
  listAircraftAssignments,
  listLogbookEntries,
  LogbookEntry,
  LogbookSection,
} from "@/lib/api";

const LOGBOOK_SECTIONS: LogbookSection[] = ["airframe", "engine", "propeller"];

function normalizeNNumber(nNumber: string) {
  return nNumber.replace(/[-\s]/g, "").toUpperCase();
}

function getSection(value: string | null): LogbookSection {
  if (value === "engine" || value === "propeller") {
    return value;
  }
  return "airframe";
}

function getPerformer(entry: LogbookEntry) {
  return [entry.performerName, entry.performerCredential].filter(Boolean).join(", ") || "Not recorded";
}

function formatRole(role: string | null | undefined) {
  return role ? role.replaceAll("_", " ") : "component";
}

function formatComponent(match: ADMatchResult) {
  const component = match.applicability?.component;
  if (!component) {
    return null;
  }
  const name = component.displayName || [component.make, component.model].filter(Boolean).join(" ") || component.componentType;
  return `${formatRole(component.role)}: ${name}${component.serialNumber ? ` · SN ${component.serialNumber}` : ""}`;
}

function formatTarget(match: ADMatchResult) {
  const target = match.applicability?.target;
  if (!target) {
    return null;
  }
  return [target.productType, target.productSubtype, target.make, target.model].filter(Boolean).join(" ");
}

function sourceWarning(match: ADMatchResult) {
  const sourceStatus = match.applicability?.sourceStatus;
  if (!sourceStatus || ["current", "active", "published"].includes(sourceStatus)) {
    return null;
  }
  return `Source ${sourceStatus.replaceAll("_", " ")}`;
}

export default function AircraftLogbookPage() {
  const { user } = useAuth();
  const params = useParams();
  const searchParams = useSearchParams();
  const nNumber = params.nNumber as string;
  const logbookType = getSection(searchParams.get("logbook"));
  const [aircraft, setAircraft] = useState<Aircraft | null>(null);
  const [assignments, setAssignments] = useState<AircraftAssignment[]>([]);
  const [entries, setEntries] = useState<LogbookEntry[]>([]);
  const [adMatches, setAdMatches] = useState<ADMatchResult[]>([]);
  const [maintenanceEmail, setMaintenanceEmail] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isAssigning, setIsAssigning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [assignmentMessage, setAssignmentMessage] = useState<string | null>(null);
  const [assignmentError, setAssignmentError] = useState<string | null>(null);
  const [adjudicationNotes, setAdjudicationNotes] = useState<Record<string, string>>({});
  const [adjudicationTags, setAdjudicationTags] = useState<Record<string, string>>({});
  const [adjudicationMessage, setAdjudicationMessage] = useState<string | null>(null);

  const displayNNumber = useMemo(() => normalizeNNumber(nNumber), [nNumber]);
  const canManageAssignments = useMemo(
    () => user?.memberships.some((membership) => membership.role.startsWith("owner_")) ?? false,
    [user],
  );

  const loadEntries = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const aircraftResponse = await listAircraft();
      const selectedAircraft = aircraftResponse.aircraft.find(
        (item) => item.nNumberNormalized === normalizeNNumber(nNumber),
      );
      if (!selectedAircraft) {
        throw new Error("Aircraft not found.");
      }

      const entriesResponse = await listLogbookEntries(selectedAircraft.id, logbookType);
      const matchesResponse = await listAircraftAdMatches(selectedAircraft.id);
      const assignmentsResponse = canManageAssignments
        ? await listAircraftAssignments(selectedAircraft.id)
        : { assignments: [] };
      setAircraft(selectedAircraft);
      setEntries(entriesResponse.entries);
      setAdMatches(matchesResponse.matches);
      setAssignments(assignmentsResponse.assignments);
    } catch (caught) {
      setAircraft(null);
      setEntries([]);
      setAdMatches([]);
      setAssignments([]);
      setError(caught instanceof Error ? caught.message : "Unable to load logbook entries.");
    } finally {
      setIsLoading(false);
    }
  }, [canManageAssignments, logbookType, nNumber]);

  useEffect(() => {
    void loadEntries();
  }, [loadEntries]);

  async function handleAssignMaintenance(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!aircraft) {
      return;
    }

    setIsAssigning(true);
    setAssignmentError(null);
    setAssignmentMessage(null);

    try {
      const assignment = await createAircraftAssignment(aircraft.id, maintenanceEmail);
      setAssignments((current) => [
        ...current.filter((item) => item.organizationId !== assignment.organizationId),
        assignment,
      ]);
      setMaintenanceEmail("");
      setAssignmentMessage(`${assignment.organizationName} can now access ${aircraft.nNumber}.`);
    } catch (caught) {
      setAssignmentError(caught instanceof Error ? caught.message : "Unable to assign maintenance access.");
    } finally {
      setIsAssigning(false);
    }
  }

  async function handleAdjudication(
    match: ADMatchResult,
    decision: "satisfied" | "not_satisfied" | "not_applicable" | "needs_more_info" | "deferred",
  ) {
    setAdjudicationMessage(null);
    try {
      await decideAdMatch(match.id, {
        decision,
        notes: adjudicationNotes[match.id] || null,
        futureImprovementTags: (adjudicationTags[match.id] ?? "")
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
      });
      setAdjudicationMessage(`AD match marked ${decision.replaceAll("_", " ")}.`);
      await loadEntries();
    } catch (caught) {
      setAdjudicationMessage(caught instanceof Error ? caught.message : "Unable to save AD adjudication.");
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <div className="mb-6">
        <Link
          href="/logbook"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-primary transition-colors"
        >
          <ChevronLeft className="mr-1 h-4 w-4" />
          Back to Dashboard
        </Link>
      </div>

      <PageHeader
        title={displayNNumber}
        description={
          aircraft ? `${aircraft.make} ${aircraft.model} logbook entries and maintenance records` : "Aircraft logbook entries and maintenance records"
        }
      >
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link href={`/logbook/${displayNNumber}/new?logbook=${logbookType}`}>
              <Plus className="mr-2 h-4 w-4" />
              Add Manual Entry
            </Link>
          </Button>
          <Button asChild>
            <Link href={`/logbook/${displayNNumber}/upload?logbook=${logbookType}`}>
              <Upload className="mr-2 h-4 w-4" />
              Upload Entry
            </Link>
          </Button>
        </div>
      </PageHeader>

      {canManageAssignments && aircraft ? (
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Building2 className="h-5 w-5" />
              Maintenance Access
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              {assignments.length ? (
                assignments.map((assignment) => (
                  <div
                    key={assignment.id}
                    className="flex flex-col gap-1 rounded-md border p-3 text-sm sm:flex-row sm:items-center sm:justify-between"
                  >
                    <span className="font-medium">{assignment.organizationName}</span>
                    <span className="text-muted-foreground">{assignment.role.replaceAll("_", " ")}</span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No maintenance shops assigned yet.</p>
              )}
            </div>

            <form className="grid gap-3 sm:grid-cols-[1fr_auto]" onSubmit={handleAssignMaintenance}>
              <div className="space-y-2">
                <Label htmlFor="maintenance-email">Maintenance user email</Label>
                <Input
                  id="maintenance-email"
                  type="email"
                  value={maintenanceEmail}
                  onChange={(event) => setMaintenanceEmail(event.target.value)}
                  placeholder="shop.demo@paprnav.local"
                  required
                />
              </div>
              <div className="flex items-end">
                <Button type="submit" disabled={isAssigning || !maintenanceEmail.trim()}>
                  <UserPlus className="mr-2 h-4 w-4" />
                  {isAssigning ? "Assigning..." : "Assign"}
                </Button>
              </div>
            </form>
            {assignmentMessage ? <p className="text-sm text-green-700 dark:text-green-400">{assignmentMessage}</p> : null}
            {assignmentError ? <p className="text-sm text-destructive">{assignmentError}</p> : null}
          </CardContent>
        </Card>
      ) : null}

      {aircraft ? (
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ShieldCheck className="h-5 w-5" />
              AD Compliance Worklist
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {adjudicationMessage ? <p className="rounded-md border p-3 text-sm">{adjudicationMessage}</p> : null}
            {adMatches.length ? (
              adMatches.map((match) => (
                <div key={match.id} className="rounded-md border p-4">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="font-medium">{match.directive.adNumber ?? match.directive.federalRegisterDocumentNumber}</p>
                      <p className="text-sm text-muted-foreground">{match.directive.title}</p>
                    </div>
                    <span className="rounded-md border px-2 py-1 text-xs font-medium">
                      {match.status.replaceAll("_", " ")} · {(match.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="mt-3 text-sm">{match.rationale}</p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Aircraft facts: {match.aircraftFacts.make} {match.aircraftFacts.model}
                    {match.aircraftFacts.serialNumber ? ` · SN ${match.aircraftFacts.serialNumber}` : ""}
                  </p>
                  {formatComponent(match) || formatTarget(match) ? (
                    <div className="mt-3 grid gap-2 rounded-md bg-muted/30 p-3 text-xs sm:grid-cols-2">
                      {formatComponent(match) ? (
                        <p>
                          <span className="font-medium">Component</span>
                          <br />
                          <span className="text-muted-foreground">{formatComponent(match)}</span>
                        </p>
                      ) : null}
                      {formatTarget(match) ? (
                        <p>
                          <span className="font-medium">Applicability target</span>
                          <br />
                          <span className="text-muted-foreground">{formatTarget(match)}</span>
                        </p>
                      ) : null}
                      {match.applicability?.basis ? (
                        <p>
                          <span className="font-medium">Basis</span>
                          <br />
                          <span className="text-muted-foreground">
                            {match.applicability.basis.replaceAll("_", " ")}
                            {match.applicability.serialStatus ? ` · Serial ${match.applicability.serialStatus}` : ""}
                          </span>
                        </p>
                      ) : null}
                      {match.applicability?.publications.length ? (
                        <p>
                          <span className="font-medium">Sources</span>
                          <br />
                          <span className="text-muted-foreground">
                            {match.applicability.publications
                              .map((publication) => `${publication.sourceSystem.replaceAll("_", " ")} ${publication.sourceIdentifier}`)
                              .join(", ")}
                          </span>
                        </p>
                      ) : null}
                    </div>
                  ) : null}
                  <div className="mt-3 flex flex-wrap gap-2 text-xs">
                    {match.directive.htmlUrl ? (
                      <a className="rounded-md border px-2 py-1 hover:bg-muted" href={match.directive.htmlUrl} target="_blank" rel="noreferrer">
                        Federal Register
                      </a>
                    ) : null}
                    {match.directive.pdfUrl ? (
                      <a className="rounded-md border px-2 py-1 hover:bg-muted" href={match.directive.pdfUrl} target="_blank" rel="noreferrer">
                        Source PDF
                      </a>
                    ) : null}
                    {match.applicability?.publications
                      .filter((publication) => publication.htmlUrl || publication.pdfUrl)
                      .map((publication) => (
                        <a
                          key={`${publication.sourceSystem}-${publication.sourceIdentifier}`}
                          className="rounded-md border px-2 py-1 hover:bg-muted"
                          href={publication.htmlUrl ?? publication.pdfUrl ?? "#"}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {publication.sourceSystem.replaceAll("_", " ")}
                        </a>
                      ))}
                  </div>
                  {sourceWarning(match) || match.unresolvedReasons.length ? (
                    <p className="mt-2 flex items-center gap-2 text-xs text-amber-700 dark:text-amber-400">
                      <FileWarning className="h-4 w-4" />
                      {[sourceWarning(match), ...match.unresolvedReasons.map((reason) => reason.replaceAll("_", " "))].filter(Boolean).join(", ")}
                    </p>
                  ) : null}
                  {match.evidence.length ? (
                    <div className="mt-3 space-y-2">
                      {match.evidence.slice(0, 2).map((evidence) => (
                        <Link
                          key={evidence.id}
                          href={`/logbook/${displayNNumber}/entry/${evidence.logbookEntryId}?logbook=${evidence.section}`}
                          className="block rounded-md bg-muted/40 p-3 text-sm hover:bg-muted"
                        >
                          <span className="font-medium">{evidence.entryDate}</span>
                          <span className="ml-2 text-muted-foreground">{evidence.rationale}</span>
                        </Link>
                      ))}
                    </div>
                  ) : null}
                  {match.status === "needs_adjudication" || match.adjudication?.status === "pending" ? (
                    <div className="mt-4 space-y-3 rounded-md bg-muted/30 p-3">
                      <Textarea
                        placeholder="Reviewer notes"
                        value={adjudicationNotes[match.id] ?? ""}
                        onChange={(event) => setAdjudicationNotes((current) => ({ ...current, [match.id]: event.target.value }))}
                      />
                      <Input
                        placeholder="Future improvement tags, comma-separated"
                        value={adjudicationTags[match.id] ?? ""}
                        onChange={(event) => setAdjudicationTags((current) => ({ ...current, [match.id]: event.target.value }))}
                      />
                      <div className="flex flex-wrap gap-2">
                        <Button size="sm" type="button" onClick={() => handleAdjudication(match, "satisfied")}>Satisfied</Button>
                        <Button size="sm" type="button" variant="outline" onClick={() => handleAdjudication(match, "not_satisfied")}>Not Satisfied</Button>
                        <Button size="sm" type="button" variant="outline" onClick={() => handleAdjudication(match, "not_applicable")}>Not Applicable</Button>
                        <Button size="sm" type="button" variant="outline" onClick={() => handleAdjudication(match, "needs_more_info")}>Needs More Info</Button>
                        <Button size="sm" type="button" variant="ghost" onClick={() => handleAdjudication(match, "deferred")}>Defer</Button>
                      </div>
                    </div>
                  ) : match.adjudication?.decision ? (
                    <p className="mt-3 rounded-md bg-muted/40 p-3 text-sm">
                      Human decision: {match.adjudication.decision.replaceAll("_", " ")}
                      {match.adjudication.notes ? ` · ${match.adjudication.notes}` : ""}
                    </p>
                  ) : null}
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">
                No AD match results yet. Run the local AD matching worker after AD extraction review.
              </p>
            )}
          </CardContent>
        </Card>
      ) : null}

      {/* Logbook Tabs */}
      <Tabs value={logbookType} className="mt-8">
        <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
          {LOGBOOK_SECTIONS.map((section) => (
            <TabsTrigger key={section} value={section} asChild>
              <Link href={`/logbook/${displayNNumber}?logbook=${section}`}>
                {section.charAt(0).toUpperCase() + section.slice(1)}
              </Link>
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value={logbookType} className="mt-6">
          {isLoading ? (
            <div className="space-y-4">
              {[0, 1, 2].map((index) => (
                <Card key={index} className="animate-pulse">
                  <CardContent className="space-y-4 p-6">
                    <div className="h-5 w-2/3 rounded bg-muted" />
                    <div className="h-4 w-1/2 rounded bg-muted" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : error ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center gap-4 py-12 text-center">
                <p className="text-sm text-destructive">{error}</p>
                <Button variant="outline" onClick={loadEntries}>
                  Retry
                </Button>
              </CardContent>
            </Card>
          ) : entries.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                <p className="text-muted-foreground mb-4">
                  No log entries yet for this logbook.
                </p>
                <Button asChild>
                  <Link href={`/logbook/${displayNNumber}/new?logbook=${logbookType}`}>
                    <Plus className="mr-2 h-4 w-4" />
                    Add First Entry
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {entries.map((entry) => (
                <Link
                  key={entry.id}
                  href={`/logbook/${displayNNumber}/entry/${entry.id}?logbook=${entry.section}`}
                  className="block"
                >
                  <Card className="transition-all duration-200 hover:shadow-md hover:border-primary/20">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg font-semibold flex items-center justify-between">
                        <span>{entry.description}</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-6 text-base text-muted-foreground">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-5 w-5" />
                          <span>{entry.entryDate}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <User className="h-5 w-5" />
                          <span>{getPerformer(entry)}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
