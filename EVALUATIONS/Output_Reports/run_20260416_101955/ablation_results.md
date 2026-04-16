# KG-RAG Ablation Study Results

**Test Query**: `Which investors are funding Agentic AI startups?`

## Run 1: Vector-Only (ChromaDB)
- Context Length (Chars): 8893
- LLM Answer:
> Based on the provided context, **no specific investors funding agentic AI startups are explicitly named** in relation to that particular trend.

However, the documents highlight several major funding events and investors in AI startups more broadly, some of which are developing agentic or advanced AI capabilities:

- **Figure AI** raised **$1B** at a $39B valuation to scale humanoid robots (implying advanced AI/autonomy). While the investor isn't named in the snippet, such large rounds typically involve top-tier VCs or strategic investors.
- **Groq** raised **$750M**, doubling its valuation to **$6.9B** — a significant bet on AI inference/acceleration, critical for agentic systems.
- **Micro1** raised **$35M** to expand human-in-the-loop AI data labeling, supporting AI training for autonomous systems.
- **Nvidia** is investing **$5B in Intel** to co-develop AI chips, signaling strategic support for AI infrastructure enabling agentic workloads.
- **Nvidia** also announced a **$100B investment in OpenAI**, which is advancing agentic capabilities via tools like GPT-5 and autonomous agents.

Though the term "agentic AI" is discussed (e.g., in McKinsey’s report and product launches like **Gamma Agent**, **Notion 3.0 AI Agents**, and **Heygen Video Agent**), the **specific investors behind these agentic AI startups are not named** in the provided texts.

👉 **Conclusion**: The documents confirm strong investor interest and capital flows into AI infrastructure and autonomous systems, with **Nvidia** acting as a major strategic investor, but **do not identify specific VCs or investors exclusively funding "agentic AI" startups**.  

Source: *AI Delivers weekly roundup*, *McKinsey & Company Tech Trends 2025*

## Run 2: Graph-Only (Neo4j)
- Context Length (Chars): 0
- LLM Answer:
> The provided context does not specify which investors are funding Agentic AI startups. Therefore, based on the given information, no definitive list of investors can be provided.

## Run 3: Hybrid KG-RAG
- Context Length (Chars): 8939
- LLM Answer:
> Based on the provided context, **Groq** is an Agentic AI startup that raised **$750M**, doubling its valuation to **$6.9B**. While the specific investors are not named in the text, the funding round itself indicates significant investor interest in Agentic AI infrastructure.

Additionally, **Figure AI** raised **$1B at a $39B valuation** to scale humanoid robots, which aligns with agentic systems due to their autonomous capabilities. Again, specific investor names are not mentioned in the context.

Other relevant developments include **Google’s Agent Payments Protocol** and **Notion 3.0 with AI Agents**, signaling strong ecosystem support for agentic workflows, though these are product launches rather than direct investments.

Therefore, while the exact investor names are not specified in the provided content, major funding is flowing into Agentic AI startups like **Groq** and **Figure AI**, suggesting institutional and strategic investor backing at scale.

Source: "Cool Startups" and "Hardware and Robots" sections of the AI updates; McKinsey & Company Tech Trends 2025.

## Conclusion
The hybrid approach provides structured investor connections from the KG alongside the rich, nuanced text from the Vector DB. This often results in a more authoritative, hallucination-free response than Vector-only, and a more comprehensive answer than Graph-only.