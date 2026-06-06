"""Agentflow FastAPI application.

Endpoints:
- GET /health — liveness check
- POST /run — single agent run (returns answer)
- POST /run/full — single agent run (returns answer + metadata)
- POST /run/supervisor — multi-agent supervisor run
- POST /eval — run full eval suite and return report
- GET /threads/{thread_id}/history — return message history from checkpoint
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agentflow.config import require_api_key
from agentflow.eval.runner import run_eval_suite
from agentflow.graph.builder import run_agent_with_state
from agentflow.graph.supervisor import run_supervisor_with_state
from agentflow.graph.tracing import write_trace

app = FastAPI(
    title="Agentflow",
    description="LangGraph research agent with structured critic, tracing, and eval harness",
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class RunRequest(BaseModel):
    message: str = Field(min_length=1)
    thread_id: str = "default"


class RunResponse(BaseModel):
    answer: str
    thread_id: str
    run_id: str = ""


class RunFullResponse(BaseModel):
    answer: str
    thread_id: str
    run_id: str
    tool_call_count: int
    revision_count: int
    trace_file: str | None = None
    error: str | None = None


class ThreadHistoryResponse(BaseModel):
    thread_id: str
    messages: list[dict]


# ---------------------------------------------------------------------------
# Rate limiting (simple in-memory)
# ---------------------------------------------------------------------------

_rate_limits: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60.0  # seconds
RATE_LIMIT_MAX = 20  # requests per window


def _check_rate_limit(client_ip: str = "default") -> None:
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW
    _rate_limits[client_ip] = [t for t in _rate_limits[client_ip] if t > cutoff]
    if len(_rate_limits[client_ip]) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {RATE_LIMIT_MAX} requests per {RATE_LIMIT_WINDOW}s",
        )
    _rate_limits[client_ip].append(now)


# ---------------------------------------------------------------------------
# Thread history (in-memory store for demo)
# ---------------------------------------------------------------------------

_thread_history: dict[str, list[dict]] = defaultdict(list)


def _store_thread_message(thread_id: str, role: str, content: str) -> None:
    _thread_history[thread_id].append(
        {
            "role": role,
            "content": content,
            "timestamp": time.time(),
        }
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
def run(request: RunRequest) -> RunResponse:
    _check_rate_limit()
    try:
        require_api_key()
        state = run_agent_with_state(request.message, thread_id=request.thread_id)
        answer = ""
        for msg in reversed(state["messages"]):
            if hasattr(msg, "tool_calls") and not getattr(msg, "tool_calls", None):
                content = getattr(msg, "content", "")
                if content:
                    answer = content
                    break

        write_trace(state, thread_id=request.thread_id)
        _store_thread_message(request.thread_id, "user", request.message)
        _store_thread_message(request.thread_id, "assistant", answer.strip())

        return RunResponse(
            answer=answer.strip(),
            thread_id=request.thread_id,
            run_id=state.get("run_id", ""),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/run/full", response_model=RunFullResponse)
def run_full(request: RunRequest) -> RunFullResponse:
    _check_rate_limit()
    try:
        require_api_key()
        state = run_agent_with_state(request.message, thread_id=request.thread_id)
        answer = ""
        for msg in reversed(state["messages"]):
            if hasattr(msg, "tool_calls") and not getattr(msg, "tool_calls", None):
                content = getattr(msg, "content", "")
                if content:
                    answer = content
                    break

        trace_path = write_trace(state, thread_id=request.thread_id)
        _store_thread_message(request.thread_id, "user", request.message)
        _store_thread_message(request.thread_id, "assistant", answer.strip())

        return RunFullResponse(
            answer=answer.strip(),
            thread_id=request.thread_id,
            run_id=state.get("run_id", ""),
            tool_call_count=state.get("tool_call_count", 0),
            revision_count=state.get("revision_count", 0),
            trace_file=str(trace_path),
            error=state.get("error"),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/run/stream")
async def run_stream(request: RunRequest):
    """SSE streaming endpoint — streams agent messages as they arrive."""
    _check_rate_limit()

    async def event_generator():
        try:
            require_api_key()
            # For streaming, we'll run the agent and stream the result
            # In a production setup, you'd use agraph.astream()
            state = run_agent_with_state(request.message, thread_id=request.thread_id)
            answer = ""
            for msg in reversed(state["messages"]):
                if hasattr(msg, "tool_calls") and not getattr(msg, "tool_calls", None):
                    content = getattr(msg, "content", "")
                    if content:
                        answer = content
                        break

            write_trace(state, thread_id=request.thread_id)
            _store_thread_message(request.thread_id, "user", request.message)
            _store_thread_message(request.thread_id, "assistant", answer.strip())

            # Stream answer in chunks
            chunk_size = 50
            for i in range(0, len(answer), chunk_size):
                chunk = answer[i : i + chunk_size]
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        except RuntimeError as e:
            yield f"data: ERROR: {e}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/run/supervisor", response_model=RunFullResponse)
def run_supervisor_endpoint(request: RunRequest) -> RunFullResponse:
    """Run the multi-agent supervisor graph."""
    _check_rate_limit()
    try:
        require_api_key()
        state = run_supervisor_with_state(request.message, thread_id=request.thread_id)
        answer = ""
        for msg in reversed(state["messages"]):
            if hasattr(msg, "tool_calls") and not getattr(msg, "tool_calls", None):
                content = getattr(msg, "content", "")
                if content:
                    answer = content
                    break

        trace_path = write_trace(state, thread_id=request.thread_id)
        _store_thread_message(request.thread_id, "user", request.message)
        _store_thread_message(request.thread_id, "assistant", answer.strip())

        return RunFullResponse(
            answer=answer.strip(),
            thread_id=request.thread_id,
            run_id=state.get("run_id", ""),
            tool_call_count=state.get("tool_call_count", 0),
            revision_count=state.get("revision_count", 0),
            trace_file=str(trace_path),
            error=state.get("error"),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/threads/{thread_id}/history", response_model=ThreadHistoryResponse)
def thread_history(thread_id: str) -> ThreadHistoryResponse:
    """Return message history for a thread."""
    messages = _thread_history.get(thread_id, [])
    return ThreadHistoryResponse(thread_id=thread_id, messages=messages)


@app.post("/eval")
def eval_suite() -> dict:
    _check_rate_limit()
    try:
        require_api_key()
        report = run_eval_suite()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return report.to_dict()


def run_server() -> None:
    import uvicorn

    uvicorn.run("agentflow.api.main:app", host="0.0.0.0", port=8080, reload=False)


if __name__ == "__main__":
    run_server()
