# Case study: Agentflow

I built Agentflow as a document Q&A system for internal policies and runbooks. Ask a question, get an answer with citations you can check. This file explains how it works and how it was built.

## Why it exists

Chatbots that answer from memory will happily invent company policy. Agentflow keeps answers tied to a document library: it retrieves chunks, drafts an answer, runs a critic pass, and only ships answers that score 4 or higher, with sources attached.

## How it works

- Ingest: .md, .txt, .pdf into Chroma, with a keyword fallback that needs no API key
- Agent: LangGraph loop (init_run, agent, run_tools, structured_critic)
- Output: citations (source, page, chunk)
- API and UI: FastAPI with SSE streaming, Next.js chat
- MCP: same tools exposed for Cursor and Claude Desktop (mcp/README.md)
- Eval: YAML task suites, pass rate and latency

## Numbers

- 49 pytest tests (graph, RAG, API, supervisor)
- 92% pass rate on eval/tasks-knowledge.yaml (12 Q&A cases)
- ruff clean, CI green

## How it was built

Four phases, roughly:

1. Plan: I sketched the graph and the eval-first approach before writing the agent loop. The critic gate came from an early failure: drafts shipped without sources, so the critic became mandatory.
2. Build: tools and RAG were written alongside tests, so every behavior had a regression anchor from day one.
3. Debug: the hard part was retrieval quality, not the graph. Chroma silently returned empty collections, which is why the retriever falls back to keyword search, and why that path is tested without an API key.
4. Refine: the eval suite drove changes. 92% means 11 of 12 tasks pass; the failing case stays in the suite as a tracked gap.

Later, a maintenance pass found a real regression: the keyword fallback only scanned top-level files, so policies in subfolders were invisible. One-line fix (recursive glob over .md and .txt), suite went from 48 to 49 green. That is the loop working: a claim, a failing test, a minimal fix, a green suite.

## Lessons

- Test the fallback paths. The happy path works in demos; the fallback is what ships.
- The eval suite is the product. A tracked failing case is more honest than a curated green list.
- Share the same tools between the agent and MCP. One implementation, two surfaces.

## Run it

See the README. uv sync --extra dev, ingest data/knowledge, run agentflow-eval, or point an MCP client at the server module.
