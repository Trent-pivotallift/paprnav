"use client";

import React, { useState } from "react";
import { Plus, Search, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { PageHeader } from "@/components/PageHeader";
import AircraftCard from "@/components/AircraftCard";
import ClientAircraftRow from "@/components/ClientAircraftRow";
import { Aircraft, listAircraft } from "@/lib/api";
import { useEffect } from "react";
import { useAuth } from "@/components/AuthProvider";

function formatAircraftType(aircraft: Aircraft) {
  return `${aircraft.make} ${aircraft.model}`.trim();
}

function formatComplianceStatus(status: string) {
  if (status === "needs_review") {
    return "Needs Review";
  }
  return status
    .split("_")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatLastEntry(date: string | null) {
  return date ?? "No entries yet";
}

export default function LogbookDashboardPage() {
  const { user } = useAuth();
  const [userRole, setUserRole] = useState<"owner" | "maintenance">("owner");
  const [aircraft, setAircraft] = useState<Aircraft[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadAircraft() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await listAircraft();
      setAircraft(response.aircraft);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load aircraft.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadAircraft();
  }, []);

  useEffect(() => {
    const hasOwnerMembership = user?.memberships.some((membership) => membership.role.startsWith("owner_"));
    const hasMaintenanceMembership = user?.memberships.some((membership) => membership.role.startsWith("maintenance_"));
    if (!hasOwnerMembership && hasMaintenanceMembership) {
      setUserRole("maintenance");
    }
  }, [user]);

  const visibleAircraft = aircraft.filter((item) => {
    const haystack = `${item.nNumber} ${item.make} ${item.model}`.toLowerCase();
    return haystack.includes(searchTerm.toLowerCase());
  });

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

          {isLoading ? (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {[0, 1, 2].map((index) => (
                <Card key={index} className="min-h-[200px] animate-pulse">
                  <CardContent className="space-y-4 p-6">
                    <div className="h-5 w-24 rounded bg-muted" />
                    <div className="h-4 w-32 rounded bg-muted" />
                    <div className="h-9 w-full rounded bg-muted" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : error ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center gap-4 py-10 text-center">
                <p className="text-sm text-destructive">{error}</p>
                <Button variant="outline" onClick={loadAircraft}>
                  Retry
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {aircraft.map((item) => (
                <AircraftCard
                  key={item.id}
                  nNumber={item.nNumber}
                  type={formatAircraftType(item)}
                  adStatus={formatComplianceStatus(item.complianceStatus)}
                  lastLogEntry={formatLastEntry(item.lastLogEntryDate)}
                />
              ))}

              {aircraft.length === 0 ? (
                <Card className="min-h-[200px]">
                  <CardContent className="flex h-full flex-col items-center justify-center py-10 text-center text-muted-foreground">
                    <p className="font-medium text-foreground">No aircraft yet</p>
                    <p className="mt-1 text-sm">Add an aircraft to start building a digital logbook.</p>
                  </CardContent>
                </Card>
              ) : null}

              <Card className="flex min-h-[200px] cursor-pointer items-center justify-center border-2 border-dashed transition-colors hover:border-primary/50 hover:bg-muted/50 group">
                <CardContent className="flex flex-col items-center justify-center py-8 text-muted-foreground transition-colors group-hover:text-primary">
                  <Plus className="mb-2 h-12 w-12" />
                  <span className="font-medium">Add New Aircraft</span>
                </CardContent>
              </Card>
            </div>
          )}
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
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
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
                  {isLoading ? (
                    <TableRow>
                      <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                        Loading aircraft...
                      </TableCell>
                    </TableRow>
                  ) : error ? (
                    <TableRow>
                      <TableCell colSpan={5} className="py-8 text-center">
                        <div className="flex flex-col items-center gap-3">
                          <p className="text-sm text-destructive">{error}</p>
                          <Button variant="outline" size="sm" onClick={loadAircraft}>
                            Retry
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : visibleAircraft.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                        No client aircraft found.
                      </TableCell>
                    </TableRow>
                  ) : (
                    visibleAircraft.map((item) => (
                      <ClientAircraftRow
                        key={item.id}
                        nNumber={item.nNumber}
                        type={formatAircraftType(item)}
                        owner="Assigned client"
                        adStatus={formatComplianceStatus(item.complianceStatus)}
                      />
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
