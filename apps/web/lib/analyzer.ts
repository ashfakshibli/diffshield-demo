const analyzerUrl = process.env.ANALYZER_URL ?? "http://127.0.0.1:8001";

export type ScanSummary = {
  id: number;
  repo_name: string;
  repo_path: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  counts: {
    assets: number;
    edges: number;
    findings: number;
    traces: number;
  };
  summary_json: {
    candidate_paths: number;
    validated_with: string;
    scanned_files: string[];
  };
};

export type Finding = {
  id: number;
  title: string;
  severity: string;
  confidence: number;
  attack_path: string;
  evidence_json: string[];
  remediation: string[];
  status: string;
};

export type WorldModel = {
  assets: Array<{
    id: number;
    asset_type: string;
    name: string;
    properties_json: Record<string, unknown>;
  }>;
  edges: Array<{
    id: number;
    from_asset_id: number;
    relation: string;
    to_asset_id: number;
    properties_json: Record<string, unknown>;
  }>;
};

export type TraceEvent = {
  id: number;
  stage: string;
  message: string;
  payload_json: Record<string, unknown>;
  created_at: string;
};

async function analyzerFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${analyzerUrl}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Analyzer request failed (${response.status}): ${text}`);
  }

  return (await response.json()) as T;
}

export async function startScan(input: { repoPath?: string; useSample?: boolean; notes?: string }) {
  return analyzerFetch<{ scan_id: number; repo_path: string }>("/scan", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function getScan(scanId: string | number) {
  return analyzerFetch<ScanSummary>(`/scan/${scanId}`);
}

export async function getFindings(scanId: string | number) {
  return analyzerFetch<Finding[]>(`/scan/${scanId}/findings`);
}

export async function getWorldModel(scanId: string | number) {
  return analyzerFetch<WorldModel>(`/scan/${scanId}/world-model`);
}

export async function getTraces(scanId: string | number) {
  return analyzerFetch<TraceEvent[]>(`/scan/${scanId}/traces`);
}

export async function getScanBundle(scanId: string | number) {
  const [scan, findings, worldModel, traces] = await Promise.all([
    getScan(scanId),
    getFindings(scanId),
    getWorldModel(scanId),
    getTraces(scanId)
  ]);

  return { scan, findings, worldModel, traces };
}

