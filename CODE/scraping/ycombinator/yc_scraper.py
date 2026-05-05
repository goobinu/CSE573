"""
YC AI Startups Scraper
======================
Scrapes all AI companies from Y Combinator's directory and saves to CSV.

SETUP (run once, NOTE: only for chromium browser):
    pip install playwright pandas tqdm
    python -m playwright install chromium

USAGE:
    python yc_ai_scraper.py

OUTPUT:
    yc_ai_companies.csv   — one row per company with all fields
"""

import csv
import json
import re
import time
import random
from pathlib import Path
from dataclasses import dataclass, fields, asdict
from typing import Optional

import pandas as pd
from tqdm import tqdm
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


# ──────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────

@dataclass
class Company:
    name: str = ""
    tagline: str = ""
    company_url: str = ""             # YC profile URL
    website: str = ""                  # Company's own site
    linkedin: str = ""
    twitter: str = ""
    facebook: str = ""
    founded: str = ""
    batch: str = ""
    team_size: str = ""
    status: str = ""
    location: str = ""
    primary_partner: str = ""
    tags: str = ""
    description: str = ""
    founder_1_name: str = ""
    founder_1_linkedin: str = ""
    founder_1_twitter: str = ""
    founder_2_name: str = ""
    founder_2_linkedin: str = ""
    founder_2_twitter: str = ""
    founder_3_name: str = ""
    founder_3_linkedin: str = ""
    founder_3_twitter: str = ""
    founder_4_name: str = ""
    founder_4_linkedin: str = ""
    founder_4_twitter: str = ""


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def random_delay(lo=1.0, hi=2.5):
    time.sleep(random.uniform(lo, hi))


def safe_text(el) -> str:
    try:
        return el.inner_text().strip() if el else ""
    except Exception:
        return ""


def safe_attr(el, attr: str) -> str:
    try:
        return (el.get_attribute(attr) or "").strip() if el else ""
    except Exception:
        return ""


# ──────────────────────────────────────────────
# Step 1: Collect all company profile URLs
# ──────────────────────────────────────────────

def collect_company_urls(page) -> list[str]:
    """
    Scrolls the YC directory search results page and collects
    all unique /companies/<slug> hrefs.
    """
    base = "https://www.ycombinator.com"
    url = f"{base}/companies?query=AI"

    print(f"\n[1/2] Loading directory: {url}")
    page.goto(url, wait_until="networkidle", timeout=60_000)
    page.wait_for_timeout(3000)

    seen: set[str] = set()
    no_new_rounds = 0
    MAX_NO_NEW = 30         # Much higher threshold for finding all companies
    scroll_count = 0

    print("      Scrolling to load all results …")
    while no_new_rounds < MAX_NO_NEW:
        links = page.query_selector_all('a[href^="/companies/"]')
        before = len(seen)
        for link in links:
            href = link.get_attribute("href") or ""
            # filter out non-company pages like /companies?...
            if re.match(r"^/companies/[^?#/]+$", href):
                seen.add(base + href)

        if len(seen) == before:
            no_new_rounds += 1
            print(f"      Scroll {scroll_count}: {len(seen)} companies (no new)", end="\r")
        else:
            no_new_rounds = 0
            print(f"      Scroll {scroll_count}: {len(seen)} companies found", end="\r")

        scroll_count += 1
        
        # More aggressive scrolling: Page Down multiple times then End
        for _ in range(3):
            page.keyboard.press("PageDown")
            page.wait_for_timeout(300)
        
        page.keyboard.press("End")
        page.wait_for_timeout(2500)  # Wait longer for dynamic content to load

    print()  # New line after progress
    urls = sorted(seen)
    print(f"      Scrolled {scroll_count} times, found {len(urls)} unique company profiles.")
    return urls


# ──────────────────────────────────────────────
# Step 2: Scrape each company profile page
# ──────────────────────────────────────────────

def parse_company_page(page, url: str) -> Company:
    co = Company(company_url=url)

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(1500)
    except PWTimeout:
        print(f"  ⚠  Timeout loading {url}")
        return co

    # ── Name & tagline ──
    # Extract from full page text since there's no reliable h1
    full_text = page.inner_text("body")
    lines = [l.strip() for l in full_text.splitlines() if l.strip()]
    
    # Company name appears exactly twice in early part of page (breadcrumb + title)
    # Skip first ~12 lines of navigation, then look for a repeated line
    line_counts = {}
    for line in lines[10:40]:
        if 2 <= len(line) <= 100 and not all(c.upper() == c or c == '›' for c in line):
            line_counts[line] = line_counts.get(line, 0) + 1
    
    # Find the line that appears exactly 2 times (the company name)
    co.name = next((line for line, count in line_counts.items() if count == 2 and len(line) > 3), "")
    if not co.name:
        # Fallback: just take a reasonable line from the middle of that range
        for line in lines[10:30]:
            if 3 <= len(line) <= 100 and not any(c in line.lower() for c in ['home', 'companies', 'partners', 'resources', 'startup jobs']):
                co.name = line
                break
    
    # Tagline is typically the line after the company name or shortly after
    name_idx = next((i for i, l in enumerate(lines) if l == co.name), -1)
    if name_idx >= 0:
        # Check the next few lines for a good tagline (10-200 chars, not navigation)
        for j in range(1, min(5, len(lines) - name_idx)):
            candidate = lines[name_idx + j]
            if 10 <= len(candidate) <= 200 and not candidate.isupper() and not any(c in candidate.lower() for c in ['home', 'companies', 'partners']):
                co.tagline = candidate
                break

    # ── Right-side info panel (Founded / Batch / Team Size / Status / Location / Primary Partner) ──
    # Use the lines we already extracted above
    
    # Build a dict of info fields found in the text
    info_dict = {}
    for i, line in enumerate(lines):
        # When we find a label like "Founded:", the value is on the next line
        if line == "Founded:" and i + 1 < len(lines):
            val = lines[i + 1].strip()
            if val and len(val) < 50 and not any(c in val.lower() for c in ['menu', 'home', 'button', 'founded']):
                info_dict['founded'] = val
        elif line == "Batch:" and i + 1 < len(lines):
            val = lines[i + 1].strip()
            if val and len(val) < 50 and not any(c in val.lower() for c in ['menu', 'home', 'batch']):
                info_dict['batch'] = val
        elif line == "Team Size:" and i + 1 < len(lines):
            val = lines[i + 1].strip()
            if val and len(val) < 30 and not any(c in val.lower() for c in ['menu', 'home', 'team']):
                info_dict['team_size'] = val
        elif line == "Status:" and i + 1 < len(lines):
            val = lines[i + 1].strip()
            if val and len(val) < 50 and not any(c in val.lower() for c in ['menu', 'home', 'status']):
                info_dict['status'] = val
        elif line == "Location:" and i + 1 < len(lines):
            val = lines[i + 1].strip()
            if val and len(val) < 100 and not any(c in val.lower() for c in ['menu', 'home', 'location']):
                info_dict['location'] = val
        elif line == "Primary Partner:" and i + 1 < len(lines):
            val = lines[i + 1].strip()
            if val and len(val) < 100 and not any(c in val.lower() for c in ['menu', 'home', 'primary']):
                info_dict['primary_partner'] = val
    
    co.founded = info_dict.get('founded', '')
    co.batch = info_dict.get('batch', '')
    co.team_size = info_dict.get('team_size', '')
    co.status = info_dict.get('status', '')
    co.location = info_dict.get('location', '')
    co.primary_partner = info_dict.get('primary_partner', '')

    # ── Company website ──
    all_links = page.query_selector_all('a[href^="https"]')
    for lk in all_links:
        href = lk.get_attribute("href") or ""
        # Look for actual company website (not YC/linkedin/twitter/facebook)
        if (href.startswith("http") and 
            "ycombinator.com" not in href and 
            "startupschool.org" not in href and
            "linkedin.com" not in href and 
            "twitter.com" not in href and 
            "facebook.com" not in href and
            "x.com" not in href):
            co.website = href
            break
    
    # If no website found, try relative or protocol-relative links
    if not co.website:
        all_links = page.query_selector_all("a[href]")
        for lk in all_links:
            href = lk.get_attribute("href") or ""
            if (href and not href.startswith("#") and
                "ycombinator" not in href.lower() and
                "linkedin" not in href and
                "twitter" not in href and
                "facebook" not in href and
                "x.com" not in href):
                co.website = href
                break

    # ── Social links ──
    all_links = page.query_selector_all("a[href]")
    for lk in all_links:
        href = lk.get_attribute("href") or ""
        if "linkedin.com/company" in href or "linkedin.com/in" in href:
            if not co.linkedin:
                co.linkedin = href
        elif "twitter.com/" in href or "x.com/" in href:
            if not co.twitter:
                co.twitter = href
        elif "facebook.com/" in href:
            if not co.facebook:
                co.facebook = href

    # ── Tags ──
    tag_els = page.query_selector_all('a[href*="?industry="], a[href*="?tags="], span[class*="tag"], span[class*="pill"]')
    co.tags = ", ".join(filter(None, [safe_text(t) for t in tag_els]))

    # ── Description ──
    # Grab the long-form description paragraphs (not the sidebar)
    desc_paras = page.query_selector_all('div[class*="prose"] p, div[class*="description"] p, section p')
    co.description = " ".join(filter(None, [safe_text(p) for p in desc_paras])).strip()
    if not co.description:
        # fallback: grab paragraphs anywhere that are long enough
        all_paras = page.query_selector_all("p")
        long_paras = [safe_text(p) for p in all_paras if len(safe_text(p)) > 60]
        co.description = " ".join(long_paras[:6]).strip()

    # ── Founders ──
    # Extract from text pattern: "Founder Name" followed by "Founder" label
    found_founders = []
    
    # Find the "Active Founders" section in the text
    active_founders_idx = next((i for i, l in enumerate(lines) if "Active Founders" in l), -1)
    
    if active_founders_idx >= 0:
        # Look for founder patterns from that point onward
        for i in range(active_founders_idx + 1, min(active_founders_idx + 50, len(lines))):
            line = lines[i]
            # When we find "Founder" label, the line before it is usually the name
            if line == "Founder" or line.startswith("Founder"):
                if i > 0:
                    candidate_name = lines[i - 1].strip()
                    # Validate it looks like a name (2-3 words, reasonable length)
                    if (3 <= len(candidate_name) <= 60 and 
                        not any(c in candidate_name.lower() for c in ['http', 'linkedin', 'twitter', ':', 'button', 'menu']) and
                        candidate_name not in ['About', 'Company', 'Jobs']):
                        
                        # Now find LinkedIn/Twitter links from the DOM by looking for all links
                        all_links = page.query_selector_all("a[href]")
                        li_href = ""
                        tw_href = ""
                        
                        # Try to match founder name with LinkedIn links nearby
                        for lk in all_links:
                            href = lk.get_attribute("href") or ""
                            link_text = lk.inner_text().strip() if lk else ""
                            
                            # Match by link text if available
                            if link_text and candidate_name.lower() in link_text.lower():
                                if "linkedin.com/in" in href and not li_href:
                                    li_href = href
                                elif ("twitter.com" in href or "x.com" in href) and not tw_href:
                                    tw_href = href
                        
                        # If we couldn't match by text, just take the next available LinkedIn/Twitter links
                        # This is a fallback for founders where link text doesn't contain their full name
                        if not li_href:
                            for lk in all_links:
                                href = lk.get_attribute("href") or ""
                                if "linkedin.com/in" in href:
                                    # Make sure it's not company profile or used by another founder
                                    if href not in [f[1] for f in found_founders]:
                                        li_href = href
                                        break
                        
                        if li_href:  # Only add if we have at least LinkedIn
                            entry = (candidate_name, li_href, tw_href)
                            if entry not in found_founders:
                                found_founders.append(entry)

    for i, (fname, fli, ftw) in enumerate(found_founders[:4], start=1):
        setattr(co, f"founder_{i}_name", fname)
        setattr(co, f"founder_{i}_linkedin", fli)
        setattr(co, f"founder_{i}_twitter", ftw)

    return co


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    out_path = Path("yc_ai_companies.csv")
    done_urls: set[str] = set()

    # Resume support: if CSV already exists, skip already-scraped rows
    if out_path.exists():
        existing = pd.read_csv(out_path)
        done_urls = set(existing["company_url"].dropna().tolist())
        print(f"Resuming — {len(done_urls)} companies already scraped.")

    col_names = [f.name for f in fields(Company)]

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/snap/bin/chromium", headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()
        # Block images/fonts to speed things up
        context.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf}", lambda route: route.abort())

        # ── Step 1: collect URLs ──
        all_urls = collect_company_urls(page)
        todo = [u for u in all_urls if u not in done_urls]
        print(f"\n[2/2] Scraping {len(todo)} company pages …\n")

        # Open CSV for appending
        write_header = not out_path.exists() or out_path.stat().st_size == 0
        csv_file = open(out_path, "a", newline="", encoding="utf-8")
        writer = csv.DictWriter(csv_file, fieldnames=col_names)
        if write_header:
            writer.writeheader()

        for url in tqdm(todo, unit="co"):
            co = parse_company_page(page, url)
            writer.writerow(asdict(co))
            csv_file.flush()
            random_delay(1.0, 2.5)   # be polite to YC's servers

        csv_file.close()
        browser.close()

    # Final report
    df = pd.read_csv(out_path)
    print(f"\nDone! {len(df)} companies saved to: {out_path.resolve()}")
    print(df[["name", "batch", "location", "status", "founder_1_name"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
