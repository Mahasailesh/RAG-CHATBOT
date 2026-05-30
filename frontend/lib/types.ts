export type Discrepancy = {
  category: "name" | "date" | "financial" | "other";
  field: string;
  expected?: string | null;
  found?: string | null;
  page?: number | null;
  severity: "low" | "medium" | "high";
  notes?: string | null;
  source?: "model" | "rule" | null;
  evidence?: string[] | null;
  confidence?: number | null;
};

export type AuditReport = {
  document_id?: string | null;
  status: "ok" | "issues_found" | "error";
  issues: Discrepancy[];
  summary?: string | null;
  review_required?: boolean;
  review_reasons?: string[];
};

export type AuditRequest = {
  document_id?: string | null;
  pages: Record<number, string>;
  provider?: string;
  model?: string | null;
  retrieval_k?: number;
};

export type ExtractedDocument = {
  documentId?: string | null;
  fileName: string;
  pageCount: number;
  pages: Record<number, string>;
};

export type AccuracyReport = {
  tp: number;
  fp: number;
  fn: number;
  precision: number;
  recall: number;
  updated_at?: string | null;
};

export type MetricsSnapshot = Record<string, number>;

export type ReviewStatus = "pending" | "in_review" | "resolved";

export type ReviewItem = {
  id?: string | null;
  document_id?: string | null;
  provider?: string | null;
  status: ReviewStatus;
  summary?: string | null;
  issues: Discrepancy[];
  review_required?: boolean;
  review_reasons?: string[];
  risk_score?: number | null;
  confidence_avg?: number | null;
  reviewer_notes?: string | null;
  tenant_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type ReviewUpdate = {
  status?: ReviewStatus;
  reviewer_notes?: string | null;
};
