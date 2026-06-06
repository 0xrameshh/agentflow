# Agentflow overview

Agentflow is a LangGraph agent runtime with two graphs: a single-agent research loop (tools + structured critic) and a supervisor multi-agent flow.

Components include a YAML regression eval harness, JSON run traces, Chroma-backed document retrieval with keyword fallback, FastAPI endpoints, and an MCP server that exposes the same tools.

Stack: Python, LangGraph, LangChain, ChromaDB, FastAPI.
