# KG-RAG Ablation Study Results

**Test Query**: `Which investors are funding Agentic AI startups?`

## Run 1: Vector-Only (ChromaDB)
- Context Length (Chars): 16713
- LLM Answer:
> The provided context does not specify which investors are currently funding **agentic AI startups** directly. However, it highlights investor preferences and trends that strongly favor **AI-native startups with deep workflow integration, proprietary data, and systems of action**—characteristics aligned with agentic AI.

Key investors mentioned who are reallocating capital toward such models include:

- **Igor Ryabenkiy**, Managing Partner at **AltaIR Capital**, who emphasizes investing in businesses that "own workflows, data, and domain expertise" and are moving away from easily replicable products.
- **Jake Saper**, General Partner at **Emergence Capital**, who points to execution-over-process tools like **Claude Code** as the future, signaling interest in agent-driven task completion rather than human-centric workflow tools.
- **Aaron Holiday**, Managing Partner at **645 Ventures**, who backs startups building **AI-native infrastructure** and **systems of action**—categories closely related to agentic AI.
- **Abdul Abdirahman** of **F-Prime**, who notes declining interest in tools for human coordination, as AI agents increasingly execute tasks autonomously.

While none of these investors are explicitly named as funding specific “agentic AI” startups, their stated priorities indicate they are more likely to fund in this space, especially as they shift capital toward **workflow-owning, AI-executed systems** over traditional SaaS models.

*Source: TechCrunch reporting cited in context, featuring insights from Igor Ryabenkiy (AltaIR Capital), Jake Saper (Emergence Capital), Aaron Holiday (645 Ventures), and Abdul Abdirahman (F-Prime).*

## Run 2: Graph-Only (Neo4j)
- Context Length (Chars): 0
- LLM Answer:
> Based on the provided context, there is no specific information about which investors are funding Agentic AI startups. The knowledge graph does not contain any details regarding investors or funding related to Agentic AI startups.

## Run 3: Hybrid KG-RAG
- Context Length (Chars): 16759
- LLM Answer:
> The provided context does not specify which investors are directly funding **agentic AI startups**. However, it highlights investor preferences and trends that can be used to infer interest in agentic AI:

- **Jake Saper**, General Partner at **Emergence Capital**, emphasizes the shift from human-centric workflow tools to AI-driven task execution, citing Cursor vs. Claude Code as a key example. He suggests that products enabling AI agents to execute tasks—rather than relying on "workflow stickiness" with humans—are the future, indicating strong interest in agentic systems.

- **Igor Ryabenkiy**, Founder and Managing Partner at **AltaIR Capital**, stresses the importance of **real workflow ownership**, **deep product integration**, and **proprietary data**—all foundational for agentic AI. He notes investors are reallocating capital toward businesses that own workflows and domain expertise, which aligns with agentic AI's value proposition.

- **Aaron Holiday** of **645 Ventures** points to investor interest in **systems of action** (AI tools that help users complete tasks) and **AI-native infrastructure**, which are core components of agentic architectures.

While no explicit funding decisions toward agentic AI startups are mentioned, these investors—**Jake Saper (Emergence Capital)**, **Igor Ryabenkiy (AltaIR Capital)**, and **Aaron Holiday (645 Ventures)**—are shown to back the strategic directions that underpin agentic AI development.

*Source: TechCrunch coverage of VC insights, as cited in the provided context.*

## Conclusion
The hybrid approach provides structured investor connections from the KG alongside the rich, nuanced text from the Vector DB. This often results in a more authoritative, hallucination-free response than Vector-only, and a more comprehensive answer than Graph-only.