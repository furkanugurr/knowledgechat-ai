interface ErrorMessageProps {
  message: string;
  onDismiss: () => void;
}

export function ErrorMessage({
  message,
  onDismiss,
}: ErrorMessageProps) {
  return (
    <div
      className="flex items-start justify-between gap-4 border-b border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
      role="alert"
    >
      <p>{message}</p>
      <button
        aria-label="Dismiss error"
        className="font-bold text-red-700 hover:text-red-900"
        onClick={onDismiss}
        type="button"
      >
        Close
      </button>
    </div>
  );
}
