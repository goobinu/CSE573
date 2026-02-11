from playwright.sync_api import sync_playwright, Playwright, Page
import csv

top_categories = []


def collect_top_categories(page: Page):
    # Use evaluate_all to extract data in the browser context in one go
    links_data = page.get_by_role("link").evaluate_all("""
        elements => elements.map(el => ({
            text: el.innerText,
            href: el.getAttribute('href')
        }))
    """)
    
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
    print("Page created:", page)
    page.goto("https://www.linkedin.com/top-content")
    print("Collecting top categories...")
    collect_top_categories(page)
    print_top_categories()
    save_top_categories()
    browser.close()
    # return page, browser

def finish(browser):
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
"""
with sync_playwright() as playwright:
    page, browser = run(playwright)
    print("Page received:", page)
    page.goto("https://www.linkedin.com/top-content")
    print("Collecting top categories...")
    collect_top_categories(page)
    finish(browser)
"""  
"""
linkedin_epp = playwright.new_page() #epp = editors pick page

linkedin_epp.goto("https://www.linkedin.com/top-content")

linkedin_epp.get_by_role("link")

print(linkedin_epp.get_by_role("link").count())
"""
