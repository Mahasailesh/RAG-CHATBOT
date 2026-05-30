"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { AlertTriangle, FileDown } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useToast } from "@/components/ui/use-toast";
import type { AuditReport } from "@/lib/types";

type ReportDashboardProps = {
  report: AuditReport;
  documentName?: string | null;
};

const renderValue = (value?: string | number | null) => {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }
  return String(value);
};

const renderConfidence = (value?: number | null) => {
  if (value === null || value === undefined) {
    return "N/A";
  }
  const percent = Math.round(value * 100);
  return `${percent}%`;
};

const sanitizeFileName = (value: string) =>
  value
    .replace(/[^a-z0-9-_]+/gi, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");

export function ReportDashboard({ report, documentName }: ReportDashboardProps) {
  const { toast } = useToast();
  const [isExporting, setIsExporting] = React.useState(false);
  const hasIssues = report.issues.length > 0;
  const highCount = report.issues.filter((issue) => issue.severity === "high").length;
  const mediumCount = report.issues.filter((issue) => issue.severity === "medium").length;
  const lowCount = report.issues.filter((issue) => issue.severity === "low").length;
  const ruleCount = report.issues.filter((issue) => issue.source === "rule").length;
  const modelCount = report.issues.filter((issue) => issue.source !== "rule").length;

  const handleDownloadPdf = async () => {
    setIsExporting(true);
    try {
      const [{ jsPDF }, autoTableModule] = await Promise.all([
        import("jspdf"),
        import("jspdf-autotable")
      ]);
      const autoTable = autoTableModule.default;
      const doc = new jsPDF({ unit: "pt", format: "a4" });
      const pageWidth = doc.internal.pageSize.getWidth();
      const margin = 40;
      let cursorY = 40;

      const generatedAt = new Date().toLocaleString();
      const title = "ClearPass AI Audit Report";
      const displayName = documentName?.trim() || "Document";
      const statusLabel = hasIssues ? `${report.issues.length} issues found` : "No issues found";

      doc.setFont("helvetica", "bold");
      doc.setFontSize(16);
      doc.setTextColor(11, 18, 32);
      doc.text(title, margin, cursorY);
      cursorY += 18;

      doc.setFont("helvetica", "normal");
      doc.setFontSize(10);
      doc.setTextColor(71, 85, 105);
      doc.text(`Document: ${displayName}`, margin, cursorY);
      cursorY += 14;
      doc.text(`Generated: ${generatedAt}`, margin, cursorY);
      cursorY += 14;

      doc.setDrawColor(226, 232, 240);
      doc.line(margin, cursorY, pageWidth - margin, cursorY);
      cursorY += 16;

      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      doc.setTextColor(11, 18, 32);
      doc.text(`Status: ${statusLabel}`, margin, cursorY);
      cursorY += 16;

      doc.setFont("helvetica", "normal");
      doc.setFontSize(10);
      doc.setTextColor(71, 85, 105);
      doc.text(`High risk: ${highCount}   Medium risk: ${mediumCount}   Low risk: ${lowCount}`, margin, cursorY);
      cursorY += 14;
      doc.text(`Rule checks flagged: ${ruleCount}   Model findings: ${modelCount}`, margin, cursorY);
      cursorY += 18;

      if (report.review_required) {
        const reviewText =
          (report.review_reasons ?? []).length > 0
            ? report.review_reasons?.join(" ") ?? ""
            : "High-risk discrepancies detected.";
        const boxHeight = 42;
        doc.setFillColor(255, 251, 235);
        doc.setDrawColor(252, 211, 77);
        doc.rect(margin, cursorY, pageWidth - margin * 2, boxHeight, "FD");
        doc.setFont("helvetica", "bold");
        doc.setFontSize(10);
        doc.setTextColor(146, 64, 14);
        doc.text("Manual review recommended", margin + 10, cursorY + 16);
        doc.setFont("helvetica", "normal");
        doc.setFontSize(9);
        doc.text(reviewText, margin + 10, cursorY + 30, {
          maxWidth: pageWidth - margin * 2 - 20
        });
        cursorY += boxHeight + 14;
      }

      if (report.summary) {
        doc.setFont("helvetica", "normal");
        doc.setFontSize(10);
        doc.setTextColor(51, 65, 85);
        doc.text(report.summary, margin, cursorY, { maxWidth: pageWidth - margin * 2 });
        cursorY += 18;
      }

      if (hasIssues) {
        const body = report.issues.map((issue) => [
          issue.category,
          renderValue(issue.field),
          renderValue(issue.expected),
          renderValue(issue.found),
          renderValue(issue.page),
          issue.severity,
          issue.source ?? "model",
          renderConfidence(issue.confidence),
          issue.evidence && issue.evidence.length > 0 ? issue.evidence.join("; ") : "N/A",
          renderValue(issue.notes)
        ]);

        autoTable(doc, {
          startY: cursorY,
          head: [[
            "Category",
            "Field",
            "Expected",
            "Found",
            "Page",
            "Severity",
            "Source",
            "Confidence",
            "Evidence",
            "Notes"
          ]],
          body,
          styles: {
            fontSize: 8,
            cellPadding: 4,
            textColor: [15, 23, 42]
          },
          headStyles: {
            fillColor: [241, 245, 249],
            textColor: [71, 85, 105],
            fontStyle: "bold"
          },
          alternateRowStyles: {
            fillColor: [248, 250, 252]
          },
          margin: { left: margin, right: margin }
        });
      } else {
        doc.setFont("helvetica", "normal");
        doc.setFontSize(10);
        doc.setTextColor(51, 65, 85);
        doc.text("No discrepancies detected.", margin, cursorY);
      }

      const baseName = sanitizeFileName(documentName?.trim() || "audit-report") || "audit-report";
      doc.save(`ClearPass-${baseName}.pdf`);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to export the PDF report.";
      toast({
        variant: "destructive",
        title: "Export failed",
        description: message
      });
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
      <Card className="border-steel-200/80">
        <CardHeader className="gap-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <CardTitle>Audit report</CardTitle>
              <CardDescription>
                {documentName ? `Document: ${documentName}` : "Review detected discrepancies."}
              </CardDescription>
            </div>
            <Button size="sm" onClick={handleDownloadPdf} disabled={isExporting}>
              <FileDown className="h-4 w-4" />
              {isExporting ? "Preparing PDF" : "Download PDF"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="grid gap-4">
          {report.review_required ? (
            <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              <div className="flex items-center gap-2 font-semibold">
                <AlertTriangle className="h-4 w-4" />
                Manual review recommended
              </div>
              <div className="text-xs text-amber-800">
                {(report.review_reasons ?? []).length > 0
                  ? report.review_reasons?.join(" ")
                  : "High-risk discrepancies detected."}
              </div>
            </div>
          ) : null}

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-md border border-steel-100 bg-white px-4 py-3">
              <div className="text-xs uppercase tracking-wide text-steel-500">High risk</div>
              <div className="text-2xl font-semibold text-ink-900">{highCount}</div>
            </div>
            <div className="rounded-md border border-steel-100 bg-white px-4 py-3">
              <div className="text-xs uppercase tracking-wide text-steel-500">Medium risk</div>
              <div className="text-2xl font-semibold text-ink-900">{mediumCount}</div>
            </div>
            <div className="rounded-md border border-steel-100 bg-white px-4 py-3">
              <div className="text-xs uppercase tracking-wide text-steel-500">Low risk</div>
              <div className="text-2xl font-semibold text-ink-900">{lowCount}</div>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-md border border-steel-100 bg-steel-50 px-4 py-3 text-sm text-steel-700">
              Rule checks flagged: <span className="font-semibold text-ink-900">{ruleCount}</span>
            </div>
            <div className="rounded-md border border-steel-100 bg-steel-50 px-4 py-3 text-sm text-steel-700">
              Model findings: <span className="font-semibold text-ink-900">{modelCount}</span>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-steel-100 bg-steel-50 px-4 py-3 text-sm">
            <span className="text-steel-600">Status</span>
            <span className="font-semibold text-ink-900">
              {hasIssues ? `${report.issues.length} issues found` : "No issues found"}
            </span>
          </div>

          {report.summary ? (
            <div className="rounded-md border border-steel-100 bg-white px-4 py-3 text-sm text-steel-600">
              {report.summary}
            </div>
          ) : null}

          {hasIssues ? (
            <Table className="min-w-[820px]">
              <TableHeader>
                <TableRow>
                  <TableHead>Category</TableHead>
                  <TableHead>Field</TableHead>
                  <TableHead>Expected</TableHead>
                  <TableHead>Found</TableHead>
                  <TableHead>Page</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Evidence</TableHead>
                  <TableHead>Notes</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {report.issues.map((issue, index) => (
                  <TableRow key={`${issue.field}-${index}`}>
                    <TableCell className="capitalize">{issue.category}</TableCell>
                    <TableCell>{issue.field}</TableCell>
                    <TableCell>{renderValue(issue.expected)}</TableCell>
                    <TableCell>{renderValue(issue.found)}</TableCell>
                    <TableCell>{renderValue(issue.page)}</TableCell>
                    <TableCell className="capitalize">{issue.severity}</TableCell>
                    <TableCell className="capitalize">{issue.source ?? "model"}</TableCell>
                    <TableCell>{renderConfidence(issue.confidence)}</TableCell>
                    <TableCell className="max-w-[220px] text-xs text-steel-600">
                      {issue.evidence && issue.evidence.length > 0
                        ? issue.evidence.join("; ")
                        : "N/A"}
                    </TableCell>
                    <TableCell>{renderValue(issue.notes)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="rounded-md border border-steel-100 bg-white px-4 py-3 text-sm text-steel-600">
              No discrepancies detected. You can export this report or run another audit.
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
