.PHONY: install dev eval api ingest web web-dev lint test ci eval-knowledge web-build

install:
	uv sync --extra dev

dev: install
	uv run agentflow-api

eval:
	uv run agentflow-eval

eval-knowledge:
	uv run agentflow-eval --tasks eval/tasks-knowledge.yaml

api:
	uv run agentflow-api

ingest:
	uv run agentflow-ingest data/knowledge --recursive

web:
	cd web && bun dev

web-build:
	cd web && bun run build

lint:
	uv run ruff check src/ tests/
	cd web && bun run lint

test:
	uv run pytest tests/ -q

ci: lint test web-build
