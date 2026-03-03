"use client";

import Link from "next/link";
import { Book, ChevronDown, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { TableCell, TableRow } from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { StatusBadge, getStatusFromAdStatus } from "@/components/StatusBadge";

interface ClientAircraftRowProps {
  nNumber: string;
  type: string;
  owner: string;
  adStatus: string;
}

export default function ClientAircraftRow({ nNumber, type, owner, adStatus }: ClientAircraftRowProps) {
  const status = getStatusFromAdStatus(adStatus);
  const statusLabel = adStatus.replace(/[^\w\s]/g, "").trim();

  return (
    <TableRow className="hover:bg-muted/50">
      <TableCell className="font-medium">{nNumber}</TableCell>
      <TableCell>{type}</TableCell>
      <TableCell>{owner}</TableCell>
      <TableCell>
        <StatusBadge status={status} label={statusLabel} />
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2 justify-end">
          {/* View Logbook Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm">
                <Book className="mr-2 h-4 w-4" />
                View Logbook
                <ChevronDown className="ml-1 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
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

          {/* Add Entry Button */}
          <Button variant="outline" size="sm" asChild>
            <Link href={`/logbook/${nNumber}/upload`}>
              <Plus className="mr-1 h-4 w-4" />
              Add Entry
            </Link>
          </Button>
        </div>
      </TableCell>
    </TableRow>
  );
}
