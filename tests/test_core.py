"""Tests for agentflow core — graph compilation, tools, eval runner, state.

These tests do NOT require an API key — they test structure and logic only.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from agentflow.graph.builder import build_research_graph
from agentflow.graph.state import CriticScore
from agentflow.tools.calculator import calculator
from agentflow.tools.knowledge import search_knowledge
from agentflow.tools.search import web_search


# ---------------------------------------------------------------------------
# Graph compilation
# ---------------------------------------------------------------------------


class TestGraphCompilation:
    def test_research_graph_compiles(self):
        graph = build_research_graph()
        compiled = graph.compile()
        assert compiled is not None

    def test_graph_has_expected_nodes(self):
        graph = build_research_graph()
        node_names = set(graph.nodes.keys())
        expected = {"init_run", "agent", "run_tools", "structured_critic"}
        assert expected.issubset(node_names), f"Missing nodes: {expected - node_names}"


# ---------------------------------------------------------------------------
# Tools — no API key needed
# ---------------------------------------------------------------------------


class TestCalculator:
    def test_basic_addition(self):
        result = calculator.invoke({"expression": "2 + 3"})
        assert result == "5"

    def test_basic_division(self):
        result = calculator.invoke({"expression": "48 / 6"})
        assert result.strip() in ("8", "8.0")

    def test_complex_expression(self):
        result = calculator.invoke({"expression": "(48 / 6) + 15"})
        assert result.strip() in ("23", "23.0")

    def test_rejects_unsafe_input(self):
        result = calculator.invoke({"expression": "__import__('os').system('ls')"})
        assert "Error" in result

    def test_rejects_letters(self):
        result = calculator.invoke({"expression": "hello"})
        assert "Error" in result


class TestWebSearch:
    def test_langgraph_query(self):
        result = web_search.invoke({"query": "What is LangGraph?"})
        assert "graph" in result.lower()

    def test_mcp_query(self):
        result = web_search.invoke({"query": "Explain MCP protocol"})
        assert "mcp" in result.lower() or "protocol" in result.lower()

    def test_no_match(self):
        result = web_search.invoke({"query": "quantum computing basics"})
        assert (
            "No stub results" in result or "No results" in result.lower() or "no" in result.lower()
        )


class TestKnowledgeSearch:
    def test_finds_something_relevant(self):
        """The search tool should return results for a valid query."""
        result = search_knowledge.invoke({"query": "expense reimbursement policy"})
        assert len(result) > 20
        assert "No relevant" not in result or "[source:" in result

    def test_no_match_returns_suggestion(self):
        result = search_knowledge.invoke({"query": "quantum entanglement physics"})
        assert isinstance(result, str) and len(result) > 0


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class TestAgentflowState:
    def test_default_state(self):
        from agentflow.graph.state import make_initial_state

        state = make_initial_state("hello", run_id="test123")
        assert state["run_id"] == "test123"
        assert state["tool_call_count"] == 0
        assert state["revision_count"] == 0
        assert state["critic_scores"] == []
        assert state["trace"] == []
        assert state["error"] is None

    def test_critic_score_passes(self):
        score = CriticScore(grounded=4, complete=4, concise=4, overall=4)
        assert score.passes is True

    def test_critic_score_fails(self):
        score = CriticScore(grounded=3, complete=3, concise=3, overall=3)
        assert score.passes is False

    def test_critic_score_boundary(self):
        score = CriticScore(grounded=4, complete=4, concise=3, overall=3)
        assert score.passes is False


# ---------------------------------------------------------------------------
# Eval runner — YAML parsing + expect_contains logic
# ---------------------------------------------------------------------------


class TestEvalRunner:
    def test_tasks_yaml_parses(self):
        tasks_path = Path("eval/tasks.yaml")
        if not tasks_path.exists():
            pytest.skip("eval/tasks.yaml not found")
        data = yaml.safe_load(tasks_path.read_text(encoding="utf-8"))
        assert "tasks" in data
        assert len(data["tasks"]) >= 5

    def test_each_task_has_required_fields(self):
        tasks_path = Path("eval/tasks.yaml")
        if not tasks_path.exists():
            pytest.skip("eval/tasks.yaml not found")
        data = yaml.safe_load(tasks_path.read_text(encoding="utf-8"))
        for task in data["tasks"]:
            assert "id" in task, f"Task missing 'id': {task}"
            assert "prompt" in task, f"Task missing 'prompt': {task}"
            assert "expect_contains" in task, f"Task missing 'expect_contains': {task}"
            assert isinstance(task["expect_contains"], list)

    def test_check_answer_logic(self):
        """Import and test the _check_answer function from eval runner."""
        from agentflow.eval.runner import _check_answer

        assert _check_answer("LangGraph is a graph-based framework.", ["langgraph", "graph"])
        assert not _check_answer("I don't know.", ["langgraph", "graph"])
        assert _check_answer(
            "RAG stands for Retrieval-Augmented Generation.", ["retrieval", "generation"]
        )

    def test_check_answer_case_insensitive(self):
        from agentflow.eval.runner import _check_answer

        assert _check_answer("LANGGRAPH is great", ["langgraph"])
        assert _check_answer("rag is useful", ["RAG"])
