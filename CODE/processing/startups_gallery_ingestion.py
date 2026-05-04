import pandas as pd
import json
import os
from config import DATA_DIR_RAW, STARTUPS_GALLERY_CLEANED_CSV_PATH

def process_startups_gallery_data():
    file_path = os.path.join(DATA_DIR_RAW, "startups_gallery", "all_startup_company_last_year.json")
    
    if not os.path.exists(file_path):
        print(f"⚠️ Warning: {file_path} not found.")
        return
        
    all_data = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data_list = json.load(f)
            
            for item in data_list:
                # Handle investors list
                investors = item.get('investors', [])
                investor_names = [inv.get('name', '') for inv in investors if isinstance(inv, dict) and inv.get('name')]
                investors_str = ", ".join(investor_names)
                
                domain_url = item.get('company_domain_url')
                if not domain_url:
                    domain_url = item.get('company_page_url', '')
                
                desc = item.get('company_description', '')
                
                row = {
                    "Name": item.get('company_name', ''),
                    "Link to profile": "",
                    "Post content": desc,
                    "Link to post": domain_url,
                    "source_topic": item.get('industry_category', ''),
                    "clean_content": desc,
                    "source": "Startups Gallery",
                    "importance": 1.0,
                    "chunk_id": "",
                    "investors": investors_str,
                    "funding_amount": item.get('funding_amount', ''),
                    "funding_amount_pretty": item.get('funding_amount_pretty', ''),
                    "funding_stage": item.get('funding_stage', '')
                }
                all_data.append(row)
        except json.JSONDecodeError:
            print("Error decoding JSON.")
            
    if all_data:
        df = pd.DataFrame(all_data)
        os.makedirs(os.path.dirname(STARTUPS_GALLERY_CLEANED_CSV_PATH), exist_ok=True)
        df.to_csv(STARTUPS_GALLERY_CLEANED_CSV_PATH, index=False)
        print(f"✅ Startups Gallery ingestion complete. Saved {len(df)} rows to {STARTUPS_GALLERY_CLEANED_CSV_PATH}")
    else:
        print("❌ No Startups Gallery data processed.")

if __name__ == "__main__":
    process_startups_gallery_data()
