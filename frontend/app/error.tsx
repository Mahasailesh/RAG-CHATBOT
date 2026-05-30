"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/button";

export default function ErrorPage({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    return () => {};
  }, []);

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-2xl font-semibold text-ink-900">Something went wrong</h1>
      <p className="text-sm text-steel-600">
        Please try again. If the issue persists, contact your system administrator.
      </p>
      <Button onClick={reset}>Try again</Button>
    </main>
  );
}
