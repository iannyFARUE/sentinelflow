import "./globals.css";
import Link from "next/link";

export const metadata = {
  title: "SentinelFlow — Demo Console",
  description: "Chat + Observability console for SentinelFlow",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="container">
          <header
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 16,
              marginBottom: 18,
            }}
          >
            <Link
              href="/"
              style={{ display: "flex", alignItems: "center", gap: 10 }}
            >
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 14,
                  background:
                    "linear-gradient(135deg, rgba(99,102,241,0.95), rgba(34,197,94,0.75))",
                  boxShadow: "0 14px 40px rgba(0,0,0,0.35)",
                }}
              />
              <div>
                <div style={{ fontWeight: 950, letterSpacing: "-0.02em" }}>
                  SentinelFlow
                </div>
                <div className="small">Agent Demo Console</div>
              </div>
            </Link>

            <nav style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <Link className="btn" href="/chat">
                Chat
              </Link>
              <Link className="btn" href="/obs">
                Observability
              </Link>
              <span className="badge">
                <span className="dot" /> Live
              </span>
            </nav>
          </header>

          {children}

          <footer style={{ marginTop: 26 }} className="small muted">
            Set <span className="kbd">Made with </span>{" "}
            <span className="hearts">&hearts;</span>{" "}
            <span className="kbd">by Ian Madhara, Simba and Tinashe</span>).
          </footer>
        </div>
      </body>
    </html>
  );
}
