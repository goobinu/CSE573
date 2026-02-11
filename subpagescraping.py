import asyncio
import time
import os
from utilities.csvhandling import read_column_from_csv, save_to_csv
from utilities.browser import AsyncBrowserManager

curated_categories = "/Users/goobinu/Documents/CSE573/curatedcategories.csv"
start_time = time.time()
# content_list = [] # No longer needed as we save per file

def save_subpage_results(url, results):
    # Create a filename from the URL or category name
    # We can try to extract a meaningful name from the URL
    if not results:
        return

    # Extract the last part of the URL path for filename, ignoring query params
    clean_url = url.split('?')[0].rstrip('/')
    filename = clean_url.split('/')[-1]
    if not filename:
        filename = "unknown_subpage"
    
    filepath = os.path.join("subpage_results", f"{filename}.csv")
    print(f"  > Saving results to {filepath}", flush=True)
    save_to_csv(filepath, ["Name", "Link to profile", "Post content", "Link to post"], results)

async def collect_post_data(page, url):
    print(f"  > [{time.strftime('%X')}] Processing {url}...", flush=True)
    
    try:
        await page.goto(url)
        # Wait for articles to be present to ensure dynamic content is loaded
        await page.wait_for_selector("article", timeout=5000)
    except Exception as e:
        print(f"  > Error loading {url}: {e}")
        return []

    # Get all article elements
    articles = await page.locator("article").all()
    print(f"  > Found {len(articles)} articles on {url}.", flush=True)
    
    results = []
    
    for i, article in enumerate(articles):
        try:
            # Scope locators to the specific article
            name_locator = article.locator('[data-tracking-control-name="keyword-landing-page_feed-actor-name"]')
            # Use the data-test-id for the content as it is a unique and stable identifier
            content_locator = article.locator('[data-test-id="main-feed-activity-card__commentary"]')
            # grab the post link from share button
            # Updated selector based on user feedback
            share_button_locator = article.locator('.share-button') 
            
            # Extract data safely
            if await name_locator.count() > 0:
                name = await name_locator.first.inner_text()
                name = name.strip()
                link_to_profile = await name_locator.first.get_attribute("href")
            else:
                name = "Unknown"
                link_to_profile = "No Link"
                
            if await content_locator.count() > 0:
                content = await content_locator.first.inner_text()
                content = content.strip()
            else:
                content = "No Content"

            link_to_post = "No Post Link"
            # Try to get the share URL
            try:
                # The share button itself might have the data-share-url attribute or a child might.
                # User pointed to: <div class="... share-button ..." ... data-share-url="...">
                # So we target the element with class share-button and get attribute data-share-url
                # We need to be careful because there might be multiple share buttons (like 'Share' text vs icon), 
                # but the user provided HTML shows a div wrapper with the class and attribute.
                
                # Check for the specific structure the user showed
                # The div has class "collapsible-dropdown ... share-button ..."
                # We can try to locate that div specifically.
                share_div = article.locator('div.share-button[data-share-url]')
                if await share_div.count() > 0:
                    link_to_post = await share_div.first.get_attribute("data-share-url")
                else:
                    # Fallback or alternative selector if the div isn't found exactly
                    pass
            except Exception as e:
                # print(f"    > Error extraction post link: {e}")
                pass
            
            # print(f"    > Article {i} on {url}: Found {name}")
            results.append((name, link_to_profile, content, link_to_post))
            
        except Exception as e:
            print(f"    > Error processing article {i} on {url}: {e}")
            continue

    print(f"  > [{time.strftime('%X')}] Finished matching for {url}. Found {len(results)} items.", flush=True)
    return results

async def process_subpage(browser_manager, url, semaphore):
    async with semaphore:
        # browser_manager is now the manager instance, so we access .browser
        page = await browser_manager.browser.new_page()
        try:
            results = await collect_post_data(page, url)
            save_subpage_results(url, results)
        finally:
            await page.close()

async def run():
    # Read links from CSV (assuming link is in the second column)
    # We skip the header row to avoid reading the column title as a link
    subpage_list = read_column_from_csv(curated_categories, 1, skip_header=True)
    print(f"ALL LINKS ({len(subpage_list)}):", subpage_list)
    
    if not subpage_list:
        print("No links found in CSV.")
        return

    # Create a semaphore to limit concurrency
    semaphore = asyncio.Semaphore(5)

    async with AsyncBrowserManager(headless=False) as manager:
        print(f"[{time.time()-start_time:.2f}s] Starting concurrent scraping...", flush=True)
        
        tasks = []
        for url in subpage_list:
            if url and url.startswith("http"):
                 tasks.append(process_subpage(manager, url, semaphore))
            else:
                print(f"Skipping invalid URL: {url}")

        await asyncio.gather(*tasks)
        print(f"[{time.time()-start_time:.2f}s] Done.", flush=True)

if __name__ == "__main__":
    asyncio.run(run())