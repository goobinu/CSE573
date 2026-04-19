import json
import logging
import os
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--subreddit", required=True)
args = parser.parse_args()

SUBREDDIT = args.subreddit

INPUT_FILE = f"data/chunks/{SUBREDDIT}_chunks.jsonl"
OUTPUT_FILE = f"data/processed/{SUBREDDIT}_tagged.jsonl"

logging.basicConfig(level=logging.INFO)

# -------------------------
# TAG DEFINITIONS
# -------------------------

TAG_RULES = {
    "FUNDING": ["funding", "raised", "seed", "series", "investment"],
    "HIRING": ["hiring", "job", "engineer", "recruit", "salary"],
    "TECH": ["ai", "llm", "model", "api", "saas", "ml"],
    "MARKETING": ["growth", "seo", "users", "acquisition", "traffic"],
    "PRODUCT": ["feature", "mvp", "build", "launch", "prototype"],
    "FINANCE": ["revenue", "profit", "burn", "runway", "valuation", "cash", "credit"],
    "CAREER": ["mba", "career", "job switch", "entry level"],
    "PRICING": ["pricing", "discount", "subscription", "freemium", "cost"],
}

# -------------------------
# TAGGING FUNCTION
# -------------------------

def assign_tags(text):
    text_lower = text.lower()
    tag_scores = {}

    for tag, keywords in TAG_RULES.items():
        score = 0
        for word in keywords:
            if word in text_lower:
                score += 1

        if score > 0:
            tag_scores[tag] = score

    # Sort by relevance
    sorted_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)

    # Limit tags (avoid over-tagging)
    top_tags = [tag for tag, _ in sorted_tags[:3]]

    return top_tags if top_tags else ["OTHER"]

# -------------------------
# PROCESS PIPELINE
# -------------------------

def tag_data():
    logging.info("Tagging chunks with baseline NLP...")

    os.makedirs("data/processed", exist_ok=True)

    total = 0

    with open(INPUT_FILE, "r") as infile, open(OUTPUT_FILE, "w") as outfile:
        for line in tqdm(infile):
            chunk = json.loads(line)

            tags = assign_tags(chunk["text"])

            chunk["tags"] = tags

            outfile.write(json.dumps(chunk) + "\n")
            total += 1

    logging.info(f"Tagging complete. Processed: {total} !")


# -------------------------
# RUN
# -------------------------

if __name__ == "__main__":
    tag_data()