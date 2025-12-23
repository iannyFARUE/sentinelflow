"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";

type Msg = { role: "user" | "assistant"; text: string; meta?: any };

function uid(prefix = "demo") {
  return `${prefix}-${Math.random().toString(16).slice(2)}-${Date.now()}`;
}

export default function ChatConsole() {
  const [busy, setBusy] = useState(false);
  const [users, setUsers] = useState<
    Array<{ id: string; full_name: string; email: string }>
  >([]);
  const [userId, setUserId] = useState<string>("");
  const [sessionId, setSessionId] = useState<string>("demo-1");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "assistant",
      text: "Seed data, pick a user, then try: “buy me a keyboard”.",
    },
  ]);

  const [lastTraceId, setLastTraceId] = useState<string | null>(null);

  const listRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    api
      .users()
      .then(setUsers)
      .catch(() => {});
  }, []);

  useEffect(() => {
    listRef.current?.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages.length]);

  const selectedUser = useMemo(
    () => users.find((u) => u.id === userId),
    [users, userId]
  );

  async function seed() {
    setBusy(true);
    try {
      await api.seed();
      const u = await api.users();
      setUsers(u);
      if (u[0]?.id) setUserId(u[0].id);
      setMessages([
        {
          role: "assistant",
          text: "Seeded ✅ Pick a user and start chatting.",
        },
      ]);
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: `Seed failed: ${e.message}` },
      ]);
    } finally {
      setBusy(false);
    }
  }

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;

    setMessages((m) => [...m, { role: "user", text: trimmed }]);
    setInput("");
    setBusy(true);

    try {
      const resp = await api.chat({
        session_id: sessionId,
        user_id: userId || null,
        message: trimmed,
      });
      setLastTraceId(resp.trace_id);
      setMessages((m) => [
        ...m,
        { role: "assistant", text: resp.message, meta: resp },
      ]);

      if (resp.confirmation_token) {
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            text: `Click to confirm: confirm ${resp.confirmation_token}`,
            meta: { quickConfirm: resp.confirmation_token },
          },
        ]);
      }
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: `Error: ${e.message}` },
      ]);
    } finally {
      setBusy(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      send(input);
    }
  }

  return (
    <div className="row cols-2">
      <div className="card">
        <div className="h2">Agent Console</div>

        <div style={{ display: "grid", gap: 10 }}>
          <div
            style={{ display: "grid", gap: 10, gridTemplateColumns: "1fr 1fr" }}
          >
            <div>
              <div className="small muted">User</div>
              <select
                className="select"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
              >
                <option value="">(none)</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.full_name} — {u.email}
                  </option>
                ))}
              </select>
              <div className="small muted" style={{ marginTop: 6 }}>
                {selectedUser ? (
                  <>
                    Selected: <span className="kbd">{selectedUser.id}</span>
                  </>
                ) : (
                  "Select a user for tool calls."
                )}
              </div>
            </div>

            <div>
              <div className="small muted">Session</div>
              <div style={{ display: "flex", gap: 10 }}>
                <input
                  className="input"
                  value={sessionId}
                  onChange={(e) => setSessionId(e.target.value)}
                  placeholder="demo-1"
                />
                <button
                  className="btn"
                  onClick={() => setSessionId(uid("demo"))}
                  disabled={busy}
                >
                  New
                </button>
              </div>
              <div className="small muted" style={{ marginTop: 6 }}>
                Keep the same session_id to test multi-turn memory.
              </div>
            </div>
          </div>

          <div className="hr" />

          <div ref={listRef} className="msglist">
            {messages.map((m, i) => {
              const quick = m.meta?.quickConfirm as string | undefined;
              return (
                <div
                  key={i}
                  className={`bubble ${m.role}`}
                  onClick={() => quick && send(`confirm ${quick}`)}
                  style={{ cursor: quick ? "pointer" : "default" }}
                  title={quick ? "Click to send confirmation" : undefined}
                >
                  <div className="small muted" style={{ marginBottom: 6 }}>
                    {m.role === "user" ? "You" : "SentinelFlow"}
                  </div>
                  <div style={{ whiteSpace: "pre-wrap" }}>{m.text}</div>
                </div>
              );
            })}
          </div>

          <textarea
            className="input"
            rows={3}
            placeholder='Try: "buy me a keyboard" or "what is my balance"'
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            disabled={busy}
          />

          <div
            style={{
              display: "flex",
              gap: 10,
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div className="small muted">
              {lastTraceId ? (
                <>
                  Last trace: <span className="kbd">{lastTraceId}</span>
                </>
              ) : (
                "No trace yet."
              )}
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn" onClick={seed} disabled={busy}>
                Seed
              </button>
              <button
                className="btn primary"
                onClick={() => send(input)}
                disabled={busy || !input.trim()}
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="h2">Demo shortcuts</div>
        <div className="p muted" style={{ display: "grid", gap: 10 }}>
          <div>
            Multi-turn flow:
            <div className="code">
              {`1) "buy me a keyboard"
2) "1"
3) "confirm <token>"`}
            </div>
          </div>

          <div className="hr" />

          <div>
            Quick prompts:
            <div
              style={{
                display: "flex",
                gap: 8,
                flexWrap: "wrap",
                marginTop: 8,
              }}
            >
              {[
                "buy me a keyboard",
                "what is my balance",
                "buy me a usb-c hub",
                "show more",
              ].map((t) => (
                <button
                  key={t}
                  className="btn"
                  onClick={() => setInput(t)}
                  disabled={busy}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
