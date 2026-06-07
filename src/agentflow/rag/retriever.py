"""Chroma-backed retriever for agentflow RAG.

Provides a query() function that returns ranked document chunks
with source citations. Falls back to keyword search if Chroma is
unavailable or AGENTFLOW_RETRIEVER=keyword.
"""

from __future__ import annotations

import os
from pathlib import Path

import chromadb
from chromadb.config import Settings

import agentflow.config  # noqa: F401 — loads .env via load_dotenv()

CHROMA_DIR = os.getenv("AGENTFLOW_CHROMA_DIR", ".chroma")
COLLECTION_NAME = os.getenv("AGENTFLOW_COLLECTION", "agentflow-docs")
EMBEDDING_MODEL = os.getenv("AGENTFLOW_EMBEDDING_MODEL", "text-embedding-3-small")
RETRIEVER_MODE = os.getenv("AGENTFLOW_RETRIEVER", "chroma")  # "chroma" | "keyword"


def query_chroma(
    query: str,
    n_results: int = 3,
    collection_name: str = COLLECTION_NAME,
    chroma_dir: str = CHROMA_DIR,
) -> list[dict]:
    """Query ChromaDB and return ranked results with source citations.

    Returns list of dicts: {document, source, chunk_index, distance}.
    """
    client = chromadb.PersistentClient(
        path=chroma_dir,
        settings=Settings(anonymized_telemetry=False),
    )

    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

    ef = OpenAIEmbeddingFunction(model_name=EMBEDDING_MODEL)

    try:
        collection = client.get_collection(
            name=collection_name,
            embedding_function=ef,
        )
    except Exception:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    output: list[dict] = []
    if not results or not results.get("documents"):
        return output

    docs = results["documents"][0]
    metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
    distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

    for doc, meta, dist in zip(docs, metas, distances):
        item = {
            "document": doc,
            "source": meta.get("source", "unknown"),
            "chunk_index": meta.get("chunk_index", 0),
            "distance": round(dist, 4),
        }
        if "file_type" in meta:
            item["file_type"] = meta["file_type"]
        if "page" in meta:
            item["page"] = meta["page"]
        output.append(item)

    return output


def query_keyword(query: str, docs_dir: str | Path | None = None) -> list[dict]:
    """Fallback keyword search over local markdown files.

    Finds the most relevant paragraph/section within each document
    rather than returning the document beginning.
    """
    if docs_dir is None:
        from agentflow.config import SAMPLE_DOCS_DIR

        docs_dir = SAMPLE_DOCS_DIR

    docs_path = Path(docs_dir)
    if not docs_path.exists():
        return []

    import re

    # Strip punctuation and lowercase
    query_terms = {t.lower() for t in re.findall(r"\w+", query) if len(t) > 2}
    results: list[dict] = []

    for path in sorted(docs_path.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        content_lower = content.lower()
        doc_score = sum(1 for t in query_terms if t in content_lower)
        if doc_score == 0:
            continue

        # Split into sections (## headings) and paragraphs
        # Try to find the best matching paragraph
        lines = content.split("\n")
        paragraphs = []
        current_para = []
        for line in lines:
            if line.strip() == "" and current_para:
                paragraphs.append("\n".join(current_para).strip())
                current_para = []
            else:
                current_para.append(line)
        if current_para:
            paragraphs.append("\n".join(current_para).strip())

        # Score each paragraph and pick the best one
        best_para = ""
        best_score = 0
        for para in paragraphs:
            para_lower = para.lower()
            para_score = sum(1 for t in query_terms if t in para_lower)
            if para_score > best_score:
                best_score = para_score
                best_para = para

        snippet = (best_para or content).strip().replace("\n", " ")
        if len(snippet) > 600:
            snippet = snippet[:600] + "..."
        results.append(
            {
                "document": snippet,
                "source": path.name,
                "chunk_index": 0,
                "distance": 1.0 / max(doc_score, 1),
            }
        )

    results.sort(key=lambda r: r["distance"])
    return results[:3]


def retrieve(query: str, n_results: int = 3) -> list[dict]:
    """Unified retrieval — uses Chroma or keyword based on config.

    Auto-detects: if Chroma collection exists and has data, uses it.
    Otherwise falls back to keyword search.
    """
    if RETRIEVER_MODE == "chroma":
        try:
            results = query_chroma(query, n_results=n_results)
            if results:
                return results
        except Exception:
            pass
    # Always try keyword as fallback if Chroma returns nothing
    return query_keyword(query)
