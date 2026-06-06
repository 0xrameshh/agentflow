"""Graph builders for agentflow.

Provides two graphs:
1. ``research_graph`` — single-agent with tool loop + structured critic
2. (Phase 3) ``supervisor_graph`` — multi-agent with planner/researcher/writer
"""

from __future__ import annotations

import uuid
from functools import lru_cache

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

from agentflow.graph.nodes import (
    call_model,
    init_run,
    run_tools,
    should_continue,
    should_finish,
    structured_critic,
)
from agentflow.graph.state import AgentflowState, make_initial_state


# ---------------------------------------------------------------------------
# Research graph: init_run -> agent -> tools -> critic loop
# ---------------------------------------------------------------------------


def build_research_graph() -> StateGraph:
    """Single-agent graph with tool calling and structured critic loop."""
    workflow = StateGraph(AgentflowState)

    workflow.add_node("init_run", init_run)
    workflow.add_node("agent", call_model)
    workflow.add_node("run_tools", run_tools)
    workflow.add_node("structured_critic", structured_critic)

    workflow.add_edge(START, "init_run")
    workflow.add_edge("init_run", "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"run_tools": "run_tools", "structured_critic": "structured_critic"},
    )
    workflow.add_edge("run_tools", "agent")
    workflow.add_conditional_edges(
        "structured_critic",
        should_finish,
        {"agent": "agent", "__end__": END},
    )

    return workflow


@lru_cache(maxsize=1)
def get_compiled_graph():
    return build_research_graph().compile()


def run_agent(message: str, thread_id: str | None = None) -> str:
    """Run the research graph and return the final assistant answer."""
    graph = get_compiled_graph()
    run_id = uuid.uuid4().hex[:12]
    config = {"configurable": {"thread_id": thread_id or run_id}}
    result = graph.invoke(make_initial_state(message, run_id), config=config)

    # Walk backwards to find the last non-tool AI message
    for item in reversed(result["messages"]):
        if isinstance(item, AIMessage) and not item.tool_calls:
            return (item.content or "").strip()

    # Fallback: last message content
    last = result["messages"][-1]
    return (getattr(last, "content", None) or str(last)).strip()


def run_agent_with_state(message: str, thread_id: str | None = None) -> dict:
    """Run the research graph and return the full final state dict."""
    graph = get_compiled_graph()
    run_id = uuid.uuid4().hex[:12]
    config = {"configurable": {"thread_id": thread_id or run_id}}
    return graph.invoke(make_initial_state(message, run_id), config=config)
