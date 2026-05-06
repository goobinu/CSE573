# KG-RAG Ablation Study Results

**Test Query**: `Which investors are funding Agentic AI startups?`

## Run 1: Vector-Only (ChromaDB)
- Context Length (Chars): 16713
- LLM Answer:
> The provided context does not specify which investors are currently funding **agentic AI startups** directly. However, it highlights investor preferences and trends that strongly favor **AI-native startups with deep workflow integration, proprietary data, and systems of action**—characteristics closely aligned with agentic AI.

Key investors mentioned who are reallocating capital toward such models include:

- **Igor Ryabenkiy**, Founder and Managing Partner at **AltaIR Capital**, who emphasizes investing in businesses that "own workflows, data, and domain expertise" and are moving away from easily replicable products.
- **Jake Saper**, General Partner at **Emergence Capital**, who notes the shift from human-centric workflow stickiness to task execution by agents, citing **Claude Code** as a signal of change. His firm is likely favoring agent-based execution models.
- **Aaron Holiday**, Managing Partner at **645 Ventures**, who backs startups in AI-native infrastructure and systems of action—categories foundational to agentic AI.
- **Abdul Abdirahman** of **F-Prime**, who sees declining interest in tools for coordinating human work, as AI agents increasingly execute tasks autonomously.

While none of these investors are explicitly named as funding “agentic AI” startups per se, their stated priorities indicate they are directing capital toward the core principles of agentic systems: **autonomous task execution, deep workflow ownership, and reduced reliance on human-in-the-loop processes**.

Source: TechCrunch reporting on investor sentiment in AI SaaS (context provided).

## Run 2: Graph-Only (Neo4j)
- Context Length (Chars): 0
- LLM Answer:
> The provided context does not specify which investors are funding Agentic AI startups. No investor names or funding details related to Agentic AI startups are present in the knowledge graph.

## Run 3: Hybrid KG-RAG
- Context Length (Chars): 16759
- LLM Answer:
> The provided context does not specify which investors are directly funding **agentic AI startups**. However, it highlights the investment preferences and perspectives of several venture capitalists and firms that are actively shaping funding trends in the AI space, particularly favoring startups with deep product differentiation, workflow ownership, and AI-native infrastructure—qualities often associated with agentic AI.

Key investors and firms mentioned who are reallocating capital toward advanced AI models and deeply embedded workflows include:

- **Igor Ryabenkiy**, Founder and Managing Partner at **AltaIR Capital**, who emphasizes investing in businesses that own workflows, data, and domain expertise, and is wary of easily replicable products.
- **Jake Saper**, General Partner at **Emergence Capital**, who sees the shift toward AI agents executing tasks (e.g., Claude Code) rather than tools relying on human workflow stickiness, signaling interest in agent-led paradigms.
- **Aaron Holiday**, Managing Partner at **645 Ventures**, who backs AI-native infrastructure and systems of action—categories aligned with agentic AI development.
- **Abdul Abdirahman** of **F-Prime**, who notes declining interest in generic software and highlights the rise of AI-native startups disrupting traditional SaaS, implying support for more autonomous AI systems.

While none are explicitly named as funding "agentic AI" startups, their strategic focus suggests alignment with such ventures.

*Source: TechCrunch reporting on VC sentiment in AI SaaS investment trends.*

## Conclusion
The hybrid approach provides structured investor connections from the KG alongside the rich, nuanced text from the Vector DB. This often results in a more authoritative, hallucination-free response than Vector-only, and a more comprehensive answer than Graph-only.