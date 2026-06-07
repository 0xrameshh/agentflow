# Support KB Copilot — Implementation Plan

> **Status:** Ready for implementation  
> **Repo:** `agentflow` (https://github.com/0xrameshh/agentflow)  
> **Goal:** Reposition Agentflow from a generic “agent runtime demo” into a **problem-solving product**: a **Support Knowledge Base copilot** with cited answers, regression evals, and a simple web UI.

---

## 1. Product framing (read this first)

### Problem

Customer support agents answer the same questions repeatedly — billing, refunds, login issues, shipping, account settings. Answers live in scattered docs (Notion, Confluence, PDFs, old tickets). Searching manually takes **5–15 minutes per ticket** and leads to **inconsistent replies**.

### Solution

**Support KB Copilot** — an internal assistant that:

1. Ingests a support knowledge base (markdown FAQs + policies + troubleshooting guides)
2. Answers agent questions using **RAG + LangGraph** (tool calls + structured critic)
3. Returns answers **with source citations** (which KB article the answer came from)
4. Is measured by a **YAML eval suite** of real support scenarios

### Primary user

Tier-1 / Tier-2 **support agent** at a SaaS company (fictional brand: **FlowDesk** — a project-management SaaS).

### Success metrics (MVP)

| Metric | Target |
|--------|--------|
| Eval pass rate on support tasks | ≥ 85% (stretch: 90%) |
| Answers cite correct KB doc | Visible in UI + trace |
| p50 latency per question | < 15s (gpt-4o-mini) |
| Demo usable without curl | Live chat UI at `/` |

### Non-goals (do NOT build in v1)

- Real ticketing (Zendesk/Intercom integration)
- User authentication / RBAC
- Multi-tenant KB management UI
- Admin panel to upload docs
- Real web search (keep existing stub or remove from support flows)
- Separate microservices repo

---

## 2. What already exists (reuse, don’t rewrite)

| Component | Location | Reuse |
|-----------|----------|-------|
| LangGraph research graph | `src/agentflow/graph/` | ✅ Update prompts only |
| Structured critic loop | `src/agentflow/graph/nodes.py` | ✅ Keep |
| Supervisor graph | `src/agentflow/graph/supervisor.py` | ✅ Optional for v1 |
| `search_knowledge` tool | `src/agentflow/tools/knowledge.py` | ✅ Update docstring + default dir |
| Chroma ingest | `src/agentflow/rag/ingest.py` | ✅ Point at new KB dir |
| Chroma retriever | `src/agentflow/rag/retriever.py` | ✅ Already loads `.env` |
| Eval harness | `src/agentflow/eval/runner.py` | ✅ New task file |
| FastAPI | `src/agentflow/api/main.py` | ✅ Extend responses + static UI |
| MCP server | `src/agentflow/mcp/server.py` | ✅ Update descriptions |
| pytest suite | `tests/` | ✅ Extend, keep 33+ passing |
| Docker | `Dockerfile`, `docker-compose.yml` | ✅ Update env/docs path |

**Engineering depth stays.** We change **data, prompts, docs, evals, API response shape, and UI** — not the graph architecture.

---

## 3. System design

```
┌─────────────────────────────────────────────────────────────┐
│  Support Agent (browser)                                     │
│  Chat UI at GET /  →  POST /run/support  (or /run/full)     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  FastAPI (agentflow.api.main)                                │
│  - serve static/index.html                                   │
│  - return { answer, citations[], run_id, latency_ms }        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  LangGraph research graph                                    │
│  init_run → agent → run_tools → structured_critic → END      │
│  Tools: search_knowledge (primary), calculator (optional)      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  RAG layer                                                   │
│  agentflow-ingest data/support-kb  →  .chroma/               │
│  search_knowledge → Chroma (default) → keyword fallback        │
└─────────────────────────────────────────────────────────────┘
```

### Key design decisions

1. **Fictional product “FlowDesk”** — all sample KB docs reference this brand so evals feel real but use no real company data.
2. **Support-only system prompt** — agent acts as internal support copilot, must call `search_knowledge` before answering KB questions.
3. **Structured citations in API** — UI needs `citations: [{source, snippet}]`, not just text parsing. Extract from tool results in graph state or trace.
4. **Static frontend** — single `static/index.html` + `static/app.js` + `static/styles.css`, served by FastAPI `StaticFiles`. No Next.js in v1.
5. **Keep calculator evals** — shows tool-calling still works; majority of evals should be support KB tasks.

---

## 4. Implementation phases

### Phase 0 — Prep (30 min)

- [ ] Read `README.md`, `docs/ARCHITECTURE.md`, `docs/RAG.md`, `src/agentflow/graph/nodes.py`
- [ ] Confirm local dev works:
  ```bash
  cd agentflow
  uv sync --extra dev
  uv run pytest tests/
  ```
- [ ] Do **not** commit `.env`, `.chroma/`, `runs/`, `eval/reports/`

---

### Phase 1 — Support knowledge base content

**Create directory:** `data/support-kb/`

**Add 6–8 markdown files** (realistic, self-contained, 300–800 words each):

| File | Topics to cover |
|------|-----------------|
| `billing-faq.md` | Plans (Free/Pro/Team), upgrade/downgrade, failed payments, invoices |
| `refund-policy.md` | 30-day refund window, pro-rated rules, how to initiate refund |
| `login-troubleshooting.md` | Password reset, 2FA lockout, SSO issues, “invalid session” |
| `account-settings.md` | Change email, delete account, export data, workspace roles |
| `shipping-and-delivery.md` | *(only if FlowDesk sells physical goods — OR repurpose as “data export delivery”)* → Prefer: `data-export.md` for GDPR export timelines |
| `integrations.md` | Slack/GitHub integration setup, webhook failures, API keys |
| `known-issues.md` | Current bugs + workarounds (e.g. mobile sync delay, calendar sync) |
| `escalation-guide.md` | When to escalate to Tier-2, SLA tiers, severity definitions |

**Content rules:**

- Write as internal support KB articles (headers, bullet steps, clear policies)
- Include **specific numbers** evals can check (e.g. “30-day refund”, “24-hour SLA for P1”)
- Cross-link by filename in prose (“see refund-policy.md”)
- **Remove or relocate** old `data/sample/` tech docs OR keep `data/sample/` for dev tests only and point production KB at `data/support-kb/`

**Config change:**

- Update `AGENTFLOW_DOCS_DIR` default in `src/agentflow/config.py` to `data/support-kb` (or add `AGENTFLOW_KB_DIR` env var; document in `.env.example`)

**Ingest:**

```bash
uv run agentflow-ingest data/support-kb
```

---

### Phase 2 — Prompts & tool descriptions

**Files to edit:**

| File | Change |
|------|--------|
| `src/agentflow/graph/nodes.py` | Replace `SYSTEM_PROMPT` with support-agent persona (FlowDesk internal copilot). Instruct: always `search_knowledge` for policy/how-to questions; cite sources in answer. |
| `src/agentflow/graph/nodes.py` | Tune `CRITIC_PROMPT`: penalize answers without grounding in KB for support questions. |
| `src/agentflow/tools/knowledge.py` | Update tool docstring: “Search FlowDesk support knowledge base…” |
| `src/agentflow/graph/supervisor.py` | Update researcher/writer prompts if supervisor kept in demo |
| `src/agentflow/mcp/server.py` | Update tool descriptions to match |

**Example system prompt tone:**

```
You are FlowDesk's internal support copilot. Support agents ask you policy and troubleshooting questions.

Rules:
- For product/policy/how-to questions, call search_knowledge before answering.
- Base answers on retrieved KB content; do not invent policies.
- Include which KB article(s) you used, e.g. [source: refund-policy.md].
- Be concise and actionable (steps, timelines, exceptions).
- If KB has no answer, say so and suggest escalation per escalation-guide.md.
```

---

### Phase 3 — API: support endpoint + citations

**File:** `src/agentflow/api/main.py`

**Add response models:**

```python
class Citation(BaseModel):
    source: str          # e.g. "refund-policy.md"
    snippet: str         # first ~200 chars of matched chunk

class SupportRunResponse(BaseModel):
    answer: str
    citations: list[Citation]
    thread_id: str
    run_id: str
    tool_call_count: int
    revision_count: int
    latency_ms: int
```

**Add helper** `_extract_citations(state: dict) -> list[Citation]`:

- Walk `state["messages"]` for `ToolMessage` results from `search_knowledge`
- Parse `[source: filename.md]` lines (already formatted in `knowledge.py`)
- Deduplicate by `source`

**Add endpoint:** `POST /run/support` (or extend `/run/full`)

- Uses existing `run_agent_with_state`
- Returns `SupportRunResponse` with citations
- UI should call this endpoint

**Optional:** `GET /kb/articles` — list ingested filenames for sidebar (nice-to-have)

---

### Phase 4 — Frontend (minimal chat UI)

**Create:**

```
static/
  index.html    # chat layout, FlowDesk branding
  app.js        # fetch POST /run/support, render messages + citation chips
  styles.css    # clean, professional (not generic AI purple gradient slop)
```

**Serve from FastAPI:**

```python
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def ui():
    return FileResponse("static/index.html")
```

**UI requirements:**

- Header: “FlowDesk Support Copilot” + one-line problem statement
- Chat input + send button
- Message bubbles (user / assistant)
- **Citation chips** under assistant messages (click to show snippet or filename)
- Loading state while waiting for API
- Example prompts as clickable chips:
  - “How do I process a refund within 30 days?”
  - “Customer locked out after 2FA — what steps?”
  - “What's the P1 escalation SLA?”
- Error handling if API key missing (friendly message, no stack trace)
- Mobile-friendly (single column, readable on phone)

**Tech:** Vanilla HTML/CSS/JS only. No React build step in v1.

**CORS:** Not needed if UI served from same origin.

---

### Phase 5 — Eval suite for support scenarios

**Create:** `eval/tasks-support-kb.yaml` (15 tasks)

**Categories:**

| Category | Count | Example |
|----------|-------|---------|
| Billing / refunds | 4 | “Can a customer get a refund after 45 days?” → expect “30” or “not eligible” |
| Login / account | 4 | “User can't reset password — first steps?” |
| Integrations | 2 | “Slack webhook failing — what to check?” |
| Escalation / SLA | 2 | “When escalate P1 vs P2?” |
| Edge / grounding | 3 | Question not in KB → expect “not found” or escalation, not hallucination |

**Keep** `eval/tasks.yaml` for generic/graph tests OR merge into one file with clear sections.

**Update CLI:**

- `agentflow-eval` accepts `--tasks eval/tasks-support-kb.yaml` flag (add if missing)
- `scripts/live_smoke.sh` — run support eval file, threshold ≥ 85%

**Update tests:**

- `tests/test_core.py` — point knowledge search tests at `data/support-kb/`
- `tests/test_rag.py` — update `_load_documents` path if sample dir changes
- Add `tests/test_api_support.py` — TestClient for `/run/support` with mocked LLM OR mark integration tests `@pytest.mark.integration`

---

### Phase 6 — Documentation rewrite (product-owner style)

**Rewrite `README.md` structure:**

```markdown
# FlowDesk Support KB Copilot (Agentflow)

## Problem
[2-3 sentences]

## Solution
[what it does]

## Demo
[Screenshot or GIF placeholder + local run instructions]

## Architecture
[link to docs/ARCHITECTURE.md — add Support KB section]

## Eval results
[example: 13/15 tasks pass, link to eval/reports sample]

## Quick start
[existing commands, updated paths]

## Development & testing
[pytest, agentflow-eval, live_smoke.sh]

## Deployment
[Phase 7]
```

**Update:**

- `docs/ARCHITECTURE.md` — add “Support KB product flow” section
- `docs/RAG.md` — ingest `data/support-kb`, example citations from support docs
- `mcp/README.md` — describe support use case
- `.env.example` — add `AGENTFLOW_DOCS_DIR=data/support-kb` if configurable

**Do NOT add:**

- Interview scripts, PepsiCo JD, “built for hiring” language
- `AGENTS.md`, `CLAUDE.md`, `TODO.md` in git

---

### Phase 7 — Deployment (prove full cycle)

**Target:** One public demo URL (recruiter can try without cloning).

**Recommended:** Railway or Fly.io (free tier friendly).

**Steps:**

1. Ensure `Dockerfile` copies `data/support-kb/` and `static/`
2. Document build-time ingest OR bake pre-ingested `.chroma` into image (prefer runtime ingest in entrypoint script if API key available via env)
3. Add `scripts/docker_entrypoint.sh`:
   ```bash
   #!/bin/sh
   uv run agentflow-ingest data/support-kb || true
   exec uv run agentflow-api
   ```
4. Env vars on host: `OPENAI_API_KEY`, `AGENTFLOW_RETRIEVER=chroma`, `AGENTFLOW_DOCS_DIR=data/support-kb`
5. Add **Deployment** section to README with platform-specific steps

**Security for public demo:**

- Rate limit already exists in API (20 req/min) — keep it
- Do **not** expose `/eval` publicly without auth, or disable in production via env flag `AGENTFLOW_ENABLE_EVAL=false`
- Add note: demo uses fictional FlowDesk data only

---

### Phase 8 — Portfolio sync (separate repo)

**File:** `portfolio/src/lib/data.ts` (repo: `0xrameshh.github.io`)

Update Agentflow project entry:

```typescript
{
  name: "FlowDesk Support KB Copilot",
  link: "https://github.com/0xrameshh/agentflow",
  // add liveDemo link when deployed
  stack: ["Python", "LangGraph", "FastAPI", "Chroma", "RAG"],
  highlights: [
    "Internal support copilot for tier-1 agents — cited answers from markdown KB via Chroma RAG.",
    "LangGraph agent with structured critic loop and 15-task regression eval suite.",
    "FastAPI backend + chat UI; Docker deploy ready.",
  ],
}
```

Only do this after MVP is working locally.

---

## 5. File checklist (summary)

| Action | Path |
|--------|------|
| CREATE | `data/support-kb/*.md` (6–8 files) |
| CREATE | `static/index.html`, `static/app.js`, `static/styles.css` |
| CREATE | `eval/tasks-support-kb.yaml` |
| CREATE | `scripts/docker_entrypoint.sh` (optional) |
| EDIT | `src/agentflow/config.py` — default KB dir |
| EDIT | `src/agentflow/graph/nodes.py` — system/critic prompts |
| EDIT | `src/agentflow/tools/knowledge.py` — docstring |
| EDIT | `src/agentflow/api/main.py` — static files, `/run/support`, citations |
| EDIT | `src/agentflow/eval/runner.py` — `--tasks` CLI flag |
| EDIT | `README.md`, `docs/ARCHITECTURE.md`, `docs/RAG.md` |
| EDIT | `tests/test_core.py`, `tests/test_rag.py` |
| CREATE | `tests/test_api_support.py` |
| EDIT | `scripts/live_smoke.sh` — support KB smoke tests |
| EDIT | `Dockerfile`, `docker-compose.yml` |
| EDIT | `.env.example` |
| OPTIONAL | `portfolio/src/lib/data.ts` |

---

## 6. Testing protocol (must pass before push)

```bash
cd agentflow
uv sync --extra dev

# 1. Unit tests (no API key)
uv run pytest tests/ -q

# 2. Lint
uv run ruff check src/ tests/

# 3. Ingest support KB (needs OPENAI_API_KEY in .env)
uv run agentflow-ingest data/support-kb

# 4. Start API
uv run agentflow-api
# Open http://localhost:8080 — ask a refund question, verify citations appear

# 5. Support eval suite
uv run agentflow-eval --tasks eval/tasks-support-kb.yaml
# Target: ≥ 85% pass rate

# 6. Full smoke (optional)
bash scripts/live_smoke.sh
```

---

## 7. Acceptance criteria (definition of done)

- [ ] README opens with **problem → solution**, not feature list
- [ ] `data/support-kb/` has ≥ 6 realistic articles for fictional FlowDesk
- [ ] `uv run agentflow-ingest data/support-kb` succeeds
- [ ] Chat UI at `http://localhost:8080/` works end-to-end
- [ ] `POST /run/support` returns `answer` + `citations[]`
- [ ] `eval/tasks-support-kb.yaml` has ≥ 15 tasks, ≥ 85% pass with gpt-4o-mini
- [ ] All pytest tests pass (≥ 33 tests)
- [ ] No interview/hiring/AI-slop language in docs
- [ ] `.env` not committed; git history shows only `0xrameshh`
- [ ] Docker build runs API + serves UI

---

## 8. Git & commit rules (critical)

This repo must stay clean for job portfolio:

1. **Account:** `0xrameshh` only
2. **Do not** use agent `git commit` (injects Cursor co-author)
3. Use **`git commit-tree`** or user commits from terminal
4. Global identity: `Ramesh <53528683+0xrameshh@users.noreply.github.com>`
5. **Never commit:** `.env`, `.chroma/`, `runs/`, `eval/reports/`, `TODO.md`

---

## 9. Suggested implementation order for the agent

```
Day 1:  Phase 1 (KB content) + Phase 2 (prompts) + ingest
Day 2:  Phase 3 (API citations) + Phase 5 (eval tasks) + tests
Day 3:  Phase 4 (UI) + Phase 6 (docs) + manual QA
Day 4:  Phase 7 (deploy) + Phase 8 (portfolio) — optional
```

**Start with Phase 1** — without realistic KB content, everything else feels fake.

---

## 10. Open questions (agent can decide)

| Question | Recommendation |
|----------|----------------|
| Keep `data/sample/` tech docs? | Keep for dev/unit tests; production KB uses `data/support-kb/` |
| Remove `web_search` from support flows? | Keep tool but evals should prefer `search_knowledge`; don't require web_search in support evals |
| Separate repo for UI? | No — static files in same repo |
| Rename repo to `flowdesk-support-copilot`? | No — keep `agentflow` URL; subtitle in README is enough |

---

## 11. Interview talking points (for README “Why this exists” section)

After implementation, the story should be:

> “Support agents at SaaS companies lose time searching internal docs. I built a copilot that ingests markdown KB articles into Chroma, answers via a LangGraph agent with a critic loop that enforces grounding, and returns cited sources. I validate quality with a 15-task YAML eval suite and ship a chat UI + FastAPI so anyone can demo it.”

That is **product owner + engineer** in one paragraph.
