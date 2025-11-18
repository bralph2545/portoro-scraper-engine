#!/usr/bin/env python3
"""
CLI script to run a scrape using a site configuration file OR a quick URL.

Usage:
    # Config-based mode:
    python scripts/run_scrape.py --config configs/example_site.yaml
    python scripts/run_scrape.py --config configs/example_site.yaml --log-level DEBUG

    # Quick "paste URL" mode:
    python scripts/run_scrape.py --url https://example.com/vacation-rentals \
        --manager-name "Example Rentals" \
        --manager-domain example.com \
        --market-name "Beach City, FL"
"""

import argparse
import asyncio
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import run_scrape_from_config
from src.models import SiteConfig, IndexPageSelectors, ListingPageSelectors, CrawlSettings
from src.db import Database
from src.main import ScraperOrchestrator
from src.utils import setup_logging


async def run_quick_scrape(url: str, manager_name: str, manager_domain: str,
                           market_name: str, log_level: str = "INFO") -> int:
    """
    Run a quick scrape from a URL without requiring a config file.

    Args:
        url: Starting URL to scrape
        manager_name: Name of the property manager
        manager_domain: Domain name (e.g., "example.com")
        market_name: Geographic market (e.g., "Miami Beach, FL")
        log_level: Logging level

    Returns:
        scrape_run_id
    """
    setup_logging(level=log_level)

    # Build a SiteConfig from the provided parameters
    config = SiteConfig(
        manager_name=manager_name,
        manager_domain=manager_domain,
        market_name=market_name,
        seed_urls=[url],
        listing_url_patterns=[f"/{manager_domain}/", "/property/", "/rental/", "/vacation-rental/"],
        excluded_url_patterns=["/blog", "/about", "/contact"],
        index_page_selectors=IndexPageSelectors(),
        listing_page_selectors=ListingPageSelectors(),
        crawl_settings=CrawlSettings()
    )

    db = Database()
    orchestrator = ScraperOrchestrator(config, db)

    run_id = await orchestrator.run_scrape()

    db.close()

    return run_id


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Run a web scraping job using a config file OR quick URL mode',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Config-based mode:
  python scripts/run_scrape.py --config configs/example_site.yaml

  # Quick URL mode:
  python scripts/run_scrape.py \\
      --url https://example.com/vacation-rentals \\
      --manager-name "Example Rentals" \\
      --manager-domain example.com \\
      --market-name "Miami Beach, FL"
        """
    )

    # Config-based mode arguments
    parser.add_argument(
        '--config',
        help='Path to the YAML configuration file'
    )

    # Quick URL mode arguments
    parser.add_argument(
        '--url',
        help='Starting URL to scrape (for quick mode)'
    )

    parser.add_argument(
        '--manager-name',
        help='Property manager name (for quick mode)'
    )

    parser.add_argument(
        '--manager-domain',
        help='Manager domain, e.g., "example.com" (for quick mode)'
    )

    parser.add_argument(
        '--market-name',
        help='Geographic market, e.g., "Miami Beach, FL" (for quick mode)'
    )

    # Common arguments
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )

    args = parser.parse_args()

    # Validate arguments
    config_mode = args.config is not None
    quick_mode = args.url is not None

    if config_mode and quick_mode:
        print("Error: Cannot use both --config and --url modes simultaneously")
        sys.exit(1)

    if not config_mode and not quick_mode:
        print("Error: Must provide either --config OR --url with related arguments")
        parser.print_help()
        sys.exit(1)

    # Quick mode validation
    if quick_mode:
        if not all([args.manager_name, args.manager_domain, args.market_name]):
            print("Error: Quick mode requires --url, --manager-name, --manager-domain, and --market-name")
            sys.exit(1)

    # Execute the appropriate mode
    try:
        if config_mode:
            # Config-based mode
            config_file = Path(args.config)

            if not config_file.exists():
                print(f"Error: Config file not found: {args.config}")
                sys.exit(1)

            print(f"Starting scrape with config: {args.config}")
            print(f"Log level: {args.log_level}")
            print("-" * 60)

            run_id = asyncio.run(run_scrape_from_config(
                config_path=str(config_file),
                log_level=args.log_level
            ))

        else:
            # Quick URL mode
            print(f"Starting quick scrape")
            print(f"  URL: {args.url}")
            print(f"  Manager: {args.manager_name}")
            print(f"  Domain: {args.manager_domain}")
            print(f"  Market: {args.market_name}")
            print(f"  Log level: {args.log_level}")
            print("-" * 60)

            run_id = asyncio.run(run_quick_scrape(
                url=args.url,
                manager_name=args.manager_name,
                manager_domain=args.manager_domain,
                market_name=args.market_name,
                log_level=args.log_level
            ))

        print("-" * 60)
        print(f"✓ Scrape completed successfully!")
        print(f"Run ID: {run_id}")
        print(f"\nTo export results, run:")
        print(f"  python scripts/export_csv.py --run-id {run_id} --output output/results_{run_id}.csv")

    except KeyboardInterrupt:
        print("\n\nScrape interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n✗ Scrape failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
