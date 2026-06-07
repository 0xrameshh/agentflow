"""Tests for RAG module — chunking, loaders, ingestion (no API key needed for chunking/loading)."""

from __future__ import annotations


from agentflow.rag.ingest import _chunk_text, _doc_id
from agentflow.rag.loaders import load_directory, load_path


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
        overlap_chunks = [c for c in chunks if c.startswith("...")]
        assert len(overlap_chunks) > 0

    def test_large_single_paragraph(self):
        text = "First sentence here. " * 50
        chunks = _chunk_text(text, chunk_size=200, overlap=0)
        assert len(chunks) >= 2


class TestLoaders:
    def test_load_markdown(self):
        chunks = load_path("data/knowledge/policies/expense-policy.md")
        assert len(chunks) == 1
        assert chunks[0].file_type == "md"
        assert chunks[0].source == "expense-policy.md"
        assert "expense" in chunks[0].text.lower()

    def test_load_text(self):
        chunks = load_path("data/knowledge/notes/product-launch-checklist.txt")
        assert len(chunks) == 1
        assert chunks[0].file_type == "txt"
        assert "launch" in chunks[0].text.lower()

    def test_load_pdf(self):
        chunks = load_path("data/knowledge/manuals/onboarding-manual.pdf")
        assert len(chunks) >= 1
        assert chunks[0].file_type == "pdf"
        assert chunks[0].page is not None

    def test_load_directory_non_recursive(self):
        chunks = load_directory("data/knowledge/notes", recursive=False)
        assert len(chunks) >= 2  # at least 2 .txt files
        assert all(c.file_type == "txt" for c in chunks)

    def test_load_directory_recursive(self):
        chunks = load_directory("data/knowledge", recursive=True)
        # Should find .md, .txt, .pdf from all subdirs
        types = {c.file_type for c in chunks}
        assert "md" in types
        assert "txt" in types
        assert "pdf" in types

    def test_empty_dir(self):
        chunks = load_directory("/nonexistent/path")
        assert chunks == []


class TestDocId:
    def test_deterministic(self):
        id1 = _doc_id("test.md", 0)
        id2 = _doc_id("test.md", 0)
        assert id1 == id2

    def test_different_for_different_chunks(self):
        id1 = _doc_id("test.md", 0)
        id2 = _doc_id("test.md", 1)
        assert id1 != id2
