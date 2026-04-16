import requests
import time
import json
import logging
from tqdm import tqdm
import os
import argparse

# =========================
# CONFIG
# =========================

parser = argparse.ArgumentParser()
parser.add_argument("--subreddit", required=True, help="Subreddit name")
args = parser.parse_args()

SUBREDDIT = args.subreddit
OUTPUT_FILE = f"data/raw/{SUBREDDIT}_posts.jsonl"
SORT = "new"
LIMIT = 25

HEADERS = {
    "User-Agent": "TrendScoutAI/1.0 (Academic Research)"
}

# =========================
# LOGGING SETUP
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# =========================
# HELPER FUNCTIONS
# =========================

def fetch_posts(subreddit, sort="new"):
    url = f"https://www.reddit.com/r/{subreddit}/{sort}/.json?limit={LIMIT}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def fetch_comments(permalink):
    url = f"https://www.reddit.com{permalink}.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def extract_comments(children):
    comments = []

    def recurse(nodes):
        for node in nodes:
            if node["kind"] != "t1":
                continue

            data = node["data"]

            comments.append({
                "id": data.get("id"),
                "author": data.get("author"),
                "body": data.get("body"),
                "score": data.get("score"),
                "created_utc": data.get("created_utc")
            })

            if data.get("replies") and isinstance(data["replies"], dict):
                recurse(data["replies"]["data"]["children"])

    recurse(children)
    return comments


def save_record(record):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# =========================
# MAIN PIPELINE
# =========================

def run_scraper():
    logging.info(f"Scraping r/{SUBREDDIT} ...")

    os.makedirs("data/raw", exist_ok=True)

    data = fetch_posts(SUBREDDIT, SORT)
    posts = data["data"]["children"]

    for item in tqdm(posts, desc="Fetching posts"):
        post = item["data"]

        record = {
            "post_id": post.get("id"),
            "title": post.get("title"),
            "selftext": post.get("selftext"),
            "author": post.get("author"),
            "score": post.get("score"),
            "num_comments": post.get("num_comments"),
            "created_utc": post.get("created_utc"),
            "permalink": post.get("permalink"),
            "fetched_at": int(time.time())
        }

        # Fetch comments
        try:
            comments_json = fetch_comments(record["permalink"])
            children = comments_json[1]["data"]["children"]
            record["comments"] = extract_comments(children)
        except Exception as e:
            logging.warning(f"Failed to fetch comments: {e}")
            record["comments"] = []

        save_record(record)
        time.sleep(1)

    logging.info("Scraping complete!")

if __name__ == "__main__":
    run_scraper()