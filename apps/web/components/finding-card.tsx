import type { Finding } from "@/lib/analyzer";

export function FindingCard({ finding }: { finding: Finding }) {
  const severityClass = finding.severity.toLowerCase();

  return (
    <article className="finding-card">
      <div className="finding-head">
        <div>
          <h3>{finding.title}</h3>
          <p>
            Confidence {Math.round(finding.confidence * 100)}% · Status {finding.status}
          </p>
        </div>
        <span className={`severity ${severityClass}`}>{finding.severity}</span>
      </div>
      <p>{finding.attack_path}</p>
      <div className="info-grid">
        <div>
          <strong>Evidence</strong>
          <ul>
            {finding.evidence_json.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div>
          <strong>Remediation</strong>
          <ul>
            {finding.remediation.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  );
}

