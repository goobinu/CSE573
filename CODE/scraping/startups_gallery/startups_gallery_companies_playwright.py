"""
Playwright-based **COMPANIES** scraper for `startups.gallery/companies/*`.

This file scrapes detailed company information from individual company pages.
Reads company URLs from `input/company_input.json` (generated from news scraper).
"""
import asyncio
import json
import random
import argparse
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page
import re


def get_companies_output_filename() -> str:
    """Generate output filename with timestamp for Companies scrape output."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return f"startups_gallery_companies_{timestamp}.json"


def normalize_investor_url(href: str) -> str:
    """Normalize investor URL to full startups.gallery URL."""
    if not href:
        return ""
    
    # Handle relative paths like ../investors/b-capital
    if href.startswith('../'):
        href = href.replace('../', '/')
    
    if href.startswith('./'):
        href = href.replace('./', '/')
    
    if href.startswith('/'):
        return f"https://startups.gallery{href}"
    elif not href.startswith('http'):
        return f"https://startups.gallery/{href}"
    
    return href


def format_investor_name(name_id: str) -> str:
    """Convert name_id to formatted name (e.g., 'figma-ventures' -> 'Figma Ventures')."""
    if not name_id:
        return ""
    
    # Split by dashes, capitalize each word, join with spaces
    return ' '.join(
        word.capitalize() 
        for word in name_id.split('-')
    )


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


async def human_like_delay(min_ms: int = 100, max_ms: int = 500):
    """Add random human-like delay."""
    delay = random.uniform(min_ms / 1000, max_ms / 1000)
    await asyncio.sleep(delay)


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


async def extract_company_data_from_page(page: Page, company_url: str) -> Optional[Dict[str, Any]]:
    """Extract company data from a company page using the known DOM structure."""
    
    # Wait for feed div to be visible
    try:
        await page.wait_for_selector("#feed", timeout=15000)
    except:
        print(f"  ⚠ Warning: Feed div not found for {company_url}")
        return None
    
    # Extract data using JavaScript
    company_data = await page.evaluate("""
        () => {
            const feed = document.getElementById('feed');
            if (!feed) {
                console.log("Feed div not found");
                return null;
            }
            
            const result = {
                company_cover_image: null,
                company_logo: null,
                company_domain_url: null,
                company_job_link: null,
                company_name: null,
                company_description: null,
                company_location: null,
                funding_amount: null,
                funding_amount_pretty: null,
                funding_stage: null,
                industry_category: null,
                work_style: null,
                company_size: null,
                investors: [],
                jobs: []
            };
            
            // ===== Company Cover Image =====
            // feed -> first child (imagediv) -> <a> -> div -> img -> src
            const imageDiv = feed.children[0];
            if (imageDiv) {
                const coverLink = imageDiv.querySelector('a');
                if (coverLink) {
                    const coverDiv = coverLink.querySelector('div');
                    if (coverDiv) {
                        const coverImg = coverDiv.querySelector('img');
                        if (coverImg) {
                            result.company_cover_image = coverImg.getAttribute('src');
                        }
                    }
                }
                
                // ===== Company Logo =====
                // imagediv -> 2nd child -> child -> img -> src
                if (imageDiv.children.length >= 2) {
                    const logoContainer = imageDiv.children[1];
                    if (logoContainer) {
                        const logoWrapper = logoContainer.children[0];
                        if (logoWrapper) {
                            const logoImg = logoWrapper.querySelector('img');
                            if (logoImg) {
                                result.company_logo = logoImg.getAttribute('src');
                            }
                        }
                    }
                }
            }
            
            // ===== Company Description =====
            // feed -> 2nd child div -> first child div (a1) -> third child div -> child p tag -> text
            if (feed.children.length >= 2) {
                const secondChildDiv = feed.children[1];
                if (secondChildDiv) {
                    const a1 = secondChildDiv.children[0];
                    if (a1 && a1.children.length >= 3) {
                        const thirdChildDiv = a1.children[2];
                        if (thirdChildDiv) {
                            const descParagraph = thirdChildDiv.querySelector('p');
                            if (descParagraph) {
                                result.company_description = (descParagraph.textContent || '').trim();
                            }
                        }
                    }
                }
            }
            
            // ===== Company Location, Funding, Industry, Work Style, Company Size =====
            // feed -> 2nd child div -> first child div (a1) -> 4th child div -> child a tags
            if (feed.children.length >= 2) {
                const secondChildDiv = feed.children[1];
                if (secondChildDiv) {
                    const a1 = secondChildDiv.children[0];
                    if (a1 && a1.children.length >= 4) {
                        const fourthChildDiv = a1.children[3];
                        if (fourthChildDiv) {
                            // Get all child elements (mix of a tags and divs)
                            const children = Array.from(fourthChildDiv.children);
                            
                            // Find location: a tag with svg > use href="#svg8851667150"
                            const locationAnchor = children.find(child => {
                                if (child.tagName !== 'A') return false;
                                const svg = child.querySelector('svg');
                                if (!svg) return false;
                                const use = svg.querySelector('use');
                                if (!use) return false;
                                return use.getAttribute('href') === '#svg8851667150';
                            });
                            
                            if (locationAnchor) {
                                const locationSecondDiv = locationAnchor.children[1];
                                if (locationSecondDiv) {
                                    const locationP = locationSecondDiv.querySelector('p');
                                    if (locationP) {
                                        result.company_location = (locationP.textContent || '').trim();
                                    }
                                }
                            }
                            
                            // Find funding value and stage: a tag with svg > use href="#svg-1866062953_705"
                            const fundingAnchor = children.find(child => {
                                if (child.tagName !== 'A') return false;
                                const svg = child.querySelector('svg');
                                if (!svg) return false;
                                const use = svg.querySelector('use');
                                if (!use) return false;
                                return use.getAttribute('href') === '#svg-1866062953_705';
                            });
                            
                            if (fundingAnchor) {
                                const fundingSecondDiv = fundingAnchor.children[1];
                                if (fundingSecondDiv) {
                                    const fundingP = fundingSecondDiv.querySelector('p');
                                    if (fundingP) {
                                        const fundingText = (fundingP.textContent || '').trim();
                                        // Parse format: "$150M Series B"
                                        const fundingMatch = fundingText.match(/\\$([\\d.]+[MBK]?)\\s*(.+)/);
                                        if (fundingMatch) {
                                            result.funding_amount_pretty = `$${fundingMatch[1]}`;
                                            result.funding_stage = fundingMatch[2].trim();
                                        } else {
                                            // Fallback: try to extract just the amount or stage
                                            if (fundingText.includes('$')) {
                                                const amountMatch = fundingText.match(/\\$([\\d.]+[MBK]?)/);
                                                if (amountMatch) {
                                                    result.funding_amount_pretty = `$${amountMatch[1]}`;
                                                }
                                            }
                                            result.funding_stage = fundingText;
                                        }
                                    }
                                }
                            }
                            
                            // Find industry category: a tag with svg > use href="#svg9767306304"
                            const industryAnchor = children.find(child => {
                                if (child.tagName !== 'A') return false;
                                const svg = child.querySelector('svg');
                                if (!svg) return false;
                                const use = svg.querySelector('use');
                                if (!use) return false;
                                return use.getAttribute('href') === '#svg9767306304';
                            });
                            
                            if (industryAnchor) {
                                const industrySecondDiv = industryAnchor.children[1];
                                if (industrySecondDiv) {
                                    const industryP = industrySecondDiv.querySelector('p');
                                    if (industryP) {
                                        result.industry_category = (industryP.textContent || '').trim();
                                    }
                                }
                            }
                            
                            // Find work style: a tag with svg > use href="#svg12681374675"
                            const workStyleAnchor = children.find(child => {
                                if (child.tagName !== 'A') return false;
                                const svg = child.querySelector('svg');
                                if (!svg) return false;
                                const use = svg.querySelector('use');
                                if (!use) return false;
                                return use.getAttribute('href') === '#svg12681374675';
                            });
                            
                            if (workStyleAnchor) {
                                const workStyleSecondDiv = workStyleAnchor.children[1];
                                if (workStyleSecondDiv) {
                                    const workStyleP = workStyleSecondDiv.querySelector('p');
                                    if (workStyleP) {
                                        result.work_style = (workStyleP.textContent || '').trim();
                                    }
                                }
                            }
                            
                            // Find company size: a tag with svg > use href="#svg12525321201"
                            const companySizeAnchor = children.find(child => {
                                if (child.tagName !== 'A') return false;
                                const svg = child.querySelector('svg');
                                if (!svg) return false;
                                const use = svg.querySelector('use');
                                if (!use) return false;
                                return use.getAttribute('href') === '#svg12525321201';
                            });
                            
                            if (companySizeAnchor) {
                                const companySizeSecondDiv = companySizeAnchor.children[1];
                                if (companySizeSecondDiv) {
                                    const companySizeP = companySizeSecondDiv.querySelector('p');
                                    if (companySizeP) {
                                        result.company_size = (companySizeP.textContent || '').trim();
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            // ===== Company Domain URL, Job Link, Name, and Investors =====
            // feed -> 2nd child div -> first child div -> first child div (investor-website-job)
            if (feed.children.length >= 2) {
                const secondChildDiv = feed.children[1];
                if (secondChildDiv) {
                    const firstChildDiv = secondChildDiv.children[0];
                    if (firstChildDiv) {
                        const investorWebsiteJobDiv = firstChildDiv.children[0];
                        if (investorWebsiteJobDiv) {
                            // ===== Company Domain URL =====
                            // investor-website-job -> 2nd child div (website-job) -> first child div -> first child <a> -> href
                            if (investorWebsiteJobDiv.children.length >= 2) {
                                const websiteJobDiv = investorWebsiteJobDiv.children[1];
                                if (websiteJobDiv) {
                                    const websiteFirstDiv = websiteJobDiv.children[0];
                                    if (websiteFirstDiv) {
                                        const websiteAnchor = websiteFirstDiv.querySelector('a');
                                        if (websiteAnchor) {
                                            result.company_domain_url = websiteAnchor.getAttribute('href');
                                        }
                                    }
                                    
                                    // ===== Company Job Link =====
                                    // website-job -> 2nd child -> second child -> first child <a> -> href
                                    if (websiteJobDiv.children.length >= 2) {
                                        const jobContainer = websiteJobDiv.children[1];
                                        if (jobContainer && jobContainer.children.length >= 2) {
                                            const jobSecondChild = jobContainer.children[1];
                                            if (jobSecondChild) {
                                                const jobAnchor = jobSecondChild.querySelector('a');
                                                if (jobAnchor) {
                                                    result.company_job_link = jobAnchor.getAttribute('href');
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // ===== Company Name =====
                            // investor-website-job -> first child div (investor) -> first child div -> first child h1 -> text
                            const investorDiv = investorWebsiteJobDiv.children[0];
                            if (investorDiv) {
                                const investorFirstDiv = investorDiv.children[0];
                                if (investorFirstDiv) {
                                    const companyNameH1 = investorFirstDiv.querySelector('h1');
                                    if (companyNameH1) {
                                        result.company_name = (companyNameH1.textContent || '').trim();
                                    }
                                }
                                
                                // ===== All Investors Details =====
                                // investor -> 2nd child div -> first child div -> 2nd child div -> all <a> tags
                                if (investorDiv.children.length >= 2) {
                                    const investorsContainer = investorDiv.children[1];
                                    if (investorsContainer) {
                                        const investorsFirstDiv = investorsContainer.children[0];
                                        if (investorsFirstDiv && investorsFirstDiv.children.length >= 2) {
                                            const investorsListDiv = investorsFirstDiv.children[1];
                                            if (investorsListDiv) {
                                                const investorAnchors = investorsListDiv.querySelectorAll('a');
                                                investorAnchors.forEach(anchor => {
                                                    const investor = {
                                                        url: anchor.getAttribute('href') || '',
                                                        name: '',
                                                        name_id: '',
                                                        logo: null
                                                    };
                                                    
                                                    // Extract investor name from first child div's id attribute
                                                    const firstChildDiv = anchor.children[0];
                                                    if (firstChildDiv) {
                                                        // Get the id attribute (e.g., 'figma-ventures-1vecohl')
                                                        const divId = firstChildDiv.getAttribute('id') || '';
                                                        
                                                        if (divId) {
                                                            // Remove last dash and everything after to get name_id
                                                            // e.g., 'figma-ventures-1vecohl' -> 'figma-ventures'
                                                            const lastDashIdx = divId.lastIndexOf('-');
                                                            if (lastDashIdx > 0) {
                                                                investor.name_id = divId.substring(0, lastDashIdx);
                                                            } else {
                                                                investor.name_id = divId;
                                                            }
                                                            
                                                            // Convert name_id to nice name
                                                            // e.g., 'figma-ventures' -> 'Figma Ventures'
                                                            investor.name = investor.name_id
                                                                .split('-')
                                                                .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
                                                                .join(' ');
                                                        }
                                                        
                                                        // Extract logo from first child div -> child -> img -> src
                                                        const logoDiv = firstChildDiv.children[0];
                                                        if (logoDiv) {
                                                            const logoImg = logoDiv.querySelector('img');
                                                            if (logoImg) {
                                                                investor.logo = logoImg.getAttribute('src');
                                                            }
                                                        }
                                                    }
                                                    
                                                    if (investor.url || investor.name || investor.name_id) {
                                                        result.investors.push(investor);
                                                    }
                                                });
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            // ===== Jobs Array =====
            // feed -> second child div -> second div (id="feed-1") -> array of <a> tags
            if (feed.children.length >= 2) {
                const secondChildDiv = feed.children[1];
                if (secondChildDiv) {
                    // Find div with id="feed-1" (could be second child or need to search)
                    let feedOneDiv = null;
                    // Try second child first
                    if (secondChildDiv.children.length >= 2) {
                        const candidate = secondChildDiv.children[1];
                        if (candidate && candidate.getAttribute('id') === 'feed-1') {
                            feedOneDiv = candidate;
                        }
                    }
                    // If not found, search all children
                    if (!feedOneDiv) {
                        for (let i = 0; i < secondChildDiv.children.length; i++) {
                            const child = secondChildDiv.children[i];
                            if (child && child.getAttribute('id') === 'feed-1') {
                                feedOneDiv = child;
                                break;
                            }
                        }
                    }
                    
                    if (feedOneDiv) {
                        // Get all <a> tags as children
                        const jobAnchors = Array.from(feedOneDiv.children).filter(
                            child => child.tagName === 'A'
                        );
                        
                        jobAnchors.forEach(anchor => {
                            const job = {
                                job_link: anchor.getAttribute('href') || '',
                                job_role: null,
                                job_description_raw: null,
                                job_location: null,
                                job_posted_date: null
                            };
                            
                            // Extract job role: 2nd child div (job-desc) -> first child div -> first h2
                            if (anchor.children.length >= 2) {
                                const jobDesc = anchor.children[1];
                                if (jobDesc) {
                                    const firstChildDiv = jobDesc.children[0];
                                    if (firstChildDiv) {
                                        const jobRoleH2 = firstChildDiv.querySelector('h2');
                                        if (jobRoleH2) {
                                            job.job_role = (jobRoleH2.textContent || '').trim();
                                        }
                                    }
                                    
                                    // Extract job description: job-desc's second child div -> first child p
                                    if (jobDesc.children.length >= 2) {
                                        const secondChildDiv = jobDesc.children[1];
                                        if (secondChildDiv) {
                                            const descP = secondChildDiv.querySelector('p');
                                            if (descP) {
                                                job.job_description_raw = (descP.textContent || '').trim();
                                                
                                                // Try to parse location and date from raw description
                                                // Format: "San Francisco, CA · Posted on Jan 23, 2026"
                                                const descText = job.job_description_raw;
                                                
                                                // Try to extract location (before "·")
                                                const parts = descText.split('·');
                                                if (parts.length >= 1) {
                                                    const locationPart = parts[0].trim();
                                                    if (locationPart) {
                                                        job.job_location = locationPart;
                                                    }
                                                }
                                                
                                                // Try to extract date (after "Posted on")
                                                const postedMatch = descText.match(/Posted on (.+)/i);
                                                if (postedMatch) {
                                                    job.job_posted_date = postedMatch[1].trim();
                                                } else {
                                                    // Try alternative format: just look for date pattern
                                                    const dateMatch = descText.match(/([A-Z][a-z]+ \\d{1,2}, \\d{4})/);
                                                    if (dateMatch) {
                                                        job.job_posted_date = dateMatch[1].trim();
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            
                            if (job.job_link || job.job_role) {
                                result.jobs.push(job);
                            }
                        });
                    }
                }
            }
            
            return result;
        }
    """)
    
    if not company_data:
        return None
    
    # Parse funding amount to integer (similar to news scraper)
    funding_amount_pretty = company_data.get("funding_amount_pretty", "")
    if funding_amount_pretty:
        funding_amount, _ = parse_funding_amount(funding_amount_pretty)
        company_data["funding_amount"] = funding_amount
    else:
        company_data["funding_amount"] = None
    
    # Normalize investor URLs and ensure name is formatted
    for investor in company_data.get("investors", []):
        if investor.get("url"):
            investor["url"] = normalize_investor_url(investor["url"])
        # Ensure name is formatted from name_id if name_id exists but name doesn't
        if investor.get("name_id") and not investor.get("name"):
            investor["name"] = format_investor_name(investor["name_id"])
    
    return company_data


async def scrape_companies(
    input_file: str = "input/company_input.json",
    max_companies: Optional[int] = None,
    debug: bool = False,
    headless: bool = False,
    browser_executable_path: Optional[str] = None,
    output_file: Optional[str] = None,
):
    """Scrape company details from `startups.gallery/companies/*` pages.
    
    Args:
        input_file: Path to JSON file with company URLs (from news scraper)
        max_companies: Maximum number of companies to scrape (None = all)
        debug: Enable debug mode - keeps browser open and adds wait prompts
        headless: Run browser in headless mode
        browser_executable_path: Optional browser binary path (e.g. Brave)
        output_file: Path to output JSON file (default: auto-generated timestamped filename)
    """
    # Generate output filename if not provided
    if output_file is None:
        output_file = get_companies_output_filename()
    
    # Load existing data if file exists (for resume capability)
    all_company_data = []
    seen_company_urls = set()
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                if isinstance(existing_data, list):
                    all_company_data = existing_data
                    seen_company_urls = {
                        item.get("company_page_url") 
                        for item in existing_data 
                        if item.get("company_page_url")
                    }
                    print(f"📂 Loaded {len(all_company_data)} existing companies from {output_file}")
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠ Warning: Could not load existing data from {output_file}: {e}")
            print("  Starting fresh...")
    
    # Load company URLs from input file
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            news_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Input file not found: {input_file}")
        return all_company_data
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {input_file}: {e}")
        return all_company_data
    
    # Extract unique company URLs (skip already scraped ones)
    company_urls = []
    for item in news_data:
        company_url = item.get("company_url")
        if company_url and company_url not in seen_company_urls:
            company_urls.append(company_url)
    
    if max_companies:
        company_urls = company_urls[:max_companies]
    
    print(f"Found {len(company_urls)} new company URLs to scrape")
    if len(company_urls) == 0:
        print("✓ All companies already scraped!")
        return all_company_data
    
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
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["geolocation"],
            geolocation={"latitude": 40.7128, "longitude": -74.0060},
            color_scheme="light",
        )
        
        page = await context.new_page()
        
        try:
            # Apply stealth techniques
            await setup_stealth_browser(page)
            
            for idx, company_url in enumerate(company_urls, 1):
                print(f"\n[{idx}/{len(company_urls)}] Scraping: {company_url}")
                
                try:
                    # Navigate to company page
                    await page.goto(
                        company_url,
                        wait_until="networkidle",
                        timeout=30000
                    )
                    
                    # Human-like delay after page load
                    await human_like_delay(2000, 4000)
                    
                    # Extract company data
                    company_data = await extract_company_data_from_page(page, company_url)
                    
                    if company_data:
                        # Add the company URL to the data
                        company_data["company_page_url"] = company_url
                        all_company_data.append(company_data)
                        print(f"  ✓ Extracted: {company_data.get('company_name', 'Unknown')}")
                        print(f"    - Investors: {len(company_data.get('investors', []))}")
                        
                        # Save incrementally after each company
                        try:
                            with open(output_file, "w", encoding="utf-8") as f:
                                json.dump(all_company_data, f, indent=2, ensure_ascii=False)
                            print(f"  💾 Saved to {output_file} ({len(all_company_data)} total companies)")
                        except Exception as save_error:
                            print(f"  ⚠ Warning: Failed to save incrementally: {save_error}")
                    else:
                        print(f"  ⚠ Failed to extract data")
                    
                    # Human-like delay before next page (important to avoid flagging)
                    # Longer delay between pages to mimic human behavior
                    if idx < len(company_urls):
                        delay_ms = random.randint(3000, 6000)  # 3-6 seconds between pages
                        print(f"  Waiting {delay_ms/1000:.1f}s before next page...")
                        await asyncio.sleep(delay_ms / 1000)
                    
                except Exception as e:
                    print(f"  ❌ Error scraping {company_url}: {e}")
                    # Continue with next company
                    await human_like_delay(2000, 3000)
                    continue
            
            print(f"\n✓ Scraping complete! Total companies scraped: {len(all_company_data)}")
            print(f"📁 Final data saved to: {output_file}")
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            print(f"💾 Partial data saved to: {output_file} ({len(all_company_data)} companies)")
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
    
    return all_company_data


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Scrape startups.gallery/companies/* using Playwright")
    parser.add_argument(
        "--input",
        type=str,
        default="input/company_input.json",
        help="Path to input JSON file with company URLs (default: input/company_input.json)"
    )
    parser.add_argument(
        "--max-companies",
        type=int,
        default=None,
        help="Maximum number of companies to scrape (default: all)"
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
        "--browser-path",
        type=str,
        default=None,
        help="Optional Chromium-based browser executable path (e.g. Brave). "
        "Alternatively set env var BROWSER_EXECUTABLE_PATH. Not committed to git.",
    )
    
    args = parser.parse_args()
    
    print("Starting Playwright scraper for startups.gallery/companies/*...")
    print("Using anti-bot detection techniques...")
    print(f"Input file: {args.input}")
    print(f"Max companies: {args.max_companies if args.max_companies else 'All'}")
    print(f"Debug mode: {args.debug}")
    print(f"Headless mode: {args.headless}")
    print(
        "Browser path: "
        f"{args.browser_path or os.getenv('BROWSER_EXECUTABLE_PATH') or 'Playwright-managed Chromium'}"
    )
    
    try:
        # Generate output filename (or use provided one)
        output_file = args.output if hasattr(args, 'output') and args.output else get_companies_output_filename()
        
        companies_data = await scrape_companies(
            input_file=args.input,
            max_companies=args.max_companies,
            debug=args.debug,
            headless=args.headless,
            browser_executable_path=args.browser_path,
            output_file=output_file,
        )
        
        # Data is already saved incrementally, but print summary
        print(f"\n✓ Final summary: {len(companies_data)} total companies in {output_file}")
        
    except KeyboardInterrupt:
        print("\n⚠ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

