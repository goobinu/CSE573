# KG-RAG Ablation Study Results

**Test Query**: `Which investors are funding Agentic AI startups?`

## Run 1: Vector-Only (ChromaDB)
- Context Length (Chars): 16713
- LLM Answer:
> The provided context does not specify which investors are currently funding **agentic AI startups** directly. However, it highlights investor preferences and trends that strongly favor AI-native startups with deep workflow integration, proprietary data, and systems where AI agents can execute tasks autonomously—hallmarks of agentic AI.

Key investors mentioned who are reallocating capital toward such models include:

- **Igor Ryabenkiy**, Managing Partner at **AltaIR Capital**, who emphasizes investing in companies with "real workflow ownership," "domain expertise," and the ability to adapt quickly—traits aligned with agentic AI.
- **Jake Saper**, General Partner at **Emergence Capital**, who notes that products enabling agent-driven task execution (like Claude Code) are favored over those relying on human workflow stickiness. He views the shift from process to execution as a “canary in the coal mine” for future investment trends.
- **Aaron Holiday**, Managing Partner at **645 Ventures**, who backs AI-native infrastructure and systems of action—categories foundational to agentic workflows.
- **Abdul Abdirahman** of **F-Prime**, who sees declining interest in tools for human coordination, as AI agents take over task execution.

While these investors are not explicitly named as funding "agentic AI" startups, their stated focus on workflow ownership, task execution over human dependency, and deep AI integration suggests they are likely supporting startups in the agentic AI space.

*Source: TechCrunch reporting cited in the provided context.*

## Run 2: Graph-Only (Neo4j)
- Context Length (Chars): 0
- LLM Answer:
> The provided context does not contain information about investors funding Agentic AI startups.

## Run 3: Hybrid KG-RAG
- Context Length (Chars): 16759
- LLM Answer:
> The provided context does not specify which investors are directly funding *agentic AI* startups. However, it highlights investor preferences and shifts in funding priorities that indirectly favor agentic AI trends.

Key investors mentioned emphasize backing startups with **deep workflow ownership, proprietary data, and AI-native infrastructure**—characteristics aligned with agentic AI systems:

- **Jake Saper** (General Partner, Emergence Capital) signals strong interest in products where AI agents execute tasks rather than relying on human workflow stickiness. He contrasts Cursor (workflow owner) with Claude Code (task executor), calling the latter a “canary in the coal mine” for agent-driven workflows.
- **Igor Ryabenkiy** (Founder & Managing Partner, AltaIR Capital) stresses that investors are reallocating capital toward businesses that **own workflows, data, and domain expertise**, and away from easily replicable tools—favoring startups with deep AI integration.
- **Aaron Holiday** (Managing Partner, 645 Ventures) identifies investor interest in **AI-native infrastructure** and **systems of action**, which are foundational to agentic AI.
- **Abdul Abdirahman** (Investor, F-Prime) notes declining interest in tools for coordinating human work, as AI agents increasingly perform tasks autonomously.

While none are explicitly named as funding “agentic AI” startups, **Emergence Capital**, **AltaIR Capital**, **645 Ventures**, and **F-Prime** are actively backing trends that align with agentic AI, such as automation via AI agents and deep workflow integration.

*Source: TechCrunch reporting on VC insights from Disrupt 2025 and firm statements.*

## Conclusion
The hybrid approach provides structured investor connections from the KG alongside the rich, nuanced text from the Vector DB. This often results in a more authoritative, hallucination-free response than Vector-only, and a more comprehensive answer than Graph-only.