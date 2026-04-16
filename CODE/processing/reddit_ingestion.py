import pandas as pd
import json
import os
from config import DATA_DIR_RAW, REDDIT_CLEANED_CSV_PATH

def process_reddit_data():
    files = ["Entrepreneur_tagged.jsonl", "startups_tagged.jsonl"]
    reddit_dir = os.path.join(DATA_DIR_RAW, "reddit")
    
    all_data = []
    
    for file in files:
        filepath = os.path.join(reddit_dir, file)
        if not os.path.exists(filepath):
            print(f"⚠️ Warning: {filepath} not found.")
            continue
            
        with open(filepath, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    # Map to master dataset schema
                    tags = data.get('tags', [])
                    topic = ", ".join(tags) if isinstance(tags, list) else str(tags)
                    
                    row = {
                        "Name": "Reddit User",
                        "Link to profile": "",
                        "Post content": data.get('text', ''),
                        "Link to post": data.get('post_id', ''),
                        "source_topic": topic,
                        "clean_content": data.get('text', ''),
                        "source": "Reddit",
                        "importance": data.get('importance', 1.0),
                        "chunk_id": data.get('chunk_id', '')
                    }
                    all_data.append(row)
                except json.JSONDecodeError:
                    print("Error decoding line.")
                    
    if all_data:
        df = pd.DataFrame(all_data)
        os.makedirs(os.path.dirname(REDDIT_CLEANED_CSV_PATH), exist_ok=True)
        df.to_csv(REDDIT_CLEANED_CSV_PATH, index=False)
        print(f"✅ Reddit ingestion complete. Saved {len(df)} rows to {REDDIT_CLEANED_CSV_PATH}")
    else:
        print("❌ No Reddit data found to process.")

if __name__ == "__main__":
    process_reddit_data()
