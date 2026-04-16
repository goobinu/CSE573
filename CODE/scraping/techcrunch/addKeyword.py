import json
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter


# -----------------------------
# LOAD DATA (your enriched file)
# -----------------------------
INPUT_FILE = "data/acs_filtered_contentrich_articles.json"
OUTPUT_FILE = "data/ak_articles_w_keyword.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)


# -----------------------------
# PREPARE DOCUMENTS
# (Boost title importance)
# -----------------------------
documents = []

for article in data:
    title = article.get("title", "")
    content = article.get("content", "")
    
    # 🔥 Boost title importance
    text = (title + " ") * 3 + content
    documents.append(text)


# -----------------------------
# TF-IDF VECTORIZATION
# -----------------------------
vectorizer = TfidfVectorizer(
    stop_words="english",
    max_features=5000,
    ngram_range=(1, 2)   # single + phrases
)

tfidf_matrix = vectorizer.fit_transform(documents)
feature_names = vectorizer.get_feature_names_out()


# -----------------------------
# GET TOP KEYWORDS PER ARTICLE
# -----------------------------
def get_top_keywords(row, top_n=10):
    scores = row.toarray().flatten()
    
    # Get top indices
    indices = scores.argsort()[-top_n:][::-1]
    
    keywords = []
    for i in indices:
        if scores[i] > 0:   # avoid zero-score words
            keywords.append(feature_names[i])
    
    return keywords


# -----------------------------
# ADD KEYWORDS TO EACH ARTICLE
# -----------------------------
for i, article in enumerate(data):
    keywords = get_top_keywords(tfidf_matrix[i], top_n=10)
    article["keywords"] = keywords


# -----------------------------
# GLOBAL TREND EXTRACTION
# -----------------------------
all_keywords = []

for article in data:
    all_keywords.extend(article.get("keywords", []))

trend_counts = Counter(all_keywords)
top_trends = trend_counts.most_common(20)


# -----------------------------
# SAVE RESULTS
# -----------------------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)


# -----------------------------
# PRINT TOP TRENDS
# -----------------------------
print("\n🔥 TOP TRENDING KEYWORDS:\n")
for word, count in top_trends:
    print(f"{word}: {count}")

print(f"\n✅ Done. Saved to {OUTPUT_FILE}")