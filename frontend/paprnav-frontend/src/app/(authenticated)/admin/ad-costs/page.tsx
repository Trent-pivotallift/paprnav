"use client";

import { useCallback, useEffect, useState } from "react";
import { Database, RefreshCw } from "lucide-react";
import { ADCostAdminSummary, getADCostAdminSummary } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/PageHeader";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 ** 2) return `${(value / 1024).toFixed(1)} KB`;
  if (value < 1024 ** 3) return `${(value / 1024 ** 2).toFixed(1)} MB`;
  return `${(value / 1024 ** 3).toFixed(2)} GB`;
}

function formatUsd(value: string) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(Number(value));
}

export default function ADCostAdminPage() {
  const [summary, setSummary] = useState<ADCostAdminSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = useCallback(async () => {
    try {
      setSummary(await getADCostAdminSummary());
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load AD cost attribution.");
    }
  }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadSummary();
    }, 0);
    return () => window.clearTimeout(timeoutId);
  }, [loadSummary]);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <PageHeader
          title="AD / DRS Cost Attribution"
          description="Shared source storage, reusable applicability coverage, and the clients benefiting from each coverage set"
        />
        <Button type="button" variant="outline" onClick={loadSummary}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {error ? (
        <p className="mt-6 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </p>
      ) : null}

      {!summary && !error ? <p className="mt-8 text-sm text-muted-foreground">Loading attribution data...</p> : null}

      {summary ? (
        <>
          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Coverage sets" value={String(summary.totals.coverageSetCount)} />
            <MetricCard label="Clients benefiting" value={String(summary.totals.clientCount)} />
            <MetricCard label="Aircraft linked" value={String(summary.totals.aircraftCount)} />
            <MetricCard label="Actual recorded cost" value={formatUsd(summary.totals.actualCostUsd)} />
          </div>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Database className="h-5 w-5" />
                Shared source storage
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="mb-4 text-sm text-muted-foreground">
                Physical DRS source storage is platform-shared and is not duplicated or charged to the first client.
                Allocation is currently {summary.allocationPolicyStatus.replaceAll("_", " ")}.
              </p>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Snapshot</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Rows</TableHead>
                    <TableHead>Physical storage</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {summary.sourceSnapshots.map((snapshot) => (
                    <TableRow key={snapshot.id}>
                      <TableCell>
                        <p className="font-medium">{snapshot.filename ?? snapshot.id}</p>
                        <p className="font-mono text-xs text-muted-foreground">{snapshot.contentHash.slice(0, 16)}</p>
                      </TableCell>
                      <TableCell>{snapshot.status}</TableCell>
                      <TableCell>{snapshot.rowCount ?? "—"}</TableCell>
                      <TableCell>{formatBytes(snapshot.storageBytes)}</TableCell>
                    </TableRow>
                  ))}
                  {!summary.sourceSnapshots.length ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-muted-foreground">No DRS snapshots recorded.</TableCell>
                    </TableRow>
                  ) : null}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="text-lg">Reusable applicability coverage</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Make / model</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>ADs</TableHead>
                    <TableHead>Logical storage</TableHead>
                    <TableHead>Clients / aircraft</TableHead>
                    <TableHead>Allocated cost</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {summary.coverages.map((coverage) => (
                    <TableRow key={coverage.id}>
                      <TableCell>
                        <p className="font-medium">{[coverage.make, coverage.model].filter(Boolean).join(" ") || "Unspecified"}</p>
                        <p className="font-mono text-xs text-muted-foreground">{coverage.coverageVersion}</p>
                      </TableCell>
                      <TableCell>{coverage.productType}</TableCell>
                      <TableCell>{coverage.status.replaceAll("_", " ")}</TableCell>
                      <TableCell>{coverage.directiveCount}</TableCell>
                      <TableCell>{formatBytes(coverage.derivedLogicalStorageBytes)}</TableCell>
                      <TableCell>
                        {coverage.clients.length ? coverage.clients.map((client) => (
                          <p key={`${client.organizationId}-${client.aircraftId}`} className="text-xs">
                            {client.organizationName} · {client.nNumber}
                            {client.triggeredCreation ? " · first trigger" : ""}
                          </p>
                        )) : "—"}
                      </TableCell>
                      <TableCell>{formatUsd(coverage.allocatedCostUsd)}</TableCell>
                    </TableRow>
                  ))}
                  {!summary.coverages.length ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-muted-foreground">No aircraft coverage has been resolved.</TableCell>
                    </TableRow>
                  ) : null}
                </TableBody>
              </Table>
              <p className="mt-4 text-xs text-muted-foreground">
                Logical storage estimates describe each derived applicability slice. They do not duplicate the physical
                source snapshot and must not be summed into a customer invoice until an allocation policy is approved.
              </p>
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="p-6">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="mt-2 text-2xl font-semibold">{value}</p>
      </CardContent>
    </Card>
  );
}
