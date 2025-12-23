import Link from "next/link";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="card" style={{ padding: 14 }}>
      <div
        style={{
          fontSize: 12,
          opacity: 0.7,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
        }}
      >
        {label}
      </div>
      <div style={{ fontSize: 22, fontWeight: 950, marginTop: 6 }}>{value}</div>
    </div>
  );
}

function Feature({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="card" style={{ padding: 16 }}>
      <div style={{ fontSize: 14, fontWeight: 900 }}>{title}</div>
      <div className="p muted" style={{ marginTop: 6 }}>
        {desc}
      </div>
    </div>
  );
}

function Pill({ text }: { text: string }) {
  return (
    <div
      className="badge"
      style={{ background: "rgba(10, 16, 28, 0.7)", borderRadius: 12 }}
    >
      {text}
    </div>
  );
}

function CheckItem({ text }: { text: string }) {
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: 999,
          background: "var(--accent)",
          boxShadow: "0 0 0 4px rgba(32, 201, 151, 0.15)",
          display: "inline-block",
        }}
      />
      <div className="small muted">{text}</div>
    </div>
  );
}

export default function Home() {
  return (
    <div style={{ display: "grid", gap: 20 }}>
      <div
        className="card"
        style={{
          padding: 16,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          flexWrap: "wrap",
          background: "var(--panel-strong)",
        }}
      >
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <div className="badge">
            <span className="dot" />
            SentinelFlow
          </div>
          <div className="small muted">Agent operations platform</div>
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <Link className="btn" href="/chat">
            Chat
          </Link>
          <Link className="btn" href="/obs">
            Observability
          </Link>
          <Link className="btn" href="/login">
            Log in
          </Link>
          <Link className="btn primary" href="/signup">
            Sign up
          </Link>
        </div>
      </div>

      <div
        className="card"
        style={{
          padding: 28,
          position: "relative",
          overflow: "hidden",
          background:
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='600' height='260' viewBox='0 0 600 260' fill='none'><path d='M20 60 C120 20 220 120 320 80 C420 40 500 30 580 60' stroke='%2394a3b8' stroke-opacity='0.18' stroke-width='2'/><path d='M10 120 C130 80 220 180 340 140 C440 100 520 90 590 120' stroke='%2394a3b8' stroke-opacity='0.14' stroke-width='2'/><path d='M30 180 C150 140 240 230 360 200 C460 170 530 150 590 170' stroke='%2394a3b8' stroke-opacity='0.12' stroke-width='2'/></svg>\")",
          backgroundRepeat: "no-repeat",
          backgroundPosition: "right top",
          backgroundSize: "520px 240px",
        }}
      >
        <div
          className="orb"
          style={{ top: -80, right: -40, background: "rgba(76,201,240,0.35)" }}
        />
        <div
          className="orb slow"
          style={{
            bottom: -120,
            left: -40,
            background: "rgba(32,201,151,0.28)",
          }}
        />
        <div
          style={{
            display: "grid",
            gap: 24,
            alignItems: "center",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            position: "relative",
            zIndex: 1,
          }}
        >
          <div>
            <div
              style={{
                display: "flex",
                gap: 10,
                flexWrap: "wrap",
                alignItems: "center",
              }}
            >
              <div className="badge" style={{ width: "fit-content" }}>
                <span className="dot" /> Built for agent reliability
              </div>
              <Pill text="SOC-ready audit trails" />
              <Pill text="Policy-enforced tools" />
              <Pill text="Human approval gates" />
            </div>

            <h1
              className="h1"
              style={{ fontSize: 46, marginTop: 16, lineHeight: 1.05 }}
            >
              The control plane for{" "}
              <span style={{ color: "var(--accent-2)" }}>
                production-grade agents
              </span>{" "}
              that ship safely.
            </h1>

            <p className="p muted" style={{ fontSize: 16, maxWidth: 620 }}>
              SentinelFlow keeps tools deterministic, approvals intentional, and
              traces audit-ready. Launch agent workflows that your security and
              ops teams can trust.
            </p>

            <div
              style={{
                display: "flex",
                gap: 10,
                flexWrap: "wrap",
                marginTop: 18,
              }}
            >
              <Link className="btn primary" href="/chat">
                Open chat console
              </Link>
              <Link className="btn" href="/obs">
                Explore observability
              </Link>
              <a
                className="btn"
                href="http://127.0.0.1:8000/docs"
                target="_blank"
                rel="noreferrer"
              >
                API reference
              </a>
            </div>

            <div style={{ marginTop: 14 }} className="small muted">
              Quick demo: <span className="kbd">Seed</span> -&gt;{" "}
              <span className="kbd">Pick user</span> -&gt;{" "}
              <span className="kbd">buy me a keyboard</span> -&gt;{" "}
              <span className="kbd">1</span> -&gt;{" "}
              <span className="kbd">confirm</span>.
            </div>

            <div
              style={{
                display: "grid",
                gap: 12,
                gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                marginTop: 20,
              }}
            >
              <Stat label="Uptime" value="99.99% workflows" />
              <Stat label="Latency" value="700ms median" />
              <Stat label="Coverage" value="36 eval suites" />
            </div>
          </div>

          <div style={{ display: "grid", gap: 14 }}>
            <div className="card" style={{ padding: 16 }}>
              <div className="h2">Agent console preview</div>
              <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
                <div className="bubble assistant">
                  <div className="small muted">User</div>
                  <div style={{ marginTop: 6 }} className="code">
                    buy me a keyboard
                  </div>
                </div>
                <div className="bubble assistant">
                  <div className="small muted">Agent</div>
                  <div style={{ marginTop: 6 }} className="code">
                    1) Mechanical Keyboard - 89.99 USD (stock: 12){"\n"}Reply
                    with option number.
                  </div>
                </div>
                <div className="bubble assistant">
                  <div className="small muted">System</div>
                  <div style={{ marginTop: 6 }} className="code">
                    search_products {"->"} confirm_token {"->"} execute_purchase
                    {"\n"}
                    audit_logs persisted
                  </div>
                </div>
              </div>
            </div>

            <div className="card" style={{ padding: 16 }}>
              <div className="h2">Ops dashboard</div>
              <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
                <div className="bubble assistant">
                  <div className="small muted">Policies</div>
                  <div className="code">Auto-repair JSON arguments</div>
                </div>
                <div className="bubble assistant">
                  <div className="small muted">Approvals</div>
                  <div className="code">Human approval required</div>
                </div>
                <div className="bubble assistant">
                  <div className="small muted">Routing</div>
                  <div className="code">Deterministic tool selection</div>
                </div>
              </div>
            </div>

            <div className="card" style={{ padding: 16 }}>
              <div className="h2">Trace highlights</div>
              <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
                <div className="bubble assistant">
                  <div className="small muted">Trace #2821</div>
                  <div className="code">3 tool calls - 1 approval gate</div>
                </div>
                <div className="bubble assistant">
                  <div className="small muted">Eval run</div>
                  <div className="code">36/36 suites passed</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        className="card"
        style={{
          padding: 16,
          display: "grid",
          gap: 12,
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          alignItems: "center",
        }}
      >
        <div className="small muted">Trusted by teams shipping agents:</div>
        <div className="badge">Mercury Ops</div>
        <div className="badge">Atlas Finance</div>
        <div className="badge">Northwind AI</div>
        <div className="badge">Lumen Health</div>
      </div>

      <div className="row">
        <div
          style={{
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          }}
        >
          <Feature
            title="Plan validation"
            desc="Schemas and repair strategies keep calls clean and deterministic."
          />
          <Feature
            title="Audit-grade traces"
            desc="Every step is tagged, timed, and stored for review."
          />
          <Feature
            title="Human approvals"
            desc="High-risk actions pause until the right people confirm."
          />
          <Feature
            title="Live observability"
            desc="Replay and inspect traces with context, inputs, and outputs."
          />
          <Feature
            title="Tool governance"
            desc="Policy rules constrain model actions in real time."
          />
          <Feature
            title="Eval suites"
            desc="Measure reliability before deploying new workflows."
          />
        </div>
      </div>

      <div className="row cols-2">
        <div className="card" style={{ padding: 18 }}>
          <div className="h2">How SentinelFlow works</div>
          <div className="p muted" style={{ marginTop: 8 }}>
            A production pipeline for every agent decision.
          </div>
          <div className="hr" />
          <div style={{ display: "grid", gap: 12 }}>
            <Feature
              title="1. Model proposes"
              desc="LLMs draft tool plans with structured arguments."
            />
            <Feature
              title="2. SentinelFlow verifies"
              desc="Schema validation + repair keeps calls deterministic."
            />
            <Feature
              title="3. Operators approve"
              desc="Sensitive actions pause for human confirmation."
            />
            <Feature
              title="4. Traces persist"
              desc="Every step is stored for audit, replay, and analytics."
            />
          </div>
        </div>

        <div className="card" style={{ padding: 18 }}>
          <div className="h2">Jump into modes</div>
          <div className="p muted" style={{ marginTop: 8 }}>
            Choose where you want to start.
          </div>
          <div className="hr" />
          <div style={{ display: "grid", gap: 10 }}>
            <Link className="btn primary" href="/chat">
              Agent console
            </Link>
            <Link className="btn" href="/obs">
              Observability
            </Link>
            <Link className="btn" href="/login">
              Log in
            </Link>
          </div>

          <div className="hr" />
          <div className="h2">Starter prompts</div>
          <div style={{ display: "grid", gap: 10, marginTop: 10 }}>
            <div className="bubble assistant">
              <div className="code">what is my balance</div>
            </div>
            <div className="bubble assistant">
              <div className="code">buy me a keyboard</div>
            </div>
            <div className="bubble assistant">
              <div className="code">1</div>
            </div>
            <div className="bubble assistant">
              <div className="code">confirm &lt;token&gt;</div>
            </div>
          </div>
        </div>
      </div>

      <div
        className="card"
        style={{
          padding: 18,
          display: "grid",
          gap: 16,
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        }}
      >
        <div>
          <div className="h2">Teams use SentinelFlow for</div>
          <div className="p muted" style={{ marginTop: 8 }}>
            Operational workflows that need confidence and traceability.
          </div>
        </div>
        <Feature
          title="Commerce approvals"
          desc="Payments and purchases pause for human confirmation."
        />
        <Feature
          title="Ops copilots"
          desc="Run customer ops with reliable tool execution."
        />
        <Feature
          title="Finance automations"
          desc="Securely execute transfers with audit trails."
        />
      </div>

      <div
        className="card"
        style={{
          padding: 20,
          display: "grid",
          gap: 16,
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
        }}
      >
        <div>
          <div className="h2">Pricing that scales</div>
          <div className="p muted" style={{ marginTop: 8 }}>
            Start free, then scale with your agent volume.
          </div>
        </div>
        <div className="card pricing-card" style={{ padding: 18 }}>
          <div className="badge">Sandbox</div>
          <div style={{ fontSize: 28, fontWeight: 900, marginTop: 10 }}>$0</div>
          <div className="p muted" style={{ marginTop: 6 }}>
            Local demos and eval runs.
          </div>
          <div style={{ display: "grid", gap: 8, marginTop: 14 }}>
            <CheckItem text="Local traces" />
            <CheckItem text="Starter policies" />
            <CheckItem text="Single workspace" />
          </div>
        </div>
        <div className="card pricing-card featured" style={{ padding: 18 }}>
          <div className="badge">Team</div>
          <div style={{ fontSize: 28, fontWeight: 900, marginTop: 10 }}>
            $249
          </div>
          <div className="p muted" style={{ marginTop: 6 }}>
            Multi-user traces + approvals.
          </div>
          <div style={{ display: "grid", gap: 8, marginTop: 14 }}>
            <CheckItem text="Role-based access" />
            <CheckItem text="Approval routing" />
            <CheckItem text="Trace exports" />
          </div>
          <div style={{ marginTop: 14 }}>
            <Link className="btn primary" href="/signup">
              Start team plan
            </Link>
          </div>
        </div>
        <div className="card pricing-card" style={{ padding: 18 }}>
          <div className="badge">Enterprise</div>
          <div style={{ fontSize: 28, fontWeight: 900, marginTop: 10 }}>
            Lets talk
          </div>
          <div className="p muted" style={{ marginTop: 6 }}>
            Custom policies and dedicated infra.
          </div>
          <div style={{ display: "grid", gap: 8, marginTop: 14 }}>
            <CheckItem text="Dedicated VPC" />
            <CheckItem text="Custom SLAs" />
            <CheckItem text="On-prem options" />
          </div>
        </div>
      </div>

      <div
        className="card"
        style={{
          padding: 18,
          display: "grid",
          gap: 16,
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        }}
      >
        <div>
          <div className="h2">FAQ</div>
          <div className="p muted" style={{ marginTop: 8 }}>
            Answers to common questions from teams getting started.
          </div>
        </div>
        <Feature
          title="Is it safe for production?"
          desc="Yes. Validation, approvals, and audit trails are built in."
        />
        <Feature
          title="How do I observe agents?"
          desc="Every run is captured with inputs, outputs, and tool calls."
        />
        <Feature
          title="Does it work with my stack?"
          desc="Use the API to orchestrate tools, policies, and traces."
        />
      </div>

      <div
        className="card"
        style={{
          padding: 22,
          display: "grid",
          gap: 12,
          alignItems: "center",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          background: "var(--panel-strong)",
        }}
      >
        <div>
          <div className="h2">Ship reliable agents today</div>
          <div className="p muted" style={{ marginTop: 8 }}>
            Launch a sandbox, run your first trace, and keep every action safe.
          </div>
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <Link className="btn primary" href="/chat">
            Launch console
          </Link>
          <Link className="btn" href="/obs">
            View traces
          </Link>
          <Link className="btn" href="/signup">
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
}
