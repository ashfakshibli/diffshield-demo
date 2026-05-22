"use client";

import { useRouter } from "next/navigation";
import { startTransition, useState } from "react";

const defaultRepoPath =
  process.env.NEXT_PUBLIC_DEMO_TARGET_REPO ??
  "/Users/ashfak/Desktop/Jobs/Latent Defense/diffshield-vuln-demo";

export function HomeClient() {
  const router = useRouter();
  const [repoPath, setRepoPath] = useState(defaultRepoPath);
  const [notes, setNotes] = useState(
    "Security demo scan: local toy repo with an exposed admin route, broad env secrets, a root container, and a public internal port."
  );
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  const launchScan = async (useSample: boolean) => {
    setError(null);
    setIsPending(true);

    try {
      const response = await fetch("/api/scans", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          repoPath: useSample ? undefined : repoPath,
          useSample,
          notes
        })
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.error ?? "Unable to start scan");
      }

      const payload = (await response.json()) as { scanId: number };
      startTransition(() => {
        router.push(`/scans/${payload.scanId}`);
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unknown error");
      setIsPending(false);
    }
  };

  return (
    <div className="page-shell">
      <section className="hero">
        <div className="hero-grid">
          <div>
            <div className="eyebrow">DiffShield demo</div>
            <h1>Threat model a repo in one scan.</h1>
            <p>
              DiffShield ingests code and deployment artifacts, builds a tiny world model,
              proposes candidate attack paths, validates likely issues, and produces
              remediation guidance with traceable pipeline stages.
            </p>
            <div className="hero-actions">
              <button
                className="button-primary"
                disabled={isPending}
                onClick={() => launchScan(true)}
                type="button"
              >
                {isPending ? "Starting scan..." : "Run sample repo scan"}
              </button>
              <button
                className="button-secondary"
                disabled={isPending}
                onClick={() => launchScan(false)}
                type="button"
              >
                Scan the path below
              </button>
            </div>
            {error ? <p style={{ color: "var(--red)" }}>{error}</p> : null}
          </div>

          <aside className="metric-board">
            <div className="metric-row">
              <div className="metric">
                <div className="label">World model</div>
                <div className="value">Assets + edges</div>
              </div>
              <div className="metric">
                <div className="label">Validation</div>
                <div className="value">Rules + AI</div>
              </div>
            </div>
            <div className="metric-row">
              <div className="metric">
                <div className="label">Inputs</div>
                <div className="value">Repo, Docker, routes</div>
              </div>
              <div className="metric">
                <div className="label">Output</div>
                <div className="value">Findings + fixes</div>
              </div>
            </div>
            <div className="metric">
              <div className="label">Security workflow signals</div>
              <div className="value" style={{ fontSize: "1.15rem" }}>
                threat modeling, git integrations, agent workflows, remediation, telemetry
              </div>
            </div>
          </aside>
        </div>
      </section>

      <div className="layout-grid">
        <section className="panel">
          <h2>Launch a scan</h2>
          <p>
            Use the built-in vulnerable repo for a quick security walkthrough. You can also point
            the analyzer at another local repo path without changing the product code.
          </p>

          <div className="scan-form">
            <label htmlFor="repoPath">Target repo path</label>
            <input
              id="repoPath"
              onChange={(event) => setRepoPath(event.target.value)}
              placeholder="/absolute/path/to/target/repo"
              value={repoPath}
            />

            <label htmlFor="notes">Analyst notes</label>
            <textarea
              id="notes"
              onChange={(event) => setNotes(event.target.value)}
              value={notes}
            />
          </div>
        </section>

        <aside className="panel">
          <h3>Demo framing</h3>
          <div className="stack-grid">
            <div className="stack-card">
              <strong>World model lite</strong>
              <p>Extract services, routes, secrets, ports, middleware, and databases.</p>
            </div>
            <div className="stack-card">
              <strong>Candidate attack paths</strong>
              <p>Generate deterministic paths before validation.</p>
            </div>
            <div className="stack-card">
              <strong>Validation layer</strong>
              <p>Use rules first, then an OpenAI-compatible explanation pass if configured.</p>
            </div>
            <div className="stack-card">
              <strong>Telemetry</strong>
              <p>Every stage is stored as a trace event so the system is explainable.</p>
            </div>
          </div>
        </aside>
      </div>

      <div className="section-header">
        <h2>Expected stack alignment</h2>
        <span>Designed to show a compact security systems workflow</span>
      </div>
      <div className="stack-grid">
        <div className="stack-card">
          <strong>Next.js + TypeScript</strong>
          <p>Operator UI, API routes, and demo presentation layer.</p>
        </div>
        <div className="stack-card">
          <strong>Python analyzer</strong>
          <p>Parsers, world-model builder, threat rules, validator, and trace pipeline.</p>
        </div>
        <div className="stack-card">
          <strong>SQLite local demo</strong>
          <p>Runnable here today, with Postgres schema and Docker Compose included for deployment discussion.</p>
        </div>
        <div className="stack-card">
          <strong>Docker path</strong>
          <p>Compose files and Dockerfiles are included even though this machine cannot run Docker.</p>
        </div>
      </div>
    </div>
  );
}
