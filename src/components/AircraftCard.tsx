"use client";

import Link from "next/link";
import { Book, Upload, ChevronDown, Plane } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { StatusBadge, getStatusFromAdStatus } from "@/components/StatusBadge";

interface AircraftCardProps {
  nNumber: string;
  type: string;
  adStatus: string;
  lastLogEntry: string;
}

export default function AircraftCard({ nNumber, type, adStatus, lastLogEntry }: AircraftCardProps) {
  const status = getStatusFromAdStatus(adStatus);
  const statusLabel = adStatus.replace(/[^\w\s]/g, "").trim();

  return (
    <Card className="group transition-all duration-200 hover:shadow-lg hover:-translate-y-1">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-primary/10 p-2">
              <Plane className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-xl font-semibold">{nNumber}</CardTitle>
              <p className="text-sm text-muted-foreground">{type}</p>
            </div>
          </div>
          <StatusBadge status={status} label={statusLabel} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-sm">
          <span className="text-muted-foreground">Last entry: </span>
          <span className="font-medium">{lastLogEntry}</span>
        </div>

        <div className="flex flex-wrap gap-2">
          {/* View Logbook Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="flex-1 sm:flex-none">
                <Book className="mr-2 h-4 w-4" />
                View Logbook
                <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              <DropdownMenuItem asChild>
                <Link href={`/logbook/${nNumber}?logbook=airframe`}>
                  Airframe Log
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href={`/logbook/${nNumber}?logbook=engine`}>
                  Engine Log
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href={`/logbook/${nNumber}?logbook=propeller`}>
                  Propeller Log
                </Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Upload Log Entry Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button size="sm" className="flex-1 sm:flex-none">
                <Upload className="mr-2 h-4 w-4" />
                Upload Entry
                <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              <DropdownMenuItem asChild>
                <Link href={`/logbook/${nNumber}/upload?logbook=airframe`}>
                  Airframe Log
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href={`/logbook/${nNumber}/upload?logbook=engine`}>
                  Engine Log
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href={`/logbook/${nNumber}/upload?logbook=propeller`}>
                  Propeller Log
                </Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardContent>
    </Card>
  );
}
