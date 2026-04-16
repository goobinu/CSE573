import json
import logging
import os
from tqdm import tqdm
import uuid
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--subreddit", required=True)
args = parser.parse_args()

SUBREDDIT = args.subreddit

INPUT_FILE = f"data/processed/{SUBREDDIT}_cleaned.jsonl"
OUTPUT_FILE = f"data/chunks/{SUBREDDIT}_chunks.jsonl"

MAX_WORDS = 120  # per chunk

logging.basicConfig(level=logging.INFO)


# -------------------------
# CHUNKING LOGIC
# -------------------------

def split_into_chunks(text, max_words=120):
    words = text.split()
    chunks = []

    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i:i + max_words])
        chunks.append(chunk)

    return chunks


# -------------------------
# PROCESS PIPELINE
# -------------------------

def create_chunks():
    logging.info("Creating chunks from cleaned data...")

    os.makedirs("data/chunks", exist_ok=True)

    total_chunks = 0

    with open(INPUT_FILE, "r") as infile, open(OUTPUT_FILE, "w") as outfile:
        for line in tqdm(infile):
            record = json.loads(line)

            text = record["text"]

            chunks = split_into_chunks(text, MAX_WORDS)

            for idx, chunk_text in enumerate(chunks):
                chunk_record = {
                    "chunk_id": f"{record['id']}_{idx}",
                    "post_id": record.get("post_id", record["id"]),
                    "url": record.get("url"),
                    "type": record["type"],
                    "text": chunk_text,
                    "importance": record["importance"]
                }

                outfile.write(json.dumps(chunk_record) + "\n")
                total_chunks += 1

    logging.info(f"Chunking complete. Total chunks: {total_chunks} !")


# -------------------------
# RUN
# -------------------------

if __name__ == "__main__":
    create_chunks()