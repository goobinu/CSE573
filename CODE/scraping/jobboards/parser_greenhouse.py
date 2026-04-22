"""
Visit each Greenhouse job URL and scrape the full description.
Reads:   DATA/raw/jobboards/greenhouse_jobs_list.csv
Outputs: DATA/raw/jobboards/greenhouse_job_details.csv
"""
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # CSE573/
RAW_DIR = PROJECT_ROOT / "DATA" / "raw" / "jobboards"
RAW_DIR.mkdir(parents=True, exist_ok=True)

MAX_JOBS = 50


def extract_job_details(urls):
    rows = []

    for i, url in enumerate(urls, start=1):
        try:
            print(f"[{i}/{len(urls)}] Visiting {url}")
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=30,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            description_el = soup.select_one("div#content, div.content, section, main")
            description = description_el.get_text(" ", strip=True) if description_el else None

            rows.append({"job_url": url, "description": description})

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            rows.append({"job_url": url, "description": None})

    df = pd.DataFrame(rows)
    out_path = RAW_DIR / "greenhouse_job_details.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved greenhouse job details to {out_path}")
    return df


if __name__ == "__main__":
    jobs_df = pd.read_csv(RAW_DIR / "greenhouse_jobs_list.csv")
    urls = jobs_df["job_url"].dropna().unique().tolist()[:MAX_JOBS]
    extract_job_details(urls)
