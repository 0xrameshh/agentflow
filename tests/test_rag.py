"""Tests for RAG module — chunking, ingestion, retrieval (no API key needed for chunking)."""

from __future__ import annotations

from agentflow.rag.ingest import _chunk_text, _doc_id, _load_documents


class TestChunking:
    def test_short_text_no_split(self):
        chunks = _chunk_text("Hello world")
        assert len(chunks) == 1
        assert chunks[0] == "Hello world"

    def test_empty_text(self):
        chunks = _chunk_text("")
        assert chunks == []

    def test_whitespace_only(self):
        chunks = _chunk_text("   \n\n   ")
        assert chunks == []

    def test_paragraph_split(self):
        text = (
            "Paragraph one about dogs.\n\nParagraph two about cats.\n\nParagraph three about birds."
        )
        chunks = _chunk_text(text, chunk_size=50, overlap=0)
        assert len(chunks) >= 2

    def test_overlap_applied(self):
        text = "A" * 100 + "\n\n" + "B" * 100 + "\n\n" + "C" * 100
        chunks = _chunk_text(text, chunk_size=80, overlap=20)
        # Overlap chunks should start with "..."
        overlap_chunks = [c for c in chunks if c.startswith("...")]
        assert len(overlap_chunks) > 0

    def test_large_single_paragraph(self):
        # A single paragraph larger than chunk_size should be split by sentences
        text = "First sentence here. " * 50  # ~650 chars
        chunks = _chunk_text(text, chunk_size=200, overlap=0)
        assert len(chunks) >= 2


class TestDocLoading:
    def test_loads_sample_docs(self):
        docs = _load_documents("data/sample")
        assert len(docs) >= 2
        names = [name for name, _ in docs]
        assert "agentflow-overview.md" in names
        assert "rag-notes.md" in names

    def test_empty_dir(self):
        docs = _load_documents("/nonexistent/path")
        assert docs == []


class TestDocId:
    def test_deterministic(self):
        id1 = _doc_id("test.md", 0)
        id2 = _doc_id("test.md", 0)
        assert id1 == id2

    def test_different_for_different_chunks(self):
        id1 = _doc_id("test.md", 0)
        id2 = _doc_id("test.md", 1)
        assert id1 != id2
