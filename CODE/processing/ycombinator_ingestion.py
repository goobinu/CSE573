import pandas as pd
import json
import os
from config import DATA_DIR_RAW, YCOMBINATOR_CLEANED_CSV_PATH

def process_ycombinator_data():
    # Processes Y Combinator data JSON file into standardized CSV format.
    file_path = os.path.join(DATA_DIR_RAW, "ycombinator", "yc_ai_companies.json")
    
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found.")
        return
        
    all_data = []
    
    with open(file_path, 'r') as f:
        try:
            data_list = json.load(f)
            
            for item in data_list:
                # Extract founder information
                founders = []
                for i in range(1, 5):
                    founder_name = item.get(f'founder_{i}_name')
                    if founder_name:
                        founders.append(founder_name)
                founders_str = ", ".join(founders)
                
                # Combine description and tagline for post content
                description = item.get('description', '')
                tagline = item.get('tagline', '')
                post_content = f"{tagline}\n\n{description}" if description else tagline
                
                # Determine primary content source
                content_source = description if description else tagline
                
                row = {
                    "Name": item.get('name', ''),
                    "Link to profile": item.get('company_url', ''),
                    "Post content": post_content,
                    "Link to post": item.get('website', ''),
                    "source_topic": "Y Combinator AI Company",
                    "clean_content": content_source,
                    "source": "Y Combinator",
                    "importance": 1.0,
                    "chunk_id": "",
                    "founders": founders_str,
                    "founded_year": item.get('founded', ''),
                    "batch": item.get('batch', ''),
                    "team_size": item.get('team_size', ''),
                    "location": item.get('location', ''),
                    "status": item.get('status', ''),
                    "linkedin": item.get('linkedin', ''),
                    "twitter": item.get('twitter', '')
                }
                all_data.append(row)
                
        except json.JSONDecodeError:
            print("Error decoding JSON.")
            return
            
    if all_data:
        df = pd.DataFrame(all_data)
        os.makedirs(os.path.dirname(YCOMBINATOR_CLEANED_CSV_PATH), exist_ok=True)
        df.to_csv(YCOMBINATOR_CLEANED_CSV_PATH, index=False)
        print(f"Y Combinator ingestion complete. Saved {len(df)} rows to {YCOMBINATOR_CLEANED_CSV_PATH}")
    else:
        print("No Y Combinator data processed.")

if __name__ == "__main__":
    process_ycombinator_data()
