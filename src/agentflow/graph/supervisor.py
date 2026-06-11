"""Multi-agent supervisor graph.

Architecture:
    START → supervisor → [researcher | writer | END]

The supervisor is a router LLM that decides:
- Does this need research? → call researcher (has tools)
- Is the answer ready? → call writer (no tools, synthesizes final answer)
- Are we done? → END

This is the "unique" second graph that differentiates agentflow from
single-agent tutorials. It demonstrates:
- Manual routing (not just create_react_agent)
- Specialized sub-agents with different tool access
- Supervisor decision-making with FINISH signal
"""

from __future__ import annotations

import time
import uuid
from functools import lru_cache

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from agentflow.config import get_chat_model
from agentflow.graph.state import AgentflowState, make_initial_state

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SUPERVISOR_PROMPT = """You are a supervisor managing a document copilot team.

Your job is to decide the next step for the user's request.

Available workers:
- "researcher": Has access to tools (search_knowledge for the indexed document library, calculator).
  Use this when the question needs policy lookups, runbook steps, or fact-finding.
- "writer": No tools. Synthesizes a final polished answer from research findings.
- "FINISH": The task is complete. Use this when the writer has already produced a final answer.

Rules:
1. Start with "researcher" for any question that needs document or policy info.
2. After researcher provides findings, route to "writer".
3. After writer produces the answer, respond with "FINISH".
4. Maximum 2 researcher rounds before routing to writer.
5. For simple questions (greetings), go straight to "writer".

Return ONLY one of: "researcher", "writer", or "FINISH"
No explanation, no quotes, just the word."""

RESEARCHER_PROMPT = """You are a researcher for the document copilot.

Your job: gather facts from the indexed knowledge base using your tools. Be thorough but concise.

Tools available:
- search_knowledge: Search policies, runbooks, manuals, and notes in the KB
- calculator: Do math calculations

After gathering information, provide a structured research brief with:
- Key findings (bullet points)
- KB sources used with [source: filename.md]
- Confidence level (high/medium/low)

Do NOT write a final polished answer — that's the writer's job.
"""

WRITER_PROMPT = """You are a writer for the document copilot.

You receive research findings from the researcher and produce a polished,
well-structured final answer for the user.

Rules:
1. Synthesize the research into a clear, actionable response.
2. Cite KB sources when available: [source: filename.md].
3. Be concise and practical (steps, timelines, exceptions).
4. Keep answers under 300 words unless asked for detail.
5. Do NOT call any tools — you only write."""


# ---------------------------------------------------------------------------
# Supervisor routing
# ---------------------------------------------------------------------------


def supervisor_node(state: AgentflowState) -> dict:
    """Route to the next worker or FINISH."""
    model = get_chat_model()
    messages = state["messages"]

    # Count researcher rounds to prevent infinite loops
    researcher_rounds = sum(
        1
        for m in messages
        if isinstance(m, HumanMessage) and m.content.startswith("[Researcher findings]")
    )

    # If we've had 2 researcher rounds, force to writer
    if researcher_rounds >= 2:
        route = "writer"
    else:
        response = model.invoke(
            [
                SystemMessage(content=SUPERVISOR_PROMPT),
                *messages,
            ]
        )
        raw = (response.content or "").strip().strip('"').strip("'").lower()

        if "finish" in raw:
            route = "FINISH"
        elif "writer" in raw:
            route = "writer"
        else:
            route = "researcher"

    return {
        "messages": [],
        "trace": [{"node": "supervisor", "ts": time.time(), "route": route}],
    }


def supervisor_route(state: AgentflowState) -> str:
    """Read the supervisor's decision from trace events."""
    trace = state.get("trace", [])
    if not trace:
        return "writer"

    last_event = trace[-1]
    if isinstance(last_event, dict) and "route" in last_event:
        route = last_event["route"]
        if route == "FINISH":
            return "__end__"
        return route

    return "writer"


# ---------------------------------------------------------------------------
# Researcher sub-agent (has tools)
# ---------------------------------------------------------------------------


def researcher_node(state: AgentflowState) -> dict:
    """Researcher: calls LLM with tools, gathers facts."""
    from agentflow.graph.nodes import _ensure_model

    model, tool_by_name = _ensure_model()
    researcher_model = model  # Already has tools bound

    # Build researcher messages
    user_msgs = [m for m in state["messages"] if isinstance(m, HumanMessage)]
    last_question = user_msgs[-1].content if user_msgs else ""

    messages = [
        SystemMessage(content=RESEARCHER_PROMPT),
        HumanMessage(content=last_question),
    ]

    # Allow tool calling loop (max 3 iterations)
    for _ in range(3):
        response = researcher_model.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        # Execute tools
        from langchain_core.messages import ToolMessage

        for call in response.tool_calls:
            tool = tool_by_name.get(call["name"])
            if tool is None:
                content = f"Unknown tool: {call['name']}"
            else:
                content = tool.invoke(call["args"])
            messages.append(
                ToolMessage(content=str(content), tool_call_id=call["id"], name=call["name"])
            )

    # Extract the final text (non-tool) response
    findings = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            findings = msg.content or ""
            break

    return {
        "messages": [HumanMessage(content=f"[Researcher findings]: {findings}")],
        "trace": [{"node": "researcher", "ts": time.time(), "findings_length": len(findings)}],
    }


# ---------------------------------------------------------------------------
# Writer sub-agent (no tools)
# ---------------------------------------------------------------------------


def writer_node(state: AgentflowState) -> dict:
    """Writer: synthesizes research into a polished answer."""
    model = get_chat_model()

    # Gather all context
    user_msgs = [m for m in state["messages"] if isinstance(m, HumanMessage)]
    researcher_msgs = [
        m
        for m in state["messages"]
        if isinstance(m, HumanMessage) and m.content.startswith("[Researcher findings]")
    ]

    original_question = user_msgs[0].content if user_msgs else ""
    research_findings = (
        "\n\n".join(m.content for m in researcher_msgs)
        if researcher_msgs
        else "No research findings."
    )

    messages = [
        SystemMessage(content=WRITER_PROMPT),
        HumanMessage(
            content=f"Original question: {original_question}\n\nResearch findings:\n{research_findings}\n\nWrite the final answer."
        ),
    ]

    response = model.invoke(messages)
    answer = (response.content or "").strip()

    return {
        "messages": [AIMessage(content=answer)],
        "trace": [{"node": "writer", "ts": time.time(), "answer_length": len(answer)}],
    }


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_supervisor_graph() -> StateGraph:
    """Multi-agent graph: supervisor routes to researcher or writer."""
    workflow = StateGraph(AgentflowState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("writer", writer_node)

    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        supervisor_route,
        {
            "researcher": "researcher",
            "writer": "writer",
            "__end__": END,
        },
    )
    # After researcher, go back to supervisor for next decision
    workflow.add_edge("researcher", "supervisor")
    # After writer, we're done
    workflow.add_edge("writer", END)

    return workflow


@lru_cache(maxsize=1)
def get_compiled_supervisor_graph():
    return build_supervisor_graph().compile()


def run_supervisor(message: str, thread_id: str | None = None) -> str:
    """Run the supervisor graph and return the final answer."""
    graph = get_compiled_supervisor_graph()
    run_id = uuid.uuid4().hex[:12]
    config = {"configurable": {"thread_id": thread_id or run_id}}
    result = graph.invoke(make_initial_state(message, run_id), config=config)

    # Find the last AI message (from writer)
    for item in reversed(result["messages"]):
        if isinstance(item, AIMessage) and not item.tool_calls:
            return (item.content or "").strip()

    last = result["messages"][-1]
    return (getattr(last, "content", None) or str(last)).strip()


def run_supervisor_with_state(message: str, thread_id: str | None = None) -> dict:
    """Run the supervisor graph and return the full final state."""
    graph = get_compiled_supervisor_graph()
    run_id = uuid.uuid4().hex[:12]
    config = {"configurable": {"thread_id": thread_id or run_id}}
    return graph.invoke(make_initial_state(message, run_id), config=config)
