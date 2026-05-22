import Link from "next/link";
import { FindingCard } from "@/components/finding-card";
import { StatPill } from "@/components/stat-pill";
import { TraceCard } from "@/components/trace-card";
import { getScanBundle } from "@/lib/analyzer";

export default async function ScanDetailPage({
  params
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const { scan, findings, worldModel, traces } = await getScanBundle(id);

  return (
    <div className="page-shell">
      <section className="hero">
        <div className="hero-grid">
          <div>
            <div className="eyebrow">Scan #{scan.id}</div>
            <h1>Repo threat review completed.</h1>
            <p>
              DiffShield built a world-model-lite view of the target repo, generated
              candidate attack paths, validated findings, and stored stage-by-stage
              trace data for operator review.
            </p>
            <div className="hero-actions">
              <Link className="button-primary" href="/">
                Run another scan
              </Link>
              <a className="button-secondary" href={`#findings`}>
                Jump to findings
              </a>
            </div>
          </div>
          <aside className="metric-board">
            <div className="metric">
              <div className="label">Repo</div>
              <div className="value" style={{ fontSize: "1.1rem" }}>
                {scan.repo_name}
              </div>
            </div>
            <div className="metric">
              <div className="label">Validation mode</div>
              <div className="value" style={{ fontSize: "1.1rem" }}>
                {scan.summary_json.validated_with}
              </div>
            </div>
            <div className="metric">
              <div className="label">Scanned files</div>
              <div className="value" style={{ fontSize: "1rem" }}>
                {scan.summary_json.scanned_files.length}
              </div>
            </div>
          </aside>
        </div>
      </section>

      <div className="section-header">
        <h2>Scan summary</h2>
        <span>{scan.repo_path}</span>
      </div>
      <div className="badge-row">
        <StatPill name="Assets" value={scan.counts.assets} />
        <StatPill name="Relationships" value={scan.counts.edges} />
        <StatPill name="Findings" value={scan.counts.findings} />
      </div>

      <div className="layout-grid" style={{ marginTop: 24 }}>
        <section className="panel">
          <h2>Talking points this demo covers</h2>
          <div className="stack-grid">
            <div className="stack-card">
              <strong>Threat modeling</strong>
              <p>Candidate attack paths are generated from repo and deployment artifacts.</p>
            </div>
            <div className="stack-card">
              <strong>Validation layer</strong>
              <p>Findings are validated and normalized before presentation.</p>
            </div>
            <div className="stack-card">
              <strong>Remediation</strong>
              <p>Every finding includes concrete operator-facing next steps.</p>
            </div>
            <div className="stack-card">
              <strong>Telemetry</strong>
              <p>Each scan stage emits trace events that make the pipeline explainable.</p>
            </div>
          </div>
        </section>

        <aside className="panel">
          <h3>Run metadata</h3>
          <p>Status: {scan.status}</p>
          <p>Started: {new Date(scan.started_at).toLocaleString()}</p>
          <p>
            Completed:{" "}
            {scan.completed_at ? new Date(scan.completed_at).toLocaleString() : "In progress"}
          </p>
          <p>Candidate paths: {scan.summary_json.candidate_paths}</p>
        </aside>
      </div>

      <div className="section-header" id="findings">
        <h2>Validated findings</h2>
        <span>{findings.length} findings</span>
      </div>
      <div className="findings-grid">
        {findings.length > 0 ? (
          findings.map((finding) => <FindingCard finding={finding} key={finding.id} />)
        ) : (
          <div className="empty-state">No findings were generated for this scan.</div>
        )}
      </div>

      <div className="section-header">
        <h2>World model</h2>
        <span>Assets and relationships extracted from the target repo</span>
      </div>
      <div className="layout-grid">
        <section className="table-shell">
          <table>
            <thead>
              <tr>
                <th>Asset type</th>
                <th>Name</th>
                <th>Properties</th>
              </tr>
            </thead>
            <tbody>
              {worldModel.assets.map((asset) => (
                <tr key={asset.id}>
                  <td>{asset.asset_type}</td>
                  <td className="mono">{asset.name}</td>
                  <td className="mono">{JSON.stringify(asset.properties_json)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
        <section className="table-shell">
          <table>
            <thead>
              <tr>
                <th>From</th>
                <th>Relation</th>
                <th>To</th>
                <th>Properties</th>
              </tr>
            </thead>
            <tbody>
              {worldModel.edges.map((edge) => (
                <tr key={edge.id}>
                  <td>{edge.from_asset_id}</td>
                  <td>{edge.relation}</td>
                  <td>{edge.to_asset_id}</td>
                  <td className="mono">{JSON.stringify(edge.properties_json)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>

      <div className="section-header">
        <h2>Trace events</h2>
        <span>{traces.length} pipeline events</span>
      </div>
      <div className="trace-grid">
        {traces.map((trace) => (
          <TraceCard key={trace.id} trace={trace} />
        ))}
      </div>

      <div className="footer-note">
        This compact demo uses a local SQLite-backed analyzer today while preserving a
        Postgres/Docker deployment path in the repo.
      </div>
    </div>
  );
}
