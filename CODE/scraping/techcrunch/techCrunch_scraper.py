import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import json
import time

# -----------------------------
# File
# -----------------------------
OUTPUT_FILE = "data/tcs_contentless_articles.json"

# =====================================================
# CONFIG
# =====================================================

FEEDS = {
    "latest": "https://techcrunch.com/",
    "startups": "https://techcrunch.com/category/startups/",
    "venture": "https://techcrunch.com/category/venture/",
    "security": "https://techcrunch.com/category/security/",
    "ai": "https://techcrunch.com/category/artificial-intelligence/"
}

# =====================================================
# SCRAPE SINGLE PAGE
# =====================================================

def scrape_page(url, page_category):
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers, timeout=10)
    print(f"\nFetching: {url} | Status:", response.status_code)

    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    cards = soup.find_all("li", class_="wp-block-post")
    print(f"Found {len(cards)} articles in {page_category}")

    results = []

    for card in cards:
        try:
            # 🔹 Article Category (from card)
            cat_elem = card.find("a", class_="loop-card__cat")
            article_category = cat_elem.get_text(strip=True) if cat_elem else "N/A"

            # 🔹 Title + URL
            title_elem = card.find("a", class_="loop-card__title-link")
            title = title_elem.get_text(strip=True) if title_elem else "N/A"
            link = title_elem["href"] if title_elem else "N/A"

            # 🔹 Author (can be multiple)
            author_elems = card.select("a.loop-card__author")
            authors = [a.get_text(strip=True) for a in author_elems] if author_elems else []

            # 🔹 Time
            time_elem = card.find("time")
            published = time_elem.get("datetime") if time_elem else "N/A"

            # 🔥 Merge categories
            def normalize_category(cat):
                return cat.strip().lower()

            page_cat_norm = normalize_category(page_category)
            article_cat_norm = normalize_category(article_category)

            combined_category = list(set([page_cat_norm, article_cat_norm]))
            combined_category = [c.capitalize() for c in combined_category]

            article = {
                "source": "TechCrunch",
                "pageCategory": page_category,
                "articleCategory": article_category,
                "category": combined_category,
                "title": title,
                "url": link,
                "authors": authors,            
                "published": published,
                "fetched_at": datetime.now(timezone.utc).isoformat()
            }

            results.append(article)

        except Exception as e:
            print("Error:", e)

    return results

# =====================================================
# SCRAPE MULTIPLE PAGES PER CATEGORY
# =====================================================

def scrape_category(base_url, category_name, num_pages=3):
    all_results = []

    for page in range(1, num_pages + 1):
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}page/{page}/"

        page_data = scrape_page(url, category_name)

        if not page_data:
            print(f"Stopping {category_name} early...")
            break

        all_results.extend(page_data)

        time.sleep(2)  # avoid blocking

    return all_results

# =====================================================
# MAIN MULTI-FEED SCRAPER WITH MERGING
# =====================================================

def scrape_all_feeds(feeds, pages_per_feed=3):
    url_map = {}  # 🔥 store unique articles by URL

    for category_name, base_url in feeds.items():
        print(f"\n========== {category_name.upper()} ==========")

        category_data = scrape_category(base_url, category_name, pages_per_feed)

        for article in category_data:
            url = article["url"]

            if url not in url_map:
                url_map[url] = article
            else:
                existing = url_map[url]

                # 🔥 Merge categories
                existing["category"] = list(set(existing["category"] + article["category"]))

                # 🔥 Merge pageCategory properly
                if isinstance(existing["pageCategory"], list):
                    if article["pageCategory"] not in existing["pageCategory"]:
                        existing["pageCategory"].append(article["pageCategory"])
                else:
                    if existing["pageCategory"] != article["pageCategory"]:
                        existing["pageCategory"] = [existing["pageCategory"], article["pageCategory"]]

    return list(url_map.values())

# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    data = scrape_all_feeds(FEEDS, pages_per_feed=10)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("\n✅ Done. Total unique articles:", len(data))