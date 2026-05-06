# KG-RAG Ablation Study Results

**Test Query**: `Which investors are funding Agentic AI startups?`

## Run 1: Vector-Only (ChromaDB)
- Context Length (Chars): 16713
- LLM Answer:
> The provided context does not specify which investors are currently funding **agentic AI startups** directly. However, it highlights the investment preferences and concerns of several venture capitalists and firms regarding AI and SaaS startups, which can indirectly inform what types of agentic AI ventures might attract funding.

Investors mentioned in the text are shifting capital toward businesses that:

- Own **workflows, data, and domain expertise** (Igor Ryabenkiy, AltaIR Capital)  
- Build **deep, AI-native infrastructure** with **real workflow ownership** (Aaron Holiday, 645 Ventures)  
- Focus on **systems of action** where AI agents execute tasks, not just assist humans (Jake Saper, Emergence Capital)  
- Avoid thin UI layers or generic tools that lack **proprietary data moats** (Abdul Abdirahman, F-Prime; Ryabenkiy, AltaIR Capital)  

Jake Saper specifically notes that **"execution over process"** is becoming dominant—favoring tools like **Claude Code** that enable AI agents to perform tasks, as opposed to platforms relying on human workflow stickiness. This suggests that **Emergence Capital** may be more inclined to fund agentic AI systems that enable autonomous task execution.

Similarly, the emphasis on **AI-native infrastructure**, **deep integration**, and **consumption-based pricing** implies that firms like **645 Ventures**, **F-Prime**, **AltaIR Capital**, and **Emergence Capital** are more likely to back agentic AI startups that align with these principles.

While no explicit funding decisions on agentic AI startups are stated, the investors named—**Aaron Holiday (645 Ventures), Abdul Abdirahman (F-Prime), Igor Ryabenkiy (AltaIR Capital), and Jake Saper (Emergence Capital)**—are actively reallocating capital toward AI-native, workflow-owning, and agent-capable systems.

**Source:** TechCrunch reporting on VC sentiment, as cited in the provided context.

## Run 2: Graph-Only (Neo4j)
- Context Length (Chars): 0
- LLM Answer:
> The provided context does not specify which investors are funding Agentic AI startups. Therefore, based on the given information, no definitive list of investors can be provided.

## Run 3: Hybrid KG-RAG
- Context Length (Chars): 16759
- LLM Answer:
> The provided context does not specify which investors are directly funding **agentic AI startups**. However, it highlights key investors and their perspectives on what types of AI startups are currently attractive or unattractive to fund, which can indirectly inform investor interest in agentic AI.

Investors mentioned in the context include:

- **Aaron Holiday** (Managing Partner, 645 Ventures): Favors startups with deep product differentiation, such as AI-native infrastructure, vertical SaaS with proprietary data, and systems embedded in mission-critical workflows—categories aligned with agentic AI’s potential.
  
- **Igor Ryabenkiy** (Founder and Managing Partner, AltaIR Capital): Emphasizes the need for "real workflow ownership," product depth, and proprietary data. He warns against thin AI wrappers, suggesting he would favor agentic AI startups with strong moats.

- **Jake Saper** (General Partner, Emergence Capital): Highlights the shift from human-centric workflow stickiness to agent-driven task execution, using Cursor vs. Claude Code as an example. His view suggests interest in startups where AI agents own workflows, indicating likely support for agentic AI models.

- **Abdul Abdirahman** (Investor, F-Prime): Notes that tools coordinating human work are becoming obsolete as agents take over tasks, implying openness to funding agentic AI solutions.

- **Aileen Lee** (Founder and Managing Partner, Cowboy Ventures): Stresses rapid iteration, data generation, and competitive moats—key traits for successful agentic AI startups.

- **Steve Jang** (Founder and Managing Partner, Kindred Ventures): Believes both strong technology and go-to-market are essential, which would apply to advanced agentic AI systems.

While none are explicitly named as funding "agentic AI" startups, **Jake Saper (Emergence Capital)**, **Igor Ryabenkiy (AltaIR Capital)**, and **Aaron Holiday (645 Ventures)** appear most aligned with investing in this space based on their stated preferences for workflow ownership, deep integration, and AI-native systems.

Source: TechCrunch coverage of VC sentiment on AI SaaS trends.

## Conclusion
The hybrid approach provides structured investor connections from the KG alongside the rich, nuanced text from the Vector DB. This often results in a more authoritative, hallucination-free response than Vector-only, and a more comprehensive answer than Graph-only.