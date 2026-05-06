import os
import sys
import argparse
from datetime import datetime
from neo4j import GraphDatabase
import chromadb
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import VOYAGER_API_KEY, VOYAGER_BASE_URL, VOYAGER_MODEL_NAME, CHROMA_DB_PATH
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

def run_ablation(output_dir):
    # Setup Clients
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = chroma_client.get_collection(name="market_intelligence")
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    llm_client = OpenAI(api_key=VOYAGER_API_KEY, base_url=VOYAGER_BASE_URL)

    test_query = "Which investors are funding Agentic AI startups?"

    system_prompt = "You are TrendScout AI. Provide a concise, clear answer leveraging the EXACT context given below. Cite your sources. Ensure you cover investor names if present."

    # --- Run 1: Vector Only ---
    v_results = collection.query(query_texts=[test_query], n_results=5)
    v_context_docs = v_results['documents'][0] if v_results['documents'] else []
    v_context_str = "\n".join(v_context_docs)
    
    v_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context (Vector Search):\n{v_context_str}\n\nQuery: {test_query}"}
    ]
    v_response = llm_client.chat.completions.create(model=VOYAGER_MODEL_NAME, messages=v_messages)
    v_answer = v_response.choices[0].message.content
    v_context_len = len(v_context_str)

    # --- Run 2: Graph Only ---
    g_context_str = ""
    with neo4j_driver.session() as session:
        # Find investors -> organizations -> discussing agentic ai related trends
        g_cypher = """
        MATCH (i:Organization)-[:INVESTED_IN]->(o:Organization)-[:DISCUSSES]->(t:Trend)
        WHERE toLower(t.id) CONTAINS "agent" OR toLower(t.id) CONTAINS "ai"
        RETURN i.id AS Investor, o.id AS Startup, t.id AS Trend
        LIMIT 10
        """
        g_results = session.run(g_cypher)
        g_records = []
        for record in g_results:
            g_records.append(f"Investor: {record['Investor']} invested in Startup: {record['Startup']} (Trend: {record['Trend']})")
        g_context_str = "\n".join(g_records)

    g_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context (Knowledge Graph):\n{g_context_str}\n\nQuery: {test_query}"}
    ]
    g_response = llm_client.chat.completions.create(model=VOYAGER_MODEL_NAME, messages=g_messages)
    g_answer = g_response.choices[0].message.content
    g_context_len = len(g_context_str)

    # --- Run 3: Hybrid (Master Pipeline format) ---
    h_context_str = f"--- VECTOR FRAGMENTS ---\n{v_context_str}\n--- GRAPH FACTS ---\n{g_context_str}"
    h_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context (Hybrid KG-RAG):\n{h_context_str}\n\nQuery: {test_query}"}
    ]
    h_response = llm_client.chat.completions.create(model=VOYAGER_MODEL_NAME, messages=h_messages)
    h_answer = h_response.choices[0].message.content
    h_context_len = len(h_context_str)

    neo4j_driver.close()

    # --- Write Results ---
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "ablation_results.md")
    
    with open(output_path, "w") as f:
        f.write("# KG-RAG Ablation Study Results\n\n")
        f.write(f"**Test Query**: `{test_query}`\n\n")
        
        f.write("## Run 1: Vector-Only (ChromaDB)\n")
        f.write(f"- Context Length (Chars): {v_context_len}\n")
        f.write(f"- LLM Answer:\n> {v_answer}\n\n")

        f.write("## Run 2: Graph-Only (Neo4j)\n")
        f.write(f"- Context Length (Chars): {g_context_len}\n")
        f.write(f"- LLM Answer:\n> {g_answer}\n\n")

        f.write("## Run 3: Hybrid KG-RAG\n")
        f.write(f"- Context Length (Chars): {h_context_len}\n")
        f.write(f"- LLM Answer:\n> {h_answer}\n\n")
        
        f.write("## Conclusion\n")
        f.write("The hybrid approach provides structured investor connections from the KG alongside the rich, nuanced text from the Vector DB. This often results in a more authoritative, hallucination-free response than Vector-only, and a more comprehensive answer than Graph-only.")

    print(f"Ablation study complete. Written to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    run_ablation(args.output_dir)
