"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { AlertCircle, Lock, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/components/ui/use-toast";
import { ReportDashboard } from "@/components/report-dashboard";
import { UploadZone } from "@/components/upload-zone";
import { auditDocument } from "@/lib/api";
import { getProviderOptions } from "@/lib/providers";
import type { AuditReport, ExtractedDocument } from "@/lib/types";

export function AuditWorkspace() {
  const { toast } = useToast();
  const providers = React.useMemo(() => getProviderOptions(), []);
  const [extracted, setExtracted] = React.useState<ExtractedDocument | null>(null);
  const [report, setReport] = React.useState<AuditReport | null>(null);
  const [isAuditing, setIsAuditing] = React.useState(false);
  const [provider, setProvider] = React.useState(providers[0]?.value ?? "gemini");
  const [model, setModel] = React.useState("");
  const [apiKey, setApiKey] = React.useState("");
  const [retrievalK, setRetrievalK] = React.useState("");

  const resetAll = () => {
    setExtracted(null);
    setReport(null);
  };

  const handleExtracted = (document: ExtractedDocument) => {
    setExtracted(document);
    setReport(null);
  };

  React.useEffect(() => {
    if (providers.length > 0 && !providers.find((item) => item.value === provider)) {
      setProvider(providers[0].value);
    }
  }, [providers, provider]);

  const handleError = (message: string) => {
    toast({
      variant: "destructive",
      title: "Action required",
      description: message
    });
  };

  const handleAudit = async () => {
    if (!extracted) {
      return;
    }
    if (retrievalK) {
      const parsed = Number(retrievalK);
      if (Number.isNaN(parsed) || parsed < 1 || parsed > 20) {
        handleError("Retrieval depth must be between 1 and 20.");
        return;
      }
    }
    setIsAuditing(true);
    try {
      const response = await auditDocument(
        {
          document_id: extracted.documentId,
          pages: extracted.pages,
          provider,
          model: model.trim() || undefined,
          retrieval_k: retrievalK ? Number(retrievalK) : undefined
        },
        { byokKey: apiKey.trim() || undefined }
      );
      setReport(response);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Audit failed.";
      handleError(message);
    } finally {
      setIsAuditing(false);
    }
  };

  return (
    <section id="audit" className="mt-16">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.3em] text-steel-500">
            Audit workspace
          </div>
          <h2 className="mt-3 text-3xl font-semibold text-ink-950">Run a secure audit</h2>
          <p className="mt-2 max-w-xl text-sm text-steel-600">
            Upload a PDF, pick your AI provider, and receive a structured discrepancy report
            without storing files or raw text.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-steel-200 bg-white/70 px-4 py-2 text-xs text-steel-600">
          <AlertCircle className="h-4 w-4 text-trust-600" />
          Zero-retention processing enforced.
        </div>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.2fr,0.8fr]">
        <div className="grid gap-6">
          <UploadZone
            extracted={extracted}
            onExtracted={handleExtracted}
            onError={handleError}
            onReset={resetAll}
            disabled={isAuditing}
          />

          {report ? (
            <ReportDashboard report={report} documentName={extracted?.fileName} />
          ) : (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
              <Card className="border-steel-200/80">
                <CardHeader>
                  <CardTitle>Audit results</CardTitle>
                  <CardDescription>
                    {isAuditing
                      ? "Audit in progress. Results will appear here."
                      : "Upload a document and run an audit to see discrepancies here."}
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-sm text-steel-600">
                  {isAuditing
                    ? "The document is being analyzed for inconsistencies."
                    : "Once the audit completes, the report will list mismatched dates, names, and financial figures across pages."}
                </CardContent>
              </Card>
            </motion.div>
          )}
        </div>

        <div className="grid gap-6 lg:sticky lg:top-24 h-fit">
          <Card className="border-steel-200/80">
            <CardHeader>
              <CardTitle>Provider settings</CardTitle>
              <CardDescription>Choose an AI provider and optional model.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="grid gap-2">
                  <Label htmlFor="provider">Provider</Label>
                  <Select value={provider} onValueChange={setProvider}>
                    <SelectTrigger id="provider">
                      <SelectValue placeholder="Select provider" />
                    </SelectTrigger>
                    <SelectContent>
                      {providers.map((item) => (
                        <SelectItem key={item.value} value={item.value}>
                          {item.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="model">Model (optional)</Label>
                  <Input
                    id="model"
                    placeholder="Optional model override"
                    value={model}
                    onChange={(event) => setModel(event.target.value)}
                  />
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="retrievalK">Retrieval depth (optional)</Label>
                <Input
                  id="retrievalK"
                  type="number"
                  min={1}
                  max={20}
                  placeholder="Defaults to 5"
                  value={retrievalK}
                  onChange={(event) => setRetrievalK(event.target.value)}
                />
                <div className="text-xs text-steel-500">
                  Higher values retrieve more reference chunks but may increase latency.
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="apiKey">Bring your own API key (optional)</Label>
                <Input
                  id="apiKey"
                  type="password"
                  placeholder="Used only for this request"
                  value={apiKey}
                  onChange={(event) => setApiKey(event.target.value)}
                />
              </div>
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-steel-100 bg-steel-50 px-4 py-3 text-xs text-steel-600">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-trust-600" />
                  API keys are never stored or logged.
                </div>
                <div>BYOK must be enabled on the server.</div>
              </div>
              <Button className="w-full" disabled={!extracted || isAuditing} onClick={handleAudit}>
                {isAuditing ? "Running audit" : "Run audit"}
              </Button>
            </CardContent>
          </Card>

          <Card className="border-steel-200/80">
            <CardHeader>
              <CardTitle>Data retention</CardTitle>
              <CardDescription>How your data is handled during analysis.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-2 text-sm text-steel-600">
              <div>PDF files remain in your browser.</div>
              <div>Only extracted text is sent to the server for audit.</div>
              <div>Audit text is processed in memory and not stored.</div>
              <div>Reference knowledge base content is stored separately for retrieval.</div>
            </CardContent>
          </Card>

          <Card className="border-steel-200/80">
            <CardHeader>
              <CardTitle>Operational safeguards</CardTitle>
              <CardDescription>Controls that protect user data end to end.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 text-sm text-steel-600">
              <div className="flex items-start gap-2">
                <ShieldCheck className="mt-0.5 h-4 w-4 text-trust-600" />
                Zero-retention policy enforced at the API boundary.
              </div>
              <div className="flex items-start gap-2">
                <Lock className="mt-0.5 h-4 w-4 text-trust-600" />
                BYOK supported for tenant-controlled model access.
              </div>
              <div className="flex items-start gap-2">
                <AlertCircle className="mt-0.5 h-4 w-4 text-trust-600" />
                Automated discrepancy flags require human review for high-risk cases.
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
