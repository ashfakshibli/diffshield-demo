CREATE TABLE repos (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE scan_runs (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER NOT NULL REFERENCES repos(id),
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    summary_json JSONB NOT NULL
);

CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    scan_run_id INTEGER NOT NULL REFERENCES scan_runs(id),
    asset_type TEXT NOT NULL,
    name TEXT NOT NULL,
    properties_json JSONB NOT NULL
);

CREATE TABLE edges (
    id SERIAL PRIMARY KEY,
    scan_run_id INTEGER NOT NULL REFERENCES scan_runs(id),
    from_asset_id INTEGER NOT NULL,
    relation TEXT NOT NULL,
    to_asset_id INTEGER NOT NULL,
    properties_json JSONB NOT NULL
);

CREATE TABLE findings (
    id SERIAL PRIMARY KEY,
    scan_run_id INTEGER NOT NULL REFERENCES scan_runs(id),
    title TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    attack_path TEXT NOT NULL,
    evidence_json JSONB NOT NULL,
    remediation JSONB NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE trace_events (
    id SERIAL PRIMARY KEY,
    scan_run_id INTEGER NOT NULL REFERENCES scan_runs(id),
    stage TEXT NOT NULL,
    message TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

