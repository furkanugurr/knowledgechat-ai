import { useState } from "react";

import { ChatInput } from "./components/ChatInput";
import { ChatLayout } from "./components/ChatLayout";
import { ErrorMessage } from "./components/ErrorMessage";
import { LoadingIndicator } from "./components/LoadingIndicator";
import { MessageBubble } from "./components/MessageBubble";
import { sendChatMessage } from "./services/chatApi";
import type { ChatMessage } from "./types/chat";

function createMessageId(): string {
  return crypto.randomUUID();
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSendMessage = async (content: string): Promise<void> => {
    const userMessage: ChatMessage = {
      id: createMessageId(),
      role: "user",
      content,
    };

    setMessages((currentMessages) => [
      ...currentMessages,
      userMessage,
    ]);
    setErrorMessage(null);
    setIsLoading(true);

    try {
      const data = await sendChatMessage({ message: content });
      const assistantMessage: ChatMessage = {
        id: createMessageId(),
        role: "assistant",
        content: data.response,
        sources: data.sources,
      };
      setMessages((currentMessages) => [
        ...currentMessages,
        assistantMessage,
      ]);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "An unexpected error occurred.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ChatLayout
      error={
        errorMessage ? (
          <ErrorMessage
            message={errorMessage}
            onDismiss={() => setErrorMessage(null)}
          />
        ) : null
      }
      input={
        <ChatInput
          disabled={isLoading}
          onSubmit={handleSendMessage}
        />
      }
    >
      {messages.length === 0 ? (
        <div className="mx-auto max-w-xl py-16 text-center sm:py-24">
          <p className="text-lg font-semibold text-ink">
            Ask your knowledge base a question
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-500">
            Answers are generated locally and include the knowledge
            sources used for context.
          </p>
        </div>
      ) : (
        messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))
      )}
      {isLoading ? <LoadingIndicator /> : null}
    </ChatLayout>
  );
}
