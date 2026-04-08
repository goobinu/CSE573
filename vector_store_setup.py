import pandas as pd
import chromadb
import hashlib
from config import MASTER_DATASET_PATH, CHROMA_DB_PATH
def generate_id(url, index):
    if url:
        return hashlib.md5(str(url).encode('utf-8')).hexdigest() + f"_{index}"
    return f"post_{index}"

def main():
    print("Loading data...")
    # Load dataset
    df = pd.read_csv(MASTER_DATASET_PATH)
    df.fillna('', inplace=True)
    
    print("Initializing ChromaDB...")
    # Init ChromaDB
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = chroma_client.get_or_create_collection(name="linkedin_posts")
    
    docs = []
    metadatas = []
    ids = []
    
    print("Preparing documents for ingestion...")
    for idx, row in df.iterrows():
        content = row.get('Post content', '')
        if not content:
            content = row.get('clean_content', '')
            
        docs.append(str(content))
        
        meta = {
            "author_name": str(row.get('Name', '')),
            "profile_url": str(row.get('Link to profile', '')),
            "post_url": str(row.get('Link to post', '')),
            "source_topic": str(row.get('source_topic', '')),
            "source": "LinkedIn"
        }
        metadatas.append(meta)
        
        post_id = generate_id(row.get('Link to post', ''), idx)
        ids.append(post_id)
        
    print(f"Total documents to ingest: {len(docs)}")
    
    # Batch Upsert. ChromaDB handles small to medium datasets fine, but we chunk to 5461 which is a safe limit.
    batch_size = 1000
    for i in range(0, len(docs), batch_size):
        end_idx = min(i + batch_size, len(docs))
        collection.upsert(
            documents=docs[i:end_idx],
            metadatas=metadatas[i:end_idx],
            ids=ids[i:end_idx]
        )
        print(f"Upserted items {i} to {end_idx - 1}")
    
    print("Ingestion complete!")
    
    # Test Query
    print("\n--- Test Query: 'AI Startups' ---")
    results = collection.query(
        query_texts=["AI Startups"],
        n_results=2
    )
    
    print("Results:")
    if results and 'documents' in results and results['documents']:
        for doc_list, meta_list in zip(results['documents'], results['metadatas']):
            for i, (d, m) in enumerate(zip(doc_list, meta_list)):
                print(f"Result {i+1}:")
                print(f"Author: {m.get('author_name', 'Unknown')}")
                print(f"Post URL: {m.get('post_url', 'Unknown')}")
                print(f"Content snippet: {d[:200]}...")
                print("-" * 50)

if __name__ == "__main__":
    main()
