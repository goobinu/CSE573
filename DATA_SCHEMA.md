# TrendScout Data Schema

To maintain the integrity and cleanliness of our Knowledge Graph and Vector Database, all incoming data must adhere to this strict schema. This document serves as the single source of truth for entity types, relationship paths, and vector metadata.

---

## 1. Vector Database (ChromaDB)
All documents embedded into ChromaDB must include the following minimum metadata keys to ensure accurate filtering during Retrieval-Augmented Generation (RAG).

### Required Metadata Keys
When calling `collection.upsert()`, the `metadatas` list must contain dictionaries with these exact keys:
- `author_name` (str): The entity/person who posted the text.
- `profile_url` (str): Link to the author's profile.
- `post_url` (str): Direct link to the source post/article.
- `source_topic` (str): Broad subject classification (e.g., "AI", "Startup Funding").
- `source` (str): The origin of the data (e.g., "LinkedIn", "TechCrunch", "X").

---

## 2. Knowledge Graph (Neo4j)
To prevent "schema drift," we restrict the types of nodes and how they connect. Any script pushing data to Neo4j MUST use the definitions below.

### A. Required Node Labels
Nodes represent entities. You may only use the following specific labels:
*   **Organization**: Companies, VCs, Startups, Universities (e.g., "OpenAI", "Sequoia").
*   **Technology**: Models, Tools, Hardware (e.g., "GPT-4", "H100 GPU", "LangChain").
*   **Trend**: Broad market concepts (e.g., "Generative AI", "Agentic Workflows").
*   **Person**: Specific people mentioned (e.g., "Sam Altman").
*   **Investor**: Capital providers placing bets on trends (e.g., "a16z").
*   **FundingRound**: Capital raises and stages (e.g., "Seed", "Series A").
*   **Skill**: Expertise in demand (e.g., "LangChain", "AutoGPT").

*Note: All nodes implicitly store a `name` property and a `sentiment` property (positive, neutral, negative).*

### B. Allowed Relationship Types
Connections between nodes must use ONLY these specific verbs. Do not invent new verbs.
*   `DISCUSSES` (General context mapping)
*   `IS_PART_OF` (Taxonomy mapping)
*   `WORKS_AT` (Person -> Organization)
*   `PARTICIPATES_IN` (Event/Trend involvement)
*   `INVESTED_IN` (VC/Investor -> Startup)
*   `ACQUIRED` (Company -> Company)
*   `PARTNERED_WITH` (Company -> Company)
*   `RELEASED` (Organization -> Technology)
*   `USES` (Organization -> Technology)
*   `WORKS_FOR` (Person -> Organization)
*   `COMPETES_WITH` (Organization -> Organization)
*   `HIRES_FOR` (Organization -> Skill)
*   `RAISED_IN` (Organization -> FundingRound)
*   `ACQUIRED_BY` (Company -> Company)

*The orchestrator pipeline contains automated checks to reject invalid labels and relationships prior to merging them into the graph.*
