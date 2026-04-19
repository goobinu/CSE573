# KG-RAG Ablation Study Results

**Test Query**: `Which investors are funding Agentic AI startups?`

## Run 1: Vector-Only (ChromaDB)
- Context Length (Chars): 8893
- LLM Answer:
> Based on the provided context, **Groq**—a startup associated with advancements in AI infrastructure that could support agentic workflows—raised **$750M** in funding, doubling its valuation to **$6.9B**. While the specific investors are not named in the text, the funding round itself signals strong investor interest in high-performance AI infrastructure enabling agentic capabilities.

Additionally, **Figure AI** raised **$1B at a $39B valuation**, with the purpose of scaling humanoid robots—an application area closely tied to agentic AI systems. Again, the specific investors are not listed in the context.

No other direct mentions of investors funding *explicitly* "agentic AI" startups are present in the provided documents. However, major activity from companies like **Nvidia** (investing $5B in Intel for AI chip development) and continued advancements by **Google**, **OpenAI**, and **Anthropic** suggest broader ecosystem support for agentic AI enablers.

**Source**: "AI Companies moved superfast last week..." (multiple bullet points) – no named investors beyond company fundraising totals.

## Run 2: Graph-Only (Neo4j)
- Context Length (Chars): 0
- LLM Answer:
> Based on the provided context, there is no information available about which investors are funding Agentic AI startups. The knowledge graph does not contain relevant data to answer the query.

## Run 3: Hybrid KG-RAG
- Context Length (Chars): 8939
- LLM Answer:
> Based on the provided context, **Groq** is an Agentic AI-related startup that raised **$750M**, doubling its valuation to **$6.9B**. While the specific investor names are not mentioned in the text, the funding round indicates significant investor interest in Agentic AI infrastructure.

Additionally, **Figure AI** raised **$1B at a $39B valuation** to scale humanoid robots — a domain closely tied to agentic systems — though again, the exact investors are not named in the fragments.

Other relevant developments include:
- **Nvidia** investing **$5B in Intel** to co-develop AI chips, signaling strategic bets on AI infrastructure.
- **Nvidia** also announced a **$100B investment in OpenAI**, which is advancing agentic capabilities via GPT-5 and autonomous agents.

Though direct investor names (e.g., venture firms) behind Agentic AI startups are not specified in the text, **Nvidia** emerges as a key financial and strategic backer of AI-native and agentic technologies through its investments in **OpenAI** and **Intel**.

Source: "AI Companies moved superfast last week...", "Cool Startups" section, and "25 major AI updates" fragments.

## Conclusion
The hybrid approach provides structured investor connections from the KG alongside the rich, nuanced text from the Vector DB. This often results in a more authoritative, hallucination-free response than Vector-only, and a more comprehensive answer than Graph-only.