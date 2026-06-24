import type { CitationItem } from "@/lib/api";

export function CitationBadge({ citation }: { citation: CitationItem }) {
  const ticker = String(citation.metadata.ticker ?? "DOC");
  const form = String(citation.metadata.form_type ?? citation.metadata.form ?? "filing");
  const date = String(citation.metadata.filing_date ?? "");

  return (
    <details className="rounded-lg border border-[var(--border)] bg-[var(--background)] p-3 text-sm">
      <summary className="cursor-pointer font-medium">
        {citation.label ?? "Source"} · {ticker} {form} {date}
      </summary>
      <p className="mt-2 text-[var(--muted)] whitespace-pre-wrap">{citation.excerpt}</p>
    </details>
  );
}
