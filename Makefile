.PHONY: install dev eval api

install:
	uv sync

dev: install
	uv run agentflow-api

eval:
	uv run agentflow-eval

api:
	uv run agentflow-api
