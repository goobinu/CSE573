import asyncio
from playwright.async_api import async_playwright

async def main():
    print("Starting async playwright...", flush=True)
    async with async_playwright() as p:
        print("Playwright initialized! (Async)", flush=True)
        browser = await p.chromium.launch(headless=False)
        print("Browser launched", flush=True)
        page = await browser.new_page()
        await page.goto("https://www.linkedin.com/top-content")
        print(f"Page loaded: {await page.title()}", flush=True)
        await browser.close()
    print("Done", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
