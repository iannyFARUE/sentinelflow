export type ChatRequest = {
  session_id: string;
  user_id?: string | null;
  message: string;
};
export type ChatResponse = {
  trace_id: string;
  session_id: string;
  message: string;
  needs_confirmation: boolean;
  confirmation_token?: string | null;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  chat: (payload: ChatRequest) =>
    http<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  seed: () => http<any>("/admin/seed", { method: "POST" }),
  users: () =>
    http<Array<{ id: string; full_name: string; email: string }>>("/users"),
  sessions: () =>
    http<Array<{ session_id: string; last_active_at: string; turns: number }>>(
      "/sessions"
    ),
  tracesBySession: (sessionId: string) =>
    http<
      Array<{
        id: string;
        session_id: string;
        user_message: string;
        assistant_message?: string | null;
        plan_json?: string | null;
        created_at: string;
      }>
    >(`/sessions/${encodeURIComponent(sessionId)}/traces`),
  auditByTrace: (traceId: string) =>
    http<
      Array<{
        id: string;
        trace_id: string;
        tool_name: string;
        status: string;
        input_json?: string | null;
        output_json?: string | null;
        error_message?: string | null;
        created_at: string;
      }>
    >(`/traces/${encodeURIComponent(traceId)}/audit`),
};
