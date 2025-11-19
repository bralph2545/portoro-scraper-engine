#!/usr/bin/env python3
"""
Batch scrape all competitors from a CSV file.

Usage:
    python scripts/batch_scrape_competitors.py --input configs/competitors_list.csv
    python scripts/batch_scrape_competitors.py --input configs/competitors_list.csv --delay 60
"""

import argparse
import asyncio
import csv
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import SiteConfig, IndexPageSelectors, ListingPageSelectors, CrawlSettings
from src.db import Database
from src.main import ScraperOrchestrator
from src.utils import setup_logging


async def scrape_single_competitor(company: str, website: str, rentals_url: str,
                                   log_level: str = "INFO") -> int:
    """
    Scrape a single competitor's website.

    Args:
        company: Company name
        website: Main website URL
        rentals_url: All rentals page URL
        log_level: Logging level

    Returns:
        scrape_run_id
    """
    # Extract domain from website
    domain = urlparse(website).netloc.replace('www.', '')

    # Infer market from URL or use generic
    market_name = "Destin / 30A, FL"  # Default for this region

    print(f"\n{'='*70}")
    print(f"Starting scrape: {company}")
    print(f"  Website: {website}")
    print(f"  Rentals URL: {rentals_url}")
    print(f"{'='*70}\n")

    # Build config
    config = SiteConfig(
        manager_name=company,
        manager_domain=domain,
        market_name=market_name,
        seed_urls=[rentals_url],
        listing_url_patterns=["/vacation-rental", "/property/", "/rental/", "/unit/"],
        excluded_url_patterns=["/blog", "/about", "/contact", "/cart", "/checkout"],
        index_page_selectors=IndexPageSelectors(),
        listing_page_selectors=ListingPageSelectors(
            address_container_selectors=[
                ".property-address",
                ".address",
                "[itemprop='address']",
                ".location-info"
            ]
        ),
        crawl_settings=CrawlSettings(
            max_concurrency=2,  # Be polite
            min_delay_ms=1000,  # 1 second between requests
            scroll_attempts=3,
            max_depth=3
        )
    )

    db = Database()
    orchestrator = ScraperOrchestrator(config, db)

    try:
        run_id = await orchestrator.run_scrape()
        print(f"\n✓ {company} completed successfully - Run ID: {run_id}\n")
        return run_id
    except Exception as e:
        print(f"\n✗ {company} failed: {str(e)}\n")
        return None
    finally:
        db.close()


async def batch_scrape_all(csv_path: str, delay_seconds: int = 30,
                           log_level: str = "INFO", skip_first: int = 0):
    """
    Scrape all competitors from CSV file.

    Args:
        csv_path: Path to CSV file with competitor data
        delay_seconds: Delay between scrapes (to be polite)
        log_level: Logging level
        skip_first: Number of competitors to skip (for resuming)
    """
    setup_logging(level=log_level)

    # Read CSV
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        competitors = list(reader)

    total = len(competitors)
    results = []

    print(f"\n{'='*70}")
    print(f"BATCH SCRAPING {total} COMPETITORS")
    print(f"Delay between scrapes: {delay_seconds} seconds")
    print(f"Starting from competitor #{skip_first + 1}")
    print(f"{'='*70}\n")

    for i, row in enumerate(competitors, 1):
        if i <= skip_first:
            print(f"Skipping {i}/{total}: {row['Company']}")
            continue

        company = row['Company']
        website = row['Website']
        rentals_url = row['All_Rentals_Page']

        print(f"\n[{i}/{total}] Processing: {company}")

        try:
            run_id = await scrape_single_competitor(
                company=company,
                website=website,
                rentals_url=rentals_url,
                log_level=log_level
            )

            results.append({
                'company': company,
                'run_id': run_id,
                'status': 'success' if run_id else 'failed'
            })

        except Exception as e:
            print(f"ERROR scraping {company}: {str(e)}")
            results.append({
                'company': company,
                'run_id': None,
                'status': 'error'
            })

        # Delay between scrapes (unless it's the last one)
        if i < total:
            print(f"\nWaiting {delay_seconds} seconds before next scrape...")
            time.sleep(delay_seconds)

    # Summary
    print(f"\n{'='*70}")
    print("BATCH SCRAPING COMPLETE")
    print(f"{'='*70}\n")

    successful = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] != 'success')

    print(f"Total: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}\n")

    print("Run IDs for successful scrapes:")
    for r in results:
        if r['run_id']:
            print(f"  - {r['company']}: Run ID {r['run_id']}")

    print("\nTo export all results:")
    for r in results:
        if r['run_id']:
            safe_name = r['company'].lower().replace(' ', '_').replace('&', 'and')
            print(f"python scripts/export_csv.py --run-id {r['run_id']} --output output/{safe_name}.csv")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Batch scrape multiple competitors from a CSV file'
    )

    parser.add_argument(
        '--input',
        required=True,
        help='Path to CSV file with columns: Company, Website, All_Rentals_Page'
    )

    parser.add_argument(
        '--delay',
        type=int,
        default=30,
        help='Delay in seconds between scrapes (default: 30)'
    )

    parser.add_argument(
        '--skip-first',
        type=int,
        default=0,
        help='Skip the first N competitors (useful for resuming)'
    )

    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )

    args = parser.parse_args()

    csv_file = Path(args.input)

    if not csv_file.exists():
        print(f"Error: CSV file not found: {args.input}")
        sys.exit(1)

    try:
        asyncio.run(batch_scrape_all(
            csv_path=str(csv_file),
            delay_seconds=args.delay,
            log_level=args.log_level,
            skip_first=args.skip_first
        ))

    except KeyboardInterrupt:
        print("\n\nBatch scraping interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n✗ Batch scraping failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
