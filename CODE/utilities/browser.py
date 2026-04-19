from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import time

class BrowserManager:
    """
    Context manager for Playwright browser setup (Synchronous).
    """
    def __init__(self, headless=False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        print(f"[{time.time()-self.start_time:.2f}s] Initializing Playwright...", flush=True)
        self.playwright = sync_playwright().start()
        print(f"[{time.time()-self.start_time:.2f}s] Launching browser...", flush=True)
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        print(f"[{time.time()-self.start_time:.2f}s] Page created.", flush=True)
        return self.page

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"[{time.time()-self.start_time:.2f}s] Closing browser.", flush=True)
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

class AsyncBrowserManager:
    """
    Context manager for Playwright browser setup (Asynchronous).
    """
    def __init__(self, headless=False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        self.start_time = None

    async def __aenter__(self):
        self.start_time = time.time()
        print(f"[{time.time()-self.start_time:.2f}s] Initializing Async Playwright...", flush=True)
        self.playwright = await async_playwright().start()
        print(f"[{time.time()-self.start_time:.2f}s] Launching browser...", flush=True)
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        print(f"[{time.time()-self.start_time:.2f}s] Page created.", flush=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print(f"[{time.time()-self.start_time:.2f}s] Closing browser.", flush=True)
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
