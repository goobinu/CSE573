import requests
from bs4 import BeautifulSoup
import json
import time

# -----------------------------
# File
# -----------------------------
INPUT_FILE = "data/af_filtered_contentless_articles.json"
OUTPUT_FILE = "data/acs_filtered_contentrich_articles.json"



# -----------------------------
# FUNCTION: FETCH FULL ARTICLE
# -----------------------------
def fetch_article_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print("Failed:", url)
            return None
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 🎯 Step 1: Find main article container
        article_body = (
            soup.find("div", class_="entry-content")
        )
        
        if not article_body:
            print("No article body found:", url)
            return None
        
        # 🎯 Step 2: Get only meaningful paragraphs
        paragraphs = article_body.find_all("p", class_="wp-block-paragraph")
        
        # 🔁 Fallback if specific class not found
        if not paragraphs:
            paragraphs = article_body.find_all("p")

        content = []
        
        # 🎯 Step 3: Clean text
        for p in paragraphs:
            text = p.get_text().strip()
            
            if not text:
                continue
            
            # Keep smaller threshold to avoid losing important lines
            if len(text) < 20:
                continue
            
            # # Minimal safety filter
            if "subscribe" in text.lower():
                continue
            
            content.append(text)
        
        # 🎯 Step 4: Combine all paragraphs and adds \n\n for better understanding of llm
        return "\n\n".join(content)
    
    except Exception as e:
        print("Error:", url, e)
        return None


# -----------------------------
# TEST PIPELINE (ONLY FEW ITEMS)
# -----------------------------
def test_scraper(input_file):
    
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # ONLY TAKE FIRST 10 ARTICLES
    # test_data = data[:10]
    test_data = data

    
    enriched = []
    
    for i, article in enumerate(test_data):
        print(f"\nProcessing {i+1}: {article['title']}")
        
        content = fetch_article_content(article["url"])
        
        if content:
            article["content"] = content
            enriched.append(article)
            
            # Print preview
            print("Content preview:")
            print(content[:300], "\n")
        else:
            print("Skipped (no content)")
        
        # ⏳ Be polite to servers
        time.sleep(1)
    
    # 💾 Save output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Test complete. Saved to " + OUTPUT_FILE)


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    test_scraper(INPUT_FILE)