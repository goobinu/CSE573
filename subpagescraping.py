import csv
import time
from playwright.sync_api import sync_playwright, Playwright, Page
# from utilities.csvhandling import read_from_csv

curated_categories = "/Users/goobinu/Documents/CSE573/curatedcategories.csv"
start_time = time.time()
subpage_list = []
content_list = []

def read_from_csv(file):
    result = []
    with open(file, mode ='r')as file:
        csvFile = csv.reader(file)
        for lines in csvFile:
            print("NEXT LINE:", lines)
            print("LINK:", lines[1])
            result.append(lines[1])
    return result

def save_subpage_data():
    with open("subpage.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Link to profile", "Post content"])
        for name, link, content in content_list:
            writer.writerow([name, link, content])

def print_subpage_data():
    for name, link, content in content_list:
        print(name, ":", link, "\n")
        print("CONTENT:", content)

def collect_post_data(page: Page):
    print(f"  > [{time.strftime('%X')}] Starting evaluate_all...", flush=True)
    
    # Wait for articles to be present to ensure dynamic content is loaded
    try:
        page.wait_for_selector("article", timeout=5000)
    except:
        print("  > No articles found or timeout waiting for articles.")
        return []

    # Get all article elements
    articles = page.locator("article").all()
    print(f"  > Found {len(articles)} articles.", flush=True)
    
    results = []
    
    for i, article in enumerate(articles):
        try:
            # Scope locators to the specific article
            name_locator = article.locator('[data-tracking-control-name="keyword-landing-page_feed-actor-name"]')
            # Use the data-test-id for the content as it is a unique and stable identifier
            content_locator = article.locator('[data-test-id="main-feed-activity-card__commentary"]')
            
            # Extract data safely
            if name_locator.count() > 0:
                name = name_locator.first.inner_text().strip()
                link = name_locator.first.get_attribute("href")
            else:
                name = "Unknown"
                link = "No Link"
                
            if content_locator.count() > 0:
                content = content_locator.first.inner_text().strip()
            else:
                content = "No Content"
            
            print(f"    > Article {i}: Found {name}")
            results.append((name, link, content))
            
        except Exception as e:
            print(f"    > Error processing article {i}: {e}")
            continue

    global content_list
    content_list.extend(results)
    print(f"  > [{time.strftime('%X')}] Collect finished. Total items: {len(content_list)}.", flush=True)
    return content_list

subpage_list = read_from_csv(curated_categories)
print("ALL LINKS:", subpage_list)
proof_of_concept_page = subpage_list[1]
print("FIRST PAGE:", proof_of_concept_page)

def run(playwright: Playwright):
    chrome = playwright.chromium
    browser = chrome.launch(headless=False)
    page = browser.new_page()
    print(f"[{time.time()-start_time:.2f}s] Page created: {page}", flush=True)
    
    print(f"[{time.time()-start_time:.2f}s] Navigating...", flush=True)

    # Grab the subpage link
    print("first page:", proof_of_concept_page)
    page.goto(proof_of_concept_page)
    
    print(f"[{time.time()-start_time:.2f}s] Page loaded. Collecting...", flush=True)
    collect_post_data(page)
    
    print(f"[{time.time()-start_time:.2f}s] Printing results...", flush=True)
    print_subpage_data()
    save_subpage_data()
    print(f"[{time.time()-start_time:.2f}s] Done. Closing browser.", flush=True)
    browser.close()
    # return page, browser

def finish(browser):
    browser.close()

print(f"[{time.time()-start_time:.2f}s] Initializing Playwright...", flush=True)
with sync_playwright() as playwright:
    print(f"[{time.time()-start_time:.2f}s] Playwright initialized. Starting run()", flush=True)
    run(playwright)