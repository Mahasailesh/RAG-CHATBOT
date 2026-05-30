"use client";

import * as React from "react";
import { AlertTriangle, BarChart3, ClipboardCheck, Gauge } from "lucide-react";

import { fetchAccuracy, fetchMetrics } from "@/lib/api";
import type { AccuracyReport, MetricsSnapshot } from "@/lib/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const formatPercent = (value: number) => `${Math.round(value * 100)}%`;

export default function AccuracyPage() {
  const [metrics, setMetrics] = React.useState<MetricsSnapshot | null>(null);
  const [accuracy, setAccuracy] = React.useState<AccuracyReport | null>(null);
  const [metricsError, setMetricsError] = React.useState<string | null>(null);
  const [accuracyError, setAccuracyError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let active = true;
    const load = async () => {
      const [metricsResult, accuracyResult] = await Promise.allSettled([
        fetchMetrics(),
        fetchAccuracy()
      ]);

      if (!active) {
        return;
      }

      if (metricsResult.status === "fulfilled") {
        setMetrics(metricsResult.value);
      } else {
        setMetricsError(
          metricsResult.reason instanceof Error
            ? metricsResult.reason.message
            : "Metrics not available."
        );
      }

      if (accuracyResult.status === "fulfilled") {
        setAccuracy(accuracyResult.value);
      } else {
        setAccuracyError(
          accuracyResult.reason instanceof Error
            ? accuracyResult.reason.message
            : "Accuracy report not available."
        );
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, []);

  const providerBreakdown = React.useMemo(() => {
    if (!metrics) {
      return [] as Array<[string, number]>;
    }
    return Object.entries(metrics)
      .filter(([key]) => key.startsWith("provider:"))
      .map(([key, value]) => [key.replace("provider:", ""), value])
      .sort((a, b) => b[1] - a[1]);
  }, [metrics]);

  return (
    <main className="min-h-screen px-6 pb-16 pt-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-8">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.3em] text-steel-500">
              Accuracy dashboard
            </div>
            <h1 className="mt-3 text-3xl font-semibold text-ink-950">
              Audit accuracy and operational metrics
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-steel-600">
              This view summarizes live audit activity and the latest benchmark run. Enable
              metrics and run the benchmark script to populate these cards.
            </p>
          </div>
        </header>

        {metricsError || accuracyError ? (
          <Card className="border-amber-200 bg-amber-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-amber-900">
                <AlertTriangle className="h-5 w-5" />
                Data unavailable
              </CardTitle>
              <CardDescription className="text-amber-800">
                {[metricsError, accuracyError].filter(Boolean).join(" ")}
              </CardDescription>
            </CardHeader>
          </Card>
        ) : null}

        <section className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-trust-600" />
                Operational metrics
              </CardTitle>
              <CardDescription>Live counters from the audit API.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-md border border-steel-100 bg-white px-4 py-3">
                  <div className="text-xs uppercase tracking-wide text-steel-500">Requests</div>
                  <div className="text-2xl font-semibold text-ink-900">
                    {metrics?.requests_total ?? "N/A"}
                  </div>
                </div>
                <div className="rounded-md border border-steel-100 bg-white px-4 py-3">
                  <div className="text-xs uppercase tracking-wide text-steel-500">Issues</div>
                  <div className="text-2xl font-semibold text-ink-900">
                    {metrics?.issues_total ?? "N/A"}
                  </div>
                </div>
                <div className="rounded-md border border-steel-100 bg-white px-4 py-3">
                  <div className="text-xs uppercase tracking-wide text-steel-500">Review required</div>
                  <div className="text-2xl font-semibold text-ink-900">
                    {metrics?.review_required_total ?? "N/A"}
                  </div>
                </div>
                <div className="rounded-md border border-steel-100 bg-white px-4 py-3">
                  <div className="text-xs uppercase tracking-wide text-steel-500">High severity</div>
                  <div className="text-2xl font-semibold text-ink-900">
                    {metrics?.high_severity_total ?? "N/A"}
                  </div>
                </div>
              </div>

              {providerBreakdown.length > 0 ? (
                <div className="rounded-md border border-steel-100 bg-steel-50 px-4 py-3 text-sm text-steel-700">
                  <div className="text-xs uppercase tracking-wide text-steel-500">Provider mix</div>
                  <div className="mt-2 flex flex-wrap gap-3">
                    {providerBreakdown.map(([provider, count]) => (
                      <div key={provider} className="rounded-full border border-steel-200 bg-white px-3 py-1 text-xs">
                        {provider}: {count}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ClipboardCheck className="h-5 w-5 text-trust-600" />
                Benchmark accuracy
              </CardTitle>
              <CardDescription>Most recent evaluation run.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-md border border-steel-100 bg-white px-4 py-3">
                  <div className="text-xs uppercase tracking-wide text-steel-500">Precision</div>
                  <div className="text-2xl font-semibold text-ink-900">
                    {accuracy ? formatPercent(accuracy.precision) : "N/A"}
                  </div>
                </div>
                <div className="rounded-md border border-steel-100 bg-white px-4 py-3">
                  <div className="text-xs uppercase tracking-wide text-steel-500">Recall</div>
                  <div className="text-2xl font-semibold text-ink-900">
                    {accuracy ? formatPercent(accuracy.recall) : "N/A"}
                  </div>
                </div>
                <div className="rounded-md border border-steel-100 bg-white px-4 py-3">
                  <div className="text-xs uppercase tracking-wide text-steel-500">True positives</div>
                  <div className="text-2xl font-semibold text-ink-900">
                    {accuracy?.tp ?? "N/A"}
                  </div>
                </div>
                <div className="rounded-md border border-steel-100 bg-white px-4 py-3">
                  <div className="text-xs uppercase tracking-wide text-steel-500">False positives</div>
                  <div className="text-2xl font-semibold text-ink-900">
                    {accuracy?.fp ?? "N/A"}
                  </div>
                </div>
              </div>

              <div className="rounded-md border border-steel-100 bg-steel-50 px-4 py-3 text-sm text-steel-700">
                <div className="flex items-center gap-2">
                  <Gauge className="h-4 w-4 text-trust-600" />
                  {accuracy?.updated_at
                    ? `Last updated: ${accuracy.updated_at}`
                    : "Run the benchmark to populate accuracy metrics."}
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  );
}
