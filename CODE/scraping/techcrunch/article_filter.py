import json
import math
# import nltk
# ---------------------------
# Ensure NLTK data (safe)
# ---------------------------
# try:
#     from nltk.corpus import wordnet
#     wordnet.ensure_loaded()
# except:
#     nltk.download('wordnet')
#     nltk.download('omw-1.4')

from nltk.stem import WordNetLemmatizer


# -----------------------------
# File
# -----------------------------
INPUT_FILE = "data/tcs_contentless_articles.json"
OUTPUT_FILE = "data/af_filtered_contentless_articles.json"



lemmatizer = WordNetLemmatizer()


# ---------------------------
# Preprocess (lemmatization)
# ---------------------------
def preprocess(text):
    words = text.lower().split()
    return [lemmatizer.lemmatize(w, "v") for w in words]


# ---------------------------
# Keyword Groups (Signals)
# ---------------------------
funding_keywords = [
    "raise", "fund", "invest", "back", "valuation",
    "round", "seed", "series", "ipo", "acquire", "merge"
]

ai_keywords = [
    "ai", "model", "llm", "agent", "automation",
    "machine", "learning", "openai", "anthropic",
    "gemini", "gpt"
]

startup_keywords = [
    "startup", "launch", "founded", "growth",
    "users", "expansion", "platform"
]

big_tech_keywords = [
    "google", "amazon", "microsoft", "meta",
    "apple", "tesla", "nvidia", "adobe", "spotify"
]

security_keywords = [
    "hack", "breach", "attack", "security",
    "vulnerability", "phishing"
]

future_keywords = [
    "robotaxi", "autonomous", "self-driving",
    "space", "biotech", "climate", "robot"
]


# ---------------------------
# Hard Filter (remove junk)
# ---------------------------
def is_valid(article):
    url = article.get("url", "")

    if "/video/" in url or "/events/" in url:
        return False

    return True


# ---------------------------
# Sigmoid Normalization
# ---------------------------
def normalize(score):
    return 1 / (1 + math.exp(-score / 5))


# ---------------------------
# Scoring Function
# ---------------------------
def score_article(article):
    title = article.get("title", "")
    words = preprocess(title)
    title_lower = title.lower()

    score = 0

    def match_count_word(keywords):
        return sum(1 for k in keywords if k in words)

    def match_count_phrase(keywords):
        return sum(1 for k in keywords if k in title_lower)

    # Combine both methods
    score += match_count_word(funding_keywords) * 5
    score += match_count_word(ai_keywords) * 4
    score += match_count_word(startup_keywords) * 3
    score += match_count_word(big_tech_keywords) * 3
    score += match_count_word(security_keywords) * 2
    score += match_count_phrase(future_keywords) * 2  # phrases handled better here

    # Normalize to 0–1
    return normalize(score)


# ---------------------------
# Main Pipeline
# ---------------------------
def filter_and_rank(data, min_score=0.5):
    results = []

    for article in data:
        if not is_valid(article):
            continue

        score = score_article(article)

        if score >= min_score:
            article["score"] = round(score, 3)
            results.append(article)

    # sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    return results


# ---------------------------
# Load Data
# ---------------------------
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)


# ---------------------------
# Run Pipeline
# ---------------------------
filtered_articles = filter_and_rank(data, min_score=0.5)


# ---------------------------
# Save Output
# ---------------------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(filtered_articles, f, indent=2)


print(f"Filtered {len(filtered_articles)} relevant articles.")