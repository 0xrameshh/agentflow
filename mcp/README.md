# Agentflow MCP Server

Exposes agentflow tools via **Model Context Protocol** (MCP) — the same tools used by the LangGraph agent, available to Cursor, Claude Desktop, and any MCP client.

## Tools

| Tool | Description |
|------|-------------|
| `search_knowledge` | Search local docs (RAG with Chroma + keyword fallback) |
| `calculator` | Evaluate math expressions |
| `web_search` | Search built-in AI topics index |
| `run_eval_summary` | Run eval suite and return report |

## Setup

### 1. Install dependencies

```bash
cd agentflow
uv sync
```

### 2. Set API key

```bash
export OPENAI_API_KEY="sk-..."
```

### 3. Configure your MCP client

#### Cursor

Add to `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "agentflow": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/agentflow", "python", "-m", "agentflow.mcp.server"],
      "env": {
        "OPENAI_API_KEY": "${env:OPENAI_API_KEY}"
      }
    }
  }
}
```

#### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agentflow": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/agentflow", "python", "-m", "agentflow.mcp.server"],
      "env": {
        "OPENAI_API_KEY": "your-key-here"
      }
    }
  }
}
```

### 4. Test

```bash
# Smoke test — should list tools
uv run python -m agentflow.mcp.server

# Or use the MCP inspector
npx @modelcontextprotocol/inspector uv run python -m agentflow.mcp.server
```

## Smoke test script

```bash
bash scripts/mcp_smoke.sh
```

## Architecture

The MCP server imports the **same tool implementations** used by the LangGraph agent:

```
src/agentflow/tools/knowledge.py  ← shared by agent + MCP
src/agentflow/tools/calculator.py ← shared by agent + MCP
src/agentflow/tools/search.py     ← shared by agent + MCP
src/agentflow/mcp/server.py       ← MCP wrapper
```

The LangGraph agent and MCP server import the same tool modules under `src/agentflow/tools/`.
