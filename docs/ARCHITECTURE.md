# Architecture

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
    run_id: str                           # unique run identifier
    tool_call_count: int                  # loop guard (max 8)
    revision_count: int                   # loop guard (max 3)
    error: str | None                     # terminal error
    trace: Annotated[list[dict], add]     # append-only trace events
    critic_scores: Annotated[list[CriticScore], add]  # append-only scores
```

### Routing

1. `START → init_run → agent`
2. `agent → run_tools` when model emitted tool calls
3. `agent → structured_critic` when no tool calls
4. `run_tools → agent`
5. `structured_critic → agent` if score < 4 (revision), else `END`

### Loop guards

- **Max tool iterations:** 8 — prevents infinite tool-calling loops
- **Max revisions:** 3 — prevents critic from endlessly requesting revisions

## Structured critic

The critic node calls the LLM with a system prompt asking for JSON scoring:

```json
{"grounded": 4, "complete": 3, "concise": 4, "overall": 3, "feedback": "Missing specific examples"}
```

If `overall >= 4`, the answer passes. Otherwise, the feedback is injected as a `REVISE:` message.

## Tracing

Every run writes a JSON file to `runs/<run_id>.json`:

```json
{
  "run_id": "a1b2c3d4e5f6",
  "thread_id": "default",
  "timestamp": 1717670000.0,
  "question": "What is RAG?",
  "answer_snippet": "RAG stands for Retrieval-Augmented Generation...",
  "tool_call_count": 2,
  "revision_count": 0,
  "critic_scores": [{"grounded": 4, "complete": 4, "concise": 4, "overall": 4, "feedback": ""}],
  "trace_events": [
    {"node": "init_run", "ts": 1717670000.0, "run_id": "a1b2c3d4e5f6"},
    {"node": "call_model", "ts": 1717670000.1, "tokens_estimate": 45},
    {"node": "run_tools", "ts": 1717670000.3, "tools_called": ["search_knowledge"]},
    {"node": "structured_critic", "ts": 1717670000.5, "score": 4, "feedback": ""}
  ]
}
```

## RAG pipeline

See [RAG.md](RAG.md) for the full pipeline.

## Tools

| Tool | Purpose |
|------|---------|
| `calculator` | Deterministic math for eval tasks |
| `search_knowledge` | Chroma vector search with keyword fallback, source citations |
| `web_search` | Stub index for LangGraph / MCP / RAG topics |

## Eval harness

`eval/tasks.yaml` defines 15 golden prompts across math / knowledge / search / multi-step / edge cases.

`uv run agentflow-eval` runs all tasks, prints JSON, and writes `eval/reports/report-*.json`.

Metrics: pass rate, per-task latency, token estimates.

## API layer

FastAPI wraps:

- `POST /run` — single agent run (returns answer)
- `POST /run/full` — single agent run (returns answer + metadata + trace file)
- `POST /eval` — run full eval suite

## Design notes

- **Custom graph** — explicit nodes and routing instead of a single prebuilt ReAct helper.
- **Structured critic** — scores answers before returning; triggers revision when quality is low.
- **Append-only trace** — each node appends events for post-run debugging.
- **Chroma + keyword fallback** — vector search when ingested; keyword match when Chroma is unavailable.
