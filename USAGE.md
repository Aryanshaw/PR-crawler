# 🛡️ Testsigma QA Agent: Connection & Testing Guide

This guide explains how to connect this MCP server to Claude Desktop and test it with real GitHub PRs.

## 1. Prerequisites
- **Claude Desktop App** (Free)
- **Neo4j AuraDB** (Free instance)
- **Groq API Key** (For Llama 3)
- **GitHub Personal Access Token** (Classic, with `repo` scope)

## 2. Connect to Codex or Claude code (Option A: Docker - Recommended)
Containerization ensures the agent works on any machine without needing Python or Playwright installed locally.

**Step 1: Build the image**
```bash
docker build -t testsigma-qa .
```

**Step 2: Add to Codex**
```bash
codex mcp add testsigma-qa -- docker run -i --rm --env-file .env testsigma-qa
```

**Step 3: Add to Claude Code**
```bash
claude mcp add testsigma-qa -- docker run -i --rm --env-file .env testsigma-qa
```

---

## 3. Connect via uv (Option B: Local Python)
If you prefer not to use Docker, ensure you are in the project root:

## 3. Connect to Claude Desktop (Option B: Manual Config)
1. Open the Claude Desktop configuration file:
   - **MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the following configuration (replace `/path/to/your/project` with the actual absolute path):

```json
{
  "mcpServers": {
    "testsigma-qa": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/aryanshaw/Documents/pracice/PRcrawler/Pr-Crawler",
        "run",
        "python",
        "server.py"
      ]
    }
  }
}
```

3. **Restart Claude Desktop.** You should now see a 🔌 icon in the message box.

## 4. Successful Installation Logs (Project Record)
The following steps were taken to successfully verify the MCP installation in Codex:
- **Initialization**: `uv init` and dependency installation with `uv add`.
- **CLI Installation**: `codex mcp add testsigma-qa -- uv run python server.py`.
- **Verification**: `codex mcp list` confirmed the status as `enabled`.
- **Environment**: The server uses the `uv` virtual environment to ensure all dependencies like `playwright` and `langchain-groq` are available.

---

## 5. Real-World Testing Examples

### Example 1: Analyze a PR for RealWorld App
**PR Link**: `https://github.com/gothinkster/react-redux-realworld-example-app/pull/314` (A real PR example)
**Target App**: `https://demo.realworld.io/`

**Conversation Flow:**
1. **User**: "Verify if my MCP tools are available. Run the `ping` tool."
2. **Claude/Codex**: *Calls `ping` tool.*
3. **User**: "I want to review this PR: `https://github.com/gothinkster/react-redux-realworld-example-app/pull/314`. First, crawl the live app at `https://demo.realworld.io/` to understand the UI."
4. **Claude/Codex**: *Calls `crawl_app` tool.*
3. **User**: "Now ingest this PRD for the RealWorld app: 'The app allows users to register, login, create articles, and follow authors. Users must be able to comment on articles.'"
4. **Claude**: *Calls `ingest_prd` and then `map_requirements`.*
5. **User**: "Analyze the blast radius of the PR and generate functional test cases."
6. **Claude**: *Calls `get_blast_radius` and `generate_test_cases`.*

### Example 2: Targeted Component Review
**User**: "This PR `https://github.com/some/repo/pull/42` changes the `LoginButton` and `CartIcon`. Crawl the app focusing on these components and tell me what requirements are at risk."

---

## 4. Troubleshooting the JSON Error
If you see a `json_invalid` error when running `uv run python server.py` manually, it's likely because you are running it in a terminal where Python is trying to print logs to `stdout`, which interferes with the MCP JSON-RPC protocol.

**Correct way to test manually:**
Use the **MCP Inspector** to avoid protocol interference:
```bash
npx @modelcontextprotocol/inspector uv run python server.py
```

## 5. Agent Capabilities
- **`parse_pr_diff`**: Extracts changed components (e.g., `Header`, `AuthService`).
- **`crawl_app`**: Intelligently identifies UI elements, roles, and fingerprints.
- **`map_requirements`**: Semantic mapping (not keyword) using embeddings.
- **`get_blast_radius`**: Graph traversal from Code -> UI -> Requirement.
- **`generate_test_cases`**: AI-generated functional tests based on the actual code change.
