# DiffShield architecture

## Surfaces

- Web UI: Next.js + TypeScript
- Analyzer: Python HTTP service
- Local demo DB: SQLite
- Deployment path: Postgres + Docker Compose

## Pipeline

1. Ingest target repo files
2. Parse Docker, compose, env, route, and middleware files
3. Build a tiny asset/edge model
4. Generate deterministic candidate findings
5. Validate and rewrite findings with an OpenAI-compatible step if configured
6. Persist findings and traces
7. Present results in the UI

## Interview mapping

- world model
- autonomous threat modeling loop
- validation layer
- remediation suggestions
- observability and telemetry
- repo/deployment artifact integration
