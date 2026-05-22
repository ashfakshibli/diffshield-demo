export type Severity = "low" | "medium" | "high" | "critical";

export type DiffShieldFinding = {
  title: string;
  severity: Severity;
  confidence: number;
  attack_path: string;
  evidence: string[];
  remediation: string[];
};

