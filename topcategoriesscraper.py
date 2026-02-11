from playwright.sync_api import sync_playwright, Playwright, Page
import csv
import time

start_time = time.time()
top_categories = []


def collect_top_categories(page: Page):
    print(f"  > [{time.strftime('%X')}] Starting evaluate_all...", flush=True)
    # Use locator("a") to avoid accessibility tree computation overhead of get_by_role("link")
    links_data = page.locator("a").evaluate_all("""
        elements => elements.map(el => ({
            text: el.innerText,
            href: el.getAttribute('href')
        }))
    """)
    print(f"  > [{time.strftime('%X')}] evaluate_all finished. Found {len(links_data)} links.", flush=True)
    
    for item in links_data:
        link = item['href']
        category = item['text']
        # Handle cases where href is None
        if link and "top-content" in link:
            top_categories.append((category, link))
    return top_categories

def print_top_categories():
    for category, link in top_categories:
        print(category, ":", link)

def save_top_categories():
    with open("results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Category", "Link"])
        for category, link in top_categories:
            writer.writerow([category, link])

def run(playwright: Playwright):
    chrome = playwright.chromium
    browser = chrome.launch(headless=False)
    page = browser.new_page()
    print(f"[{time.time()-start_time:.2f}s] Page created: {page}", flush=True)
    
    print(f"[{time.time()-start_time:.2f}s] Navigating...", flush=True)
    page.goto("https://www.linkedin.com/top-content")
    
    print(f"[{time.time()-start_time:.2f}s] Page loaded. Collecting...", flush=True)
    collect_top_categories(page)
    
    print(f"[{time.time()-start_time:.2f}s] Printing results...", flush=True)
    print_top_categories()
    save_top_categories()
    print(f"[{time.time()-start_time:.2f}s] Done. Closing browser.", flush=True)
    browser.close()
    # return page, browser

def finish(browser):
    browser.close()

print(f"[{time.time()-start_time:.2f}s] Initializing Playwright...", flush=True)
with sync_playwright() as playwright:
    print(f"[{time.time()-start_time:.2f}s] Playwright initialized. Starting run()", flush=True)
    run(playwright)

