#!/usr/bin/env bash
# Live LLM smoke test — run BEFORE pushing to GitHub.
# Requires: cp .env.example .env and set OPENAI_API_KEY (or ANTHROPIC_API_KEY)
#
# Usage: bash scripts/live_smoke.sh

set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== Knowledge Copilot — live LLM smoke test ==="
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
echo "--- Test 2: Knowledge base (expense policy) ---"
uv run python -c "
from agentflow.graph.builder import run_agent
answer = run_agent('What is the meal expense limit per day? Search the KB.')
print(answer)
lower = answer.lower()
assert '75' in lower or 'meal' in lower, f'Weak answer: {answer!r}'
print('✅ Test 2 passed')
"

echo ""
echo "--- Test 3: Supervisor graph ---"
uv run python -c "
from agentflow.graph.supervisor import run_supervisor
answer = run_supervisor('What are the SEV1 incident response requirements?')
print(answer)
assert len(answer) > 100, f'Answer too short: {answer!r}'
print('✅ Test 3 passed')
"

echo ""
echo "--- Test 4: Domain-agnostic eval suite (13 tasks) ---"
uv run agentflow-eval --tasks eval/tasks-knowledge.yaml 2>&1 | tee /tmp/agentflow-eval.log
PASS_RATE=$(uv run python -c "
import json, pathlib
reports = sorted(pathlib.Path('eval/reports').glob('report-*.json'))
if not reports:
    raise SystemExit('no report written')
data = json.loads(reports[-1].read_text())
print(data['pass_rate'])
")
echo "Knowledge KB pass rate: ${PASS_RATE}%"
if python3 -c "exit(0 if float('${PASS_RATE}') >= 85 else 1)"; then
  echo "✅ Test 4 passed (≥85%)"
else
  echo "⚠️  Knowledge KB pass rate below 85% — tune prompts/tasks before shipping"
  exit 1
fi

echo ""
echo "=== All live smoke tests passed ==="
echo "Safe to push to GitHub."
