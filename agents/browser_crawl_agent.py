import sys
import asyncio
import hashlib
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from utils.llm_helper import LLMHelper
from utils.models import ScreenAnalysisModel
from database.neo4j_manager import Neo4jManager
import json

class BrowserCrawlAgent:
    def __init__(self):
        self.llm_helper = LLMHelper()
        self.db_manager = Neo4jManager()
        self.visited_urls = set()

    async def crawl(self, start_url, max_depth=2, focus_components=None):
        """
        Crawls the app. If focus_components is provided, it tries to prioritize 
        screens that might contain those components.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            queue = [(start_url, 0)]
            
            while queue:
                url, depth = queue.pop(0)
                if url in self.visited_urls or depth > max_depth:
                    continue
                
                print(f"Crawling: {url} at depth {depth}", file=sys.stderr)
                self.visited_urls.add(url)
                
                try:
                    await page.goto(url, wait_until="networkidle")
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1) # Wait for potential animations
                    
                    content = await page.content()
                    cleaned_html = self._clean_html(content)
                    
                    analysis = self._analyze_screen(cleaned_html, url, focus_components)
                    self._store_analysis(analysis, url)
                    
                    # If we are looking for specific components and found them, 
                    # we might decide to stop or focus more here.
                    
                    if depth < max_depth:
                        links = await self._extract_links(page, start_url)
                        for link in links:
                            if link not in self.visited_urls:
                                queue.append((link, depth + 1))
                                
                except Exception as e:
                    print(f"Error crawling {url}: {e}", file=sys.stderr)
            
            await browser.close()

    def _clean_html(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(['script', 'style', 'svg', 'path', 'iframe', 'noscript']):
            tag.decompose()
        
        # Keep essential tags for UI discovery
        interactive_tags = ['button', 'a', 'input', 'select', 'textarea', 'form', 'label', 'nav', 'header', 'footer']
        for tag in soup.find_all(True):
            if tag.name not in interactive_tags and not tag.find(interactive_tags) and not tag.get_text(strip=True):
                tag.decompose()
                
        return soup.prettify()[:15000] # Slightly larger limit for Llama 3

    def _analyze_screen(self, html, url, focus_components=None):
        focus_msg = f"\nFOCUS: Pay special attention to components related to: {focus_components}" if focus_components else ""
        
        prompt = f"""
        Analyze the following HTML content of a web page at URL: {url}.
        Extract the screen's purpose, interactive elements, and possible user actions.
        {focus_msg}
        
        HTML:
        {html}
        """
        return self.llm_helper.get_structured_output(prompt, ScreenAnalysisModel, {"url": url})

    def _store_analysis(self, analysis, url):
        screen_data = {
            "id": analysis['id'],
            "url": url,
            "title": analysis['title'],
            "purpose": analysis['purpose']
        }
        self.db_manager.add_screen(screen_data)
        
        for elem in analysis['elements']:
            self.db_manager.add_ui_element(elem, analysis['id'])
            
        for action in analysis['actions']:
            target_id = None
            if action.get('target_screen_url'):
                target_id = action['target_screen_url'].split('/')[-1] or "home"
            
            self.db_manager.add_user_action(action, action['id'], target_id)

    async def _extract_links(self, page, base_url):
        links = await page.eval_on_selector_all("a", "elements => elements.map(e => e.href)")
        domain = base_url.split('//')[-1].split('/')[0]
        return [l for l in links if domain in l and not l.endswith(('.pdf', '.jpg', '.png', '.zip'))]
