"use client";

import { useState } from "react";
import { Report } from "@/components/report";
import type { AuditReport, AuditResponse } from "@/lib/types";

export function Checker() {
  const [url, setUrl] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<AuditReport | null>(null);

  async function run(target: string) {
    const next = target.trim();
    setUrl(next);
    setError(null);
    setReport(null);
    setPending(true);
    try {
      const response = await fetch("/api/audit", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ url: next }),
      });
      const data = (await response.json()) as AuditResponse;
      if (!data.ok) {
        setError(data.error || "The page could not be checked.");
        return;
      }
      setReport(data);
    } catch {
      setError("The check did not finish. Try the address again.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div>
      <form
        className="mt-10"
        onSubmit={(event) => {
          event.preventDefault();
          void run(url);
        }}
      >
        <label htmlFor="page-url" className="text-[11px] uppercase tracking-[0.1em] text-ink-55">
          Public page address
        </label>
        <div className="mt-3 flex flex-col gap-3 sm:flex-row">
          <input
            id="page-url"
            name="url"
            type="url"
            inputMode="url"
            autoComplete="url"
            required
            placeholder="https://example.com/page"
            value={url}
            disabled={pending}
            onChange={(event) => setUrl(event.target.value)}
            className="min-h-11 w-full rounded-xl border border-ink-10 bg-card px-4 text-base text-ink-100 outline-none placeholder:text-ink-40"
          />
          <button
            type="submit"
            disabled={pending}
            className="press-feedback inline-flex min-h-11 shrink-0 items-center justify-center rounded-xl bg-ink px-8 text-sm font-medium tracking-[0.1em] text-on-ink hover:bg-ink-soft disabled:opacity-60"
          >
            {pending ? "Reading" : "Check this page"}
          </button>
        </div>
      </form>
      <button
        type="button"
        className="press-feedback mt-4 min-h-11 text-sm tracking-[0.04em] text-ink-60 hover:text-ink-100"
        disabled={pending}
        onClick={() => void run("https://jslabs.xyz")}
      >
        Check jslabs.xyz
      </button>
      {error ? (
        <p role="alert" className="mt-6 max-w-xl text-sm leading-relaxed text-ink-100">
          {error}
        </p>
      ) : null}
      {pending ? <p className="mt-10 text-sm text-ink-55">Reading the page.</p> : null}
      {report ? <Report report={report} /> : null}
    </div>
  );
}
