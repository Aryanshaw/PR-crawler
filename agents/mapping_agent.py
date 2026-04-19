import sys
import numpy as np
from utils.llm_helper import LLMHelper
from database.neo4j_manager import Neo4jManager
from pydantic import BaseModel, Field
import json

class MappingVerification(BaseModel):
    is_match: bool = Field(description="Whether the UI element implements the requirement")
    reasoning: str = Field(description="Reasoning for the decision")

class MappingAgent:
    def __init__(self):
        self.llm_helper = LLMHelper()
        self.db_manager = Neo4jManager()

    def map_all(self):
        requirements = self._get_all_requirements()
        ui_elements = self._get_all_ui_elements()
        
        if not requirements or not ui_elements:
            print("Missing requirements or UI elements to map.", file=sys.stderr)
            return

        # 1. Get embeddings
        req_embeddings = {r['id']: self.llm_helper.get_embeddings(r['text']) for r in requirements}
        elem_embeddings = {e['id']: self.llm_helper.get_embeddings(f"{e['label']} {e['role']} {e['type']}") for e in ui_elements}

        # 2. Candidate matching
        for req_id, req_emb in req_embeddings.items():
            req_text = next(r['text'] for r in requirements if r['id'] == req_id)
            
            candidates = []
            for elem_id, elem_emb in elem_embeddings.items():
                similarity = self._cosine_similarity(req_emb, elem_emb)
                if similarity > 0.4:  # Slightly higher threshold
                    candidates.append((elem_id, similarity))
            
            candidates.sort(key=lambda x: x[1], reverse=True)
            top_candidates = candidates[:3] # Focus on top 3
            
            # 3. Verification
            for elem_id, sim in top_candidates:
                elem = next(e for e in ui_elements if e['id'] == elem_id)
                verification = self._verify_mapping(req_text, elem)
                if verification and verification.is_match:
                    print(f"Mapped {elem_id} to {req_id}", file=sys.stderr)
                    self.db_manager.add_mapping(elem_id, req_id, verification.reasoning)

    def _get_all_requirements(self):
        query = "MATCH (r:Requirement) RETURN r.id as id, r.text as text"
        return [dict(record) for record in self.db_manager.query(query)]

    def _get_all_ui_elements(self):
        query = "MATCH (e:UIElement) RETURN e.id as id, e.label as label, e.role as role, e.type as type"
        return [dict(record) for record in self.db_manager.query(query)]

    def _cosine_similarity(self, v1, v2):
        v1 = np.array(v1)
        v2 = np.array(v2)
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

    def _verify_mapping(self, requirement_text, element):
        prompt = f"""
        Does this UI element implement this requirement?
        
        Requirement: {requirement_text}
        UI Element: Label: {element['label']}, Role: {element['role']}, Type: {element['type']}
        
        Respond with reasoning and a boolean decision.
        """
        try:
            return self.llm_helper.get_structured_output(prompt, MappingVerification)
        except Exception as e:
            print(f"Verification error: {e}")
            return None
