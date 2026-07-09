import { useEffect, useRef, type ReactNode } from "react";

interface ChatLayoutProps {
  children: ReactNode;
  error: ReactNode;
  input: ReactNode;
}

export function ChatLayout({
  children,
  error,
  input,
}: ChatLayoutProps) {
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [children]);

  return (
    <main className="min-h-screen bg-mist px-3 py-3 sm:px-6 sm:py-6">
      <section className="mx-auto flex h-[calc(100vh-1.5rem)] max-w-5xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-panel sm:h-[calc(100vh-3rem)] sm:rounded-3xl">
        <header className="border-b border-slate-200 bg-white px-5 py-5 sm:px-8">
          <div className="flex items-center gap-4">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-ocean-600 font-black text-white">
              K
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-ink sm:text-2xl">
                KnowledgeChat AI
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                Your local RAG-powered knowledge assistant
              </p>
            </div>
          </div>
        </header>
        {error}
        <div
          aria-live="polite"
          className="flex-1 space-y-5 overflow-y-auto bg-slate-50/70 p-4 sm:p-8"
        >
          {children}
          <div ref={endOfMessagesRef} />
        </div>
        {input}
      </section>
    </main>
  );
}
