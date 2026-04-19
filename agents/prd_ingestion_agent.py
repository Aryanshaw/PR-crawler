from utils.llm_helper import LLMHelper
from utils.models import PRDAnalysisModel
from database.neo4j_manager import Neo4jManager
import json

class PRDIngestionAgent:
    def __init__(self):
        self.llm_helper = LLMHelper()
        self.db_manager = Neo4jManager()

    def ingest(self, prd_text):
        prompt = f"""
        Analyze the following Product Requirements Document (PRD).
        Extract features, their associated requirements, and user flows.
        
        PRD:
        {prd_text}
        """
        analysis = self.llm_helper.get_structured_output(prompt, PRDAnalysisModel)
        self._store_analysis(analysis)
        return analysis

    def _store_analysis(self, analysis):
        for feature in analysis['features']:
            feature_data = {
                "id": feature['id'],
                "name": feature['name'],
                "description": feature['description']
            }
            self.db_manager.add_feature(feature_data)
            
            for req in feature['requirements']:
                req_data = {
                    "id": req['id'],
                    "text": req['text'],
                    "acceptance_criteria": req['acceptance_criteria'],
                    "priority": req['priority']
                }
                self.db_manager.add_requirement(req_data, feature['id'])
        
        for flow in analysis['user_flows']:
            flow_data = {
                "id": flow['id'],
                "name": flow['name'],
                "steps": ", ".join(flow['steps'])
            }
            self.db_manager.add_user_flow(flow_data, flow['requirement_ids'])
