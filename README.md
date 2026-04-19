# 🛡️ Living Application Knowledge Graph (Testsigma QA Agent)

An intelligent 4-agent system that connects **Product Requirements**, **UI Elements**, and **Code Changes** into a queryable Neo4j graph to reason about the blast radius of any code change.

## 🚀 Overview
Most QA tools look at code. This agent looks at the running application — the way a real user sees it — and maps it to intent. It crawls a live web app, understands what it sees, connects it to product documentation, and uses that connected knowledge to analyze the impact of PRs.

## 🧠 The 4-Agent Architecture

1.  **Browser Crawl Agent**: Uses Playwright to traverse the app and extract semantic UI structure (roles, labels, purposes).
2.  **PRD Ingestion Agent**: Parses raw markdown PRDs into structured `Feature`, `Requirement`, and `UserFlow` nodes.
3.  **Mapping Agent**: Uses Groq (Llama 3) and local HuggingFace embeddings to semantically link UI elements to requirements.
4.  **Impact & Test Review Agent**: Analyzes GitHub PR diffs, traverses the graph (Code → UI → Requirement), and generates a "Blast Radius Report" with functional test cases.

## 🛠️ Tech Stack
- **Orchestration**: [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- **LLM**: Groq (Llama 3.3 70B)
- **Embeddings**: HuggingFace (Local `all-MiniLM-L6-v2`)
- **Graph DB**: Neo4j (AuraDB)
- **Crawler**: Playwright (Python)
- **Environment**: `uv` for lightning-fast dependency management

## 📦 Installation & Setup

### 1. Prerequisites
- **Neo4j AuraDB** (Free instance)
- **Groq API Key**
- **GitHub Personal Access Token** (Classic, with `repo` scope)
- **Docker** (Recommended) or `uv`

### 2. Configure Environment
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key
NEO4J_URI=bolt://your-neo4j-uri
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
GITHUB_TOKEN=ghp_your_github_token
```

### 3. Connect as MCP Server
To ensure portability, use the `uv run` command. This ensures all dependencies are managed automatically.

```bash
# For Codex
codex mcp add testsigma-qa -- uv run python "$(pwd)/server.py"

# For Claude Code
claude mcp add testsigma-qa -- uv run python "$(pwd)/server.py"
```

## 🛡️ Usage Example
Ask your AI assistant (Codex/Claude) to perform a full review:

1.  **Verify**: "Check if the `testsigma-qa` MCP tools are available by running the `ping` tool."
2.  **Crawl**: "Crawl the live app at `https://demo.realworld.io/` to understand the UI."
3.  **Ingest PRD**: "Ingest this PRD for the RealWorld app: 'Users must be able to login, create articles, and follow authors.'"
4.  **Analyze PR**: "Analyze this PR: `https://github.com/gothinkster/react-redux-realworld-example-app/pull/314`. Generate a blast radius report and test cases."

## 📄 Detailed Guide
For more information on testing and troubleshooting, see the [USAGE.md](./USAGE.md) file.
