This is a [Next.js](https://nextjs.org) chat UI for the Agentflow document Q&A API.

The backend is Python FastAPI (`src/agentflow/`). This directory holds only the
frontend: chat components plus a thin client in `src/lib/api.ts` that calls the
API at `NEXT_PUBLIC_API_URL` (default `http://localhost:8081`).

## Commands (run inside `web/`)

```bash
bun install
bun dev        # Next.js on :3000, expects the API on :8081
bun run lint
bun run test   # vitest, UI and MCP client tests
bun run build
```

## Start the full stack (repo root)

```bash
uv run agentflow-api              # terminal 1, port 8081
cd web && bun install && bun dev  # terminal 2, port 3000
```

Ingest the sample KB first if Chroma is empty:

```bash
uv run agentflow-ingest data/knowledge --recursive
```
