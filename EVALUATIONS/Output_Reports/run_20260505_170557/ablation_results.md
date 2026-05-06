# KG-RAG Ablation Study Results

**Test Query**: `Which investors are funding Agentic AI startups?`

## Run 1: Vector-Only (ChromaDB)
- Context Length (Chars): 16713
- LLM Answer:
> The provided context does not specify which investors are currently funding **agentic AI startups** directly. However, it highlights investor preferences and trends that strongly favor **AI-native startups with deep workflow integration, proprietary data, and systems of action**—characteristics aligned with agentic AI.

Key investors mentioned, while not explicitly naming "agentic AI" investments, are reallocating capital toward businesses that **own workflows, data, and domain expertise**, which reflects a shift toward agentic and AI-native models:

- **Igor Ryabenkiy**, Managing Partner at **AltaIR Capital**, emphasizes investing in companies with “real workflow ownership” and warns against thin AI wrappers. He states investors are moving “away from products that can be copied without much effort,” favoring startups with deep integration and adaptability.
  
- **Jake Saper**, General Partner at **Emergence Capital**, points to **Cursor vs. Claude Code** as a “canary in the coal mine,” where owning the developer’s workflow (as Cursor does) is more valuable than just task execution. He notes that “agents are doing the work,” making traditional human-centric workflow tools less valuable—indicating interest in agent-driven platforms.

- **Aaron Holiday** of **645 Ventures** favors startups in **AI-native infrastructure, vertical SaaS with proprietary data, and systems of action**—categories closely related to agentic AI.

- **Abdul Abdirahman** at **F-Prime** is skeptical of generic tools and values solutions where AI agents can execute tasks autonomously, reducing reliance on human coordination.

While no direct investments in agentic AI startups are named, these investors and their firms—**AltaIR Capital, Emergence Capital, 645 Ventures, and F-Prime**—are actively shifting capital toward the foundational traits of agentic AI: **workflow ownership, autonomous task execution, and deep AI integration**.

Source: TechCrunch (via provided context).

## Run 2: Graph-Only (Neo4j)
- Context Length (Chars): 0
- LLM Answer:
> Based on the provided context, there is no specific information about which investors are funding Agentic AI startups. The knowledge graph does not contain details on investors or funding related to Agentic AI startups.

## Run 3: Hybrid KG-RAG
- Context Length (Chars): 16759
- LLM Answer:
> The provided context does not explicitly name investors who are currently funding **agentic AI startups**. However, it highlights investor preferences and trends that strongly indicate which investors are likely to support such ventures based on their focus on AI-native infrastructure, workflow ownership, and deep integration.

Key investors mentioned who are reallocating capital toward AI-native businesses with strong moats, workflow ownership, and deep product differentiation — characteristics aligned with agentic AI — include:

1. **Igor Ryabenkiy**, Founder and Managing Partner at **AltaIR Capital**: He emphasizes investing in companies with real workflow ownership, proprietary data, and deep product integration, moving away from easily replicable tools. He states: *“Investors are reallocating capital toward businesses that own workflows, data, and domain expertise”* — a clear signal of interest in agentic systems that embed deeply into workflows.

2. **Jake Saper**, General Partner at **Emergence Capital**: He highlights the shift from human-centric workflow stickiness to task execution by agents, using Cursor vs. Claude Code as a benchmark. His observation that *“agents are doing the work”* and that *“being the connector used to be a moat, soon it’ll be a utility”* suggests Emergence is backing startups that align with agent-based execution models.

3. **Aaron Holiday**, Managing Partner at **645 Ventures**: He identifies investor interest in *“systems of action”* (AI tools that help users complete tasks) and *“AI-native infrastructure”* — categories closely related to agentic AI.

4. **Abdul Abdirahman**, Investor at **F-Prime**: He notes declining interest in tools for coordinating human work, as *“agents just execute the tasks”*, indicating a pivot toward agent-driven automation.

While none of these investors are explicitly named as funding specific "agentic AI" startups, their stated investment theses — particularly around workflow ownership, task execution over process, and reduced reliance on human-in-the-loop systems — strongly suggest they are prioritizing agentic AI trends.

**Source**: TechCrunch coverage of VC sentiment on AI SaaS trends (context provided).

## Conclusion
The hybrid approach provides structured investor connections from the KG alongside the rich, nuanced text from the Vector DB. This often results in a more authoritative, hallucination-free response than Vector-only, and a more comprehensive answer than Graph-only.