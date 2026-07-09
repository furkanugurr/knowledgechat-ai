import { useState, type FormEvent, type KeyboardEvent } from "react";

interface ChatInputProps {
  disabled: boolean;
  onSubmit: (message: string) => Promise<void>;
}

export function ChatInput({
  disabled,
  onSubmit,
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const canSubmit = message.trim().length > 0 && !disabled;

  const submitMessage = async (): Promise<void> => {
    const normalizedMessage = message.trim();
    if (!normalizedMessage || disabled) {
      return;
    }

    setMessage("");
    await onSubmit(normalizedMessage);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    void submitMessage();
  };

  const handleKeyDown = (
    event: KeyboardEvent<HTMLTextAreaElement>,
  ): void => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submitMessage();
    }
  };

  return (
    <form
      className="border-t border-slate-200 bg-white p-3 sm:p-5"
      onSubmit={handleSubmit}
    >
      <div className="flex items-end gap-3 rounded-2xl border border-slate-300 bg-white p-2 shadow-sm transition focus-within:border-ocean-500 focus-within:ring-4 focus-within:ring-ocean-100">
        <label className="sr-only" htmlFor="chat-message">
          Ask a question
        </label>
        <textarea
          id="chat-message"
          className="max-h-36 min-h-12 flex-1 resize-none border-0 bg-transparent px-3 py-3 text-base text-ink outline-none placeholder:text-slate-400"
          disabled={disabled}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about the knowledge base..."
          rows={1}
          value={message}
        />
        <button
          className="mb-0.5 rounded-xl bg-ocean-600 px-5 py-3 font-semibold text-white transition hover:bg-ocean-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          disabled={!canSubmit}
          type="submit"
        >
          Send
        </button>
      </div>
      <p className="mt-2 px-1 text-xs text-slate-500">
        Press Enter to send. Use Shift + Enter for a new line.
      </p>
    </form>
  );
}
