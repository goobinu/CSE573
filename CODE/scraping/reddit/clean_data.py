import json
import re
import math
import logging
import os
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--subreddit", required=True)
args = parser.parse_args()

SUBREDDIT = args.subreddit

INPUT_FILE = f"data/raw/{SUBREDDIT}_posts.jsonl"
OUTPUT_FILE = f"data/processed/{SUBREDDIT}_cleaned.jsonl"

MIN_SCORE = 1
MIN_TEXT_LENGTH = 20

logging.basicConfig(level=logging.INFO)

# -------------------------
# TEXT CLEANING
# -------------------------

def normalize_text(text):
    if not text:
        return ""

    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def calculate_importance(score, text):
    length_bonus = 0.1 if len(text.split()) > 50 else 0

    return (
        0.7 * math.log1p(score) +   # engagement signal
        0.2 * length_bonus          # small boost for detailed content
    )

def is_valid_record(text, score, author):
    if not text or len(text) < MIN_TEXT_LENGTH:
        return False
    if len(text.split()) < 8:
        return False
    if score < MIN_SCORE:
        return False
    if author == "AutoModerator":
        return False
    return True


# -------------------------
# PROCESSING
# -------------------------

def process_data():
    logging.info("Cleaning and filtering Reddit data...")

    os.makedirs("data/processed", exist_ok=True)

    with open(INPUT_FILE, "r") as infile, open(OUTPUT_FILE, "w") as outfile:
        for line in tqdm(infile):
            post = json.loads(line)

            post_id = post["post_id"]

            # ---- Process Post ----
            text = normalize_text(post.get("title", "") + " " + post.get("selftext", ""))
            score = post.get("score", 0)
            author = post.get("author")

            if is_valid_record(text, score, author):
                importance = calculate_importance(score, text)

                if importance < 1.0:
                    continue
                record = {
                    "id": post_id,
                    "type": "post",
                    "url": post.get("url"),
                    "text": text,
                    "score": score,
                    "importance": importance
                }
                outfile.write(json.dumps(record) + "\n")

            # ---- Process Comments ----
            for comment in post.get("comments", []):
                c_text = normalize_text(comment.get("body", ""))
                c_score = comment.get("score", 0)
                c_author = comment.get("author")

                if is_valid_record(c_text, c_score, c_author):
                    c_importance = calculate_importance(c_score, c_text)
                    if c_importance < 1.0:
                        continue
                    record = {
                        "id": comment.get("id"),
                        "type": "comment",
                        "url": comment.get("url"),
                        "post_id": post_id,
                        "text": c_text,
                        "score": c_score,
                        "importance": c_importance
                    }
                    outfile.write(json.dumps(record) + "\n")

    logging.info("Cleaning complete!")


if __name__ == "__main__":
    process_data()