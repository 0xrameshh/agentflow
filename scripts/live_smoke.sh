#!/usr/bin/env bash
# Live LLM smoke test — run BEFORE pushing to GitHub.
# Requires: cp .env.example .env and set OPENAI_API_KEY (or ANTHROPIC_API_KEY)
#
# Usage: bash scripts/live_smoke.sh

set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== Agentflow live LLM smoke test ==="
echo ""

if [ ! -f .env ]; then
  echo "❌ No .env file. Run: cp .env.example .env"
  echo "   Then add OPENAI_API_KEY=sk-... (or ANTHROPIC_API_KEY)"
  exit 1
fi

# shellcheck disable=SC1091
source .env 2>/dev/null || true

if [ -z "${OPENAI_API_KEY:-}" ] && [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "❌ Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env"
  exit 1
fi

echo "✅ API key found"
echo "   Provider: ${AGENTFLOW_MODEL_PROVIDER:-openai}"
echo "   Model:    ${AGENTFLOW_MODEL_NAME:-gpt-4o-mini}"
echo ""

echo "--- Test 1: Calculator (tool call) ---"
uv run python -c "
from agentflow.graph.builder import run_agent
answer = run_agent('Use the calculator: what is (48 / 6) + 15?')
print(answer)
assert '23' in answer, f'Expected 23 in answer, got: {answer!r}'
print('✅ Test 1 passed')
"

echo ""
echo "--- Test 2: Local knowledge (RAG-lite) ---"
uv run python -c "
from agentflow.graph.builder import run_agent
answer = run_agent('What is agentflow? Search local knowledge docs.')
print(answer)
lower = answer.lower()
assert 'agentflow' in lower or 'langgraph' in lower, f'Weak answer: {answer!r}'
print('✅ Test 2 passed')
"

echo ""
echo "--- Test 3: Supervisor graph ---"
uv run python -c "
from agentflow.graph.supervisor import run_supervisor
answer = run_supervisor('In 3 bullets: what is LangGraph vs MCP?')
print(answer)
assert len(answer) > 100, f'Answer too short: {answer!r}'
print('✅ Test 3 passed')
"

echo ""
echo "--- Test 4: Eval suite (15 tasks) ---"
uv run agentflow-eval 2>&1 | tee /tmp/agentflow-eval.log
PASS_RATE=$(uv run python -c "
import json, pathlib
reports = sorted(pathlib.Path('eval/reports').glob('report-*.json'))
if not reports:
    raise SystemExit('no report written')
data = json.loads(reports[-1].read_text())
print(data['pass_rate'])
")
echo "Pass rate: ${PASS_RATE}%"
if python3 -c "exit(0 if float('${PASS_RATE}') >= 80 else 1)"; then
  echo "✅ Test 4 passed (≥80%)"
else
  echo "⚠️  Pass rate below 80% — tune prompts/tasks before shipping"
  exit 1
fi

echo ""
echo "=== All live smoke tests passed ==="
echo "Safe to push to GitHub."
