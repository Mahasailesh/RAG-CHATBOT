"use client";

import * as React from "react";
import { ClipboardCheck, RefreshCw } from "lucide-react";

import { fetchReviewQueue, updateReviewItem } from "@/lib/api";
import type { ReviewItem, ReviewStatus } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/components/ui/use-toast";

const statusOptions: ReviewStatus[] = ["pending", "in_review", "resolved"];

export default function ReviewQueuePage() {
  const { toast } = useToast();
  const [token, setToken] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState<string | undefined>(undefined);
  const [items, setItems] = React.useState<ReviewItem[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [notes, setNotes] = React.useState<Record<string, string>>({});
  const [statuses, setStatuses] = React.useState<Record<string, ReviewStatus>>({});

  const loadQueue = async () => {
    setIsLoading(true);
    try {
      const data = await fetchReviewQueue({
        token: token.trim() || undefined,
        status: statusFilter,
        limit: 50
      });
      setItems(data);
      const nextNotes: Record<string, string> = {};
      const nextStatuses: Record<string, ReviewStatus> = {};
      data.forEach((item) => {
        if (item.id) {
          nextNotes[item.id] = item.reviewer_notes ?? "";
          nextStatuses[item.id] = item.status;
        }
      });
      setNotes(nextNotes);
      setStatuses(nextStatuses);
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Unable to load review queue",
        description: err instanceof Error ? err.message : "Review queue not available."
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdate = async (item: ReviewItem) => {
    if (!item.id) {
      return;
    }
    try {
      const updated = await updateReviewItem(
        item.id,
        {
          status: statuses[item.id] ?? item.status,
          reviewer_notes: notes[item.id] ?? ""
        },
        token.trim() || undefined
      );
      setItems((prev) => prev.map((entry) => (entry.id === updated.id ? updated : entry)));
      toast({
        title: "Review updated",
        description: `Status set to ${updated.status}.`
      });
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Update failed",
        description: err instanceof Error ? err.message : "Unable to update review."
      });
    }
  };

  return (
    <main className="min-h-screen px-6 pb-16 pt-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-8">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.3em] text-steel-500">
              Human review
            </div>
            <h1 className="mt-3 text-3xl font-semibold text-ink-950">
              Manual review queue
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-steel-600">
              Review high-risk audits, capture reviewer notes, and resolve discrepancies.
            </p>
          </div>
        </header>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ClipboardCheck className="h-5 w-5 text-trust-600" />
              Access
            </CardTitle>
            <CardDescription>
              Provide the review token if required by the server.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-3">
            <div className="grid gap-2">
              <Label htmlFor="reviewToken">Review token</Label>
              <Input
                id="reviewToken"
                type="password"
                value={token}
                onChange={(event) => setToken(event.target.value)}
                placeholder="Optional token"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="statusFilter">Status filter</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger id="statusFilter">
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pending">pending</SelectItem>
                  <SelectItem value="in_review">in_review</SelectItem>
                  <SelectItem value="resolved">resolved</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button onClick={loadQueue} disabled={isLoading} className="w-full">
                <RefreshCw className="h-4 w-4" />
                {isLoading ? "Loading" : "Load queue"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <section className="grid gap-4">
          {items.length === 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>No review items</CardTitle>
                <CardDescription>Load the queue to see pending reviews.</CardDescription>
              </CardHeader>
            </Card>
          ) : (
            items.map((item) => (
              <Card key={item.id ?? item.document_id}>
                <CardHeader>
                  <CardTitle>Document {item.document_id ?? "unknown"}</CardTitle>
                  <CardDescription>
                    Status: {item.status} | Risk score: {item.risk_score ?? "N/A"}
                  </CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4">
                  <div className="grid gap-2 md:grid-cols-2">
                    <div className="rounded-md border border-steel-100 bg-white px-4 py-3 text-sm text-steel-600">
                      Issues: {item.issues.length} | Confidence: {item.confidence_avg ?? "N/A"}
                    </div>
                    <div className="rounded-md border border-steel-100 bg-white px-4 py-3 text-sm text-steel-600">
                      Reasons: {(item.review_reasons ?? []).join(" ") || "N/A"}
                    </div>
                  </div>

                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="grid gap-2">
                      <Label>Status</Label>
                      <Select
                        value={statuses[item.id ?? ""] ?? item.status}
                        onValueChange={(value) =>
                          setStatuses((prev) => ({
                            ...prev,
                            [item.id ?? ""]: value as ReviewStatus
                          }))
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {statusOptions.map((status) => (
                            <SelectItem key={status} value={status}>
                              {status}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid gap-2 md:col-span-2">
                      <Label>Reviewer notes</Label>
                      <Input
                        value={notes[item.id ?? ""] ?? ""}
                        onChange={(event) =>
                          setNotes((prev) => ({
                            ...prev,
                            [item.id ?? ""]: event.target.value
                          }))
                        }
                        placeholder="Add notes for this review"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <Button variant="secondary" onClick={() => handleUpdate(item)}>
                      Save review
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </section>
      </div>
    </main>
  );
}
