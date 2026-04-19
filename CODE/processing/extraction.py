import pandas as pd
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from tqdm import tqdm

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from json_repair import repair_json

from config import MASTER_DATASET_PATH, EXTRACTED_KNOWLEDGE_PATH, REDDIT_CLEANED_CSV_PATH, TECHCRUNCH_CLEANED_CSV_PATH, STARTUPS_GALLERY_CLEANED_CSV_PATH
from utilities.llm_client import get_llm

# How often to save to disk? (e.g., save every 5 posts)
SAVE_BATCH_SIZE = 5

MAX_WORKERS = 5
results_lock = Lock()

OUTPUT_FILE = EXTRACTED_KNOWLEDGE_PATH

# --- THE IMPROVED PROMPT ---
# We now enforce specific VERBS for relationships.
extraction_prompt = ChatPromptTemplate.from_template("""
You are an expert Knowledge Graph engineer for the TrendScout AI project.
Your goal is to extract structured knowledge from the text below.

### 1. EXTRACT ENTITIES
Identify entities and assign one of these types:
- **Organization**: Companies, VCs, Startups (e.g., "OpenAI", "Sequoia").
- **Technology**: Models, Tools, Hardware (e.g., "GPT-4", "H100 GPU", "LangChain").
- **Trend**: Broad market concepts (e.g., "Generative AI", "Agentic Workflows").
- **Person**: Specific people mentioned (e.g., "Sam Altman").

### 2. EXTRACT RELATIONSHIPS
Connect entities using ONLY the following specific verbs. 
**CRITICAL:** Do NOT use generic labels like "Organization->Technology". Use the specific verb that describes the action.

**Allowed Relationship Verbs:**
- **INVESTED_IN** (VC -> Startup)
- **ACQUIRED** (Company -> Company)
- **PARTNERED_WITH** (Company -> Company)
- **RELEASED** (Organization -> Technology)
- **USES** (Organization -> Technology)
- **WORKS_FOR** (Person -> Organization)
- **DISCUSSES** (Person/Organization -> Trend)
- **IS_PART_OF** (Technology -> Trend)
- **COMPETES_WITH** (Organization -> Organization)
- **ADVISES_ON** (Person -> Topic/Trend)
- **OPPOSES** (Entity -> Entity)
- **SUPPORTS** (Entity -> Entity)
- **RELATED_TO** (Generic Catch-All)

CRITICAL RULE: You must map all discovered relationships to ONE of the exact verbs provided in the allowed schema list. Do NOT invent new relationship verbs. If you find a nuanced relationship that does not perfectly fit, categorize it under 'RELATED_TO' and explain the nuance in the node's 'description' property.

### 3. OUTPUT FORMAT
Return valid JSON only.

Input Text:
{text}

JSON Output:
{{
  "entities": [
    {{"name": "Entity Name", "type": "Organization|Technology|Trend|Person", "sentiment": "positive|neutral|negative"}}
  ],
  "relationships": [
    {{"source": "Entity Name", "relation": "SPECIFIC_VERB_FROM_LIST", "target": "Entity Name"}}
  ]
}}

CRITICAL FORMATTING RULE: You MUST include all keys in every JSON object. NEVER drop the 'target' key in the relationships array. An example of a FATAL ERROR is {{"source": "A", "relation": "B", "C"}}. The CORRECT format is {{"source": "A", "relation": "B", "target": "C"}}. DO NOT BE LAZY.
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

def process_row(row, index, chain):
    """Worker function to process a single row with exponential backoff"""
    extraction = None
    retries = 3
    delay = 2
    
    for attempt in range(retries):
        try:
            raw_response = chain.invoke({"text": row['clean_content']})
            extraction = repair_json(raw_response.content, return_dict=True)
            break
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "50" in err_str:
                if attempt < retries - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
            tqdm.write(f"⚠️ Fatal Error on post {index}: {e}")
            return None
            
    if extraction:
        has_entities = bool(extraction.get('entities'))
        has_relations = bool(extraction.get('relationships'))
        
        if not (has_entities or has_relations):
            return None
            
        # Metadata
        extraction['metadata'] = {
            "source_url": row.get('Link to post', 'N/A'),
            "author": row.get('Name', 'Unknown'),
            "topic": row.get('source_topic', 'AI')
        }
        return (index, extraction)
    return None

def extract_knowledge():
    dfs = []
    if os.path.exists(MASTER_DATASET_PATH):
        dfs.append(pd.read_csv(MASTER_DATASET_PATH))
    else:
        print(f"⚠️ Warning: {MASTER_DATASET_PATH} not found.")
        
    if os.path.exists(REDDIT_CLEANED_CSV_PATH):
        dfs.append(pd.read_csv(REDDIT_CLEANED_CSV_PATH))
    else:
        print(f"⚠️ Warning: {REDDIT_CLEANED_CSV_PATH} not found.")
        
    if os.path.exists(TECHCRUNCH_CLEANED_CSV_PATH):
        dfs.append(pd.read_csv(TECHCRUNCH_CLEANED_CSV_PATH))
    else:
        print(f"⚠️ Warning: {TECHCRUNCH_CLEANED_CSV_PATH} not found.")
        
    if os.path.exists(STARTUPS_GALLERY_CLEANED_CSV_PATH):
        dfs.append(pd.read_csv(STARTUPS_GALLERY_CLEANED_CSV_PATH))
    else:
        print(f"⚠️ Warning: {STARTUPS_GALLERY_CLEANED_CSV_PATH} not found.")
        
    if not dfs:
        print("❌ Error: No data files found for extraction.")
        return

    df = pd.concat(dfs, ignore_index=True)
    print(f"Total posts to process from all sources: {len(df)}")
 
    # --- RESUME LOGIC ---
    existing_results = load_existing_results()
    
    # Task 1 & 2: Scrub out any incomplete ghost entries created by early termination/Ctrl+C
    valid_json_data = []
    for item in existing_results:
        if isinstance(item, dict):
            has_entities = bool(item.get('entities'))
            has_relations = bool(item.get('relationships'))
            if has_entities or has_relations:
                valid_json_data.append(item)
                
    if len(valid_json_data) < len(existing_results):
        print(f"🧹 Scrubbed {len(existing_results) - len(valid_json_data)} invalid ghost entries from last run.")
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(valid_json_data, f, indent=2)
            
    existing_results = valid_json_data
    print(f"Loaded {len(valid_json_data)} fully completed extractions from previous runs.")
    
    # Create a Checksum/Tracking Set using the Link to post URL
    processed_urls = set()
    for item in existing_results:
        if 'metadata' in item and 'source_url' in item['metadata']:
            processed_urls.add(item['metadata']['source_url'])
    
    # Filter the incoming Pandas DataFrame to drop any rows whose unique identifier is already in the tracking set.
    df_to_process = df[~df['Link to post'].isin(processed_urls)]
    
    skipped_count = len(df) - len(df_to_process)
    new_rows_count = len(df_to_process)

    if new_rows_count == 0:
        print(f"Skipping {skipped_count} already processed rows. Extracting 0 new rows...")
        print("🎉 All posts have been processed!")
        return

    try:
        llm = get_llm()
    except Exception as e:
        print(e)
        return

    # We remove the strict parser to allow json_repair to handle it natively over the raw string
    chain = extraction_prompt | llm

    results = existing_results
    processed_in_this_run = 0
    
    print(f"Skipping {skipped_count} already processed rows. Extracting {new_rows_count} new rows...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Build the futures
        future_to_row = {executor.submit(process_row, row, index, chain): index for index, row in df_to_process.iterrows()}
        
        # Iterate as they complete using tqdm for a clean progress bar
        for future in tqdm(as_completed(future_to_row), total=len(future_to_row), desc="Extracting"):
            index = future_to_row[future]
            try:
                res = future.result()
                if res is not None:
                    _, extraction = res
                    
                    with results_lock:
                        results.append(extraction)
                        processed_in_this_run += 1
                        
                        # --- CHECKPOINT: BATCH SAVE ---
                        if processed_in_this_run % SAVE_BATCH_SIZE == 0:
                            tqdm.write(f"💾 Checkpointing... Saved {len(results)} total posts to disk.")
                            with open(OUTPUT_FILE, 'w') as f:
                                json.dump(results, f, indent=2)
            except Exception as e:
                tqdm.write(f"⚠️ Unexpected error processing post {index}: {e}")

    # --- FINAL SAVE ---
    # Catch any remaining posts that didn't trigger the batch save
    if processed_in_this_run > 0 and processed_in_this_run % SAVE_BATCH_SIZE != 0:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(results, f, indent=2)
    
    print(f"\n✅ Success! Semantic Extraction fully saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_knowledge()