#!/bin/sh
# Docker entrypoint — ingest KB at runtime if API key available, then start API.

set -e

if [ -n "${OPENAI_API_KEY:-}" ] || [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo "→ Ingesting knowledge base (data/knowledge)..."
  uv run agentflow-ingest data/knowledge --recursive || echo "⚠️  Ingest failed (non-fatal)"
else
  echo "⚠️  No API key found — skipping ingest. KB will use keyword fallback."
fi

PORT="${AGENTFLOW_PORT:-8081}"
echo "→ Starting Agentflow API on :${PORT}..."
exec uv run uvicorn agentflow.api.main:app --host 0.0.0.0 --port "${PORT}"
