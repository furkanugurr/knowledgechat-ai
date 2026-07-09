import type { CitationSource } from "../types/chat";
import { formatSimilarity } from "../utils/formatSimilarity";

interface SourceListProps {
  sources: CitationSource[];
}

export function SourceList({ sources }: SourceListProps) {
  if (sources.length === 0) {
    return (
      <p className="mt-4 text-sm text-slate-500">No sources found.</p>
    );
  }

  return (
    <section className="mt-5 border-t border-slate-200 pt-4">
      <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500">
        Sources
      </h3>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        {sources.map((source) => (
          <article
            className="rounded-xl border border-slate-200 bg-slate-50 p-3"
            key={`${source.relative_path}:${source.section_title}:${source.chunk_index}`}
          >
            <div className="flex items-start justify-between gap-3">
              <p className="font-semibold text-ink">
                {source.document_name}
              </p>
              <span className="shrink-0 rounded-full bg-ocean-100 px-2 py-1 text-xs font-bold text-ocean-700">
                {formatSimilarity(source.similarity_score)}
              </span>
            </div>
            <p className="mt-1 break-all text-xs text-slate-500">
              {source.relative_path}
            </p>
            <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 text-xs">
              <dt className="text-slate-500">Section</dt>
              <dd className="text-right text-slate-700">
                {source.section_title ?? "Not specified"}
              </dd>
              <dt className="text-slate-500">Chunk</dt>
              <dd className="text-right text-slate-700">
                {source.chunk_index}
              </dd>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}
