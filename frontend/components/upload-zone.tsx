"use client";

import * as React from "react";
import { CloudUpload, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { ExtractedDocument } from "@/lib/types";
import { extractPdfText } from "@/lib/pdf";

type UploadZoneProps = {
  extracted: ExtractedDocument | null;
  onExtracted: (document: ExtractedDocument) => void;
  onError: (message: string) => void;
  onReset: () => void;
  disabled?: boolean;
};

export function UploadZone({
  extracted,
  onExtracted,
  onError,
  onReset,
  disabled
}: UploadZoneProps) {
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = React.useState(false);
  const [isExtracting, setIsExtracting] = React.useState(false);
  const [progress, setProgress] = React.useState<{ current: number; total: number } | null>(
    null
  );

  const handleFile = React.useCallback(
    async (file: File) => {
      if (!file.type.includes("pdf") && !file.name.toLowerCase().endsWith(".pdf")) {
        onError("Please upload a PDF file.");
        return;
      }

      setIsExtracting(true);
      setProgress(null);
      try {
        const result = await extractPdfText(file, (current, total) =>
          setProgress({ current, total })
        );
        onExtracted(result);
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Unable to extract text from the PDF.";
        onError(message);
      } finally {
        setIsExtracting(false);
      }
    },
    [onError, onExtracted]
  );

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) {
      return;
    }
    void handleFile(files[0]);
  };

  const onDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (disabled || isExtracting) {
      return;
    }
    setIsDragging(false);
    handleFiles(event.dataTransfer.files);
  };

  return (
    <Card className="border-steel-200/80">
      <CardHeader>
        <CardTitle>Upload a PDF</CardTitle>
        <CardDescription>
          Files stay in the browser. Only extracted text is sent for audit.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-steel-100 bg-steel-50 px-4 py-3 text-xs text-steel-600">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-trust-600" />
            Zero-retention extraction in your browser.
          </div>
          <div>PDF only. No uploads.</div>
        </div>

        <div
          data-testid="upload-dropzone"
          className={[
            "flex min-h-[200px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed px-6 py-8 text-center transition-colors",
            isDragging ? "border-trust-600 bg-trust-600/5" : "border-steel-200 bg-white/80",
            disabled || isExtracting ? "opacity-60" : "cursor-pointer hover:border-trust-500"
          ].join(" ")}
          onDragOver={(event) => {
            event.preventDefault();
            if (!disabled && !isExtracting) {
              setIsDragging(true);
            }
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={onDrop}
          onClick={() => {
            if (!disabled && !isExtracting) {
              fileInputRef.current?.click();
            }
          }}
        >
          <CloudUpload className="h-7 w-7 text-trust-600" />
          <div className="text-base font-semibold text-ink-900">
            {isExtracting ? "Extracting text" : "Drop your PDF here"}
          </div>
          <div className="text-xs text-steel-600">
            {isExtracting && progress
              ? `Page ${progress.current} of ${progress.total}`
              : "Or click to select from your device"}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(event) => handleFiles(event.target.files)}
          />
        </div>

        {extracted ? (
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-steel-100 bg-white px-4 py-3 text-sm">
            <div className="text-ink-900">
              {extracted.fileName} - {extracted.pageCount} pages
            </div>
            <Button variant="outline" size="sm" onClick={onReset} disabled={isExtracting}>
              Replace file
            </Button>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
