"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";

type SessionRow = { session_id: string; last_active_at: string; turns: number };
type TraceRow = {
  id: string;
  session_id: string;
  user_message: string;
  assistant_message?: string | null;
  plan_json?: string | null;
  created_at: string;
};
type AuditRow = {
  id: string;
  trace_id: string;
  tool_name: string;
  status: string;
  input_json?: string | null;
  output_json?: string | null;
  error_message?: string | null;
  created_at: string;
};

function fmtDate(iso: string) {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function ObservabilityConsole() {
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [selectedSession, setSelectedSession] = useState<string>("");
  const [traces, setTraces] = useState<TraceRow[]>([]);
  const [selectedTrace, setSelectedTrace] = useState<string>("");
  const [audit, setAudit] = useState<AuditRow[]>([]);
  const [err, setErr] = useState<string | null>(null);

  async function refreshSessions() {
    setErr(null);
    try {
      const s = await api.sessions();
      setSessions(s);
      if (!selectedSession && s[0]?.session_id)
        setSelectedSession(s[0].session_id);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    refreshSessions();
  }, []);

  useEffect(() => {
    if (!selectedSession) return;
    setErr(null);
    api
      .tracesBySession(selectedSession)
      .then((t) => {
        setTraces(t);
        if (t[0]?.id) setSelectedTrace(t[0].id);
      })
      .catch((e) => setErr(e.message));
  }, [selectedSession]);

  useEffect(() => {
    if (!selectedTrace) return;
    setErr(null);
    api
      .auditByTrace(selectedTrace)
      .then(setAudit)
      .catch((e) => setErr(e.message));
  }, [selectedTrace]);

  const selectedTraceObj = useMemo(
    () => traces.find((t) => t.id === selectedTrace),
    [traces, selectedTrace]
  );

  return (
    <div className="row cols-2">
      <div className="card">
        <div className="h2">Sessions</div>
        {err ? <div className="bubble assistant">Error: {err}</div> : null}

        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <select
            className="select"
            value={selectedSession}
            onChange={(e) => setSelectedSession(e.target.value)}
          >
            <option value="">(select session)</option>
            {sessions.map((s) => (
              <option
                key={s.session_id + new Date().getMilliseconds()}
                value={s.session_id}
              >
                {s.session_id} — {s.turns} turns
              </option>
            ))}
          </select>
          <button className="btn" onClick={refreshSessions}>
            Refresh
          </button>
        </div>

        <div className="hr" />

        <div className="h2">Traces</div>
        <table className="table">
          <thead>
            <tr>
              <th>Time</th>
              <th>User</th>
              <th>Assistant</th>
            </tr>
          </thead>
          <tbody>
            {traces.map((t) => (
              <tr
                key={t.id}
                style={{
                  cursor: "pointer",
                  background:
                    t.id === selectedTrace
                      ? "rgba(99,102,241,0.12)"
                      : "transparent",
                }}
                onClick={() => setSelectedTrace(t.id)}
              >
                <td className="small">{fmtDate(t.created_at)}</td>
                <td style={{ maxWidth: 260 }}>{t.user_message}</td>
                <td style={{ maxWidth: 360 }}>{t.assistant_message || ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <div className="h2">Audit log</div>
        <div className="small muted" style={{ marginBottom: 10 }}>
          {selectedTraceObj ? (
            <>
              <span className="kbd">{selectedTraceObj.id}</span> •{" "}
              {fmtDate(selectedTraceObj.created_at)}
            </>
          ) : (
            "Select a trace."
          )}
        </div>

        {selectedTraceObj?.plan_json ? (
          <>
            <div className="h2">Plan</div>
            <div className="bubble assistant">
              <div className="code">{selectedTraceObj.plan_json}</div>
            </div>
            <div className="hr" />
          </>
        ) : null}

        <div className="h2">Tool calls</div>
        {audit.length === 0 ? (
          <div className="p muted">No audit rows yet for this trace.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Tool</th>
                <th>Status</th>
                <th>Input</th>
                <th>Output / Error</th>
              </tr>
            </thead>
            <tbody>
              {audit.map((a) => (
                <tr key={a.id}>
                  <td>
                    <span className="kbd">{a.tool_name}</span>
                  </td>
                  <td>{a.status}</td>
                  <td>
                    <div className="code">{a.input_json || ""}</div>
                  </td>
                  <td>
                    <div className="code">
                      {a.output_json || a.error_message || ""}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
