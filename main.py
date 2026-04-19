import asyncio
from agents.browser_crawl_agent import BrowserCrawlAgent
from agents.prd_ingestion_agent import PRDIngestionAgent
from agents.mapping_agent import MappingAgent
from agents.code_change_impact_agent import CodeChangeImpactAgent
from database.neo4j_manager import Neo4jManager

async def main():
    db_manager = Neo4jManager()
    
    print("Step 0: Initializing Database...")
    try:
        # Test connection
        db_manager.query("RETURN 1")
        print("Successfully connected to Neo4j!")
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
        print("Please check your NEO4J_URI, USERNAME, and PASSWORD in .env")
        return

    db_manager.clear_database()
    db_manager.create_constraints()
    
    print("\nStep 1: Running Browser Crawl Agent...")
    crawl_agent = BrowserCrawlAgent()
    # Crawling only a few pages for demo purposes
    await crawl_agent.crawl("https://demo.opencart.com/", max_depth=1)
    
    print("\nStep 2: Running PRD Ingestion Agent...")
    prd_agent = PRDIngestionAgent()
    sample_prd = """
    # OpenCart E-commerce PRD
    
    ## Feature: User Authentication
    - REQ-001: Users must be able to register for a new account.
    - REQ-002: Users must be able to log in with their credentials.
    - REQ-003: Users must be able to recover their password.
    
    ## Feature: Shopping Cart
    - REQ-004: Users can add products to the cart from the product page.
    - REQ-005: Users can view their cart contents.
    - REQ-006: Users can remove items from the cart.
    
    ## User Flow: Checkout Process
    1. Log in to account
    2. Add product to cart
    3. Navigate to checkout
    4. Provide payment details
    5. Confirm order
    """
    prd_agent.ingest(sample_prd)
    
    print("\nStep 3: Running Mapping Agent...")
    mapping_agent = MappingAgent()
    mapping_agent.map_all()
    
    print("\nStep 4: Running Code Change Impact Agent...")
    impact_agent = CodeChangeImpactAgent()
    # Sample diff changing a component that likely maps to a UI element
    sample_diff = """
--- a/src/components/AccountButton.jsx
+++ b/src/components/AccountButton.jsx
@@ -5,5 +5,5 @@
-  return <button onClick={login}>Login</button>;
+  return <button className="login-btn" onClick={login}>Login</button>;
    """
    impact = impact_agent.analyze_diff(sample_diff)
    report = impact_agent.generate_report(impact)
    
    print("\nFinal Blast Radius Report:")
    print(report)
    
    db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
