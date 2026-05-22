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

2. Add local runtime vars at the repo root:

```bash
cp .env.example .env.local
```

3. Set `OPENAI_API_KEY` in `.env.local` if you want the validator to use the OpenAI pass.

4. Start the full demo:

```bash
./run-demo.sh
```

5. Open `http://localhost:3007`

6. Run the built-in scan against:

`/Users/ashfak/Desktop/Jobs/Latent Defense/diffshield-vuln-demo`

If you want a fresh demo state before the interview:

```bash
RESET_DB=1 ./run-demo.sh
```

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
./test-demo.sh
```

```bash
cd apps/web
npm run build
```
