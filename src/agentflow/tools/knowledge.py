"""Knowledge search tool — retrieves from Chroma RAG or keyword fallback.

Includes source citations in output: [source: filename.md]
"""

from __future__ import annotations

from langchain.tools import tool


def _format_results(results: list[dict]) -> str:
    """Format retrieval results with source citations."""
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


@tool
def search_knowledge(query: str) -> str:
    """Search local knowledge docs for information about agentflow, RAG, and AI engineering topics.

    Uses Chroma vector search if available, otherwise falls back to keyword matching.
    Results include source citations in the format [source: filename.md].
    """
    from agentflow.rag.retriever import retrieve

    results = retrieve(query)
    return _format_results(results)
