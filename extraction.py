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

# 1. LOAD ENVIRONMENT VARIABLES
dotenv_file = find_dotenv()
if dotenv_file:
    print(f"✅ Found .env file at: {dotenv_file}")
    load_dotenv(dotenv_file)
else:
    print("❌ WARNING: No .env file found! Trying to proceed with system variables...")

DATA_FILE = os.path.join(SCRIPT_DIR, "data", "master_dataset_cleaned.csv")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "data", "extracted_knowledge.json")

# --- ASU VOYAGER CONFIG ---
VOYAGER_MODEL_NAME = "qwen3-235b-a22b-instruct-2507" 
VOYAGER_BASE_URL = "https://openai.rc.asu.edu/v1"
VOYAGER_API_KEY = os.environ.get("VOYAGER_API_KEY", "")

def get_llm():
    print(f"--- Connecting to ASU Voyager API: {VOYAGER_MODEL_NAME} ---")
    if not VOYAGER_API_KEY:
        raise ValueError("CRITICAL: VOYAGER_API_KEY not found. Please check your .env file.")
    
    return ChatOpenAI(
        model=VOYAGER_MODEL_NAME,
        openai_api_key=VOYAGER_API_KEY,
        openai_api_base=VOYAGER_BASE_URL,
        temperature=0.1, 
        max_retries=3
    )

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

def extract_knowledge():
    if not os.path.exists(DATA_FILE):
        print(f"❌ Error: {DATA_FILE} not found.")
        return

    df = pd.read_csv(DATA_FILE)
    print(f"Total posts to process: {len(df)}")

    try:
        llm = get_llm()
    except Exception as e:
        print(e)
        return

    parser = JsonOutputParser()
    chain = extraction_prompt | llm | parser

    results = []
    
    # Process all available rows/posts
    for index, row in df.iterrows():
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
            
        except Exception as e:
            print(f"⚠️ Error on post {index}: {e}")

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Success! Semantic Extraction saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_knowledge()