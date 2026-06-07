// API client for the Knowledge Copilot backend

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081";

export interface Citation {
  source: string;
  snippet: string;
  file_type?: string | null;
  page?: number | null;
}

export interface SupportRunResponse {
  answer: string;
  citations: Citation[];
  thread_id: string;
  run_id: string;
  tool_call_count: number;
  revision_count: number;
  latency_ms: number;
}

export interface KbArticlesResponse {
  articles: string[];
  count: number;
}

export type StreamEvent =
  | { type: "status"; phase: string }
  | { type: "chunk"; text: string }
  | {
      type: "done";
      answer: string;
      citations: Citation[];
      thread_id: string;
      run_id: string;
      tool_call_count: number;
      revision_count: number;
      latency_ms: number;
    }
  | { type: "error"; message: string };

export interface StreamSupportHandlers {
  onStatus?: (phase: string) => void;
  onChunk?: (text: string) => void;
  onDone?: (data: Extract<StreamEvent, { type: "done" }>) => void;
  onError?: (message: string) => void;
}

export async function postSupport(message: string): Promise<SupportRunResponse> {
  const response = await fetch(`${API_URL}/run/support`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
    throw new Error(err.detail || `Server error (${response.status})`);
  }

  return response.json();
}

export async function streamSupport(
  message: string,
  handlers: StreamSupportHandlers
): Promise<void> {
  const response = await fetch(`${API_URL}/run/support/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
    throw new Error(err.detail || `Server error (${response.status})`);
  }

  if (!response.body) {
    throw new Error("Streaming not supported in this browser");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const raw = line.slice(6).trim();
      if (!raw) continue;

      let event: StreamEvent;
      try {
        event = JSON.parse(raw) as StreamEvent;
      } catch {
        continue;
      }

      switch (event.type) {
        case "status":
          handlers.onStatus?.(event.phase);
          break;
        case "chunk":
          handlers.onChunk?.(event.text);
          break;
        case "done":
          handlers.onDone?.(event);
          break;
        case "error":
          handlers.onError?.(event.message);
          break;
      }
    }
  }
}

export async function getKbArticles(): Promise<KbArticlesResponse> {
  const response = await fetch(`${API_URL}/kb/articles`);
  if (!response.ok) {
    return { articles: [], count: 0 };
  }
  return response.json();
}

export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
