"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { ChevronLeft, Upload, FileText, X, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { PageHeader } from "@/components/PageHeader";
import { listAircraft, LogbookSection, uploadLogbookFile, Upload as StoredUpload } from "@/lib/api";
import { cn } from "@/lib/utils";

function normalizeNNumber(nNumber: string) {
  return nNumber.replace(/[-\s]/g, "").toUpperCase();
}

function getSection(value: string | null): LogbookSection {
  if (value === "engine" || value === "propeller") {
    return value;
  }
  return "airframe";
}

function proxyDownloadUrl(downloadUrl: string) {
  if (downloadUrl.startsWith("/api/v1/")) {
    return `/api/backend${downloadUrl}`;
  }
  return downloadUrl;
}

export default function LogbookUploadPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const nNumber = params.nNumber as string;
  const section = getSection(searchParams.get("logbook"));
  const displayNNumber = normalizeNNumber(nNumber);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "success" | "error">("idle");
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [storedUpload, setStoredUpload] = useState<StoredUpload | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
      setUploadStatus("idle");
      setUploadMessage(null);
      setStoredUpload(null);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    if (event.dataTransfer.files && event.dataTransfer.files[0]) {
      setSelectedFile(event.dataTransfer.files[0]);
      setUploadStatus("idle");
      setUploadMessage(null);
      setStoredUpload(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadMessage("Please select a file to upload.");
      setUploadStatus("error");
      return;
    }

    setIsUploading(true);
    setUploadMessage("Uploading...");
    setUploadStatus("idle");
    setStoredUpload(null);

    try {
      const aircraftResponse = await listAircraft();
      const aircraft = aircraftResponse.aircraft.find((item) => item.nNumberNormalized === displayNNumber);
      if (!aircraft) {
        throw new Error("Aircraft not found.");
      }

      const response = await uploadLogbookFile(aircraft.id, selectedFile, section);
      setStoredUpload(response.upload);
      setUploadMessage(`Stored ${response.upload.originalFilename}`);
      setUploadStatus("success");
      setSelectedFile(null);
    } catch (caught) {
      setUploadMessage(caught instanceof Error ? caught.message : "Upload failed. Please try again.");
      setUploadStatus("error");
    } finally {
      setIsUploading(false);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    setUploadStatus("idle");
    setUploadMessage(null);
    setStoredUpload(null);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
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
        title="Upload Logbook Entry"
        description={`${displayNNumber} ${section} logbook`}
      />

      <Card className="mt-8">
        <CardContent className="pt-6">
          {/* Drop Zone */}
          <div
            className={cn(
              "relative rounded-lg border-2 border-dashed p-12 text-center transition-all duration-200 cursor-pointer",
              isDragOver
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50",
              selectedFile && "border-primary bg-primary/5"
            )}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById("fileInput")?.click()}
          >
            {selectedFile ? (
              <div className="flex flex-col items-center gap-4">
                <div className="rounded-full bg-primary/10 p-4">
                  <FileText className="h-8 w-8 text-primary" />
                </div>
                <div>
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    clearFile();
                  }}
                >
                  <X className="mr-1 h-4 w-4" />
                  Remove
                </Button>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <div className="rounded-full bg-muted p-4">
                  <Upload className="h-8 w-8 text-muted-foreground" />
                </div>
                <div>
                  <p className="font-medium">
                    Drop your logbook scan here
                  </p>
                  <p className="text-sm text-muted-foreground">
                    or click to browse
                  </p>
                </div>
                <p className="text-xs text-muted-foreground">
                  Supports PDF, JPG, PNG (max 100MB)
                </p>
              </div>
            )}

            <input
              id="fileInput"
              type="file"
              className="hidden"
              onChange={handleFileChange}
              accept=".pdf,.jpg,.jpeg,.png"
            />
          </div>

          {/* Status Message */}
          {uploadMessage && (
            <div
              className={cn(
                "mt-4 flex items-center gap-2 rounded-lg p-3 text-sm",
                uploadStatus === "success" && "bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300",
                uploadStatus === "error" && "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300"
              )}
            >
              {uploadStatus === "success" && <CheckCircle className="h-4 w-4" />}
              {uploadStatus === "error" && <AlertCircle className="h-4 w-4" />}
              <span>{uploadMessage}</span>
              {storedUpload ? (
                <span className="ml-auto flex gap-3">
                  <Link href={`/logbook/${displayNNumber}?logbook=${section}`} className="underline underline-offset-4">
                    Back to logbook
                  </Link>
                  <Link href={proxyDownloadUrl(storedUpload.downloadUrl)} className="underline underline-offset-4">
                    Download
                  </Link>
                </span>
              ) : null}
            </div>
          )}

          {/* Upload Button */}
          <div className="mt-6 flex justify-center">
            <Button
              onClick={handleUpload}
              disabled={!selectedFile || isUploading}
              size="lg"
              className="min-w-[200px]"
            >
              {isUploading ? (
                <>
                  <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload Logbook
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
