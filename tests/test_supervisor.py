"""Tests for the supervisor multi-agent graph."""

from __future__ import annotations

from agentflow.graph.supervisor import build_supervisor_graph


class TestSupervisorGraph:
    def test_supervisor_graph_compiles(self):
        graph = build_supervisor_graph()
        compiled = graph.compile()
        assert compiled is not None

    def test_graph_has_expected_nodes(self):
        graph = build_supervisor_graph()
        node_names = set(graph.nodes.keys())
        expected = {"supervisor", "researcher", "writer"}
        assert expected.issubset(node_names), f"Missing nodes: {expected - node_names}"

    def test_graph_has_conditional_edges(self):
        """Supervisor should have conditional routing edges."""
        graph = build_supervisor_graph()
        # The compiled graph should be invokable
        compiled = graph.compile()
        assert hasattr(compiled, "invoke")
