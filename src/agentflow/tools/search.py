from langchain.tools import tool

# Placeholder search tool for demos and eval tasks without external APIs.
_STUB_RESULTS = {
    "langgraph": "LangGraph is a framework for building stateful, multi-step agent workflows as graphs.",
    "mcp": "Model Context Protocol (MCP) standardizes how LLM clients connect to tools and data sources.",
    "rag": "Retrieval-Augmented Generation combines vector search with LLM generation for grounded answers.",
}


@tool
def web_search(query: str) -> str:
    """Search a small built-in knowledge index for AI engineering topics."""
    query_lower = query.lower()
    hits = [
        text
        for key, text in _STUB_RESULTS.items()
        if key in query_lower or any(word in query_lower for word in key.split())
    ]
    if hits:
        return "\n".join(hits)
    return f"No stub results for '{query}'. Try keywords: langgraph, mcp, rag."
