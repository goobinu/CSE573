import pandas as pd
import json
import os
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI

# --- CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Ensure this matches your actual path from ingestion.py
DATA_FILE = os.path.join(SCRIPT_DIR, "data", "master_dataset_cleaned.csv")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "data", "extracted_knowledge.json")

# --- ASU VOYAGER CONFIG ---
# Model recommendation: qwen3-235b-a22b-instruct-2507 for highest accuracy
VOYAGER_MODEL_NAME = "qwen3-235b-a22b-instruct-2507" 
VOYAGER_BASE_URL = "https://openai.rc.asu.edu/v1"

# Get key from environment variable: export VOYAGER_API_KEY="your_key"
VOYAGER_API_KEY = os.environ.get("VOYAGER_API_KEY", "")

def get_llm():
    print(f"--- Connecting to ASU Voyager API: {VOYAGER_MODEL_NAME} ---")
    if not VOYAGER_API_KEY:
        raise ValueError("CRITICAL: VOYAGER_API_KEY not found in environment variables.")
    
    return ChatOpenAI(
        model=VOYAGER_MODEL_NAME,
        openai_api_key=VOYAGER_API_KEY,
        openai_api_base=VOYAGER_BASE_URL,
        temperature=0.1, # Keep low for deterministic extraction
        max_retries=3
    )

# --- THE PROMPT (The "Extractor Logic") ---
extraction_prompt = ChatPromptTemplate.from_template("""
You are an expert Knowledge Graph engineer for the TrendScout AI project. 
Extract structured entities and their relationships from the LinkedIn post below.

ENTITIES to identify:
1. **Organization**: Startups, VCs (e.g., Sequoia), Tech Giants (e.g., Nvidia).
2. **Technology**: AI models (e.g., Llama 3), hardware (e.g., Jetson Orin), frameworks.
3. **Trend**: Sector movements (e.g., "Agentic AI", "Drone Swarms").
4. **Person**: Influencers, Founders, or CEOs mentioned.

RELATIONSHIPS to identify (Source -> Relation -> Target):
- Organization --[FUNDED]--> Organization
- Organization --[DEVELOPED]--> Technology
- Person --[WORKS_FOR]--> Organization
- Organization --[USES]--> Technology

Input Text:
{text}

Return ONLY a valid JSON object. Do not include markdown blocks or conversational text.
Structure:
{{
  "entities": [
    {{"name": "Entity Name", "type": "Organization|Technology|Trend|Person", "sentiment": "positive|neutral|negative"}}
  ],
  "relationships": [
    {{"source": "Entity Name", "relation": "RELATIONSHIP_TYPE", "target": "Entity Name"}}
  ]
}}
""")

def extract_knowledge():
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found. Run ingestion.py first.")
        return

    df = pd.read_csv(DATA_FILE)
    print(f"Total posts to process: {len(df)}")

    llm = get_llm()
    parser = JsonOutputParser()
    chain = extraction_prompt | llm | parser

    results = []
    
    # Start with 10 posts for validation. Remove .head(10) to run full dataset.
    for index, row in df.head(10).iterrows():
        try:
            print(f"[{index+1}/{len(df)}] Extracting: {row.get('Name', 'Unknown')}...")
            
            # Run the extraction
            extraction = chain.invoke({"text": row['clean_content']})
            
            # Attach source metadata for graph provenance
            extraction['metadata'] = {
                "source_url": row.get('Link to post', 'N/A'),
                "author": row.get('Name', 'Unknown'),
                "topic": row.get('source_topic', 'AI')
            }
            
            results.append(extraction)
            
        except Exception as e:
            print(f"Skipping post {index} due to error: {e}")

    # Final Save
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ PHASE 1 COMPLETE! Knowledge saved to: {OUTPUT_FILE}")
    print("Next step: Import this JSON into Neo4j using the Load Script.")

if __name__ == "__main__":
    extract_knowledge()