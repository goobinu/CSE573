import pandas as pd
import json
import os
import time
from dotenv import load_dotenv, find_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI

# --- CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(find_dotenv())

DATA_FILE = os.path.join(SCRIPT_DIR, "data", "subpage_results", "master_dataset_cleaned.csv")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "data", "subpage_results", "extracted_knowledge.json")

VOYAGER_MODEL_NAME = "qwen3-235b-a22b-instruct-2507" 
VOYAGER_BASE_URL = "https://openai.rc.asu.edu/v1"
VOYAGER_API_KEY = os.environ.get("VOYAGER_API_KEY", "")

def get_llm():
    if not VOYAGER_API_KEY:
        raise ValueError("CRITICAL: VOYAGER_API_KEY not found.")
    return ChatOpenAI(
        model=VOYAGER_MODEL_NAME,
        openai_api_key=VOYAGER_API_KEY,
        openai_api_base=VOYAGER_BASE_URL,
        temperature=0.1, 
        max_retries=3
    )

extraction_prompt = ChatPromptTemplate.from_template("""
You are an expert Knowledge Graph engineer for the TrendScout AI project.

### 1. EXTRACT ENTITIES
- Organization, Technology, Trend, Person.

### 2. EXTRACT RELATIONSHIPS
Use ONLY these verbs: INVESTED_IN, ACQUIRED, PARTNERED_WITH, RELEASED, USES, WORKS_FOR, DISCUSSES, IS_PART_OF, COMPETES_WITH.

Input Text:
{text}

JSON Output:
{{
  "entities": [ {{"name": "...", "type": "...", "sentiment": "..."}} ],
  "relationships": [ {{"source": "...", "relation": "SPECIFIC_VERB", "target": "..."}} ]
}}
""")

def load_existing_results():
    """Reads the JSON file to see what we've already processed."""
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Warning: Output file exists but is corrupted. Starting fresh.")
            return []
    return []

def extract_knowledge():
    if not os.path.exists(DATA_FILE):
        print(f"❌ Error: {DATA_FILE} not found.")
        return

    df = pd.read_csv(DATA_FILE)
    
    # --- RESUME LOGIC ---
    existing_results = load_existing_results()
    
    # We use the source_url to keep track of what we've done
    processed_urls = {item['metadata']['source_url'] for item in existing_results if 'metadata' in item}
    
    print(f"Total posts in CSV: {len(df)}")
    print(f"Already processed: {len(processed_urls)}")
    
    # Filter the dataframe to ONLY include rows we haven't processed yet
    df_to_process = df[~df['Link to post'].isin(processed_urls)]
    print(f"Remaining to process: {len(df_to_process)}")

    if len(df_to_process) == 0:
        print("🎉 All posts have been processed!")
        return

    try:
        llm = get_llm()
    except Exception as e:
        print(e)
        return

    parser = JsonOutputParser()
    chain = extraction_prompt | llm | parser

    # We append to the existing list
    results = existing_results
    
    for index, row in df_to_process.iterrows():
        try:
            print(f"Extracting [{index}]: {row.get('Name', 'Unknown')}...")
            extraction = chain.invoke({"text": row['clean_content']})
            
            extraction['metadata'] = {
                "source_url": row.get('Link to post', 'N/A'),
                "author": row.get('Name', 'Unknown'),
                "topic": row.get('source_topic', 'AI')
            }
            results.append(extraction)
            
            # --- CHECKPOINT: SAVE AFTER EVERY POST ---
            # This ensures if the script dies right now, this post is saved.
            with open(OUTPUT_FILE, 'w') as f:
                json.dump(results, f, indent=2)
                
            # Optional: Be nice to the API
            time.sleep(0.5)
            
        except Exception as e:
            print(f"⚠️ Error on post {index}: {e}")

    print(f"\n✅ Finished processing batch. Total saved: {len(results)}")

if __name__ == "__main__":
    extract_knowledge()