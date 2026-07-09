export function LoadingIndicator() {
  return (
    <div
      aria-label="KnowledgeChat AI is preparing a response"
      className="flex justify-start"
      role="status"
    >
      <div className="flex items-center gap-3 rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 shadow-sm">
        <span className="h-2 w-2 animate-pulse rounded-full bg-ocean-500" />
        <span className="text-sm text-slate-600">
          Searching the knowledge base...
        </span>
      </div>
    </div>
  );
}
