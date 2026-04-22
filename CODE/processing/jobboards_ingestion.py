import os
import sys
import hashlib
import pandas as pd

# Add root directory to path so config can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import CHROMA_DB_PATH

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Primary source: produced by CODE/scraping/jobboards/clean_jobs.py
JOBS_MASTER_PATH = os.path.join(BASE_DIR, "DATA", "raw", "greenhouse", "jobs_master.csv")
# Legacy fallback: original trendscout_jobboards pipeline output (includes enriched skills)
JOBS_ENRICHED_PATH = os.path.join(
    BASE_DIR, "trendscout_jobboards", "data", "processed", "jobs_enriched.csv"
)
OUTPUT_PATH = os.path.join(
    BASE_DIR, "DATA", "processed", "jobboards_cleaned_for_extraction.csv"
)


def generate_id(url: str, index: int) -> str:
    """Stable deterministic ID matching the pattern used by vector_store_setup.py."""
    if url:
        return hashlib.md5(str(url).encode("utf-8")).hexdigest() + f"_{index}"
    return f"jobboard_post_{index}"


def build_document_content(row: pd.Series) -> str:
    """Combine title and description into the main searchable text."""
    title = str(row.get("title", "")).strip()
    description = str(row.get("description", "")).strip()
    parts = [p for p in [title, description] if p]
    return "\n\n".join(parts)


def main():
    # Prefer the main-project scraped data; fall back to trendscout_jobboards legacy output
    if os.path.exists(JOBS_MASTER_PATH):
        source_path = JOBS_MASTER_PATH
        print(f"[JobBoards Ingestion] Using primary source: {source_path}")
    elif os.path.exists(JOBS_ENRICHED_PATH):
        source_path = JOBS_ENRICHED_PATH
        print(f"[JobBoards Ingestion] Primary source not found. Using legacy fallback: {source_path}")
    else:
        print(
            "[JobBoards Ingestion] No source file found.\n"
            f"  Expected primary:  {JOBS_MASTER_PATH}\n"
            f"  Expected fallback: {JOBS_ENRICHED_PATH}\n"
            "Run CODE/scraping/jobboards/ scripts first, or the trendscout_jobboards pipeline."
        )
        sys.exit(1)

    print(f"[JobBoards Ingestion] Loading {source_path} ...")
    df = pd.read_csv(source_path)
    df = df.astype(object).fillna("")

    print(f"[JobBoards Ingestion] {len(df)} job records loaded.")

    rows = []
    for idx, row in df.iterrows():
        # Build the shared-schema row that vector_store_setup.py expects
        shared_row = {
            # ── Core document content (matches 'Post content' lookup in vector_store_setup) ──
            "Post content": build_document_content(row),
            # ── Standard author / link fields ──
            "Name": str(row.get("company", "")),
            "Link to profile": "",          # no personal profile for job postings
            "Link to post": str(row.get("job_url", "")),
            # ── Classification ──
            "source_topic": str(row.get("role_category", "")),
            "source": "JobBoards",
            "keywords": str(row.get("skills", "")),
            # ── Job-specific extra metadata (stored as-is; vector_store_setup
            #    includes any unrecognised columns via its fallback loop) ──
            "job_title": str(row.get("title", "")),
            "location": str(row.get("location", "")),
            "role_category": str(row.get("role_category", "")),
            "company": str(row.get("company", "")),
        }
        rows.append(shared_row)

    out_df = pd.DataFrame(rows)

    # Remove rows where document content is empty
    out_df = out_df[out_df["Post content"].str.strip() != ""]
    print(f"[JobBoards Ingestion] {len(out_df)} records after filtering empty content.")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    out_df.to_csv(OUTPUT_PATH, index=False)
    print(f"[JobBoards Ingestion] Saved cleaned CSV → {OUTPUT_PATH}")

    # ── Ingest directly into the shared ChromaDB collection ──────────────────
    try:
        import chromadb
        print(f"[JobBoards Ingestion] Connecting to ChromaDB at {CHROMA_DB_PATH} ...")
        chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        collection = chroma_client.get_or_create_collection(name="linkedin_posts")

        docs, metadatas, ids = [], [], []

        for idx, row in out_df.iterrows():
            docs.append(str(row["Post content"]))

            meta = {
                "author_name": str(row.get("Name", "")),
                "authors":     str(row.get("Name", "")),
                "profile_url": str(row.get("Link to profile", "")),
                "post_url":    str(row.get("Link to post", "")),
                "source_topic": str(row.get("source_topic", "")),
                "source":      "JobBoards",
                "keywords":    str(row.get("keywords", "")),
                # Job-specific extras (always strings so ChromaDB accepts them)
                "job_title":     str(row.get("job_title", "")),
                "location":      str(row.get("location", "")),
                "role_category": str(row.get("role_category", "")),
                "company":       str(row.get("company", "")),
            }
            metadatas.append(meta)
            ids.append(generate_id(row.get("Link to post", ""), idx))

        batch_size = 1000
        for i in range(0, len(docs), batch_size):
            end = min(i + batch_size, len(docs))
            collection.upsert(
                documents=docs[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end],
            )
            print(f"[JobBoards Ingestion] Upserted items {i} – {end - 1}")

        print(
            f"[JobBoards Ingestion] Done. {len(docs)} job postings ingested "
            f"into ChromaDB collection 'linkedin_posts' with source='JobBoards'."
        )

        # ── Quick smoke-test ──────────────────────────────────────────────────
        print("\n[JobBoards Ingestion] --- Smoke test: 'machine learning engineer' ---")
        test = collection.query(
            query_texts=["machine learning engineer"],
            n_results=3,
            where={"source": "JobBoards"},
        )
        if test and test.get("documents") and test["documents"][0]:
            for doc, meta in zip(test["documents"][0], test["metadatas"][0]):
                print(f"  [{meta.get('job_title', 'N/A')} @ {meta.get('company', 'N/A')}] {doc[:80]}...")
        else:
            print("  No results returned (collection may need more data).")

    except ImportError:
        print(
            "[JobBoards Ingestion] chromadb not installed — skipping direct ChromaDB upsert.\n"
            f"The cleaned CSV is available at {OUTPUT_PATH} and will be picked up "
            "by vector_store_setup.py on the next --upload run."
        )


if __name__ == "__main__":
    main()
