#!/bin/sh
# Docker entrypoint — ingest KB at runtime if API key available, then start API.

set -e

if [ -n "${OPENAI_API_KEY:-}" ] || [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo "→ Ingesting support KB..."
  uv run agentflow-ingest data/support-kb || echo "⚠️  Ingest failed (non-fatal)"
else
  echo "⚠️  No API key found — skipping ingest. KB will use keyword fallback."
fi

echo "→ Starting FlowDesk Support KB Copilot API..."
exec uv run uvicorn agentflow.api.main:app --host 0.0.0.0 --port 8080
