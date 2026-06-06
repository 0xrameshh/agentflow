"""Document ingestion pipeline — chunk markdown files and store in Chroma.

Usage:
    uv run python -m agentflow.rag.ingest data/sample
    uv run python -m agentflow.rag.ingest data/sample --collection mydocs

Requires OPENAI_API_KEY for text-embedding-3-small (default embedding model).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import chromadb
from chromadb.config import Settings

from agentflow.config import require_api_key  # loads .env via load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CHROMA_DIR = os.getenv("AGENTFLOW_CHROMA_DIR", ".chroma")
COLLECTION_NAME = os.getenv("AGENTFLOW_COLLECTION", "agentflow-docs")
EMBEDDING_MODEL = os.getenv("AGENTFLOW_EMBEDDING_MODEL", "text-embedding-3-small")
CHUNK_SIZE = int(os.getenv("AGENTFLOW_CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("AGENTFLOW_CHUNK_OVERLAP", "50"))


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Recursive character split with overlap.

    Tries to split on paragraph boundaries first, then sentences, then words.
    """
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    chunks: list[str] = []
    # Try paragraph splits first
    paragraphs = text.split("\n\n")
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}" if current else para
        else:
            if current:
                chunks.append(current)
            # If single paragraph is too large, split by sentences
            if len(para) > chunk_size:
                sentences = para.replace(". ", ".\n").split("\n")
                current = ""
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    if len(current) + len(sent) + 1 <= chunk_size:
                        current = f"{current} {sent}" if current else sent
                    else:
                        if current:
                            chunks.append(current)
                        current = sent
            else:
                current = para

    if current:
        chunks.append(current)

    # Apply overlap by prepending tail of previous chunk
    if overlap > 0 and len(chunks) > 1:
        overlapped: list[str] = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:]
            overlapped.append(f"...{prev_tail} {chunks[i]}")
        chunks = overlapped

    return [c.strip() for c in chunks if c.strip()]


def _load_documents(root: str | Path) -> list[tuple[str, str]]:
    """Load all .md files from a directory."""
    root_path = Path(root)
    if not root_path.exists():
        return []
    docs: list[tuple[str, str]] = []
    for path in sorted(root_path.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        if content.strip():
            docs.append((path.name, content))
    return docs


def _doc_id(filename: str, chunk_idx: int) -> str:
    """Deterministic ID for a chunk: filename + index hash."""
    raw = f"{filename}::chunk::{chunk_idx}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------


def ingest_directory(
    directory: str | Path,
    collection_name: str = COLLECTION_NAME,
    chroma_dir: str = CHROMA_DIR,
) -> dict:
    """Chunk markdown files and ingest into ChromaDB.

    Returns stats: {docs, chunks, collection}.
    """
    client = chromadb.PersistentClient(
        path=chroma_dir,
        settings=Settings(anonymized_telemetry=False),
    )

    # Use OpenAI embedding function
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

    ef = OpenAIEmbeddingFunction(model_name=EMBEDDING_MODEL)

    # Delete and recreate for clean ingest
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        embedding_function=ef,
    )

    docs = _load_documents(directory)
    if not docs:
        return {"docs": 0, "chunks": 0, "collection": collection_name}

    all_ids: list[str] = []
    all_docs: list[str] = []
    all_metas: list[dict] = []

    for filename, content in docs:
        chunks = _chunk_text(content)
        for idx, chunk in enumerate(chunks):
            all_ids.append(_doc_id(filename, idx))
            all_docs.append(chunk)
            all_metas.append(
                {
                    "source": filename,
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                }
            )

    # Batch add (ChromaDB handles batching internally)
    collection.add(
        ids=all_ids,
        documents=all_docs,
        metadatas=all_metas,
    )

    return {
        "docs": len(docs),
        "chunks": len(all_ids),
        "collection": collection_name,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    import argparse

    require_api_key()

    parser = argparse.ArgumentParser(description="Ingest markdown docs into ChromaDB")
    parser.add_argument("directory", help="Directory containing .md files")
    parser.add_argument("--collection", default=COLLECTION_NAME, help="Collection name")
    parser.add_argument("--chroma-dir", default=CHROMA_DIR, help="ChromaDB storage path")
    args = parser.parse_args()

    stats = ingest_directory(args.directory, args.collection, args.chroma_dir)
    print(f"Ingested {stats['docs']} docs → {stats['chunks']} chunks into '{stats['collection']}'")


if __name__ == "__main__":
    main()
