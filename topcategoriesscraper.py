from utilities.browser import BrowserManager
from utilities.csvhandling import save_to_csv
import time

start_time = time.time()
top_categories = []

def collect_top_categories(page):
    print(f"  > [{time.strftime('%X')}] Starting evaluate_all...", flush=True)
    # Use locator("a") to avoid accessibility tree computation overhead of get_by_role("link")
    links_data = page.locator("a").evaluate_all("""
        elements => elements.map(el => ({
            text: el.innerText,
            href: el.getAttribute('href')
        }))
    """)
    print(f"  > [{time.strftime('%X')}] evaluate_all finished. Found {len(links_data)} links.", flush=True)
    
    results = []
    for item in links_data:
        link = item['href']
        category = item['text']
        # Handle cases where href is None
        if link and "top-content" in link:
            results.append((category, link))
    
    global top_categories
    top_categories.extend(results)
    return top_categories

def print_top_categories():
    for category, link in top_categories:
        print(category, ":", link)

def run():
    with BrowserManager(headless=False) as page:
        print(f"[{time.time()-start_time:.2f}s] Navigating...", flush=True)
        page.goto("https://www.linkedin.com/top-content")
        
        print(f"[{time.time()-start_time:.2f}s] Page loaded. Collecting...", flush=True)
        collect_top_categories(page)
        
        print(f"[{time.time()-start_time:.2f}s] Printing results...", flush=True)
        print_top_categories()
        
        save_to_csv("results.csv", ["Category", "Link"], top_categories)
        print(f"[{time.time()-start_time:.2f}s] Done.", flush=True)

if __name__ == "__main__":
    run()
