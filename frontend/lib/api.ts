import type {
  AccuracyReport,
  AuditReport,
  AuditRequest,
  MetricsSnapshot,
  ReviewItem,
  ReviewUpdate
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function auditDocument(
  payload: AuditRequest,
  options?: { byokKey?: string }
): Promise<AuditReport> {
  const response = await fetch(`${API_BASE_URL}/api/audit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(options?.byokKey ? { "X-Provider-Api-Key": options.byokKey } : {})
    },
    body: JSON.stringify(payload),
    cache: "no-store"
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.detail ?? "Audit request failed.";
    throw new Error(message);
  }
  return data as AuditReport;
}

export async function fetchMetrics(): Promise<MetricsSnapshot> {
  const response = await fetch(`${API_BASE_URL}/api/metrics`, {
    cache: "no-store"
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.detail ?? "Metrics not available.";
    throw new Error(message);
  }
  return data as MetricsSnapshot;
}

export async function fetchAccuracy(): Promise<AccuracyReport> {
  const response = await fetch(`${API_BASE_URL}/api/accuracy`, {
    cache: "no-store"
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.detail ?? "Accuracy report not available.";
    throw new Error(message);
  }
  return data as AccuracyReport;
}

export async function fetchReviewQueue(options?: {
  token?: string;
  status?: string;
  limit?: number;
}): Promise<ReviewItem[]> {
  const params = new URLSearchParams();
  if (options?.status) {
    params.set("status", options.status);
  }
  if (options?.limit) {
    params.set("limit", options.limit.toString());
  }
  const response = await fetch(`${API_BASE_URL}/api/review?${params.toString()}`, {
    cache: "no-store",
    headers: {
      ...(options?.token ? { "X-Review-Token": options.token } : {})
    }
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.detail ?? "Review queue not available.";
    throw new Error(message);
  }
  return data as ReviewItem[];
}

export async function updateReviewItem(
  reviewId: string,
  payload: ReviewUpdate,
  token?: string
): Promise<ReviewItem> {
  const response = await fetch(`${API_BASE_URL}/api/review/${reviewId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "X-Review-Token": token } : {})
    },
    body: JSON.stringify(payload),
    cache: "no-store"
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.detail ?? "Unable to update review.";
    throw new Error(message);
  }
  return data as ReviewItem;
}
