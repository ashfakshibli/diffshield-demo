# DiffShield

DiffShield is a lightweight repo threat modeler built as a compact security systems example.

It scans a local target repo or public GitHub repo, extracts a tiny world model from code and deployment artifacts, generates candidate attack paths, validates findings, and suggests remediations.

## Stack

- Next.js + TypeScript UI
- Python analyzer service
- SQLite for the local runnable flow
- Postgres-backed hosted mode for deployment

## Why SQLite locally

The local flow keeps SQLite for quick startup while the hosted deployment path can switch to Postgres by setting `DATABASE_URL`.

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

`https://github.com/ashfakshibli/latent-defense-diffshield-vuln-demo`

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

## Deploy branch

The `deploy/heroku` branch adds:

- Heroku-friendly runtime ports
- optional Postgres persistence through `DATABASE_URL`
- public GitHub repo download for hosted scans
- GitHub Actions auto-deploy to Heroku on branch pushes

The local `main` branch remains the simplest local demo path.

## Repos

- Product repo: `diffshield-demo`
- Sample target repo: `diffshield-vuln-demo`

## Test commands

```bash
cd services/analyzer
python3 -m app.main
```

```bash
cd apps/web
npm run build
```
