"""
Scrape job listings from Greenhouse (job-boards.greenhouse.io/xai).
Outputs: DATA/raw/greenhouse/greenhouse_jobs_list.csv
         DATA/raw/greenhouse/greenhouse_page.html
"""
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # CSE573/
RAW_DIR = PROJECT_ROOT / "DATA" / "raw" / "greenhouse"
RAW_DIR.mkdir(parents=True, exist_ok=True)

START_URL = "https://job-boards.greenhouse.io/xai"


def scrape_greenhouse_jobs():
    print(f"Opening {START_URL}")
    response = requests.get(
        START_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
        allow_redirects=True,
    )

    print("Final URL:", response.url)
    print("Status code:", response.status_code)
    response.raise_for_status()

    html = response.text
    (RAW_DIR / "greenhouse_page.html").write_text(html, encoding="utf-8")

    soup = BeautifulSoup(html, "lxml")
    jobs = []

    for a in soup.select("a[href]"):
        href = a.get("href")
        title = a.get_text(" ", strip=True)

        if not href or not title:
            continue

        if href.startswith("/"):
            href = "https://job-boards.greenhouse.io" + href

        if "/jobs/" in href:
            jobs.append({
                "company": "xAI",
                "department": None,
                "title": title,
                "location": None,
                "job_url": href,
            })

    df = pd.DataFrame(jobs).drop_duplicates(subset=["job_url"])
    out_path = RAW_DIR / "greenhouse_jobs_list.csv"
    df.to_csv(out_path, index=False)

    print(df.head(10))
    print(f"Saved {len(df)} jobs to {out_path}")
    return df


if __name__ == "__main__":
    scrape_greenhouse_jobs()
