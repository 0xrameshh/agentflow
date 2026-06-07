# RAG Pipeline

Two-tier retrieval: **Chroma vector search** (primary) with **keyword fallback** (reliability).

## Architecture

```
User Query → Retriever → Chroma (vector) or Keyword (fallback) → Ranked results + citations
```

## Supported formats

| Extension | Loader | Notes |
|-----------|--------|-------|
| `.md` | `loaders._load_markdown` | Full file as one logical doc |
| `.txt` | `loaders._load_text` | UTF-8 with error replacement |
| `.pdf` | `loaders._load_pdf` | Per-page chunks via `pypdf`; `page` metadata for citations |

Loader module: `src/agentflow/rag/loaders.py`

## Knowledge base

**Primary demo KB:** `data/knowledge/`

```
data/knowledge/
├── policies/          # .md — expense, remote work
├── notes/             # .txt — incident response, launch checklist
└── manuals/           # .pdf — onboarding manual
```

**Example tenant:** `data/tenants/support-saas/` — 8 markdown support articles (FlowDesk fictional brand).

Configure via `AGENTFLOW_DOCS_DIR` (default: `data/knowledge`).

## Ingestion

```bash
# Recursive ingest (recommended)
uv run agentflow-ingest data/knowledge --recursive

# Custom collection
uv run agentflow-ingest data/knowledge --recursive --collection mydocs

# Support tenant example
uv run agentflow-ingest data/tenants/support-saas --recursive
```

### Chunking

- Recursive paragraph → sentence split
- Default chunk size: 500 chars (`AGENTFLOW_CHUNK_SIZE`)
- Overlap: 50 chars (`AGENTFLOW_CHUNK_OVERLAP`)
- PDF: one chunk per page before sub-chunking

### Embeddings

- Model: `text-embedding-3-small` (OpenAI)
- Storage: `.chroma/` (`AGENTFLOW_CHROMA_DIR`)

## Retrieval

```python
from agentflow.rag.retriever import retrieve
results = retrieve("What is the meal expense limit?", n_results=4)
# [{document, source, file_type, page, chunk_index, distance}, ...]
```

## Citations

Tool output format:

```
[source: expense-policy.md] Employees may claim up to $75 per day for meals...
[source: onboarding-manual.pdf p.2] Laptop refresh cycle is 3 years...
[source: incident-response.txt] SEV1 incidents require 15-minute response...
```

API response:

```json
{
  "answer": "The meal limit is $75 per day...",
  "citations": [
    {
      "source": "expense-policy.md",
      "snippet": "Employees may claim up to $75 per day...",
      "file_type": "md",
      "page": null
    }
  ]
}
```

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `AGENTFLOW_DOCS_DIR` | `data/knowledge` | Default docs path for keyword fallback |
| `AGENTFLOW_RETRIEVER` | `chroma` | `chroma` or `keyword` |
| `AGENTFLOW_CHROMA_DIR` | `.chroma` | ChromaDB path |
| `AGENTFLOW_COLLECTION` | `agentflow-docs` | Collection name |
| `AGENTFLOW_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `AGENTFLOW_CHUNK_SIZE` | `500` | Max chars per chunk |
| `AGENTFLOW_CHUNK_OVERLAP` | `50` | Chunk overlap |
