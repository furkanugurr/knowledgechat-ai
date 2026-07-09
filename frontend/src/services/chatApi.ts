import type { ChatRequest, ChatResponse } from "../types/chat";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, "");

function isChatResponse(value: unknown): value is ChatResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const candidate = value as Partial<ChatResponse>;
  return (
    typeof candidate.response === "string" &&
    Array.isArray(candidate.sources)
  );
}

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const errorBody = (await response.json()) as { detail?: unknown };
    if (typeof errorBody.detail === "string") {
      return errorBody.detail;
    }
  } catch {
    // Fall through to the status-based message.
  }

  return `The chat request failed with status ${response.status}.`;
}

export async function sendChatMessage(
  request: ChatRequest,
): Promise<ChatResponse> {
  if (!apiBaseUrl) {
    throw new Error(
      "VITE_API_BASE_URL is not configured. Add it to the frontend environment.",
    );
  }

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}/api/v1/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });
  } catch {
    throw new Error(
      "Unable to reach the backend. Confirm that the API is running.",
    );
  }

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  const responseBody: unknown = await response.json();
  if (!isChatResponse(responseBody)) {
    throw new Error("The backend returned an invalid chat response.");
  }

  return responseBody;
}
