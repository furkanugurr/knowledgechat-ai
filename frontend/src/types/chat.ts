export interface ChatRequest {
  message: string;
}

export interface CitationSource {
  document_name: string;
  relative_path: string;
  section_title: string | null;
  chunk_index: number;
  similarity_score: number;
  language: string | null;
}

export interface ChatResponse {
  response: string;
  sources: CitationSource[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: CitationSource[];
}
