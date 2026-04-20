# Design Document: Living Application Knowledge Graph

## 1. Executive Summary
This project implements an agentic system designed to bridge the gap between product requirements, live UI implementations, and underlying code changes. By constructing a queryable Neo4j graph, the system enables automated QA impact analysis, commonly referred to as "blast radius" detection.

## 2. Choice of Application and PRD
- **Application**: [RealWorld App (demo.realworld.io)](https://demo.realworld.io/)
  - **Reasoning**: It is a standard "Conduit" clone with a rich but manageable UI surface area (auth, articles, comments, profiles). It provides a realistic testbed for navigation flows and semantic element mapping.
- **PRD**: A structured markdown specification covering core user stories for authentication and article management.
  - **Reasoning**: Using a standard feature set allows for clear validation of the mapping agent's accuracy against well-understood product intent.

## 3. Graph Schema Design
The schema is designed to represent three distinct layers of knowledge:

### Nodes
- `(:Screen)`: Represents a unique URL or state (e.g., Home, Login).
- `(:UIElement)`: Interactive components (buttons, inputs) with semantic roles.
- `(:UserAction)`: Transitions triggered by elements.
- `(:Requirement)`: Atomic units of product intent from the PRD.
- `(:Feature)`: Higher-level groupings of requirements.
- `(:UserFlow)`: End-to-end sequences (e.g., "Post an Article").

### Relationships
- `(:Screen)-[:CONTAINS]->(:UIElement)`
- `(:UIElement)-[:IMPLEMENTS]->(:Requirement)`: The core semantic link.
- `(:Requirement)-[:PART_OF]->(:Feature)`
- `(:UserFlow)-[:INCLUDES]->(:Requirement)`
- `(:UIElement)-[:TRIGGERS]->(:UserAction)-[:NAVIGATES_TO]->(:Screen)`

## 4. Element Fingerprinting and Graph Stability
To avoid the "fragile selector" problem, we use **Semantic Fingerprinting**:
- **Role + Label + Context**: Instead of CSS paths, we hash the ARIA role, visible text/placeholder, and surrounding structural context.
- **Stability**: This allows the graph to remain valid even if the underlying CSS classes change, as long as the user-facing intent (e.g., a button labeled "Sign In") remains the same.
- **Persistence**: Fingerprints are stored as IDs to enable merging across multiple crawls.

## 5. Mapping Agent Challenges
The Mapping Agent uses vector embeddings followed by LLM verification. Known challenges include:
- **Ambiguity**: A "Submit" button might implement multiple requirements.
- **Context Loss**: Small elements without clear labels require "ancestor context" to map correctly.
- **False Positives**: Generic labels like "Close" or "X" can be incorrectly mapped if the screen purpose isn't strongly weighted.

## 6. V2 at Scale
Scaling to thousands of screens and hundreds of requirements requires:
- **Distributed Crawling**: Parallelizing Playwright instances across a cluster.
- **Incremental Mapping**: Only re-mapping requirements affected by the latest code change.
- **Vector Database Integration**: Moving from local embeddings to a managed vector store (e.g., Neo4j Vector Index) for sub-second similarity searches across millions of nodes.
- **Hierarchical Clustering**: Grouping screens into "Sub-Apps" to limit the search space for the Mapping Agent.
