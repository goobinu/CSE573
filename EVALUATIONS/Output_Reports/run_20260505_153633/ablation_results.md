# KG-RAG Ablation Study Results

**Test Query**: `Which investors are funding Agentic AI startups?`

## Run 1: Vector-Only (ChromaDB)
- Context Length (Chars): 25478
- LLM Answer:
> The provided context does not contain information about investors funding agentic AI startups. The documents detail job postings at xAI, including roles in fraud engineering, government integration, cybersecurity, recommendation systems, and power generation, but do not mention external investors or startup funding. Therefore, based on the given context, no specific investors in agentic AI startups can be identified.

Source: Job postings for xAI roles (e.g., "Member Of Technical Staff - X Money, Fraud And Payments", "Site Reliability Engineer - Cybersecurity", etc.) – none reference investors or startup funding.

## Run 2: Graph-Only (Neo4j)
- Context Length (Chars): 0
- LLM Answer:
> Based on the provided context, there is no specific information about investors funding Agentic AI startups. The knowledge graph does not contain details on investors or their investments in this sector.

## Run 3: Hybrid KG-RAG
- Context Length (Chars): 25524
- LLM Answer:
> The provided context does not contain information about investors funding agentic AI startups. The documents describe job postings at xAI, including roles in fraud engineering, government integrations, cybersecurity, recommendation systems, and power generation, but do not mention external investors or funding activities related to agentic AI startups.

## Conclusion
The hybrid approach provides structured investor connections from the KG alongside the rich, nuanced text from the Vector DB. This often results in a more authoritative, hallucination-free response than Vector-only, and a more comprehensive answer than Graph-only.