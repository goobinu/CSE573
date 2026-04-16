import os
from dotenv import load_dotenv, find_dotenv

# Find and load the .env file automatically
dotenv_file = find_dotenv()
if dotenv_file:
    load_dotenv(dotenv_file)

# --- DIRECTORIES & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR_RAW = os.path.join(BASE_DIR, "DATA", "raw")
DATA_DIR_PROCESSED = os.path.join(BASE_DIR, "DATA", "processed")

EXPECTED_SOURCES = ["LinkedIn", "Reddit"]
RESULTS_CSV_PATH = os.path.join(DATA_DIR_RAW, "results.csv")
CURATED_CATEGORIES_PATH = os.path.join(DATA_DIR_RAW, "curatedcategories.csv")
SUBPAGE_RESULTS_DIR = os.path.join(DATA_DIR_RAW, "subpage_results")

MASTER_DATASET_PATH = os.path.join(DATA_DIR_RAW, "master_dataset_cleaned.csv")
REDDIT_CLEANED_CSV_PATH = os.path.join(DATA_DIR_PROCESSED, "reddit_cleaned_for_extraction.csv")
EXTRACTED_KNOWLEDGE_PATH = os.path.join(DATA_DIR_PROCESSED, "extracted_knowledge.json")
FINAL_KG_PATH = os.path.join(DATA_DIR_PROCESSED, "final_knowledge_graph.json")
CHROMA_DB_PATH = os.path.join(DATA_DIR_PROCESSED, "chroma_db")

# --- ASU VOYAGER CONFIG ---
VOYAGER_MODEL_NAME = "qwen3-235b-a22b-instruct-2507" 
VOYAGER_BASE_URL = "https://openai.rc.asu.edu/v1"
VOYAGER_API_KEY = os.environ.get("VOYAGER_API_KEY", "")

# --- NEO4J CONFIG ---
NEO4J_URI = os.environ.get("NEO4J_URI", "")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME", "")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")

# --- SCHEMA VALIDATION ---
SCHEMA_CONFIG = {
    "NODE_LABELS": [
        "Organization", 
        "Trend", 
        "Technology", 
        "Person",
        "Investor",
        "FundingRound",
        "Skill"
    ],
    "RELATIONSHIP_TYPES": [
        "DISCUSSES", 
        "IS_PART_OF", 
        "WORKS_AT", 
        "PARTICIPATES_IN",
        "INVESTED_IN",
        "ACQUIRED",
        "PARTNERED_WITH",
        "RELEASED",
        "USES",
        "WORKS_FOR",
        "COMPETES_WITH",
        "HIRES_FOR",
        "RAISED_IN",
        "ACQUIRED_BY"
    ]
}
