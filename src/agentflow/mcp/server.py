"""Agentflow MCP Server — exposes tools via Model Context Protocol.

Tools exposed:
- search_knowledge: Search local docs for AI/RAG/project information
- calculator: Evaluate basic math expressions
- web_search: Search built-in knowledge index for AI topics
- run_eval_summary: Run the eval suite and return a summary

Usage:
    uv run python -m agentflow.mcp.server

Then configure in Cursor / Claude Desktop per mcp/README.md.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP(
    "Agentflow",
    json_response=True,
)


@mcp.tool()
def search_knowledge(query: str) -> str:
    """Search local knowledge docs for information about agentflow, RAG, AI engineering, and software topics.

    Returns document snippets with source citations in [source: filename.md] format.
    Use this when you need facts from the project's knowledge base.
    """
    from agentflow.rag.retriever import retrieve

    results = retrieve(query)
    if not results:
        return "No relevant documents found."

    parts: list[str] = []
    for r in results:
        source = r.get("source", "unknown")
        doc = r.get("document", "")
        snippet = doc.strip().replace("\n", " ")
        if len(snippet) > 600:
            snippet = snippet[:600] + "..."
        parts.append(f"[source: {source}] {snippet}")

    return "\n\n".join(parts)


@mcp.tool()
def calculator(expression: str) -> str:
    """Evaluate a basic math expression. Use for arithmetic only.

    Supports: +, -, *, /, %, **, parentheses, decimal numbers.
    Examples: "2 + 3", "(48 / 6) + 15", "2 ** 10"

    Returns the numeric result as a string.
    """
    from agentflow.tools.calculator import _safe_eval

    allowed = set("0123456789+-*/().% ")
    if not all(ch in allowed for ch in expression):
        return "Error: expression contains unsupported characters"
    try:
        result = _safe_eval(expression)
        if result == int(result) and not expression.strip().endswith(".0"):
            return str(int(result))
        return str(result)
    except (ValueError, ZeroDivisionError) as exc:
        return f"Error: {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"Error: {exc}"


@mcp.tool()
def web_search(query: str) -> str:
    """Search a built-in knowledge index for AI engineering topics.

    Covers: LangGraph, MCP (Model Context Protocol), RAG (Retrieval-Augmented Generation).
    Returns relevant descriptions for matching topics.
    """
    stub_results = {
        "langgraph": "LangGraph is a framework for building stateful, multi-step agent workflows as graphs.",
        "mcp": "Model Context Protocol (MCP) standardizes how LLM clients connect to tools and data sources.",
        "rag": "Retrieval-Augmented Generation combines vector search with LLM generation for grounded answers.",
    }

    query_lower = query.lower()
    hits = [
        text
        for key, text in stub_results.items()
        if key in query_lower or any(word in query_lower for word in key.split())
    ]
    if hits:
        return "\n".join(hits)
    return f"No results for '{query}'. Try keywords: langgraph, mcp, rag."


@mcp.tool()
def run_eval_summary() -> str:
    """Run the agentflow evaluation suite and return a summary report.

    Executes all 15 eval tasks and returns pass rate, average latency,
    and token estimates. Use this to verify the agent is working correctly.

    Note: Requires OPENAI_API_KEY to be set.
    """

    from agentflow.config import require_api_key
    from agentflow.eval.runner import run_eval_suite

    try:
        require_api_key()
    except RuntimeError as e:
        return f"Error: {e}"

    try:
        report = run_eval_suite()
        data = report.to_dict()
        summary = (
            f"Eval Report:\n"
            f"  Total tasks: {data['total']}\n"
            f"  Passed: {data['passed']}\n"
            f"  Pass rate: {data['pass_rate']}%\n"
            f"  Avg latency: {data['avg_latency_ms']}ms\n"
            f"  Total tokens (est): {data['total_token_estimate']}\n"
        )
        # Add per-task summary
        for result in data["results"]:
            status = "✅" if result["passed"] else "❌"
            summary += f"  {status} {result['id']}: {result['latency_ms']}ms"
            if result.get("error"):
                summary += f" (error: {result['error'][:80]})"
            summary += "\n"
        return summary
    except Exception as e:
        return f"Eval failed: {e}"


def main():
    """Run the MCP server with stdio transport (for Cursor/Claude Desktop)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
