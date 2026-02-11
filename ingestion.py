import pandas as pd
import glob
import os

# --- CONFIGURATION ---
# Path to where you stored your CSV files
DATA_DIR = "data/subpage_results/" 
# Pattern to match all your specific CSVs
FILE_PATTERN = "*.csv"

def load_and_clean_data(data_dir):
    """
    Step 1: Loads all CSVs from the data directory and cleans the content.
    """
    search_path = os.path.join(data_dir, FILE_PATTERN)
    print(f"Searching for files in {search_path}...")
    all_files = glob.glob(search_path)
    
    if not all_files:
        print(f"Error: No CSV files found in {search_path}")
        return None

    print(f"Found {len(all_files)} files: {[os.path.basename(f) for f in all_files]}")

    # Generator to read files one by one (memory efficient)
    df_list = []
    for filename in all_files:
        try:
            # Read CSV
            temp_df = pd.read_csv(filename)
            # Add a 'source_file' column so we know where data came from (provenance)
            temp_df['source_topic'] = os.path.basename(filename).replace('.csv', '')
            df_list.append(temp_df)
        except Exception as e:
            print(f"Warning: Could not read {filename}. Reason: {e}")

    if not df_list:
        return None

    # Combine into one big DataFrame
    combined_df = pd.concat(df_list, ignore_index=True)

    # --- CLEANING LOGIC ---
    print(f"Initial row count: {len(combined_df)}")
    
    # 1. Remove rows where 'Post content' is missing/empty
    combined_df = combined_df.dropna(subset=['Post content'])
    
    # 2. Define cleaning function
    def clean_text_content(text):
        if not isinstance(text, str):
            return ""
        # Remove common LinkedIn artifacts
        text = text.replace("...see more", "").replace("See more", "")
        # Remove extra whitespace/newlines
        text = " ".join(text.split())
        return text

    # 3. Apply cleaning
    combined_df['clean_content'] = combined_df['Post content'].apply(clean_text_content)
    
    # 4. Remove duplicates (same post content appearing in multiple files)
    combined_df = combined_df.drop_duplicates(subset=['clean_content'])
    
    print(f"Cleaned row count: {len(combined_df)}")
    print("Step 1 Complete. Data is ready for LLM extraction.")
    
    return combined_df

if __name__ == "__main__":
    # This block runs only if you execute the script directly
    df = load_and_clean_data(DATA_DIR)
    
    if df is not None:
        # Show the first few rows to verify
        print("\n--- Preview of Cleaned Data ---")
        print(df[['source_topic', 'Name', 'clean_content']].head())
        
        # Optional: Save to a master CSV for the next step
        df.to_csv("data/master_dataset_cleaned.csv", index=False)