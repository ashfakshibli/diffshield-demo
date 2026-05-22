# DiffShield

DiffShield is a lightweight repo threat modeler built as a compact security systems demo.

It scans a local target repo, extracts a tiny world model from code and deployment artifacts, generates candidate attack paths, validates findings, and suggests remediations.

## Stack

- Next.js + TypeScript UI
- Python analyzer service
- SQLite for the local runnable demo
- Postgres schema and Docker Compose path included for deployment-oriented discussion

## Why SQLite in the local demo

The current machine does not have Docker or PostgreSQL installed, so the runnable local demo uses SQLite while preserving a Postgres-ready schema and Docker Compose layout under `infra/`.

## Quick start

1. Install web dependencies:

```bash
cd apps/web
npm install
```

2. Start the analyzer:

```bash
cd ../../services/analyzer
python3 -m app.main
```

3. Start the web app:

```bash
cd ../../apps/web
npm run dev
```

4. Open `http://localhost:3007`

5. Run the built-in scan against:

`/Users/ashfak/Desktop/Jobs/Latent Defense/diffshield-vuln-demo`

## Demo flow

- Start a scan from the homepage
- Open the generated scan detail page
- Show:
  - extracted assets
  - asset relationships
  - findings
  - evidence
  - remediations
- trace events

## Repos

- Product repo: `diffshield-demo`
- Toy target repo: `diffshield-vuln-demo`

## Test commands

```bash
cd services/analyzer
python3 -m app.main
```

```bash
cd apps/web
npm run build
```
