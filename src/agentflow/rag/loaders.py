"""Multi-format document loaders for Agentflow RAG ingest.

Supports: .md, .txt, .pdf
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}


@dataclass
class LoadedChunk:
    """A logical chunk from a loaded document.

    For markdown and text files, returns one chunk per file.
    For PDFs, returns one chunk per page.
    """

    text: str
    source: str  # filename
    file_type: str  # "md" | "txt" | "pdf"
    page: int | None = None  # PDF page number (1-indexed), None for md/txt
    extra: dict = field(default_factory=dict)


def load_path(filepath: str | Path) -> list[LoadedChunk]:
    """Load a single file and return chunks.

    Args:
        filepath: Path to a .md, .txt, or .pdf file.

    Returns:
        List of LoadedChunk objects.
    """
    path = Path(filepath)
    ext = path.suffix.lower()
    source = path.name

    if ext == ".md":
        return _load_markdown(path, source)
    elif ext == ".txt":
        return _load_text(path, source)
    elif ext == ".pdf":
        return _load_pdf(path, source)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}")


def load_directory(directory: str | Path, recursive: bool = False) -> list[LoadedChunk]:
    """Load all supported documents from a directory.

    Args:
        directory: Path to directory containing .md, .txt, .pdf files.
        recursive: If True, walk subdirectories recursively.

    Returns:
        List of LoadedChunk objects from all files.
    """
    root = Path(directory)
    if not root.exists():
        return []

    chunks: list[LoadedChunk] = []

    if recursive:
        files = sorted(root.rglob("*"))
    else:
        files = sorted(root.glob("*"))

    for path in files:
        if path.is_dir() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            file_chunks = load_path(path)
            chunks.extend(file_chunks)
        except Exception as exc:
            # Log and skip problematic files
            print(f"Warning: skipping {path.name}: {exc}")
            continue

    return chunks


def _load_markdown(path: Path, source: str) -> list[LoadedChunk]:
    """Load a markdown file as a single chunk."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return []
    return [LoadedChunk(text=text, source=source, file_type="md")]


def _load_text(path: Path, source: str) -> list[LoadedChunk]:
    """Load a text file as a single chunk."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return []
    return [LoadedChunk(text=text, source=source, file_type="txt")]


def _load_pdf(path: Path, source: str) -> list[LoadedChunk]:
    """Load a PDF file — one chunk per page with page numbers."""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    chunks: list[LoadedChunk] = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            chunks.append(
                LoadedChunk(
                    text=text,
                    source=source,
                    file_type="pdf",
                    page=page_num,
                )
            )

    return chunks
