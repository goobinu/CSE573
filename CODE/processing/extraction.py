import pandas as pd
import json
import os
import time

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from config import MASTER_DATASET_PATH, EXTRACTED_KNOWLEDGE_PATH, REDDIT_CLEANED_CSV_PATH
from utilities.llm_client import get_llm

# How often to save to disk? (e.g., save every 5 posts)
SAVE_BATCH_SIZE = 5

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
    dfs = []
    if os.path.exists(MASTER_DATASET_PATH):
        dfs.append(pd.read_csv(MASTER_DATASET_PATH))
    else:
        print(f"⚠️ Warning: {MASTER_DATASET_PATH} not found.")
        
    if os.path.exists(REDDIT_CLEANED_CSV_PATH):
        dfs.append(pd.read_csv(REDDIT_CLEANED_CSV_PATH))
    else:
        print(f"⚠️ Warning: {REDDIT_CLEANED_CSV_PATH} not found.")
        
    if not dfs:
        print("❌ Error: No data files found for extraction.")
        return

    df = pd.concat(dfs, ignore_index=True)
    print(f"Total posts to process from all sources: {len(df)}")
 
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

    results = []
    # We append to the existing list
    results = existing_results
    processed_in_this_run = 0
    
    # Process all available rows/posts
    for index, row in df_to_process.iterrows():
        try:
            print(f"[{index+1}] Extracting: {row.get('Name', 'Unknown')}...")
            extraction = chain.invoke({"text": row['clean_content']})
            
            # Metadata
            extraction['metadata'] = {
                "source_url": row.get('Link to post', 'N/A'),
                "author": row.get('Name', 'Unknown'),
                "topic": row.get('source_topic', 'AI')
            }
            results.append(extraction)
            processed_in_this_run += 1

            # --- CHECKPOINT: BATCH SAVE ---
            # Only save to disk if we've hit our batch size limit
            if processed_in_this_run % SAVE_BATCH_SIZE == 0:
                print(f"💾 Checkpointing... Saved {len(results)} total posts to disk.")
                with open(OUTPUT_FILE, 'w') as f:
                    json.dump(results, f, indent=2)
                
            # Optional: Be nice to the API
            # time.sleep(0.5)
            
        except Exception as e:
            print(f"⚠️ Error on post {index}: {e}")

    # --- FINAL SAVE ---
    # Catch any remaining posts that didn't trigger the batch save (e.g. if we processed 12 posts, we need to save the last 2)
    if processed_in_this_run % SAVE_BATCH_SIZE != 0:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(results, f, indent=2)
    
    print(f"\n✅ Success! Semantic Extraction fully saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_knowledge()