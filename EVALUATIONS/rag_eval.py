import os
import sys
import argparse
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import VOYAGER_API_KEY, VOYAGER_BASE_URL, VOYAGER_MODEL_NAME, CHROMA_DB_PATH

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb
from openai import OpenAI

def run_ragas(output_dir):
    # Load ChromaDB for context retrieval
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = chroma_client.get_collection(name="market_intelligence")
    
    # Simple ASU Voyager raw client for Answer Generation (Mimicking app.py)
    raw_api_client = OpenAI(
        api_key=VOYAGER_API_KEY,
        base_url=VOYAGER_BASE_URL
    )

    # Prepare custom LLM and Embeddings for RAGAS evaluation
    voyager_llm = ChatOpenAI(
        api_key=VOYAGER_API_KEY,
        base_url=VOYAGER_BASE_URL,
        model=VOYAGER_MODEL_NAME
    )
    # Using local embeddings as ASU Voyager does not strictly provide an embedding endpoint in this setup
    hf_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    questions = [
        "Which venture capital firms recently invested in AI startups, and what was the valuation?",
        "What is the general sentiment and primary challenges developers are discussing regarding AI Agent tools?",
        "Based on recent news and social discussions, how is the market responding to AI startups raising Series A funding?"
    ]
    
    ground_truths = [
        "Recent reports indicate significant VC interest in AI startups. Notable investments highlight firms driving the valuation of several agent AI platforms significantly up.",
        "Developers are expressing cautious optimism but highlight major challenges with hallucination, latency, and integration difficulties when integrating AI agents into production environments.",
        "The market is responding robustly, with a surge in Series A funds being allocated to startups demonstrating tangible enterprise solutions, though many warn of an impending correction."
    ]
    
    answers = []
    contexts_lists = []
    
    for q in questions:
        # Retrieve context from Chroma
        results = collection.query(
            query_texts=[q],
            n_results=3
        )
        context_docs = results['documents'][0] if results['documents'] else ["No context found."]
        contexts_lists.append(context_docs)
        
        context_string = "\n".join(context_docs)
        system_prompt = (
            "You are TrendScout AI, an elite market intelligence analyst. Provide insights strictly based on Context."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context_string}\n\nQuery:\n{q}"}
        ]
        
        response = raw_api_client.chat.completions.create(
            model=VOYAGER_MODEL_NAME,
            messages=messages
        )
        answers.append(response.choices[0].message.content)

    # Format the dataset for RAGAS (RAGAS requires specific keys)
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts_lists,
        "ground_truth": ground_truths
    }
    dataset = Dataset.from_dict(data)

    # Execute Evaluation
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy],
        llm=voyager_llm,
        embeddings=hf_embeddings
    )
    
    # Output Results
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "ragas_scores.json")
    
    out_dict = result.to_pandas().to_dict(orient="records")
    with open(output_path, "w") as f:
        json.dump(out_dict, f, indent=4)
        
    print(f"RAGAS Evaluation complete. Scores written to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    run_ragas(args.output_dir)
