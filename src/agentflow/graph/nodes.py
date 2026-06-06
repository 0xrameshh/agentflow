"""Graph nodes for the agentflow research graph.

Nodes are pure functions that take state and return partial state updates.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agentflow.config import get_chat_model
from agentflow.graph.state import AgentflowState, CriticScore
from agentflow.tools import ALL_TOOLS

# ---------------------------------------------------------------------------
# Limits
# ---------------------------------------------------------------------------
MAX_TOOL_ITERATIONS = 8
MAX_REVISIONS = 3

SYSTEM_PROMPT = """You are a research assistant for software engineering topics.

Use tools when you need facts from local docs, stub web search, or math.
Prefer search_knowledge for project-specific questions.
After using tools, give a concise, accurate final answer.
If a critic message says REVISE, fix gaps and answer again.
Keep final answers under 300 words unless asked for detail.
"""

CRITIC_PROMPT = """You are a strict critic evaluating the last assistant answer.

Score the answer on three dimensions (1-5 each):
- grounded: Is it backed by evidence from tools or known facts?
- complete: Does it fully address the user's question?
- concise: Is it clear and free of unnecessary fluff?

Return ONLY a JSON object:
{{"grounded": <1-5>, "complete": <1-5>, "concise": <1-5>, "overall": <1-5>, "feedback": "<one sentence with specific fix if overall < 4>"}}

Overall = average of the three scores, rounded down.
"""

_model_with_tools = None
_tool_by_name: dict | None = None


def _ensure_model():
    global _model_with_tools, _tool_by_name
    if _model_with_tools is None:
        model = get_chat_model()
        _model_with_tools = model.bind_tools(ALL_TOOLS)
        _tool_by_name = {tool.name: tool for tool in ALL_TOOLS}
    return _model_with_tools, _tool_by_name


def _get_critic_model():
    return get_chat_model()


def _emit_trace(node: str, detail: dict | None = None) -> dict:
    """Return a trace event to append to state.

    With operator.add reducer on trace, returning {"trace": [event]}
    appends to the existing list automatically.
    """
    event = {"node": node, "ts": time.time(), **(detail or {})}
    return {"trace": [event]}


# ---------------------------------------------------------------------------
# Core nodes
# ---------------------------------------------------------------------------


def init_run(state: AgentflowState) -> dict:
    """Entry node: assign a run_id if missing and emit a start trace."""
    run_id = state.get("run_id") or uuid.uuid4().hex[:12]
    updates: dict = {"run_id": run_id}
    updates.update(_emit_trace("init_run", {"run_id": run_id}))
    return updates


def call_model(state: AgentflowState) -> dict:
    """Invoke the LLM with tool bindings."""
    model, _ = _ensure_model()
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    response = model.invoke(messages)

    trace_update = _emit_trace(
        "call_model",
        {
            "tokens_estimate": len(str(response.content or "")) // 4,
        },
    )
    return {"messages": [response], **trace_update}


def run_tools(state: AgentflowState) -> dict:
    """Execute tool calls from the last AI message."""
    _, tool_by_name = _ensure_model()
    last = state["messages"][-1]
    if not isinstance(last, AIMessage) or not last.tool_calls:
        return {"messages": []}

    # Guard: check tool call count
    current_count = state.get("tool_call_count", 0)
    if current_count >= MAX_TOOL_ITERATIONS:
        error_msg = f"Max tool iterations ({MAX_TOOL_ITERATIONS}) reached. Stopping."
        return {
            "messages": [HumanMessage(content=f"STOP: {error_msg}")],
            "error": error_msg,
        }

    from langchain_core.messages import ToolMessage

    tool_messages = []
    tool_names = []
    for call in last.tool_calls:
        tool = tool_by_name.get(call["name"])
        if tool is None:
            content = f"Unknown tool: {call['name']}"
        else:
            content = tool.invoke(call["args"])
        tool_names.append(call["name"])
        tool_messages.append(
            ToolMessage(content=str(content), tool_call_id=call["id"], name=call["name"])
        )

    trace_update = _emit_trace("run_tools", {"tools_called": tool_names})
    return {
        "messages": tool_messages,
        "tool_call_count": current_count + len(tool_messages),
        **trace_update,
    }


def structured_critic(state: AgentflowState) -> dict:
    """Structured critic: score the last answer on grounded/complete/concise."""
    messages = state["messages"]
    last_ai = next(
        (m for m in reversed(messages) if isinstance(m, AIMessage) and not m.tool_calls),
        None,
    )
    if last_ai is None:
        return {"messages": []}

    answer = (last_ai.content or "").strip()
    if not answer:
        return {"messages": []}

    # Check revision limit
    revision_count = state.get("revision_count", 0)
    if revision_count >= MAX_REVISIONS:
        trace_update = _emit_trace("critic", {"action": "skip_max_revisions"})
        return {"messages": [], **trace_update}

    # Get the original user question
    user_msg = next(
        (
            m
            for m in messages
            if isinstance(m, HumanMessage) and not m.content.startswith("REVISE:")
        ),
        None,
    )
    user_question = (user_msg.content if user_msg else "") if user_msg else ""

    # Call critic LLM
    critic_model = _get_critic_model()
    critic_input = [
        SystemMessage(content=CRITIC_PROMPT),
        HumanMessage(content=f"User question: {user_question}\n\nAssistant answer:\n{answer}"),
    ]
    response = critic_model.invoke(critic_input)

    # Parse critic JSON
    try:
        raw = response.content or "{}"
        # Extract JSON from possible markdown code block
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        score_data = json.loads(raw.strip())
        score = CriticScore(
            grounded=int(score_data.get("grounded", 0)),
            complete=int(score_data.get("complete", 0)),
            concise=int(score_data.get("concise", 0)),
            overall=int(score_data.get("overall", 0)),
            feedback=score_data.get("feedback", ""),
        )
    except (json.JSONDecodeError, ValueError, TypeError):
        # If critic fails to return valid JSON, pass by default
        score = CriticScore(
            grounded=3, complete=3, concise=3, overall=3, feedback="Critic parse failed"
        )

    # With operator.add reducer on critic_scores, returning [score] appends.
    trace_update = _emit_trace(
        "structured_critic",
        {
            "score": score.overall,
            "feedback": score.feedback,
        },
    )

    if score.passes:
        return {"critic_scores": [score], **trace_update}

    # Revision needed — append feedback
    return {
        "messages": [HumanMessage(content=f"REVISE: Score {score.overall}/5. {score.feedback}")],
        "revision_count": revision_count + 1,
        "critic_scores": [score],
        **trace_update,
    }


# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------


def should_continue(state: AgentflowState) -> Literal["run_tools", "structured_critic"]:
    """After agent node: route to tools if tool calls exist, else to critic."""
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "run_tools"
    return "structured_critic"


def should_finish(state: AgentflowState) -> Literal["agent", "__end__"]:
    """After critic: route back to agent if revision needed, else end."""
    messages = state["messages"]
    if len(messages) < 2:
        return "agent"

    last = messages[-1]
    if isinstance(last, HumanMessage) and "REVISE" in last.content:
        return "agent"

    # If we have a passing critic score, end
    scores = state.get("critic_scores", [])
    if scores and scores[-1].passes:
        return "__end__"

    # If no critique message, check if answer is reasonable
    last_ai = next(
        (m for m in reversed(messages) if isinstance(m, AIMessage) and not m.tool_calls),
        None,
    )
    if last_ai and not last_ai.tool_calls:
        return "__end__"
    return "__end__"
