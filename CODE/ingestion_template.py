"""
TrendScout Ingestion Template
-----------------------------
Use this boilerplate script when adding a new data source to the pipeline.
It demonstrates how to import the correct configuration paths and apply
the standard embedding structure we expect for ChromaDB.

Instructions:
1. Copy this file into your working directory (e.g., `feature_x_ingestion.py`).
2. Implement the `clean_data()` function to handle your specific CSV format.
3. Ensure the metadata structure matches `DATA_SCHEMA.md`.
4. Tie your script into the `main.py` orchestrator when ready.
"""

import pandas as pd
import hashlib

# TODO: If this script needs to speak to the LLM, use our standard utility:
# from utils.llm_client import get_llm

from config import CHROMA_DB_PATH
import chromadb

def generate_id(unique_identifier, index):
    """Generates a stable ID for vector DB upserts."""
    if unique_identifier:
        return hashlib.md5(str(unique_identifier).encode('utf-8')).hexdigest() + f"_{index}"
    return f"record_{index}"

def clean_data(file_path):
    """
    TODO: Implement your specific CSV parsing/cleaning logic here.
    Return a pandas DataFrame with normalized columns.
    """
    # Example:
    df = pd.read_csv(file_path)
    df.fillna('', inplace=True)
    return df

def push_to_vector_store(df, source_name):
    """
    Pushes cleaned data to the shared ChromaDB collection 
    using the strict metadata schema.
    """
    print(f"Connecting to ChromaDB at {CHROMA_DB_PATH}...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    # We use a single shared collection for all textual knowledge discovery
    collection = chroma_client.get_or_create_collection(name="trendscout_knowledge")

    docs = []
    metadatas = []
    ids = []

    for idx, row in df.iterrows():
        # TODO: Define the primary text blob
        content = row.get('text_content', '')
        if not content:
            continue
            
        # TODO: Conform to metadata rules outlined in DATA_SCHEMA.md
        meta = {
            "author_name": str(row.get('author', 'Unknown')),
            "profile_url": str(row.get('author_url', '')),
            "post_url": str(row.get('source_url', '')),
            "source_topic": str(row.get('category', 'General')),
            "source": source_name # e.g. "TechCrunch", "Reddit"
        }
        
        doc_id = generate_id(row.get('source_url', ''), idx)

        docs.append(str(content))
        metadatas.append(meta)
        ids.append(doc_id)

    # Batch Upsert Loop (safest for large datasets)
    batch_size = 1000
    for i in range(0, len(docs), batch_size):
        end_idx = min(i + batch_size, len(docs))
        collection.upsert(
            documents=docs[i:end_idx],
            metadatas=metadatas[i:end_idx],
            ids=ids[i:end_idx]
        )
        print(f"Upserted items {i} to {end_idx - 1} from {source_name}")

if __name__ == "__main__":
    # TODO: Replace with your actual path 
    YOUR_DATA_FILE = "data/your_raw_file.csv"
    
    # df_cleaned = clean_data(YOUR_DATA_FILE)
    # push_to_vector_store(df_cleaned, source_name="YourDataSource")
    print("Template execution structure loaded.")
