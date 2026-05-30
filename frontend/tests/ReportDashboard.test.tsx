import { render, screen } from "@testing-library/react";

import { ReportDashboard } from "@/components/report-dashboard";
import { ToastStateProvider } from "@/components/ui/toaster";
import type { AuditReport } from "@/lib/types";

describe("ReportDashboard", () => {
  it("renders a table of discrepancies", () => {
    const report: AuditReport = {
      status: "issues_found",
      issues: [
        {
          category: "name",
          field: "applicant_name",
          expected: "Alex Carter",
          found: "Alex Karter",
          page: 1,
          severity: "high",
          notes: "Spelling mismatch"
        }
      ],
      summary: "One mismatch detected."
    };

    render(
      <ToastStateProvider>
        <ReportDashboard report={report} documentName="sample.pdf" />
      </ToastStateProvider>
    );

    expect(screen.getByText("1 issues found")).toBeInTheDocument();
    expect(screen.getByText("applicant_name")).toBeInTheDocument();
    expect(screen.getByText("Alex Carter")).toBeInTheDocument();
    expect(screen.getByText("Alex Karter")).toBeInTheDocument();
  });
});
