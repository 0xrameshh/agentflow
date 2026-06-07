"""Agentflow FastAPI application — Knowledge Copilot.

Ingests documents (Markdown, PDF, TXT), answers questions with cited sources.

Endpoints:
- GET /health — liveness check
- POST /run — single agent run (returns answer)
- POST /run/full — single agent run (returns answer + metadata)
- POST /run/support — KB copilot (returns answer + citations)
- POST /run/support/stream — KB copilot SSE stream (chunks + citations)
- POST /run/supervisor — multi-agent supervisor run
- POST /eval — run full eval suite and return report
- GET /threads/{thread_id}/history — return message history
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agentflow.config import require_api_key
from agentflow.eval.runner import run_eval_suite
from agentflow.graph.builder import run_agent_with_state
from agentflow.graph.supervisor import run_supervisor_with_state
from agentflow.graph.tracing import write_trace

app = FastAPI(
    title="Agentflow — Knowledge Copilot",
    description="Document Q&A with cited sources. Ingest markdown, PDFs, and text; get cited answers via LangGraph.",
    version="0.2.0",
)

# ---------------------------------------------------------------------------
# CORS — allow Next.js dev server
# ---------------------------------------------------------------------------

CORS_ORIGINS = os.getenv("AGENTFLOW_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
_origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/")
def root() -> dict:
    """API root — chat UI lives in Next.js (web/)."""
    return {
        "name": "Agentflow — Knowledge Copilot",
        "version": "0.2.0",
        "ui": "Run the Next.js app: cd web && bun dev → http://localhost:3000",
        "health": "/health",
        "chat": "POST /run/support",
        "chat_stream": "POST /run/support/stream",
    }


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


class Citation(BaseModel):
    source: str
    snippet: str
    file_type: str | None = None
    page: int | None = None


class SupportRunResponse(BaseModel):
    answer: str
    citations: list[Citation]
    thread_id: str
    run_id: str
    tool_call_count: int
    revision_count: int
    latency_ms: int


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
# Citation extraction
# ---------------------------------------------------------------------------

# Matches [source: filename.ext] or [source: filename.pdf p.N]
CITATION_PATTERN = re.compile(r"\[source:\s*([^\]]+?)(?:\s+p\.(\d+))?\]")


def _extract_citations(state: dict) -> list[Citation]:
    """Walk tool messages for search_knowledge results and extract citations."""
    seen: set[str] = set()
    citations: list[Citation] = []

    for msg in state.get("messages", []):
        msg_type = getattr(msg, "type", None)
        if msg_type != "tool" or getattr(msg, "name", None) != "search_knowledge":
            continue

        content = getattr(msg, "content", "") or ""

        # Find [source: ...] markers
        for match in CITATION_PATTERN.finditer(content):
            source = match.group(1).strip()
            page_str = match.group(2)
            page = int(page_str) if page_str else None

            key = f"{source}:p{page}" if page else source
            if key in seen:
                continue
            seen.add(key)

            # Extract snippet following this source marker
            idx = content.find(f"[source: {source}]" if not page else match.group(0))
            snippet = ""
            if idx >= 0:
                snippet_start = idx + len(match.group(0))
                next_marker = content.find("[source:", snippet_start)
                if next_marker >= 0:
                    snippet = content[snippet_start:next_marker].strip()
                else:
                    snippet = content[snippet_start:].strip()
                snippet = snippet.replace("\n", " ")[:200].strip()

            # Determine file_type from extension
            file_type = None
            if "." in source:
                ext = source.rsplit(".", 1)[1].lower()
                if ext in ("md", "txt", "pdf"):
                    file_type = ext

            citations.append(
                Citation(
                    source=source,
                    snippet=snippet or f"Cited from {source}",
                    file_type=file_type,
                    page=page,
                )
            )

    return citations


def _extract_answer(state: dict) -> str:
    """Extract the final assistant answer from state messages."""
    for msg in reversed(state["messages"]):
        if hasattr(msg, "tool_calls") and not getattr(msg, "tool_calls", None):
            content = getattr(msg, "content", "")
            if content:
                return content.strip()
    last = state["messages"][-1]
    return (getattr(last, "content", None) or str(last)).strip()


def _strip_inline_sources(text: str) -> str:
    """Remove inline [source: ...] markers; citations are returned separately."""
    cleaned = CITATION_PATTERN.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def _format_sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _execute_support_run(message: str, thread_id: str) -> tuple[dict, str, list[Citation], int]:
    """Run the knowledge copilot graph and persist trace/history."""
    started = time.perf_counter()
    require_api_key()
    state = run_agent_with_state(message, thread_id=thread_id)
    answer = _strip_inline_sources(_extract_answer(state))
    citations = _extract_citations(state)
    latency_ms = int(round((time.perf_counter() - started) * 1000))

    write_trace(state, thread_id=thread_id)
    _store_thread_message(thread_id, "user", message)
    _store_thread_message(thread_id, "assistant", answer)

    return state, answer, citations, latency_ms


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
        answer = _extract_answer(state)

        write_trace(state, thread_id=request.thread_id)
        _store_thread_message(request.thread_id, "user", request.message)
        _store_thread_message(request.thread_id, "assistant", answer)

        return RunResponse(
            answer=answer,
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
        answer = _extract_answer(state)

        trace_path = write_trace(state, thread_id=request.thread_id)
        _store_thread_message(request.thread_id, "user", request.message)
        _store_thread_message(request.thread_id, "assistant", answer)

        return RunFullResponse(
            answer=answer,
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
            state = run_agent_with_state(request.message, thread_id=request.thread_id)
            answer = _extract_answer(state)

            write_trace(state, thread_id=request.thread_id)
            _store_thread_message(request.thread_id, "user", request.message)
            _store_thread_message(request.thread_id, "assistant", answer)

            chunk_size = 50
            for i in range(0, len(answer), chunk_size):
                chunk = answer[i : i + chunk_size]
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        except RuntimeError as e:
            yield f"data: ERROR: {e}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/run/support", response_model=SupportRunResponse)
def run_support(request: RunRequest) -> SupportRunResponse:
    """Run the knowledge copilot and return the answer with citations."""
    _check_rate_limit()
    try:
        state, answer, citations, latency_ms = _execute_support_run(
            request.message, request.thread_id
        )
        return SupportRunResponse(
            answer=answer,
            citations=citations,
            thread_id=request.thread_id,
            run_id=state.get("run_id", ""),
            tool_call_count=state.get("tool_call_count", 0),
            revision_count=state.get("revision_count", 0),
            latency_ms=latency_ms,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/run/support/stream")
async def run_support_stream(request: RunRequest):
    """SSE stream for the knowledge copilot.

    Events (JSON in ``data:`` lines):
    - ``{"type":"status","phase":"searching"}`` — agent is running
    - ``{"type":"chunk","text":"..."}`` — answer text chunk
    - ``{"type":"done","citations":[],"run_id":"","latency_ms":0,...}`` — final metadata
    - ``{"type":"error","message":"..."}`` — on failure
    """
    _check_rate_limit()

    async def event_generator():
        try:
            yield _format_sse({"type": "status", "phase": "searching"})

            state, answer, citations, latency_ms = await asyncio.to_thread(
                _execute_support_run, request.message, request.thread_id
            )

            chunk_size = 24
            for i in range(0, len(answer), chunk_size):
                yield _format_sse({"type": "chunk", "text": answer[i : i + chunk_size]})
                await asyncio.sleep(0.012)

            yield _format_sse(
                {
                    "type": "done",
                    "answer": answer,
                    "citations": [c.model_dump() for c in citations],
                    "thread_id": request.thread_id,
                    "run_id": state.get("run_id", ""),
                    "tool_call_count": state.get("tool_call_count", 0),
                    "revision_count": state.get("revision_count", 0),
                    "latency_ms": latency_ms,
                }
            )
        except RuntimeError as exc:
            yield _format_sse({"type": "error", "message": str(exc)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/run/supervisor", response_model=RunFullResponse)
def run_supervisor_endpoint(request: RunRequest) -> RunFullResponse:
    """Run the multi-agent supervisor graph."""
    _check_rate_limit()
    try:
        require_api_key()
        state = run_supervisor_with_state(request.message, thread_id=request.thread_id)
        answer = _extract_answer(state)

        trace_path = write_trace(state, thread_id=request.thread_id)
        _store_thread_message(request.thread_id, "user", request.message)
        _store_thread_message(request.thread_id, "assistant", answer)

        return RunFullResponse(
            answer=answer,
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


@app.get("/kb/articles")
def kb_articles() -> dict:
    """List available knowledge base documents."""
    from agentflow.config import SAMPLE_DOCS_DIR

    kb_dir = Path(SAMPLE_DOCS_DIR)
    articles: list[str] = []
    if kb_dir.exists():
        for path in sorted(kb_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in (".md", ".txt", ".pdf"):
                articles.append(path.name)
    return {"articles": articles, "count": len(articles)}


def run_server() -> None:
    import os

    import uvicorn

    import agentflow.config  # noqa: F401 — loads .env

    port = int(os.getenv("AGENTFLOW_PORT", "8081"))
    uvicorn.run("agentflow.api.main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    run_server()
