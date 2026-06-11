# Architecture

## Product: Enterprise Document Copilot

**Agentflow** is an industry-agnostic document Q&A system. Users point at a folder of files (Markdown, PDF, text); the system ingests, indexes, and answers with cited sources.

**Example tenant:** `data/tenants/support-saas/` — sample SaaS support articles for tenant evals. The primary demo KB is `data/knowledge/` (mixed formats).

**Flow:**
1. User asks a question in the Next.js chat UI (`web/`, port 3000)
2. Frontend calls `POST /run/support` on FastAPI (port 8081)
3. `search_knowledge` queries Chroma (or keyword fallback) against ingested docs
4. LLM synthesizes answer with citations (`[source: file.pdf p.3]`)
5. Structured critic scores grounding, completeness, conciseness
6. API returns `{ answer, citations[], latency_ms }`
7. UI renders markdown + expandable citation chips

## System layers

```
┌─────────────────────────────────────────┐
│  web/  Next.js 15  (localhost:3000)    │
│  Chat.tsx → lib/api.ts                  │
└──────────────────┬──────────────────────┘
                   │  CORS + fetch
┌──────────────────▼──────────────────────┐
│  FastAPI  (agentflow.api.main)  :8081   │
│  POST /run/support, GET /kb/articles    │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  LangGraph StateGraph                     │
│  init_run → agent → tools → critic        │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  RAG: loaders → ingest → Chroma           │
│  .md .txt .pdf  (data/knowledge/)         │
└─────────────────────────────────────────┘
```

## Graph design

Agentflow uses a custom **LangGraph** `StateGraph` over `MessagesState`:

### Research graph

```
START → init_run → agent → [run_tools | structured_critic] → END
                                  ↑          ↓
                                  └──────────┘ (revision loop)
```

| Node | Role |
|------|------|
| `init_run` | Assigns `run_id`, emits start trace |
| `agent` | Calls the chat model with bound tools |
| `run_tools` | Executes tool calls from the last AI message |
| `structured_critic` | LLM scores answer on `{grounded, complete, concise}` (1–5); revises if score < 4 |

### State schema

```python
class AgentflowState(MessagesState):
    run_id: str
    tool_call_count: int
    revision_count: int
    error: str | None
    trace: Annotated[list[dict], add]
    critic_scores: Annotated[list[CriticScore], add]
```

### Loop guards

- **Max tool iterations:** 8
- **Max revisions:** 3

## Structured critic

The critic scores answers before returning. If `overall < 4`, feedback is injected as a `REVISE:` message and the agent loops.

## Tracing

Every run writes `runs/<run_id>.json` with trace events, critic scores, and tool call counts.

## RAG pipeline

See [RAG.md](RAG.md) for loaders, ingest, and citation format.

## Tools

| Tool | Purpose |
|------|---------|
| `search_knowledge` | Chroma vector search + keyword fallback; primary for KB questions |
| `calculator` | Deterministic math for eval tasks |
| `web_search` | Stub index (supplementary) |

## Eval harness

| File | Purpose |
|------|---------|
| `eval/tasks-knowledge.yaml` | 12 domain-agnostic tasks (md, txt, pdf, grounding) |
| `eval/tasks-support-kb.yaml` | 16 support-SaaS tenant tasks |
| `eval/tasks.yaml` | Original generic graph tasks |

```bash
uv run agentflow-eval --tasks eval/tasks-knowledge.yaml
```

Target: ≥ 85% pass rate with `gpt-4o-mini`.

## API layer

| Endpoint | Description |
|----------|-------------|
| `GET /` | API info JSON (UI is Next.js at `:3000`) |
| `GET /health` | Liveness |
| `POST /run/support` | Knowledge copilot — answer + citations |
| `POST /run`, `/run/full`, `/run/stream` | Agent runs |
| `POST /run/supervisor` | Multi-agent graph |
| `GET /kb/articles` | List indexed documents |
| `POST /eval` | Run eval suite |
| `GET /threads/{id}/history` | Thread history (in-memory) |

## Design notes

- **Custom graph** — explicit nodes and routing, not a single ReAct helper
- **Structured critic** — quality gate before returning answers
- **Multi-format loaders** — `src/agentflow/rag/loaders.py` for md/txt/pdf
- **Split frontend** — Next.js for UI; Python for agent logic
