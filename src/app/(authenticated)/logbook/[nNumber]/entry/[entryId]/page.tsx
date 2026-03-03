"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/PageHeader";

export default function LogbookEntryDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const nNumber = params.nNumber as string;
  const entryId = params.entryId as string;
  const logbookType = searchParams.get('logbook') || 'airframe';

  // Dummy data
  const [logEntry, setLogEntry] = useState({
    date: '2026-02-15',
    description: 'Annual inspection completed, oil changed, filters replaced. AD 2022-14-08 complied with.',
    signature: 'John Doe, A&P 12345',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setLogEntry((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = () => {
    console.log('Saving changes:', logEntry);
    alert('Changes saved (simulated)!');
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <PageHeader
        title={`Log Entry: ${logEntry.date}`}
        description={`Editing entry #${entryId} for N-${nNumber} (${logbookType} logbook)`}
        backLinkHref={`/logbook/${nNumber}?logbook=${logbookType}`}
        backLinkLabel="Back to Logbook"
      />

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
                <Label htmlFor="date">Date</Label>
                <Input
                  type="date"
                  id="date"
                  name="date"
                  value={logEntry.date}
                  onChange={handleChange}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  name="description"
                  rows={6}
                  value={logEntry.description}
                  onChange={handleChange}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="signature">Signature / Certificate #</Label>
                <Input
                  type="text"
                  id="signature"
                  name="signature"
                  value={logEntry.signature}
                  onChange={handleChange}
                />
              </div>

              <div className="flex justify-end space-x-3">
                <Button variant="outline" type="button">
                  Cancel
                </Button>
                <Button type="button" onClick={handleSave}>
                  Save Changes
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
