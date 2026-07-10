import ReactMarkdown from "react-markdown";

import type { ChatMessage } from "../types/chat";
import { SourceList } from "./SourceList";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const assistantContent = message.content.trim();

  return (
    <article
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[92%] rounded-2xl px-4 py-3 sm:max-w-[82%] sm:px-5 ${
          isUser
            ? "rounded-br-md bg-ocean-600 text-white"
            : "rounded-bl-md border border-slate-200 bg-white text-ink shadow-sm"
        }`}
      >
        <p
          className={`mb-2 text-xs font-bold uppercase tracking-wider ${
            isUser ? "text-ocean-100" : "text-ocean-700"
          }`}
        >
          {isUser ? "You" : "KnowledgeChat AI"}
        </p>
        {isUser ? (
          <p className="whitespace-pre-wrap leading-7">{message.content}</p>
        ) : (
          <>
            {assistantContent ? (
              <div
                className="markdown-content break-words text-slate-700"
                data-testid="assistant-response"
              >
                <ReactMarkdown>{assistantContent}</ReactMarkdown>
              </div>
            ) : (
              <p
                className="leading-7 text-slate-500"
                data-testid="assistant-response"
              >
                No answer text was returned.
              </p>
            )}
            <SourceList sources={message.sources ?? []} />
          </>
        )}
      </div>
    </article>
  );
}
