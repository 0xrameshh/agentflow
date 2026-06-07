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
