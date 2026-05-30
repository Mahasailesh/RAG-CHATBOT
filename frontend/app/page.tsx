"use client";

import { motion } from "framer-motion";
import { FileSearch, Lock, ShieldCheck, Sparkles } from "lucide-react";

import { AuditWorkspace } from "@/components/audit-workspace";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const metrics = [
  {
    label: "Files stored",
    value: "0",
    detail: "Zero retention by design"
  },
  {
    label: "Client-side extraction",
    value: "100%",
    detail: "PDFs never leave the browser"
  },
  {
    label: "Audit output",
    value: "Strict JSON",
    detail: "Schema-first discrepancy report"
  }
];

const workflow = [
  {
    step: "01",
    title: "Extract locally",
    description: "PDF text is mapped by page in the browser.",
    icon: FileSearch
  },
  {
    step: "02",
    title: "Audit with your provider",
    description: "Run a secure analysis using your preferred AI model.",
    icon: Sparkles
  },
  {
    step: "03",
    title: "Review discrepancies",
    description: "Receive a structured JSON report for manual review.",
    icon: ShieldCheck
  }
];

const trustPillars = [
  {
    title: "Zero-retention verification",
    description: "Text is processed in memory only. No storage, no logging.",
    icon: ShieldCheck
  },
  {
    title: "Client-side extraction",
    description: "PDFs stay in the browser. Only page-mapped text is sent.",
    icon: FileSearch
  },
  {
    title: "Provider freedom",
    description: "Choose Gemini or bring your own key for approved providers.",
    icon: Sparkles
  }
];

const fadeUp = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0 }
};

export default function HomePage() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute -left-32 top-[-140px] h-[360px] w-[360px] rounded-full bg-trust-500/20 blur-3xl" />
        <div className="absolute right-[-140px] top-[120px] h-[300px] w-[300px] rounded-full bg-ink-900/10 blur-3xl" />
        <div className="absolute inset-0 bg-[radial-gradient(rgba(148,163,184,0.35)_1px,transparent_1px)] [background-size:28px_28px] opacity-30" />
      </div>

      <div className="relative mx-auto flex min-h-screen max-w-7xl flex-col gap-14 px-6 pb-20 pt-10">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div className="text-sm font-semibold uppercase tracking-[0.2em] text-steel-500">
            ClearPass AI
          </div>
          <nav className="hidden items-center gap-6 text-sm text-steel-600 md:flex">
            <a href="#security" className="transition hover:text-ink-900">
              Security
            </a>
            <a href="#audit" className="transition hover:text-ink-900">
              Audit workspace
            </a>
            <a href="#trust" className="transition hover:text-ink-900">
              Trust center
            </a>
            <a href="/accuracy" className="transition hover:text-ink-900">
              Accuracy
            </a>
            <a href="/review" className="transition hover:text-ink-900">
              Review
            </a>
          </nav>
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="secondary">Trust center</Button>
            <Button>Request access</Button>
          </div>
        </header>

        <section className="grid gap-10 lg:grid-cols-[1.2fr,0.8fr] lg:items-center">
          <motion.div
            initial="hidden"
            animate="visible"
            transition={{ duration: 0.4 }}
            variants={fadeUp}
          >
            <div className="inline-flex items-center gap-2 rounded-full border border-steel-200 bg-white/70 px-4 py-2 text-xs text-steel-600">
              <Lock className="h-4 w-4 text-trust-600" />
              Privacy-first auditing for immigration workflows.
            </div>
            <h1 className="mt-5 text-4xl font-semibold leading-tight text-ink-950 md:text-5xl">
              Enterprise-grade document audits with uncompromising privacy.
            </h1>
            <p className="mt-4 text-lg text-steel-600">
              ClearPass AI extracts text locally, analyzes inconsistencies with your chosen
              provider, and returns a strict JSON discrepancy report in seconds.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button onClick={() => document.getElementById("audit")?.scrollIntoView({ behavior: "smooth" })}>
                Start a new audit
              </Button>
              <Button variant="outline">View security posture</Button>
            </div>
          </motion.div>

          <motion.div
            initial="hidden"
            animate="visible"
            transition={{ duration: 0.4, delay: 0.15 }}
            variants={fadeUp}
            className="grid gap-4"
          >
            <Card className="border-steel-200/80 bg-white/95">
              <CardHeader>
                <CardTitle>Audit readiness snapshot</CardTitle>
                <CardDescription>Real-time checks you can expect.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 text-sm">
                <div className="flex items-start justify-between border-b border-steel-100 pb-3">
                  <span className="text-steel-600">Applicant name match</span>
                  <span className="font-semibold text-ink-900">Checked</span>
                </div>
                <div className="flex items-start justify-between border-b border-steel-100 pb-3">
                  <span className="text-steel-600">Date consistency</span>
                  <span className="font-semibold text-ink-900">Auto-flagged</span>
                </div>
                <div className="flex items-start justify-between">
                  <span className="text-steel-600">Financial evidence</span>
                  <span className="font-semibold text-ink-900">Verified</span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-steel-200/80 bg-white/95">
              <CardHeader>
                <CardTitle>Privacy posture</CardTitle>
                <CardDescription>Controls that keep client data protected.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 text-sm text-steel-600">
                <div className="flex items-start gap-2">
                  <ShieldCheck className="mt-0.5 h-4 w-4 text-trust-600" />
                  Zero-retention processing with in-memory text handling.
                </div>
                <div className="flex items-start gap-2">
                  <FileSearch className="mt-0.5 h-4 w-4 text-trust-600" />
                  Client-side PDF parsing keeps files off the network.
                </div>
                <div className="flex items-start gap-2">
                  <Lock className="mt-0.5 h-4 w-4 text-trust-600" />
                  BYOK support for regulated environments.
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          {metrics.map((metric, index) => (
            <motion.div
              key={metric.label}
              initial="hidden"
              animate="visible"
              transition={{ duration: 0.35, delay: 0.1 + index * 0.1 }}
              variants={fadeUp}
            >
              <Card className="border-steel-200/80">
                <CardHeader>
                  <CardDescription className="text-xs uppercase tracking-[0.2em] text-steel-500">
                    {metric.label}
                  </CardDescription>
                  <CardTitle className="text-2xl">{metric.value}</CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-steel-600">
                  {metric.detail}
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </section>

        <section id="security" className="grid gap-10 lg:grid-cols-[0.9fr,1.1fr]">
          <motion.div
            initial="hidden"
            animate="visible"
            transition={{ duration: 0.4 }}
            variants={fadeUp}
          >
            <div className="text-xs font-semibold uppercase tracking-[0.3em] text-steel-500">
              Security by design
            </div>
            <h2 className="mt-4 text-3xl font-semibold text-ink-950">
              Privacy-first workflows for high-stakes documentation.
            </h2>
            <p className="mt-3 text-sm text-steel-600">
              Every audit step is built to protect sensitive immigration records. The system
              enforces zero retention, transparent provider selection, and structured outputs
              so teams can act quickly and confidently.
            </p>
            <div className="mt-6 grid gap-4">
              {trustPillars.map((feature) => {
                const Icon = feature.icon;
                return (
                  <div key={feature.title} className="flex items-start gap-3">
                    <div className="mt-1 rounded-full border border-steel-200 bg-white p-2">
                      <Icon className="h-4 w-4 text-trust-600" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-ink-900">{feature.title}</div>
                      <div className="text-sm text-steel-600">{feature.description}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>

          <div className="grid gap-4">
            {workflow.map((step, index) => {
              const Icon = step.icon;
              return (
                <motion.div
                  key={step.title}
                  initial="hidden"
                  animate="visible"
                  transition={{ duration: 0.35, delay: 0.2 + index * 0.1 }}
                  variants={fadeUp}
                >
                  <Card className="border-steel-200/80">
                    <CardHeader className="flex-row items-center justify-between">
                      <div>
                        <CardDescription className="text-xs uppercase tracking-[0.2em] text-steel-500">
                          Step {step.step}
                        </CardDescription>
                        <CardTitle className="mt-2 text-lg">{step.title}</CardTitle>
                      </div>
                      <div className="rounded-full border border-steel-200 bg-white p-3">
                        <Icon className="h-5 w-5 text-trust-600" />
                      </div>
                    </CardHeader>
                    <CardContent className="text-sm text-steel-600">
                      {step.description}
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </section>

        <AuditWorkspace />

        <section id="trust" className="grid gap-6 rounded-2xl border border-steel-200 bg-white/80 p-8">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.3em] text-steel-500">
              Trust center
            </div>
            <h2 className="mt-3 text-2xl font-semibold text-ink-950">
              Keep applicants informed and protected.
            </h2>
            <p className="mt-2 text-sm text-steel-600">
              ClearPass AI keeps sensitive documents in the browser and gives teams full
              control over provider selection and audit scope.
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-lg border border-steel-200 bg-white px-4 py-3 text-sm text-steel-600">
              Zero retention enforced for uploaded text.
            </div>
            <div className="rounded-lg border border-steel-200 bg-white px-4 py-3 text-sm text-steel-600">
              Optional BYOK support for regulated environments.
            </div>
            <div className="rounded-lg border border-steel-200 bg-white px-4 py-3 text-sm text-steel-600">
              Structured JSON outputs for auditability.
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
