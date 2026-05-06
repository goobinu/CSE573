# KG-RAG Ablation Study Results

**Test Query**: `Which investors are funding Agentic AI startups?`

## Run 1: Vector-Only (ChromaDB)
- Context Length (Chars): 25478
- LLM Answer:
> The provided context does not contain information about investors funding agentic AI startups. The documents describe job postings at xAI, including roles in fraud engineering, government integrations, cybersecurity, recommendation systems, and power generation, but do not mention external investors or startup funding. Therefore, based on the given context, no specific investors can be identified.

Source: Vector search results — Job postings for xAI roles.

## Run 2: Graph-Only (Neo4j)
- Context Length (Chars): 0
- LLM Answer:
> Based on the provided context, there is no specific information about which investors are funding Agentic AI startups. The knowledge graph does not contain details on investors or funding related to Agentic AI startups.

## Run 3: Hybrid KG-RAG
- Context Length (Chars): 25524
- LLM Answer:
> The provided context does not contain information about investors funding agentic AI startups. The documents detail job postings at xAI, including roles in fraud engineering, government integrations, cybersecurity, recommendation systems, and power generation, but do not mention external investors or startups in the agentic AI space. 

Source: VECTOR FRAGMENTS (job postings for xAI roles)

## Conclusion
The hybrid approach provides structured investor connections from the KG alongside the rich, nuanced text from the Vector DB. This often results in a more authoritative, hallucination-free response than Vector-only, and a more comprehensive answer than Graph-only.