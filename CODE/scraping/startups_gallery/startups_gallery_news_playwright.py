"""
Playwright-based **NEWS** scraper for `startups.gallery/news`.

This file is intentionally scoped to the "News" entity only.
Next entities to add separately:
- Explore (Companies)
- Investors
- Jobs
"""
import asyncio
import json
import random
import time
import argparse
import os
from datetime import datetime
from typing import List, Dict, Any
from playwright.async_api import async_playwright, Browser, Page
import re


# Set cutoff date - stop scraping when reaching startups with funding date before/equal to this date
# Format: YYYY-MM-DD (e.g., "2026-01-01")
# Set to None to scrape all startups regardless of date
NEWS_CUTOFF_DATE = "2025-01-01"  # Change this date as needed


def get_news_output_filename() -> str:
    """Generate output filename with timestamp for News scrape output."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return f"startups_gallery_news_{timestamp}.json"


def parse_funding_amount(amount_str: str) -> tuple[int, str]:
    """
    Parse funding amount string to integer and return both formats.
    Examples: "$125M" -> (125000000, "$125M"), "$1.4B" -> (1400000000, "$1.4B")
    """
    if not amount_str or amount_str == "N/A":
        return (0, amount_str)
    
    # Remove $ and spaces
    clean = amount_str.replace("$", "").replace(",", "").strip()
    
    # Extract number and multiplier
    match = re.match(r"([\d.]+)\s*([MBK]?)", clean, re.IGNORECASE)
    if not match:
        return (0, amount_str)
    
    number = float(match.group(1))
    multiplier = match.group(2).upper()
    
    multipliers = {
        "B": 1_000_000_000,
        "M": 1_000_000,
        "K": 1_000,
        "": 1
    }
    
    amount_int = int(number * multipliers.get(multiplier, 1))
    return (amount_int, amount_str)


def parse_date(date_str: str) -> tuple[str, str]:
    """
    Parse date string to YYYY-MM-DD format and return both formats.
    Example: "Feb 4, 2026" -> ("2026-02-04", "Feb 4, 2026")
    """
    if not date_str or date_str == "N/A":
        return ("", date_str)
    
    try:
        # Try to parse common date formats
        date_formats = [
            "%b %d, %Y",  # "Feb 4, 2026"
            "%B %d, %Y",   # "February 4, 2026"
            "%Y-%m-%d",    # "2026-02-04"
            "%m/%d/%Y",    # "02/04/2026"
        ]
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt)
                break
            except ValueError:
                continue
        
        if parsed_date:
            return (parsed_date.strftime("%Y-%m-%d"), date_str)
    except:
        pass
    
    return ("", date_str)


async def human_like_delay(min_ms: int = 100, max_ms: int = 500):
    """Add random human-like delay."""
    delay = random.uniform(min_ms / 1000, max_ms / 1000)
    await asyncio.sleep(delay)


async def human_like_scroll(page: Page):
    """Scroll in a human-like manner with random pauses."""
    viewport_height = page.viewport_size["height"]
    
    # Scroll in chunks with random pauses
    for _ in range(3):
        scroll_amount = random.randint(300, 600)
        await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        await human_like_delay(200, 800)
    
    # Sometimes scroll back up a bit (humans do this)
    if random.random() < 0.3:
        await page.evaluate("window.scrollBy(0, -100)")
        await human_like_delay(100, 300)


async def setup_stealth_browser(page: Page):
    """Apply stealth techniques to avoid bot detection."""
    # Set realistic viewport
    await page.set_viewport_size({"width": 1920, "height": 1080})
    
    # Override navigator properties
    await page.add_init_script("""
        // Override webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Mock chrome object
        window.chrome = {
            runtime: {}
        };
        
        // Override permissions
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: async () => ({ state: 'granted' })
            })
        });
    """)
    
    # Set realistic user agent
    await page.set_extra_http_headers({
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    })


async def extract_news_items_from_page(page: Page) -> List[Dict[str, Any]]:
    """Extract News items from the current page state using the known DOM structure."""
    news_items: list[dict[str, Any]] = []
    
    # Wait for content div to be visible
    try:
        await page.wait_for_selector("#content", timeout=10000)
        print("Content div found")
    except:
        print("Warning: Content div not found")
        return []
    
    # Extract data using JavaScript with the correct structure
    extracted_data = await page.evaluate("""
        () => {
            const newsItems = [];
            
            // ===== DOM Structure Navigation =====
            // content div -> first child -> second child -> Post divs
            
            const contentContainer = document.getElementById('content');
            if (!contentContainer) {
                console.log("Content container not found");
                return [];
            }
            
            const contentWrapper = contentContainer.children[0];
            if (!contentWrapper) {
                console.log("Content wrapper not found");
                return [];
            }
            
            const contentWrapperChildren = Array.from(contentWrapper.children);
            if (contentWrapperChildren.length < 2) {
                console.log("Content wrapper has less than 2 children");
                return [];
            }
            
            const postsContainer = contentWrapperChildren[1]; // 2nd child (0-indexed)
            
            // Get all startup Post divs
            const postCards = Array.from(postsContainer.children).filter(
                child => child.getAttribute('data-framer-name') === 'Post'
            );
            console.log("News post cards found:", postCards.length);
            
            // ===== Extract Data from Each News Post Card =====
            postCards.forEach(postCard => {
                try {
                    // ===== Company Name and URL (1st child of Post) =====
                    const companySection = postCard.children[0];
                    if (!companySection) return;
                    
                    const companyLinkWrapper = companySection.children[0];
                    if (!companyLinkWrapper) return;
                    
                    const companyAnchor = companyLinkWrapper.querySelector('a[href]');
                    if (!companyAnchor) return;
                    
                    // Extract and normalize company URL
                    let companyUrl = companyAnchor.getAttribute('href');
                    if (companyUrl) {
                        if (companyUrl.startsWith('./') || companyUrl.startsWith('/')) {
                            companyUrl = 'https://startups.gallery' + companyUrl.replace('./', '/');
                        } else if (!companyUrl.startsWith('http')) {
                            companyUrl = 'https://startups.gallery' + (companyUrl.startsWith('/') ? '' : '/') + companyUrl;
                        }
                    }
                    
                    // Extract company name from h2 tag
                    const companyNameContainer = companyAnchor.querySelector('div');
                    if (!companyNameContainer) return;
                    
                    const companyNameElement = companyNameContainer.querySelector('h2');
                    if (!companyNameElement) return;
                    
                    const companyName = (companyNameElement.textContent || '').trim();
                    
                    // ===== Funding Amount and Stage (2nd child of Post) =====
                    let fundingAmountPretty = '';
                    let fundingStage = '';
                    
                    if (postCard.children.length >= 2) {
                        const fundingSection = postCard.children[1];
                        const fundingParagraph = fundingSection.querySelector('p');
                        
                        if (fundingParagraph) {
                            const fundingText = (fundingParagraph.textContent || '').trim();
                            // Parse format: "$24M · Series A"
                            const fundingMatch = fundingText.match(/\\$([\\d.]+[MBK]?)\\s*·\\s*(.+)/);
                            
                            if (fundingMatch) {
                                fundingAmountPretty = `$${fundingMatch[1]}`;
                                fundingStage = fundingMatch[2].trim();
                            } else {
                                // Fallback: try to extract just the amount
                                if (fundingText.includes('$')) {
                                    const amountMatch = fundingText.match(/\\$([\\d.]+[MBK]?)/);
                                    if (amountMatch) {
                                        fundingAmountPretty = `$${amountMatch[1]}`;
                                    }
                                }
                                fundingStage = fundingText;
                            }
                        }
                    }
                    
                    // ===== Funding Date (3rd child of Post) =====
                    let fundingDatePretty = '';
                    
                    if (postCard.children.length >= 3) {
                        const dateSection = postCard.children[2];
                        const dateParagraph = dateSection.querySelector('p');
                        
                        if (dateParagraph) {
                            fundingDatePretty = (dateParagraph.textContent || '').trim();
                        }
                    }
                    
                    // ===== Lead Investor Name and URL (4th child of Post) =====
                    let leadInvestor = '';
                    let leadInvestorUrl = null;
                    
                    if (postCard.children.length >= 4) {
                        const investorSection = postCard.children[3];
                        const investorFirstDiv = investorSection.children[0];
                        
                        if (investorFirstDiv) {
                            const investorLinkWrapper = investorFirstDiv.children[0];
                            
                            if (investorLinkWrapper) {
                                const investorAnchor = investorLinkWrapper.querySelector('a[href]');
                                
                                if (investorAnchor) {
                                    // Extract and normalize investor URL
                                    let investorUrl = investorAnchor.getAttribute('href');
                                    if (investorUrl) {
                                        if (investorUrl.startsWith('./') || investorUrl.startsWith('/')) {
                                            investorUrl = 'https://startups.gallery' + investorUrl.replace('./', '/');
                                        } else if (!investorUrl.startsWith('http')) {
                                            investorUrl = 'https://startups.gallery' + (investorUrl.startsWith('/') ? '' : '/') + investorUrl;
                                        }
                                        leadInvestorUrl = investorUrl;
                                    }
                                    
                                    // Extract investor name from h2 tag
                                    const investorNameContainer = investorAnchor.querySelector('div');
                                    if (investorNameContainer) {
                                        const investorNameElement = investorNameContainer.querySelector('h2');
                                        if (investorNameElement) {
                                            leadInvestor = (investorNameElement.textContent || '').trim();
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    // ===== News Source URL (5th child of Post) =====
                    let newsSourceUrl = null;
                    
                    if (postCard.children.length >= 5) {
                        const newsSection = postCard.children[4];
                        const newsAnchor = newsSection.querySelector('a[href]');
                        
                        if (newsAnchor) {
                            let newsUrl = newsAnchor.getAttribute('href');
                            if (newsUrl) {
                                // Normalize news URL
                                if (newsUrl.startsWith('./') || newsUrl.startsWith('/')) {
                                    newsUrl = 'https://startups.gallery' + newsUrl.replace('./', '/');
                                } else if (!newsUrl.startsWith('http')) {
                                    newsUrl = 'https://startups.gallery' + (newsUrl.startsWith('/') ? '' : '/') + newsUrl;
                                }
                                newsSourceUrl = newsUrl;
                            }
                        }
                    }
                    
                    // ===== Create News Item Object =====
                    if (companyName && companyName.length > 0) {
                        newsItems.push({
                            name: companyName,
                            company_url: companyUrl,
                            funding_amount_pretty: fundingAmountPretty,
                            funding_stage: fundingStage,
                            funding_date_pretty: fundingDatePretty,
                            lead_investor: leadInvestor,
                            lead_investor_url: leadInvestorUrl,
                            news_source_url: newsSourceUrl
                        });
                    }
                } catch (error) {
                    console.error('Error extracting startup:', error);
                }
            });
            
            return newsItems;
        }
    """)
    
    print(extracted_data)
    
    # Process and enrich the data
    for startup in extracted_data:
        # Parse funding amount to integer while keeping the pretty version
        funding_amount_pretty = startup.get("funding_amount_pretty", "")
        funding_amount, _ = parse_funding_amount(funding_amount_pretty)
        
        # Keep both versions
        startup["funding_amount"] = funding_amount
        startup["funding_amount_pretty"] = funding_amount_pretty  # Keep the original extracted string
        
        # Parse funding date to YYYY-MM-DD format while keeping the pretty version
        funding_date_pretty = startup.get("funding_date_pretty", "")
        funding_date, _ = parse_date(funding_date_pretty)
        
        # Keep both versions
        startup["funding_date"] = funding_date
        startup["funding_date_pretty"] = funding_date_pretty  # Keep the original extracted string
    
    return extracted_data


async def scrape_news(
    max_scrolls: int | None = None,
    debug: bool = False,
    headless: bool = False,
    cutoff_date: str | None = None,
    browser_executable_path: str | None = None,
):
    """Scrape `startups.gallery/news` using Playwright + anti-bot techniques.
    
    Args:
        max_scrolls: Maximum number of "Load More" attempts (None = no limit, default: None)
        debug: Enable debug mode - keeps browser open and adds wait prompts (default: False)
        headless: Run browser in headless mode (default: False)
        cutoff_date: Stop scraping once funding_date <= cutoff_date (YYYY-MM-DD). None disables cutoff.
        browser_executable_path: Optional browser binary path (e.g. Brave). If None, uses system Chromium.
    """
    all_startups = []
    seen_names = set()
    
    async with async_playwright() as p:
        effective_browser_path = (
            browser_executable_path
            if browser_executable_path is not None
            else os.getenv("BROWSER_EXECUTABLE_PATH")
        )

        # Launch browser with realistic settings
        browser = await p.chromium.launch(
            headless=headless,
            executable_path=effective_browser_path,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
        )
        
        # Create context with realistic settings
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            # user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["geolocation"],
            geolocation={"latitude": 40.7128, "longitude": -74.0060},  # NYC
            color_scheme="light",
        )
        
        page = await context.new_page()
        
        try:
            # Apply stealth techniques
            await setup_stealth_browser(page)
            
            print("Navigating to startups.gallery/news...")
            await page.goto(
                "https://startups.gallery/news",
                wait_until="networkidle",
                timeout=30000
            )
            
            # Wait for page to load
            await human_like_delay(2000, 4000)
            
            # Initial extraction
            print("Extracting initial news items...")
            current_startups = await extract_news_items_from_page(page)
            
            for startup in current_startups:
                name = startup.get("name")
                if name and name not in seen_names:
                    seen_names.add(name)
                    all_startups.append(startup)
            
            print(f"Found {len(all_startups)} news items initially")
            
            # DEBUG: Wait here for inspection if debug mode is enabled
            if debug:
                print("\n" + "="*50)
                print("DEBUG MODE: Browser will stay open for inspection")
                print("Press Enter in the terminal to continue...")
                print("="*50)
                input()
            
            # Scroll and load more content
            last_count = len(all_startups)
            scroll_attempts = 0
            no_new_data_count = 0
            
            # Continue until max_scrolls (if set) or until cutoff date or no new data
            while max_scrolls is None or scroll_attempts < max_scrolls:
                # Get current count of Post elements before clicking
                initial_post_count = await page.evaluate("""
                    () => {
                        const contentDiv = document.getElementById('content');
                        if (!contentDiv) return 0;
                        const firstChild = contentDiv.children[0];
                        if (!firstChild) return 0;
                        const secondChild = firstChild.children[1];
                        if (!secondChild) return 0;
                        const postDivs = Array.from(secondChild.children).filter(
                            child => child.getAttribute('data-framer-name') === 'Post'
                        );
                        return postDivs.length;
                    }
                """)
                
                # Try to click "Load More" button
                load_more_clicked = False
                try:
                    # Find the Load More button using Playwright selector
                    # Path: content div -> first child -> second child -> last element -> element with "Load More" text
                    load_more_selector = '#content > div:first-child > div:nth-child(2) > div:last-child [data-framer-name="Default"]:has-text("Load More")'
                    
                    # Check if button exists and is visible
                    load_more_button = page.locator(load_more_selector)
                    if await load_more_button.is_visible(timeout=2000):
                        # Click the button
                        await load_more_button.click(timeout=5000)
                        load_more_clicked = True
                        print(f"  Scroll {scroll_attempts + 1}: Clicked 'Load More' button")
                        
                        # Wait for new Post elements to appear (new elements are appended after existing ones)
                        try:
                            await page.wait_for_function(
                                f"""
                                () => {{
                                    const contentDiv = document.getElementById('content');
                                    if (!contentDiv) return false;
                                    const firstChild = contentDiv.children[0];
                                    if (!firstChild) return false;
                                    const secondChild = firstChild.children[1];
                                    if (!secondChild) return false;
                                    const postDivs = Array.from(secondChild.children).filter(
                                        child => child.getAttribute('data-framer-name') === 'Post'
                                    );
                                    return postDivs.length > {initial_post_count};
                                }}
                                """,
                                timeout=10000
                            )
                            print(f"  New elements loaded! Post count increased from {initial_post_count}")
                            await human_like_delay(1000, 2000)  # Additional wait for rendering
                        except Exception as e:
                            print(f"  Warning: Could not detect new elements: {e}")
                            await human_like_delay(3000, 4000)  # Wait longer if detection fails
                    else:
                        # Fallback: scroll if Load More button not found
                        print(f"  Scroll {scroll_attempts + 1}: Load More button not found or not visible, scrolling instead")
                        await human_like_scroll(page)
                        await human_like_delay(1000, 2000)
                except Exception as e:
                    # If clicking fails, fallback to scrolling
                    print(f"  Scroll {scroll_attempts + 1}: Could not click Load More, scrolling instead: {e}")
                    await human_like_scroll(page)
                    await human_like_delay(1000, 2000)
                
                # Extract all news items (new ones are appended to the list)
                current_startups = await extract_news_items_from_page(page)
                
                new_count = 0
                reached_cutoff_date = False
                
                for startup in current_startups:
                    name = startup.get("name")
                    if name and name not in seen_names:
                        # Check if we've reached the cutoff date
                        effective_cutoff_date = cutoff_date if cutoff_date is not None else NEWS_CUTOFF_DATE
                        if effective_cutoff_date:
                            funding_date = startup.get("funding_date", "")
                            if funding_date:
                                # Compare dates (YYYY-MM-DD format)
                                if funding_date <= effective_cutoff_date:
                                    print(
                                        f"  Reached cutoff date {effective_cutoff_date}. "
                                        f"Found item '{name}' with date {funding_date}"
                                    )
                                    reached_cutoff_date = True
                                    break
                        
                        seen_names.add(name)
                        all_startups.append(startup)
                        new_count += 1
                
                # Stop if we've reached the cutoff date
                if reached_cutoff_date:
                    effective_cutoff_date = cutoff_date if cutoff_date is not None else NEWS_CUTOFF_DATE
                    print(f"\n✓ Reached cutoff date {effective_cutoff_date}. Stopping scraping.")
                    break
                
                if new_count > 0:
                    print(
                        f"Scroll {scroll_attempts + 1}: Found {new_count} new news items "
                        f"(total: {len(all_startups)})"
                    )
                    no_new_data_count = 0
                else:
                    no_new_data_count += 1
                    if no_new_data_count >= 3:
                        print("No new data after multiple scrolls. Stopping...")
                        break
                
                # Check if we've reached the end
                if len(all_startups) == last_count:
                    no_new_data_count += 1
                else:
                    last_count = len(all_startups)
                
                scroll_attempts += 1
                
                # Progress update
                if scroll_attempts % 10 == 0:
                    print(f"Progress: {scroll_attempts} scrolls, {len(all_startups)} total startups")
            
            print(f"\nScraping complete! Total news items: {len(all_startups)}")
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            raise
        finally:
            # DEBUG: Keep browser open for inspection if debug mode is enabled
            if debug:
                print("\n" + "="*50)
                print("DEBUG MODE: Browser will stay open")
                print("Close the browser window manually when done debugging")
                print("="*50)
                input("Press Enter to close browser and exit...")
            await browser.close()
    
    return all_startups


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Scrape startups.gallery/news using Playwright")
    parser.add_argument(
        "--max-scrolls",
        type=int,
        default=None,
        help="Maximum number of scrolls to perform (default: no limit)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode - keeps browser open and adds wait prompts"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--cutoff-date",
        type=str,
        default=None,
        help="Stop scraping once funding_date <= cutoff date (YYYY-MM-DD). Defaults to NEWS_CUTOFF_DATE at top of file.",
    )
    parser.add_argument(
        "--browser-path",
        type=str,
        default=None,
        help="Optional Chromium-based browser executable path (e.g. Brave). "
        "Alternatively set env var BROWSER_EXECUTABLE_PATH. Not committed to git.",
    )
    
    args = parser.parse_args()
    
    print("Starting Playwright scraper for startups.gallery/news...")
    print("Using anti-bot detection techniques...")
    print(f"Max scrolls: {args.max_scrolls if args.max_scrolls else 'No limit'}")
    print(f"Debug mode: {args.debug}")
    print(f"Headless mode: {args.headless}")
    print(f"Cutoff date: {args.cutoff_date if args.cutoff_date is not None else NEWS_CUTOFF_DATE}")
    print(
        "Browser path: "
        f"{args.browser_path or os.getenv('BROWSER_EXECUTABLE_PATH') or 'Playwright-managed Chromium'}"
    )
    
    try:
        startups_data = await scrape_news(
            max_scrolls=args.max_scrolls,
            debug=args.debug,
            headless=args.headless,
            cutoff_date=args.cutoff_date,
            browser_executable_path=args.browser_path,
        )
        
        # Generate output filename with timestamp
        output_file = get_news_output_filename()
        
        # Save to JSON file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(startups_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Data saved to {output_file}")
        print(f"Total startups scraped: {len(startups_data)}")
        
    except KeyboardInterrupt:
        print("\n⚠ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

