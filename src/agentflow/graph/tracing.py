"""Structured run tracing — writes per-run JSON to runs/ directory.

Each run produces a JSON file with:
- run_id, thread_id, timestamps
- node events (from state.trace)
- tool call count, revision count
- final answer snippet
- critic scores
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

RUNS_DIR = Path(os.getenv("AGENTFLOW_RUNS_DIR", "runs"))


def write_trace(state: dict[str, Any], thread_id: str = "default") -> Path:
    """Write a trace JSON file from the final graph state.

    Returns the path to the written file.
    """
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    run_id = state.get("run_id", "unknown")
    trace_events = state.get("trace", [])
    messages = state.get("messages", [])
    critic_scores = state.get("critic_scores", [])

    # Extract answer
    answer = ""
    for msg in reversed(messages):
        if hasattr(msg, "tool_calls") and not getattr(msg, "tool_calls", None):
            content = getattr(msg, "content", "")
            if content:
                answer = content
                break

    # Extract user question
    question = ""
    for msg in messages:
        content = getattr(msg, "content", "")
        if content and not content.startswith("REVISE"):
            question = content
            break

    # Serialize critic scores (handle both dataclass and dict)
    serialized_scores = []
    for score in critic_scores:
        if hasattr(score, "__dict__"):
            serialized_scores.append(score.__dict__)
        elif isinstance(score, dict):
            serialized_scores.append(score)
        else:
            serialized_scores.append(str(score))

    # Serialize trace events (handle float timestamps)
    serialized_trace = []
    for event in trace_events:
        if isinstance(event, dict):
            serialized_trace.append(event)
        else:
            serialized_trace.append(str(event))

    trace = {
        "run_id": run_id,
        "thread_id": thread_id,
        "timestamp": time.time(),
        "question": question[:500],
        "answer_snippet": answer[:500],
        "tool_call_count": state.get("tool_call_count", 0),
        "revision_count": state.get("revision_count", 0),
        "error": state.get("error"),
        "critic_scores": serialized_scores,
        "trace_events": trace_events,
    }

    out_file = RUNS_DIR / f"{run_id}.json"
    out_file.write_text(json.dumps(trace, indent=2, default=str), encoding="utf-8")
    return out_file
