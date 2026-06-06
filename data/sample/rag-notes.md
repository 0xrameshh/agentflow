# RAG notes

Retrieval-Augmented Generation (RAG) grounds LLM answers by fetching relevant documents before generation.

Typical pipeline: ingest documents, chunk text, embed chunks, store vectors, retrieve top-k matches for a query, inject context into the prompt.

Agentflow uses a simple keyword retriever over markdown files for demos. Production systems (like StrictlyAI / sassy) use pgvector or Pinecone with hybrid search and tenant isolation.
