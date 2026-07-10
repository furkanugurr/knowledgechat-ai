import type { CitationSource } from "../types/chat";
import { formatSimilarity } from "../utils/formatSimilarity";

interface SourceListProps {
  sources: CitationSource[];
}

export function SourceList({ sources }: SourceListProps) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <details className="source-disclosure mt-4 overflow-hidden rounded-xl border border-slate-200 bg-slate-50/80">
      <summary className="flex cursor-pointer select-none items-center gap-2 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ocean-500">
        <svg
          aria-hidden="true"
          className="source-chevron size-4 shrink-0 text-slate-400 transition-transform"
          fill="none"
          viewBox="0 0 24 24"
        >
          <path
            d="m6 9 6 6 6-6"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
          />
        </svg>
        <span>Kaynaklar</span>
        <span className="rounded-full bg-ocean-100 px-2 py-0.5 text-xs font-bold text-ocean-700">
          {sources.length}
        </span>
      </summary>
      <ul className="border-t border-slate-200 px-3">
        {sources.map((source) => (
          <li
            className="min-w-0 border-t border-slate-200 py-2.5 first:border-t-0"
            key={`${source.relative_path}:${source.section_title}:${source.chunk_index}`}
          >
            <div className="flex min-w-0 items-center gap-3">
              <p
                className="min-w-0 flex-1 truncate text-sm font-semibold text-ink"
                title={source.document_name}
              >
                {source.document_name}
              </p>
              <span className="shrink-0 text-xs font-bold text-ocean-700">
                {formatSimilarity(source.similarity_score)}
              </span>
            </div>
            <div className="mt-1 flex min-w-0 items-center gap-2 text-xs text-slate-500">
              <span
                className="min-w-0 flex-1 truncate"
                title={source.section_title ?? "Bölüm belirtilmemiş"}
              >
                {source.section_title ?? "Bölüm belirtilmemiş"}
              </span>
              <span aria-hidden="true" className="text-slate-300">
                •
              </span>
              <span className="shrink-0">Chunk {source.chunk_index}</span>
            </div>
          </li>
        ))}
      </ul>
    </details>
  );
}
