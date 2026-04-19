import sys
import os
import asyncio
import json
import logging
from typing import Optional, List

# Redirect logging to stderr to prevent MCP protocol interference
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

# Dynamic Path Resolution
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Force load .env from the project root
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from mcp.server.fastmcp import FastMCP
from agents.browser_crawl_agent import BrowserCrawlAgent
from agents.prd_ingestion_agent import PRDIngestionAgent
from agents.mapping_agent import MappingAgent
from agents.code_change_impact_agent import CodeChangeImpactAgent
from database.neo4j_manager import Neo4jManager

# Initialize FastMCP Server
mcp = FastMCP("Testsigma QA Agent")

# Initialize Agents
crawl_agent = None
prd_agent = None
mapping_agent = None
impact_agent = None
db_manager = None

def get_agents():
    global crawl_agent, prd_agent, mapping_agent, impact_agent, db_manager
    if crawl_agent is None:
        try:
            crawl_agent = BrowserCrawlAgent()
            prd_agent = PRDIngestionAgent()
            mapping_agent = MappingAgent()
            impact_agent = CodeChangeImpactAgent()
            db_manager = Neo4jManager()
            db_manager.create_constraints()
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            raise
    return crawl_agent, prd_agent, mapping_agent, impact_agent, db_manager

@mcp.tool()
async def parse_pr_diff(pr_url: str) -> str:
    """
    Fetches and parses a GitHub PR diff to identify changed components and files.
    """
    _, _, _, impact, _ = get_agents()
    try:
        diff_text = impact.fetch_pr_diff(pr_url)
        components = impact.parse_diff(diff_text)
        return json.dumps({
            "status": "success",
            "changed_components": components,
            "diff_preview": diff_text[:500] + "..."
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool()
async def crawl_app(url: str, max_depth: int = 1, focus_components: Optional[List[str]] = None) -> str:
    """
    Crawls a web application to build its UI knowledge graph. 
    Can be targeted towards specific components.
    """
    crawl, _, _, _, _ = get_agents()
    try:
        await crawl.crawl(url, max_depth=max_depth, focus_components=focus_components)
        return json.dumps({"status": "success", "message": f"Crawled {url} and updated graph."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool()
async def ingest_prd(prd_text: str) -> str:
    """
    Parses a Product Requirements Document (PRD) and stores requirements in the graph.
    """
    _, prd, _, _, _ = get_agents()
    try:
        analysis = prd.ingest(prd_text)
        return json.dumps({"status": "success", "data": analysis})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool()
async def map_requirements() -> str:
    """
    Semantically maps ingested requirements to discovered UI elements in the graph.
    """
    _, _, mapping, _, _ = get_agents()
    try:
        mapping.map_all()
        return json.dumps({"status": "success", "message": "Requirement-to-UI mapping complete."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool()
async def get_blast_radius(pr_url: str) -> str:
    """
    Analyzes a PR and traverses the knowledge graph to determine the blast radius and QA impact.
    """
    _, _, _, impact, _ = get_agents()
    try:
        diff_text = impact.fetch_pr_diff(pr_url)
        components = impact.parse_diff(diff_text)
        impact_report = impact.get_blast_radius(components)
        report = impact.generate_qa_report(impact_report)
        return report
    except Exception as e:
        return f"Error analyzing blast radius: {str(e)}"

@mcp.tool()
async def generate_test_cases(pr_url: str) -> str:
    """
    Generates detailed functional test cases for a specific PR based on the impacted UI elements.
    """
    _, _, _, impact, _ = get_agents()
    try:
        diff_text = impact.fetch_pr_diff(pr_url)
        components = impact.parse_diff(diff_text)
        impact_report = impact.get_blast_radius(components)
        test_cases = impact.generate_test_cases(impact_report, diff_text)
        return test_cases
    except Exception as e:
        return f"Error generating test cases: {str(e)}"

@mcp.tool()
async def ping() -> str:
    """
    Simple health check tool to verify if the MCP server is connected and responsive.
    """
    return "pong"

@mcp.tool()
async def query_graph(cypher_query: str) -> str:
    """
    Executes a custom Cypher query against the Neo4j knowledge graph.
    """
    _, _, _, _, db = get_agents()
    try:
        results = db.query(cypher_query)
        return json.dumps({"status": "success", "results": [dict(r) for r in results]})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    mcp.run()
