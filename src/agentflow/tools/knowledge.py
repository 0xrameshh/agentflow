"""Knowledge search tool — retrieves from Chroma RAG or keyword fallback.

Includes source citations in output: [source: filename.md]
"""

from __future__ import annotations

from langchain.tools import tool


def _format_results(results: list[dict]) -> str:
    """Format retrieval results with source citations.

    Citation formats:
        [source: handbook.pdf p.3]
        [source: refund-policy.md]
        [source: faq.txt]
    """
    if not results:
        return "No relevant documents found."

    parts: list[str] = []
    for r in results:
        source = r.get("source", "unknown")
        doc = r.get("document", "")
        snippet = doc.strip().replace("\n", " ")
        if len(snippet) > 1000:
            snippet = snippet[:1000] + "..."

        # Build citation with page number for PDFs
        citation = f"[source: {source}]"
        file_type = r.get("file_type", "")
        page = r.get("page")
        if file_type == "pdf" and page is not None:
            citation = f"[source: {source} p.{page}]"

        parts.append(f"{citation} {snippet}")

    return "\n\n".join(parts)


@tool
def search_knowledge(query: str) -> str:
    """Search the configured knowledge base for policies, troubleshooting, product information, and documentation.

    Supports multiple formats: Markdown (.md), text (.txt), and PDF (.pdf).
    Uses Chroma vector search if available, otherwise falls back to keyword matching.
    Results include source citations: [source: filename.ext] or [source: filename.pdf p.N] for PDFs.
    Always call this before answering questions about the knowledge base.
    """
    from agentflow.rag.retriever import retrieve

    results = retrieve(query, n_results=4)
    return _format_results(results)
