"use client";

import { useEffect, useMemo, useState } from "react";

type ChatRequest = { session_id: string; user_id?: string; message: string };
type ChatResponse = {
  trace_id: string;
  session_id: string;
  message: string;
  needs_confirmation: boolean;
  confirmation_token: string | null;
};

type User = { id: string; full_name: string; email: string };
type Trace = {
  id: string;
  session_id: string;
  user_message: string;
  assistant_message?: string | null;
  plan_json?: string | null;
  created_at: string;
};
type AuditLog = {
  id: string;
  trace_id: string;
  tool_name: string;
  status: string;
  input_json?: string | null;
  output_json?: string | null;
  error_message?: string | null;
  created_at: string;
};

const API = process.env.NEXT_PUBLIC_API_BASE!;

async function apiGet<T>(path: string): Promise<T> {
  const r = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

async function apiPost<T>(path: string, body?: any): Promise<T> {
  const r = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function prettyJson(maybeJson: string | null | undefined) {
  if (!maybeJson) return "";
  try {
    const obj =
      typeof maybeJson === "string" ? JSON.parse(maybeJson) : maybeJson;
    return JSON.stringify(obj, null, 2);
  } catch {
    return maybeJson;
  }
}

export default function Page() {
  // ---- global selections ----
  const [plannerMode, setPlannerMode] = useState<"heuristic" | "llm">("llm");
  const [users, setUsers] = useState<User[]>([]);
  const [userId, setUserId] = useState<string>("");
  const [sessionId, setSessionId] = useState<string>("demo-1");

  // ---- chat state ----
  const [input, setInput] = useState("");
  const [chatLog, setChatLog] = useState<
    Array<{ role: "user" | "assistant"; text: string }>
  >([]);

  // ---- observability state ----
  const [latestTrace, setLatestTrace] = useState<Trace | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const canSend = useMemo(
    () => input.trim().length > 0 && sessionId.trim().length > 0,
    [input, sessionId]
  );

  // Initial load: users
  useEffect(() => {
    (async () => {
      try {
        setErr(null);
        const u = await apiGet<User[]>("/users");
        setUsers(u);
        if (u.length && !userId) setUserId(u[0].id);
      } catch (e: any) {
        setErr(e.message || String(e));
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Apply planner mode (admin endpoint you already used in eval)
  useEffect(() => {
    (async () => {
      try {
        await apiPost("/admin/planner_mode", { planner_mode: plannerMode });
      } catch {
        // non-fatal (frontend still works)
      }
    })();
  }, [plannerMode]);

  // Poll latest trace + audit logs
  useEffect(() => {
    if (!autoRefresh) return;

    const t = setInterval(async () => {
      try {
        // get latest trace for session
        const traces = await apiGet<Trace[]>(
          `/traces?session_id=${encodeURIComponent(sessionId)}&limit=1`
        );
        const tr = traces?.[0] || null;
        setLatestTrace(tr);

        if (tr?.id) {
          const logs = await apiGet<AuditLog[]>(
            `/audit?trace_id=${encodeURIComponent(tr.id)}`
          );
          setAuditLogs(logs);
        } else {
          setAuditLogs([]);
        }
      } catch {
        // ignore transient polling errors
      }
    }, 1500);

    return () => clearInterval(t);
  }, [autoRefresh, sessionId]);

  async function seed() {
    try {
      setErr(null);
      await apiPost("/admin/seed");
      const u = await apiGet<User[]>("/users");
      setUsers(u);
      if (u.length) setUserId(u[0].id);
    } catch (e: any) {
      setErr(e.message || String(e));
    }
  }

  async function sendMessage(text: string) {
    const msg = text.trim();
    if (!msg) return;
    setLoading(true);
    setErr(null);

    setChatLog((prev) => [...prev, { role: "user", text: msg }]);
    setInput("");

    try {
      const payload: ChatRequest = {
        session_id: sessionId,
        user_id: userId || undefined,
        message: msg,
      };
      const resp = await apiPost<ChatResponse>("/chat", payload);

      setChatLog((prev) => [
        ...prev,
        { role: "assistant", text: resp.message },
      ]);

      // If backend returns confirm token, show it (user can click a button)
      if (resp.needs_confirmation && resp.confirmation_token) {
        setChatLog((prev) => [
          ...prev,
          {
            role: "assistant",
            text: `To confirm: confirm ${resp.confirmation_token}`,
          },
        ]);
      }
    } catch (e: any) {
      setErr(e.message || String(e));
      setChatLog((prev) => [
        ...prev,
        { role: "assistant", text: "Error: request failed." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function quickDemo(kind: "balance" | "buy") {
    if (kind === "balance") sendMessage("what is my balance");
    if (kind === "buy") sendMessage("buy me a keyboard");
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-neutral-800 bg-neutral-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-neutral-800" />
            <div>
              <div className="text-sm font-semibold">SentinelFlow Console</div>
              <div className="text-xs text-neutral-400">
                Agent chat + observability
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select
              className="rounded-lg border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm"
              value={plannerMode}
              onChange={(e) => setPlannerMode(e.target.value as any)}
            >
              <option value="llm">LLM planner</option>
              <option value="heuristic">Heuristic planner</option>
            </select>

            <select
              className="min-w-[220px] rounded-lg border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
            >
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name} ({u.email})
                </option>
              ))}
            </select>

            <input
              className="w-[160px] rounded-lg border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              placeholder="session_id"
            />

            <button
              onClick={seed}
              className="rounded-lg border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm hover:bg-neutral-800"
            >
              Seed
            </button>
          </div>
        </div>
      </header>

      {/* Body */}
      <main className="mx-auto grid max-w-6xl grid-cols-1 gap-4 px-4 py-4 md:grid-cols-2">
        {/* Chat */}
        <section className="rounded-2xl border border-neutral-800 bg-neutral-900/40">
          <div className="border-b border-neutral-800 px-4 py-3">
            <div className="text-sm font-semibold">Chat</div>
            <div className="text-xs text-neutral-400">Session: {sessionId}</div>
          </div>

          <div className="h-[520px] overflow-auto px-4 py-3">
            {chatLog.length === 0 ? (
              <div className="text-sm text-neutral-400">
                Try the demo buttons below, or type a message.
              </div>
            ) : (
              <div className="space-y-3">
                {chatLog.map((m, i) => (
                  <div
                    key={i}
                    className={m.role === "user" ? "text-right" : "text-left"}
                  >
                    <div
                      className={
                        "inline-block max-w-[85%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-sm " +
                        (m.role === "user"
                          ? "bg-neutral-200 text-neutral-900"
                          : "bg-neutral-800 text-neutral-100")
                      }
                    >
                      {m.text}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="border-t border-neutral-800 px-4 py-3">
            <div className="mb-2 flex gap-2">
              <button
                onClick={() => quickDemo("balance")}
                className="rounded-lg border border-neutral-800 bg-neutral-900 px-3 py-2 text-xs hover:bg-neutral-800"
              >
                Demo: Balance
              </button>
              <button
                onClick={() => quickDemo("buy")}
                className="rounded-lg border border-neutral-800 bg-neutral-900 px-3 py-2 text-xs hover:bg-neutral-800"
              >
                Demo: Buy keyboard
              </button>
            </div>

            {err ? (
              <div className="mb-2 text-xs text-red-400">{err}</div>
            ) : null}

            <div className="flex gap-2">
              <input
                className="flex-1 rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm outline-none"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder='Try: "buy me a keyboard"'
                onKeyDown={(e) => {
                  if (e.key === "Enter" && canSend && !loading)
                    sendMessage(input);
                }}
              />
              <button
                disabled={!canSend || loading}
                onClick={() => sendMessage(input)}
                className="rounded-lg bg-neutral-200 px-4 py-2 text-sm font-semibold text-neutral-900 disabled:opacity-50"
              >
                {loading ? "Sending…" : "Send"}
              </button>
            </div>
          </div>
        </section>

        {/* Observability */}
        <section className="rounded-2xl border border-neutral-800 bg-neutral-900/40">
          <div className="flex items-center justify-between border-b border-neutral-800 px-4 py-3">
            <div>
              <div className="text-sm font-semibold">Observability</div>
              <div className="text-xs text-neutral-400">
                Latest trace + audit logs
              </div>
            </div>
            <label className="flex items-center gap-2 text-xs text-neutral-300">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              Auto-refresh
            </label>
          </div>

          <div className="space-y-4 px-4 py-3">
            <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-3">
              <div className="text-xs text-neutral-400">Latest trace</div>
              {latestTrace ? (
                <div className="mt-1 text-sm">
                  <div className="text-xs text-neutral-400">trace_id</div>
                  <div className="font-mono text-xs break-all">
                    {latestTrace.id}
                  </div>
                  <div className="mt-2 text-xs text-neutral-400">plan_json</div>
                  <pre className="mt-1 max-h-[200px] overflow-auto rounded-lg bg-neutral-900 p-2 text-xs">
                    {prettyJson(latestTrace.plan_json)}
                  </pre>
                </div>
              ) : (
                <div className="mt-1 text-sm text-neutral-400">
                  No traces yet.
                </div>
              )}
            </div>

            <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-3">
              <div className="text-xs text-neutral-400">Audit logs</div>
              {auditLogs.length ? (
                <div className="mt-2 space-y-2">
                  {auditLogs.map((a) => (
                    <div
                      key={a.id}
                      className="rounded-lg border border-neutral-800 bg-neutral-900 p-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-semibold">
                          {a.tool_name}
                        </div>
                        <div className="text-xs text-neutral-400">
                          {a.status}
                        </div>
                      </div>
                      {a.error_message ? (
                        <div className="mt-1 text-xs text-red-400">
                          {a.error_message}
                        </div>
                      ) : null}
                      <details className="mt-2 text-xs text-neutral-300">
                        <summary className="cursor-pointer text-neutral-400">
                          Input / Output
                        </summary>
                        <pre className="mt-2 max-h-[160px] overflow-auto rounded bg-neutral-950 p-2">
                          Input: {prettyJson(a.input_json || "")}
                          Output: {prettyJson(a.output_json || "")}
                        </pre>
                      </details>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-2 text-sm text-neutral-400">
                  No audit logs for latest trace.
                </div>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
