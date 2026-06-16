"use client";

import React, { useState } from "react";
import { Plus, Search, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { PageHeader } from "@/components/PageHeader";
import AircraftCard from "@/components/AircraftCard";
import ClientAircraftRow from "@/components/ClientAircraftRow";

const dummyOwnerAircraft = [
  { nNumber: "N12345", type: "Cessna 172", adStatus: "2 Overdue", lastLogEntry: "2026-02-10" },
  { nNumber: "N54321", type: "Piper PA-28", adStatus: "All Compliant", lastLogEntry: "2026-01-15" },
];

const dummyClientAircraft = [
  { nNumber: "N12345", type: "Cessna 172", owner: "Peter Jones", adStatus: "2 Overdue" },
  { nNumber: "N54321", type: "Piper PA-28", owner: "Susan Smith", adStatus: "Compliant" },
  { nNumber: "N98765", type: "Cirrus SR22", owner: "David Chen", adStatus: "1 Warning" },
];

export default function LogbookDashboardPage() {
  const [userRole, setUserRole] = useState<"owner" | "maintenance">("owner");

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Role Switcher */}
      <div className="mb-6 flex justify-end">
        <div className="inline-flex rounded-lg border bg-muted p-1">
          <Button
            variant={userRole === "owner" ? "default" : "ghost"}
            size="sm"
            onClick={() => setUserRole("owner")}
            className="rounded-md"
          >
            Owner View
          </Button>
          <Button
            variant={userRole === "maintenance" ? "default" : "ghost"}
            size="sm"
            onClick={() => setUserRole("maintenance")}
            className="rounded-md"
          >
            Maintenance Shop
          </Button>
        </div>
      </div>

      {/* Conditional Dashboard Rendering */}
      {userRole === "owner" ? (
        // Aircraft Owner Dashboard
        <div className="space-y-6">
          <PageHeader
            title="My Fleet"
            description="Manage your aircraft logbooks and compliance status"
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {dummyOwnerAircraft.map((aircraft) => (
              <AircraftCard
                key={aircraft.nNumber}
                nNumber={aircraft.nNumber}
                type={aircraft.type}
                adStatus={aircraft.adStatus}
                lastLogEntry={aircraft.lastLogEntry}
              />
            ))}

            {/* Add New Aircraft Card */}
            <Card className="flex items-center justify-center border-2 border-dashed hover:border-primary/50 hover:bg-muted/50 transition-colors cursor-pointer group min-h-[200px]">
              <CardContent className="flex flex-col items-center justify-center text-muted-foreground group-hover:text-primary transition-colors py-8">
                <Plus className="h-12 w-12 mb-2" />
                <span className="font-medium">Add New Aircraft</span>
              </CardContent>
            </Card>
          </div>
        </div>
      ) : (
        // Maintenance Shop Dashboard
        <div className="space-y-6">
          <PageHeader
            title="Client Aircraft"
            description="View and manage maintenance records for client aircraft"
          />

          {/* Search and Filter */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by N# or Owner"
                className="pl-9"
              />
            </div>
            <Button variant="outline">
              <Filter className="mr-2 h-4 w-4" />
              Filter
            </Button>
          </div>

          {/* Client Aircraft Table */}
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>N-Number</TableHead>
                    <TableHead>Aircraft Type</TableHead>
                    <TableHead>Owner</TableHead>
                    <TableHead>ADs Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dummyClientAircraft.map((aircraft) => (
                    <ClientAircraftRow
                      key={aircraft.nNumber}
                      nNumber={aircraft.nNumber}
                      type={aircraft.type}
                      owner={aircraft.owner}
                      adStatus={aircraft.adStatus}
                    />
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
