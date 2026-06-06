# RAG Pipeline

Agentflow implements a two-tier RAG pipeline: **Chroma vector search** (primary) with **keyword fallback** (reliability).

## Architecture

```
                    ┌─────────────┐
                    │  User Query  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Retriever   │
                    │  (retriever) │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │                         │
     ┌────────▼────────┐     ┌──────────▼──────────┐
     │  Chroma Search   │     │  Keyword Fallback    │
     │  (vector sim.)   │     │  (term matching)     │
     └────────┬────────┘     └──────────┬──────────┘
              │                         │
              └────────────┬────────────┘
                           │
                    ┌──────▼──────┐
                    │  Ranked      │
                    │  Results     │
                    │  + Citations │
                    └─────────────┘
```

## Ingestion

```bash
# Ingest sample docs into Chroma
uv run agentflow-ingest data/sample

# Custom collection name
uv run agentflow-ingest data/sample --collection mydocs
```

### Chunking strategy

- **Algorithm:** Recursive paragraph → sentence → word split
- **Chunk size:** 500 characters (configurable via `AGENTFLOW_CHUNK_SIZE`)
- **Overlap:** 50 characters (configurable via `AGENTFLOW_CHUNK_OVERLAP`)
- **Overlap format:** `"...<tail of previous> <current chunk>"`

### Embeddings

- **Model:** `text-embedding-3-small` (OpenAI, configurable via `AGENTFLOW_EMBEDDING_MODEL`)
- **Storage:** Local ChromaDB at `.chroma/` (configurable via `AGENTFLOW_CHROMA_DIR`)

## Retrieval

### Chroma mode (default)

```python
from agentflow.rag.retriever import query_chroma
results = query_chroma("What is RAG?", n_results=3)
# Returns: [{document, source, chunk_index, distance}, ...]
```

### Keyword fallback

```python
from agentflow.rag.retriever import query_keyword
results = query_keyword("What is RAG?")
```

### Unified retriever

```python
from agentflow.rag.retriever import retrieve
results = retrieve("What is RAG?")
# Auto-detects: Chroma if available, keyword otherwise
```

## Source citations

The `search_knowledge` tool returns results with citations:

```
[source: rag-notes.md] Retrieval-Augmented Generation (RAG) grounds LLM answers...
[source: agentflow-overview.md] Agentflow is a LangGraph agent runtime...
```

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `AGENTFLOW_RETRIEVER` | `chroma` | `chroma` or `keyword` |
| `AGENTFLOW_CHROMA_DIR` | `.chroma` | ChromaDB storage path |
| `AGENTFLOW_COLLECTION` | `agentflow-docs` | Collection name |
| `AGENTFLOW_EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `AGENTFLOW_CHUNK_SIZE` | `500` | Max chars per chunk |
| `AGENTFLOW_CHUNK_OVERLAP` | `50` | Overlap between chunks |

## Connection to sassy

This RAG pipeline mirrors the architecture of StrictlyAI (sassy):

- **sassy:** pgvector + hybrid search + tenant isolation + multi-tenant chunking
- **agentflow:** Chroma (local) + keyword fallback + single-tenant

Same concepts (embed, chunk, retrieve, inject context), different scale and deployment model.
