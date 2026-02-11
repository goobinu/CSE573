import time

print("Starting debug script...")
from playwright.sync_api import sync_playwright
start = time.time()

try:
    print("Calling sync_playwright()...")
    with sync_playwright() as p:
        print(f"Playwright initialized in {time.time() - start:.2f}s")
        print("Launching browser...")
        browser = p.chromium.launch(headless=False)
        print("Browser launched.")
        browser.close()
        print("Browser closed.")
except Exception as e:
    print(f"An error occurred: {e}")

print("Done.")
