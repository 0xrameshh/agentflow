"""Typed state for agentflow graphs.

Subclasses LangGraph's MessagesState (a TypedDict) and adds metadata
fields for tracing, loop guards, and critic scoring.

List fields that nodes append to use Annotated[list, operator.add]
reducers so returns like {"trace": [event]} APPEND rather than overwrite.
"""

from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Annotated, Any

from langgraph.graph import MessagesState


@dataclass
class CriticScore:
    """Structured critic output — scores on a 1–5 scale."""

    grounded: int = 0
    complete: int = 0
    concise: int = 0
    overall: int = 0
    feedback: str = ""

    @property
    def passes(self) -> bool:
        return self.overall >= 4


class AgentflowState(MessagesState):
    """Extended state for agentflow graphs.

    Adds to MessagesState:
    - ``run_id``: unique run identifier
    - ``tool_call_count``: tool invocation counter (loop guard)
    - ``revision_count``: critic revision counter (loop guard)
    - ``critic_scores``: append-only list of critic evaluations
    - ``trace``: append-only list of node trace events
    - ``error``: terminal error string if run fails
    """

    run_id: str = ""
    tool_call_count: int = 0
    revision_count: int = 0
    error: str | None = None
    # Append-only: nodes return {"trace": [event]} and reducer concatenates
    trace: Annotated[list[dict[str, Any]], operator.add] = []
    critic_scores: Annotated[list[CriticScore], operator.add] = []


def make_initial_state(message: str, run_id: str = "") -> dict:
    """Create a clean initial state dict for graph invocation."""
    from langchain_core.messages import HumanMessage

    return {
        "messages": [HumanMessage(content=message)],
        "run_id": run_id,
        "tool_call_count": 0,
        "revision_count": 0,
        "critic_scores": [],
        "trace": [],
        "error": None,
    }
