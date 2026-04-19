"""
Orchestrator for scraping startups.gallery entities.

- Phase 1: scrape *index/list pages* for each entity (News / Explore / Investors / Jobs)
  and persist the canonical URLs/IDs + lightweight fields.
- Phase 2: crawl *detail pages* off the persisted URLs, with retries, idempotency, and caching.

Why:
- Faster iterations: list scraping is cheap, detail scraping can be retried independently.
- Better reliability: you can resume from a persisted queue.
- Better data quality: detail scrapers can be specialized per entity.

Right now we only implement `news` (Playwright) and leave stubs for the rest.
"""

import argparse
import asyncio


async def run_news(args: argparse.Namespace) -> None:
    # Local import so orchestrator doesn't force Playwright load for other commands
    from startups_gallery_news_playwright import scrape_news, get_news_output_filename
    import json

    data = await scrape_news(
        max_scrolls=args.max_scrolls,
        debug=args.debug,
        headless=args.headless,
        cutoff_date=args.cutoff_date,
    )

    output_file = args.output or get_news_output_filename()
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved {len(data)} news items to {output_file}")


async def run_companies(args: argparse.Namespace) -> None:
    from startups_gallery_companies_playwright import scrape_companies, get_companies_output_filename
    import json

    # Generate output filename (or use provided one)
    output_file = args.output or get_companies_output_filename()

    # Data is saved incrementally inside scrape_companies, so we just call it
    data = await scrape_companies(
        input_file=args.input,
        max_companies=args.max_companies,
        debug=args.debug,
        headless=args.headless,
        browser_executable_path=args.browser_path,
        output_file=output_file,  # Pass output file so it saves incrementally
    )

    print(f"\n✓ Final summary: {len(data)} companies in {output_file}")


async def run_investors(_: argparse.Namespace) -> None:
    raise NotImplementedError("Investors scraper not implemented yet.")


async def run_jobs(_: argparse.Namespace) -> None:
    raise NotImplementedError("Jobs scraper not implemented yet.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="orchestrate.py", description="Startups.gallery scraping orchestrator")
    sub = p.add_subparsers(dest="command", required=True)

    news = sub.add_parser("news", help="Scrape /news (funding feed)")
    news.add_argument("--max-scrolls", type=int, default=None, help="Max Load More attempts (default: no limit)")
    news.add_argument("--cutoff-date", type=str, default=None, help="Stop when funding_date <= YYYY-MM-DD")
    news.add_argument("--debug", action="store_true", help="Pause for debugging and keep browser open longer")
    news.add_argument("--headless", action="store_true", help="Run headless")
    news.add_argument("--output", type=str, default=None, help="Output JSON path (default: timestamped)")
    news.set_defaults(func=run_news)

    companies = sub.add_parser("companies", help="Scrape company detail pages from input file")
    companies.add_argument("--input", type=str, default="input/company_input.json", help="Input JSON with company URLs")
    companies.add_argument("--max-companies", type=int, default=None, help="Max companies to scrape (default: all)")
    companies.add_argument("--debug", action="store_true", help="Pause for debugging and keep browser open longer")
    companies.add_argument("--headless", action="store_true", help="Run headless")
    companies.add_argument("--browser-path", type=str, default=None, help="Browser executable path (or BROWSER_EXECUTABLE_PATH env var)")
    companies.add_argument("--output", type=str, default=None, help="Output JSON path (default: timestamped)")
    companies.set_defaults(func=run_companies)

    investors = sub.add_parser("investors", help="Scrape Investors [TODO]")
    investors.set_defaults(func=run_investors)

    jobs = sub.add_parser("jobs", help="Scrape Jobs [TODO]")
    jobs.set_defaults(func=run_jobs)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(args.func(args))


if __name__ == "__main__":
    main()


