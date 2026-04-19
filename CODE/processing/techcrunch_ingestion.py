import pandas as pd
import json
import os
from config import DATA_DIR_RAW, TECHCRUNCH_CLEANED_CSV_PATH

def process_techcrunch_data():
    tc_dir = os.path.join(DATA_DIR_RAW, "techcrunch")
    
    all_data = []
    
    files = [f for f in os.listdir(tc_dir) if f.endswith('.json')]
    
    for file in files:
        filepath = os.path.join(tc_dir, file)
        if not os.path.exists(filepath):
            print(f"⚠️ Warning: {filepath} not found.")
            continue
            
        with open(filepath, 'r') as f:
            try:
                data_list = json.load(f)
                if not isinstance(data_list, list):
                    data_list = [data_list]
                    
                for data in data_list:
                    # Map to master dataset schema
                    authors = data.get('authors', [])
                    author_str = ", ".join(authors) if isinstance(authors, list) else str(authors)
                    
                    keywords = data.get('keywords', [])
                    keyword_str = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
                    
                    row = {
                        "Name": author_str,
                        "Link to profile": "",
                        "Post content": data.get('content', ''),
                        "Link to post": data.get('url', ''),
                        "source_topic": data.get('title', ''),
                        "clean_content": data.get('content', ''),
                        "source": "TechCrunch",
                        "importance": 1.0,
                        "chunk_id": "",
                        "keywords": keyword_str
                    }
                    all_data.append(row)
            except json.JSONDecodeError:
                print(f"Error decoding JSON in file {file}.")
                    
    if all_data:
        df = pd.DataFrame(all_data)
        os.makedirs(os.path.dirname(TECHCRUNCH_CLEANED_CSV_PATH), exist_ok=True)
        df.to_csv(TECHCRUNCH_CLEANED_CSV_PATH, index=False)
        print(f"✅ TechCrunch ingestion complete. Saved {len(df)} rows to {TECHCRUNCH_CLEANED_CSV_PATH}")
    else:
        print("❌ No TechCrunch data found to process.")

if __name__ == "__main__":
    process_techcrunch_data()
