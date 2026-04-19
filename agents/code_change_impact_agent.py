import requests
import json
from unidiff import PatchSet
from database.neo4j_manager import Neo4jManager
from utils.llm_helper import LLMHelper
from config import GITHUB_TOKEN
import re

class CodeChangeImpactAgent:
    def __init__(self):
        self.db_manager = Neo4jManager()
        self.llm_helper = LLMHelper()

    def fetch_pr_diff(self, pr_url):
        """
        Fetches the diff from a GitHub PR URL.
        Example: https://github.com/owner/repo/pull/123
        """
        # Convert PR URL to diff URL
        if not pr_url.endswith('.diff'):
            # Using API if possible, otherwise simple .diff suffix
            api_url = pr_url.replace('github.com', 'api.github.com/repos').replace('/pull/', '/pulls/')
            headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                diff_url = response.json().get('diff_url')
                response = requests.get(diff_url, headers=headers)
                return response.text
            else:
                # Fallback to simple .diff
                diff_url = pr_url + '.diff'
                response = requests.get(diff_url)
                return response.text
        return requests.get(pr_url).text

    def parse_diff(self, diff_text):
        patch = PatchSet(diff_text)
        changed_components = self._extract_changed_components(patch)
        return changed_components

    def _extract_changed_components(self, patch):
        components = set()
        for pfile in patch:
            file_path = pfile.path
            # Heuristic for component names
            if any(ext in file_path for ext in ['.js', '.jsx', '.ts', '.tsx', '.css', '.scss']):
                component_name = file_path.split('/')[-1].split('.')[0]
                components.add(component_name)
                
                # Also analyze the hunks for added/removed classes or component names
                for hunk in pfile:
                    for line in hunk:
                        if line.is_added or line.is_removed:
                            # Look for CamelCase component names or specific UI identifiers
                            matches = re.findall(r'([A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)*)', line.value)
                            for m in matches:
                                if len(m) > 3: components.add(m)
        return list(components)

    def get_blast_radius(self, component_names):
        impact_report = []
        for component in component_names:
            query = """
            MATCH (e:UIElement)
            WHERE e.component_source CONTAINS $component_name 
               OR e.label CONTAINS $component_name 
               OR e.fingerprint CONTAINS $component_name
            OPTIONAL MATCH (e)-[:IMPLEMENTS]->(r:Requirement)
            OPTIONAL MATCH (e)-[:PART_OF_FLOW]->(fl:UserFlow)
            RETURN e.id as element_id, e.label as label, 
                   collect(distinct r.id) as requirements, 
                   collect(distinct fl.name) as flows
            """
            results = self.db_manager.query(query, {"component_name": component})
            if results:
                impact_report.append({
                    "component": component,
                    "impacted_elements": [dict(res) for res in results]
                })
        return impact_report

    def generate_qa_report(self, impact_report):
        if not impact_report:
            return "No direct impact on UI elements detected in the graph."
            
        report = "### 🛡️ Testsigma QA Blast Radius Report\n\n"
        for item in impact_report:
            report += f"#### Component: `{item['component']}`\n"
            for elem in item['impacted_elements']:
                report += f"- **Impacted UI Element**: `{elem['label']}` (ID: {elem['element_id']})\n"
                if elem['requirements']:
                    report += f"  - ✅ Implements Requirements: {', '.join(elem['requirements'])}\n"
                if elem['flows']:
                    report += f"  - 🔄 Part of User Flows: {', '.join(elem['flows'])}\n"
            report += "\n"
        
        # Summary reasoning
        summary_prompt = f"Based on this impact report, provide a high-level QA summary and recommended regression areas:\n{json.dumps(impact_report)}"
        summary = self.llm_helper.simple_chat("You are a Senior QA Engineer.", summary_prompt)
        report += "### 🧪 QA Recommendation\n" + summary
        
        return report

    def generate_test_cases(self, impact_report, diff_text):
        """
        Generates specific test cases based on the impact report and the code diff.
        """
        prompt = f"""
        As a Senior QA Engineer at Testsigma, generate a set of functional test cases for the following code change.
        
        CODE DIFF:
        {diff_text[:2000]}
        
        IMPACTED UI ELEMENTS & REQUIREMENTS:
        {json.dumps(impact_report)}
        
        For each test case, include:
        1. Title
        2. Description
        3. Steps to Reproduce
        4. Expected Result
        5. Automated Test Feasibility (High/Medium/Low)
        """
        
        return self.llm_helper.simple_chat("You are a QA Automation Expert.", prompt)
