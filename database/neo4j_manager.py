import sys
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

class Neo4jManager:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]

    def clear_database(self):
        query = "MATCH (n) DETACH DELETE n"
        self.query(query)

    def create_constraints(self):
        # Create unique constraints for IDs
        queries = [
            "CREATE CONSTRAINT screen_id IF NOT EXISTS FOR (s:Screen) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT element_id IF NOT EXISTS FOR (e:UIElement) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT action_id IF NOT EXISTS FOR (a:UserAction) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT requirement_id IF NOT EXISTS FOR (r:Requirement) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT feature_id IF NOT EXISTS FOR (f:Feature) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT flow_id IF NOT EXISTS FOR (fl:UserFlow) REQUIRE fl.id IS UNIQUE"
        ]
        for q in queries:
            try:
                self.query(q)
            except Exception as e:
                # Redirect error to stderr so it doesn't break MCP protocol
                print(f"Error creating constraint: {e}", file=sys.stderr)

    # Screen Layer
    def add_screen(self, screen_data):
        query = """
        MERGE (s:Screen {id: $id})
        SET s.url = $url, s.title = $title, s.purpose = $purpose
        """
        self.query(query, screen_data)

    def add_ui_element(self, element_data, screen_id):
        query = """
        MERGE (e:UIElement {id: $id})
        SET e.type = $type, e.label = $label, e.role = $role, e.fingerprint = $fingerprint, e.component_source = $component_source
        WITH e
        MATCH (s:Screen {id: $screen_id})
        MERGE (s)-[:CONTAINS]->(e)
        """
        element_data['screen_id'] = screen_id
        self.query(query, element_data)

    def add_user_action(self, action_data, element_id, target_screen_id=None):
        query = """
        MERGE (a:UserAction {id: $id})
        SET a.description = $description, a.trigger = $trigger, a.outcome = $outcome
        WITH a
        MATCH (e:UIElement {id: $element_id})
        MERGE (e)-[:TRIGGERS]->(a)
        """
        params = {**action_data, "element_id": element_id}
        self.query(query, params)
        
        if target_screen_id:
            query = """
            MATCH (a:UserAction {id: $id})
            MATCH (s:Screen {id: $target_screen_id})
            MERGE (a)-[:NAVIGATES_TO]->(s)
            """
            self.query(query, {"id": action_data['id'], "target_screen_id": target_screen_id})

    # PRD Layer
    def add_requirement(self, req_data, feature_id=None):
        query = """
        MERGE (r:Requirement {id: $id})
        SET r.text = $text, r.acceptance_criteria = $acceptance_criteria, r.priority = $priority
        """
        self.query(query, req_data)
        
        if feature_id:
            query = """
            MATCH (r:Requirement {id: $id})
            MATCH (f:Feature {id: $feature_id})
            MERGE (f)-[:CONTAINS]->(r)
            """
            self.query(query, {"id": req_data['id'], "feature_id": feature_id})

    def add_feature(self, feature_data):
        query = """
        MERGE (f:Feature {id: $id})
        SET f.name = $name, f.description = $description
        """
        self.query(query, feature_data)

    def add_user_flow(self, flow_data, requirement_ids=None):
        query = """
        MERGE (fl:UserFlow {id: $id})
        SET fl.name = $name, fl.steps = $steps
        """
        self.query(query, flow_data)
        
        if requirement_ids:
            for req_id in requirement_ids:
                query = """
                MATCH (fl:UserFlow {id: $id})
                MATCH (r:Requirement {id: $req_id})
                MERGE (fl)-[:INCLUDES]->(r)
                """
                self.query(query, {"id": flow_data['id'], "req_id": req_id})

    # Mapping Layer
    def add_mapping(self, element_id, requirement_id, reasoning=None):
        query = """
        MATCH (e:UIElement {id: $element_id})
        MATCH (r:Requirement {id: $requirement_id})
        MERGE (e)-[rel:IMPLEMENTS]->(r)
        SET rel.reasoning = $reasoning
        """
        self.query(query, {"element_id": element_id, "requirement_id": requirement_id, "reasoning": reasoning})

    def add_screen_feature_mapping(self, screen_id, feature_id):
        query = """
        MATCH (s:Screen {id: $screen_id})
        MATCH (f:Feature {id: $feature_id})
        MERGE (s)-[:SATISFIES]->(f)
        """
        self.query(query, {"screen_id": screen_id, "feature_id": feature_id})
