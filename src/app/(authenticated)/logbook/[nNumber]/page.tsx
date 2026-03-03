"use client";

import React from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { ChevronLeft, Upload, Plus, Calendar, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader } from "@/components/PageHeader";

const dummyLogEntries = [
  { id: 1, date: "2026-02-15", description: "Annual Inspection", performedBy: "John Doe, A&P 12345" },
  { id: 2, date: "2026-01-20", description: "AD 2022-14-08 Complied", performedBy: "Jane Smith, A&P 67890" },
];

export default function AircraftLogbookPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const nNumber = params.nNumber as string;
  const logbookType = searchParams.get("logbook") || "airframe";

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
        title={`N-${nNumber}`}
        description="Aircraft logbook entries and maintenance records"
      >
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link href={`/logbook/${nNumber}/upload?logbook=${logbookType}`}>
              <Plus className="mr-2 h-4 w-4" />
              Add Manual Entry
            </Link>
          </Button>
          <Button asChild>
            <Link href={`/logbook/${nNumber}/upload?logbook=${logbookType}`}>
              <Upload className="mr-2 h-4 w-4" />
              Upload Entry
            </Link>
          </Button>
        </div>
      </PageHeader>

      {/* Logbook Tabs */}
      <Tabs defaultValue={logbookType} className="mt-8">
        <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
          <TabsTrigger value="airframe" asChild>
            <Link href={`/logbook/${nNumber}?logbook=airframe`}>Airframe</Link>
          </TabsTrigger>
          <TabsTrigger value="engine" asChild>
            <Link href={`/logbook/${nNumber}?logbook=engine`}>Engine</Link>
          </TabsTrigger>
          <TabsTrigger value="propeller" asChild>
            <Link href={`/logbook/${nNumber}?logbook=propeller`}>Propeller</Link>
          </TabsTrigger>
        </TabsList>

        <TabsContent value={logbookType} className="mt-6">
          <div className="space-y-4">
            {dummyLogEntries.map((entry) => (
              <Link
                key={entry.id}
                href={`/logbook/${nNumber}/entry/${entry.id}`}
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
                        <span>{entry.date}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <User className="h-5 w-5" />
                        <span>{entry.performedBy}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          {dummyLogEntries.length === 0 && (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                <p className="text-muted-foreground mb-4">
                  No log entries yet for this logbook.
                </p>
                <Button asChild>
                  <Link href={`/logbook/${nNumber}/upload?logbook=${logbookType}`}>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload First Entry
                  </Link>
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
