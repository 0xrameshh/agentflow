# Knowledge Copilot v2 — Implementation Plan

> **Status:** Ready for implementation  
> **Repo:** `agentflow` (https://github.com/0xrameshh/agentflow)  
> **Builds on:** v1 Support KB MVP (`plan.md`) — LangGraph agent, Chroma RAG, eval harness, FastAPI `/run/support`, static chat UI  
> **Goal:** Evolve into an **industry-agnostic document Q&A product** with **multi-format ingest** (PDF, TXT, MD) and a **Next.js** chat frontend.

---

## 1. Why v2 (brother’s review)

| Feedback | v1 state | v2 target |
|----------|----------|-----------|
| Industry agnostic | Locked to FlowDesk / support SaaS | **Knowledge Copilot** — any domain via configurable KB folder |
| Multiple file formats | Markdown only | **`.md`, `.txt`, `.pdf`** (v2); `.docx` optional later |
| Better frontend | Vanilla HTML in `static/` | **Next.js** app in `web/`, created via `create-next-app` |

**Keep the engineering depth** (LangGraph, critic, evals, citations). Change positioning, ingest pipeline, and UI stack.

---

## 2. Product framing

### Problem (generic)

Teams store knowledge in **PDFs, Word exports, text files, and wikis**. Finding answers means opening many files — slow and inconsistent. Generic chatbots hallucinate policy.

### Solution

**Knowledge Copilot** — point at a folder of documents; the system ingests, indexes, and answers with **cited sources**. Support/FlowDesk is **one sample deployment**, not the product identity.

### Primary users

- Operations / support staff (any industry)
- Internal teams onboarding to company docs
- Developers querying technical manuals

### Success metrics (v2)

| Metric | Target |
|--------|--------|
| Ingest formats | `.md`, `.txt`, `.pdf` in one CLI command |
| Eval pass rate | ≥ 85% on `eval/tasks-knowledge.yaml` |
| Citations | Include `source` + `file_type` + `page` (PDF) when available |
| Frontend | Next.js chat at `http://localhost:3000` talking to API on `:8081` |
| Industry story | README + UI do **not** hardcode FlowDesk as product name |

### Non-goals (v2)

- File upload UI / drag-and-drop (CLI ingest only)
- Auth, multi-tenant SaaS, billing
- Real-time collaborative editing
- `.docx`, `.html`, `.csv` (defer to v3 unless trivial)
- Replacing FastAPI with Next.js API routes for the agent (Python stays the brain)

---

## 3. Target architecture

```
┌─────────────────────────────────────────────────────────────┐
│  web/  (Next.js 15, App Router, TypeScript, Tailwind)        │
│  localhost:3000  →  fetch POST /run/support                  │
└──────────────────────────┬──────────────────────────────────┘
                           │  NEXT_PUBLIC_API_URL
┌──────────────────────────▼──────────────────────────────────┐
│  FastAPI  (agentflow.api.main)  :8081                       │
│  POST /run/support  →  { answer, citations[], latency_ms }   │
│  GET  /health, /kb/articles                                  │
│  CORS enabled for localhost:3000                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  LangGraph agent  →  search_knowledge tool                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  Ingest:  agentflow-ingest <dir>                             │
│  Loaders: .md .txt .pdf  →  chunk  →  Chroma (.chroma/)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Repo layout (after v2)

```
agentflow/
├── src/agentflow/          # Python backend (existing)
├── web/                    # NEW — Next.js app (create-next-app)
│   ├── app/
│   │   ├── page.tsx        # Chat page
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── Chat.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── CitationChips.tsx
│   │   └── Composer.tsx
│   ├── lib/
│   │   └── api.ts          # typed fetch to FastAPI
│   ├── .env.local.example  # NEXT_PUBLIC_API_URL=http://localhost:8081
│   └── package.json
├── data/
│   ├── knowledge/          # NEW — generic sample KB (rename/migrate from support-kb)
│   │   ├── policies/       # .md
│   │   ├── manuals/        # .pdf samples (add 1–2 small PDFs)
│   │   └── notes/          # .txt
│   └── tenants/
│       └── support-saas/   # OPTIONAL — keep FlowDesk articles as example tenant
├── eval/
│   ├── tasks-knowledge.yaml    # NEW — domain-agnostic eval tasks
│   └── tasks-support-kb.yaml   # KEEP — reference tenant evals
├── static/                 # DEPRECATE after Next.js works (remove in Phase 5)
├── plan.md                 # v1 plan (historical)
└── plan-v2.md              # this file
```

---

## 5. Implementation phases

### Phase 0 — Prep (30 min)

- [ ] Read current code: `src/agentflow/rag/ingest.py`, `api/main.py`, `graph/nodes.py`, `static/`
- [ ] Confirm v1 works:
  ```bash
  cd agentflow
  uv sync --extra dev
  uv run pytest tests/ -q
  ```
- [ ] Note: port **8080** may be taken by `goproxy` on this machine — use `AGENTFLOW_PORT=8081` in `.env`

---

### Phase 1 — Industry-agnostic rebrand

**Goal:** Product reads as **Knowledge Copilot**, not FlowDesk-only.

| File | Change |
|------|--------|
| `README.md` | Title: **Agentflow — Knowledge Copilot**. Problem = generic doc search. FlowDesk = example tenant. |
| `src/agentflow/graph/nodes.py` | System prompt: domain-neutral (“answer from ingested knowledge base; cite sources; don’t invent facts”). |
| `src/agentflow/tools/knowledge.py` | Docstring: “Search the configured knowledge base…” |
| `src/agentflow/api/main.py` | FastAPI `title` / `description` — neutral naming. |
| `static/*` (until removed) | Replace “FlowDesk” with configurable title or “Knowledge Copilot”. |
| `web/` (Phase 4) | Header: **Knowledge Copilot** + subtitle “Cited answers from your documents”. |

**Data migration:**

- [ ] Create `data/knowledge/` with mixed sample content (move/copy from `data/support-kb/`)
- [ ] Add 1–2 **`.txt`** files (plain policy snippets)
- [ ] Update `AGENTFLOW_DOCS_DIR` default in `config.py` → `data/knowledge`
- [ ] Keep `data/support-kb/` or `data/tenants/support-saas/` for support-specific evals only

**Env:**

```bash
# .env.example
AGENTFLOW_DOCS_DIR=data/knowledge
AGENTFLOW_KB_NAME=Knowledge Base   # optional display name for UI
```

---

### Phase 2 — Multi-format ingest

**Goal:** `agentflow-ingest <directory>` ingests `.md`, `.txt`, `.pdf`.

#### 2a. Add dependencies

In `pyproject.toml`:

```toml
dependencies = [
    # ... existing ...
    "pypdf>=5.0.0",   # PDF text extraction (lightweight)
]
```

Alternative: `pdfplumber` if `pypdf` fails on sample PDFs — agent should test one real PDF.

#### 2b. Create loader module

**CREATE:** `src/agentflow/rag/loaders.py`

```python
SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}

def load_document(path: Path) -> list[LoadedChunk]:
    """
    Returns one or more logical documents per file.
    PDF: one entry per page (or merged — agent decides; prefer per-page metadata for citations).
    """
```

**Types:**

```python
@dataclass
class LoadedChunk:
    text: str
    source: str          # filename
    file_type: str       # md | txt | pdf
    page: int | None     # PDF page number, else None
```

| Format | Loader |
|--------|--------|
| `.md`, `.txt` | `path.read_text(encoding="utf-8", errors="replace")` |
| `.pdf` | `pypdf.PdfReader` → extract text per page; skip empty pages |

#### 2c. Refactor ingest

**EDIT:** `src/agentflow/rag/ingest.py`

- Replace `_load_documents()` (glob `*.md` only) with `load_directory()` using `loaders.py`
- Walk directory **recursively** (optional flag `--no-recursive` default false)
- Metadata stored in Chroma: `source`, `file_type`, `page`, `chunk_index`
- CLI: `uv run agentflow-ingest data/knowledge`

#### 2d. Update retriever + citations

**EDIT:** `src/agentflow/tools/knowledge.py`, `api/main.py` `_extract_citations()`

Citation format examples:

```
[source: handbook.pdf p.3]
[source: refund-policy.md]
[source: faq.txt]
```

API `Citation` model — extend if needed:

```python
class Citation(BaseModel):
    source: str
    snippet: str
    file_type: str | None = None
    page: int | None = None
```

#### 2e. Sample PDFs for demo

- [ ] Add **1–2 small PDFs** under `data/knowledge/manuals/` (generate via script or use public-domain PDF; keep repo size small, &lt; 500KB each)
- [ ] Document in README how to add your own PDFs

#### 2f. Tests

**CREATE/EDIT:**

- `tests/test_loaders.py` — md, txt, pdf parsing (use tiny fixtures in `tests/fixtures/`)
- `tests/test_rag.py` — update paths
- No API key needed for loader unit tests

---

### Phase 3 — Domain-agnostic eval suite

**CREATE:** `eval/tasks-knowledge.yaml` (12–16 tasks)

Categories:

| Category | Example |
|----------|---------|
| PDF content | “According to the manual PDF, what is X?” |
| TXT policy | “What does the notes file say about Y?” |
| MD article | “Summarize Z from the policies folder.” |
| Grounding | Question not in corpus → expect “not found” / no hallucination |
| Cross-file | “Compare policy A and policy B.” |

**EDIT:** `src/agentflow/eval/runner.py` — default `--tasks` can stay generic; document both task files in README.

**Threshold:** ≥ 85% pass with `gpt-4o-mini` + Chroma ingested.

---

### Phase 4 — Next.js frontend (`web/`)

**Goal:** Professional React UI; API remains FastAPI.

#### 4a. Scaffold with create-next-app

Run from **repo root** (`agentflow/`):

**Preferred (bun):**

```bash
cd agentflow
bunx create-next-app@latest web \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --turbopack \
  --no-git
```

**Fallback (npx):**

```bash
cd agentflow
npx create-next-app@latest web \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --turbopack \
  --no-git
```

> Use `--no-git` so Next doesn’t init a nested git repo.  
> If CLI prompts interactively, choose: TypeScript **Yes**, ESLint **Yes**, Tailwind **Yes**, `src/` **Yes**, App Router **Yes**, no src dir → match flags above.

#### 4b. Environment

**CREATE:** `web/.env.local.example`

```bash
NEXT_PUBLIC_API_URL=http://localhost:8081
NEXT_PUBLIC_KB_NAME=Knowledge Copilot
```

**CREATE:** `web/.env.local` (gitignored) — copy from example.

#### 4c. CORS on FastAPI

**EDIT:** `src/agentflow/api/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

For production: add Vercel URL via `AGENTFLOW_CORS_ORIGINS` env (comma-separated).

#### 4d. UI components (minimum)

| Component | Responsibility |
|-----------|----------------|
| `Chat.tsx` | Message list state, scroll-to-bottom |
| `MessageBubble.tsx` | User vs assistant styling, markdown render |
| `CitationChips.tsx` | Source pills + expand snippet |
| `Composer.tsx` | Textarea, Enter to send, loading state |
| `lib/api.ts` | `postSupport(message) → SupportRunResponse` |

**Design notes:**

- Chat layout: messages anchored to bottom (like iMessage)
- Example prompt chips on empty state (generic, not FlowDesk-specific):
  - “What documents are in the knowledge base?”
  - “Summarize the refund policy.”
  - “What does page 1 of the manual say?”
- Fetch `GET /kb/articles` on load for status line (“8 documents indexed”)
- Use `react-markdown` for assistant messages (optional dep: `bun add react-markdown`)

#### 4e. Dev workflow

```bash
# Terminal 1 — API
cd agentflow
uv run agentflow-ingest data/knowledge
AGENTFLOW_PORT=8081 uv run agentflow-api

# Terminal 2 — Next.js
cd agentflow/web
bun install   # or npm install
bun dev       # or npm run dev
# Open http://localhost:3000
```

#### 4f. Root-level convenience (optional)

**CREATE:** `Makefile` target or `scripts/dev.sh`:

```bash
#!/usr/bin/env bash
# Start API + web (background) — document in README
```

---

### Phase 5 — Cleanup & docs

- [ ] **Remove** `static/` serving from FastAPI once Next.js is verified (`GET /` can redirect to docs or return JSON “use web app”)
- [ ] Update `Dockerfile` / `docker-compose.yml`:
  - Option A: API-only container; web deployed separately on Vercel
  - Option B: multi-stage with Node build — only if agent has time; **prefer split deploy**
- [ ] Rewrite `docs/RAG.md` — multi-format ingest, loader table
- [ ] Rewrite `docs/ARCHITECTURE.md` — add `web/` layer diagram
- [ ] Update `scripts/live_smoke.sh` — ingest `data/knowledge`, hit API, optional curl health
- [ ] Update `.gitignore`:
  ```
  web/.next/
  web/node_modules/
  web/.env.local
  ```

---

### Phase 6 — Deploy (optional but strong for portfolio)

| Service | What |
|---------|------|
| **Railway / Fly** | FastAPI + Chroma volume + `OPENAI_API_KEY` |
| **Vercel** | Next.js `web/` with `NEXT_PUBLIC_API_URL=https://api...` |

README **Demo** section: two links (Web UI + API health).

---

### Phase 7 — Portfolio sync

**EDIT:** `portfolio/src/lib/data.ts` (repo `0xrameshh.github.io`)

```typescript
{
  name: "Agentflow — Knowledge Copilot",
  link: "https://github.com/0xrameshh/agentflow",
  liveDemo: "https://...",  // Vercel URL when ready
  stack: ["Python", "LangGraph", "FastAPI", "Chroma", "Next.js", "TypeScript"],
  highlights: [
    "Industry-agnostic RAG copilot — ingests PDF, TXT, and Markdown into Chroma with cited answers.",
    "LangGraph agent with structured critic loop and YAML regression eval suite.",
    "Next.js chat UI + FastAPI backend; full-stack deploy ready.",
  ],
}
```

---

## 6. File checklist (summary)

| Action | Path |
|--------|------|
| CREATE | `src/agentflow/rag/loaders.py` |
| EDIT | `src/agentflow/rag/ingest.py` — multi-format + recursive walk |
| EDIT | `src/agentflow/rag/retriever.py` — metadata in results |
| EDIT | `src/agentflow/tools/knowledge.py` — citation format |
| EDIT | `src/agentflow/api/main.py` — CORS, Citation model, neutral titles |
| EDIT | `src/agentflow/graph/nodes.py` — neutral system prompt |
| EDIT | `src/agentflow/config.py` — `data/knowledge` default |
| EDIT | `pyproject.toml` — add `pypdf` |
| CREATE | `data/knowledge/**` — md, txt, pdf samples |
| CREATE | `eval/tasks-knowledge.yaml` |
| CREATE | `tests/test_loaders.py`, `tests/fixtures/*.pdf` (tiny) |
| CREATE | `web/` via `bunx create-next-app@latest` (or `npx`) |
| CREATE | `web/src/components/*`, `web/src/lib/api.ts` |
| CREATE | `web/.env.local.example` |
| EDIT | `README.md`, `docs/RAG.md`, `docs/ARCHITECTURE.md` |
| EDIT | `.env.example`, `.gitignore` |
| REMOVE | `static/` (after Next.js validated) |
| OPTIONAL | `portfolio/src/lib/data.ts`, deploy configs |

---

## 7. Testing protocol

```bash
cd agentflow
uv sync --extra dev
uv run pytest tests/ -q
uv run ruff check src/ tests/

# Ingest multi-format KB
uv run agentflow-ingest data/knowledge

# Eval
uv run agentflow-eval --tasks eval/tasks-knowledge.yaml

# API
AGENTFLOW_PORT=8081 uv run agentflow-api

# Next.js (separate terminal)
cd web && bun install && bun dev
# Manual: chat at localhost:3000, verify citations for .pdf and .md

# Build check
cd web && bun run build
```

---

## 8. Acceptance criteria (definition of done)

- [ ] README positions product as **industry-agnostic Knowledge Copilot**
- [ ] `agentflow-ingest data/knowledge` ingests **.md + .txt + .pdf** successfully
- [ ] Citations show filename and PDF page when applicable
- [ ] `eval/tasks-knowledge.yaml` ≥ 85% pass rate
- [ ] Next.js app at `localhost:3000` chats with API via `NEXT_PUBLIC_API_URL`
- [ ] CORS works (no browser blocked fetch)
- [ ] All pytest tests pass (45+ tests)
- [ ] `bun run build` succeeds in `web/`
- [ ] `static/` removed or deprecated; FastAPI no longer primary UI
- [ ] No FlowDesk-hardcoded product name in README title (OK as example tenant)
- [ ] Git rules followed (Section 9)

---

## 9. Git & commit rules (critical)

1. **Account:** `0xrameshh` only  
2. **Do not** use agent `git commit` (Cursor co-author injection)  
3. Use **`git commit-tree`** or user commits from terminal  
4. **Never commit:** `.env`, `web/.env.local`, `.chroma/`, `runs/`, `eval/reports/`, `web/node_modules/`, `web/.next/`  
5. **Commit `web/package.json` + lockfile** (`bun.lock` or `package-lock.json`) — yes  

---

## 10. Suggested implementation order

```
Day 1:  Phase 1 (rebrand) + Phase 2a–2c (loaders + ingest) + sample PDFs
Day 2:  Phase 2d–2f (citations + tests) + Phase 3 (eval tasks)
Day 3:  Phase 4 (create-next-app + chat UI + CORS)
Day 4:  Phase 5 (docs, remove static) + Phase 6–7 (deploy + portfolio)
```

**Start with Phase 2 loaders** — multi-format ingest is the highest credibility upgrade.

---

## 11. create-next-app reference (copy-paste)

```bash
cd /path/to/agentflow

# Bun (preferred)
bunx create-next-app@latest web \
  --ts --tailwind --eslint --app --src-dir \
  --import-alias "@/*" --turbopack --no-git

# Node fallback
npx create-next-app@latest web \
  --ts --tailwind --eslint --app --src-dir \
  --import-alias "@/*" --turbopack --no-git

cd web
cp .env.local.example .env.local
bun install
bun dev
```

---

## 12. Interview talking points (v2)

> “I built an industry-agnostic knowledge copilot: ingest PDFs, markdown, and text into Chroma, answer via a LangGraph agent with a critic that enforces grounding, and return cited sources with page numbers for PDFs. The stack is FastAPI + LangGraph on the backend and Next.js on the frontend, with a YAML eval suite for regression testing. Support SaaS is one example tenant, not the product.”

---

## 13. Relationship to plan.md (v1)

| v1 (`plan.md`) | v2 (`plan-v2.md`) |
|----------------|-------------------|
| FlowDesk Support KB Copilot | Knowledge Copilot (generic) |
| `data/support-kb/*.md` | `data/knowledge/**` + pdf + txt |
| `static/` HTML UI | `web/` Next.js |
| `eval/tasks-support-kb.yaml` | + `eval/tasks-knowledge.yaml` |

**Do not delete v1 work** — migrate and generalize it.
