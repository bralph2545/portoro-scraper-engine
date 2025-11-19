#!/usr/bin/env python3
"""
Universal Property Scraper - Extract property data from ANY vacation rental website.

This tool:
1. Accepts a "all rentals" index page URL
2. Discovers all individual property listing URLs
3. Uses OpenAI to intelligently extract property data from each listing
4. Works on ANY vacation rental website without custom configuration

Usage:
    python scripts/universal_property_scraper.py \
        --url "https://www.example.com/vacation-rentals" \
        --company "Example Rentals" \
        --output properties.json

    # With OpenAI API key
    export OPENAI_API_KEY="sk-..."
    python scripts/universal_property_scraper.py \
        --url "https://www.30aescapes.com/all-rentals" \
        --company "30A Escapes" \
        --output 30a_properties.json \
        --format json
"""

import argparse
import asyncio
import json
import csv
import sys
import os
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crawler import Crawler
from src.llm_extractor import LLMPropertyExtractor
from src.models import SiteConfig, CrawlSettings
from src.utils import setup_logging, is_likely_listing_url

logger = None


async def discover_property_urls(index_url: str, company_domain: str) -> list:
    """
    Discover all property listing URLs from an index page.

    Args:
        index_url: URL of the "all rentals" or main listings page
        company_domain: Domain of the company (e.g., "30aescapes.com")

    Returns:
        List of discovered property listing URLs
    """
    logger.info(f"Discovering property listings from: {index_url}")

    # Create minimal config for crawler
    config = SiteConfig(
        manager_name="temp",
        manager_domain=company_domain,
        market_name="Unknown",
        seed_urls=[index_url],
        listing_url_patterns=["/property/", "/rental/", "/vacation-rental/", "/unit/"],
        excluded_url_patterns=["/blog", "/about", "/contact", "/cart", "/checkout", "/search"],
        crawl_settings=CrawlSettings(
            max_concurrency=2,
            min_delay_ms=1000,
            scroll_attempts=3,
            max_depth=2
        )
    )

    crawler = Crawler(config)
    listing_urls = await crawler.discover_listing_urls()

    logger.info(f"Discovered {len(listing_urls)} potential property listings")

    return listing_urls


async def extract_property_data(urls: list, company_name: str,
                                api_key: str = None, model: str = "gpt-4o-mini") -> list:
    """
    Extract property data from all discovered URLs using OpenAI.

    Args:
        urls: List of property listing URLs
        company_name: Name of the property management company
        api_key: OpenAI API key
        model: OpenAI model to use

    Returns:
        List of extracted property data dictionaries
    """
    logger.info(f"Extracting property data from {len(urls)} listings using {model}")

    extractor = LLMPropertyExtractor(api_key=api_key, model=model)

    properties = []
    crawler = Crawler(SiteConfig(
        manager_name=company_name,
        manager_domain=urlparse(urls[0]).netloc if urls else "",
        market_name="Unknown",
        seed_urls=[],
        crawl_settings=CrawlSettings(min_delay_ms=1000)
    ))

    await crawler.start()

    try:
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing {i}/{len(urls)}: {url}")

            try:
                # Fetch the property page
                html_content, success = await crawler.fetch_page_content(url)

                if not success:
                    logger.warning(f"Failed to fetch {url}")
                    continue

                # Extract property data using LLM
                property_data = extractor.extract_property_data(
                    html_content=html_content,
                    url=url,
                    company_name=company_name
                )

                # Add timestamp
                property_data['extracted_at'] = datetime.now().isoformat()

                properties.append(property_data)

                logger.info(f"  ✓ Extracted: {property_data.get('property_name', 'Unknown')}")

            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
                properties.append({
                    'listing_url': url,
                    'error': str(e),
                    'property_management_company': company_name
                })

    finally:
        await crawler.close()

    logger.info(f"Extraction complete: {len(properties)} properties processed")

    return properties


def save_to_json(properties: list, output_path: str):
    """Save properties to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(properties, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(properties)} properties to JSON: {output_path}")


def save_to_csv(properties: list, output_path: str):
    """Save properties to CSV file."""
    if not properties:
        logger.warning("No properties to save")
        return

    # Define field order
    fieldnames = [
        'property_management_company',
        'property_name',
        'listing_url',
        'street_address',
        'city',
        'state',
        'zip_code',
        'country',
        'bedrooms',
        'bathrooms',
        'sleeps',
        'nightly_rate_min',
        'nightly_rate_max',
        'property_id',
        'description',
        'confidence',
        'extraction_method',
        'model_used',
        'extracted_at'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for prop in properties:
            # Convert amenities list to string
            if 'amenities' in prop and isinstance(prop['amenities'], list):
                prop['amenities_count'] = len(prop['amenities'])
                # Don't write amenities to CSV (too large), use JSON for that

            writer.writerow(prop)

    logger.info(f"Saved {len(properties)} properties to CSV: {output_path}")


async def main_async(args):
    """Main async function."""
    global logger
    setup_logging(level=args.log_level)
    logger = __import__('logging').getLogger(__name__)

    # Validate OpenAI API key
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: OpenAI API key required!")
        print("Set OPENAI_API_KEY environment variable or use --api-key argument")
        sys.exit(1)

    # Extract domain from URL
    domain = urlparse(args.url).netloc.replace('www.', '')

    print(f"\n{'='*70}")
    print(f"UNIVERSAL PROPERTY SCRAPER")
    print(f"{'='*70}")
    print(f"Company: {args.company}")
    print(f"URL: {args.url}")
    print(f"Domain: {domain}")
    print(f"Model: {args.model}")
    print(f"Output: {args.output}")
    print(f"{'='*70}\n")

    # Step 1: Discover property URLs
    print("STEP 1: Discovering property listing URLs...")
    property_urls = await discover_property_urls(args.url, domain)

    if not property_urls:
        print("ERROR: No property listings discovered!")
        print("This might mean:")
        print("  - The URL is not an index/listings page")
        print("  - The site uses unusual URL patterns")
        print("  - Network/access issues")
        sys.exit(1)

    print(f"✓ Found {len(property_urls)} property listings\n")

    # Limit if requested
    if args.limit and args.limit < len(property_urls):
        print(f"Limiting to first {args.limit} properties")
        property_urls = property_urls[:args.limit]

    # Step 2: Extract property data using OpenAI
    print(f"STEP 2: Extracting property data using {args.model}...")
    print(f"This will make {len(property_urls)} API calls to OpenAI")
    print(f"Estimated cost: ${len(property_urls) * 0.001:.2f} - ${len(property_urls) * 0.01:.2f}\n")

    if not args.yes:
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled")
            sys.exit(0)

    properties = await extract_property_data(
        urls=property_urls,
        company_name=args.company,
        api_key=api_key,
        model=args.model
    )

    # Step 3: Save results
    print(f"\nSTEP 3: Saving results...")

    if args.format == 'json':
        save_to_json(properties, args.output)
    elif args.format == 'csv':
        save_to_csv(properties, args.output)
    else:  # both
        json_path = args.output.replace('.csv', '.json')
        csv_path = args.output.replace('.json', '.csv')
        save_to_json(properties, json_path)
        save_to_csv(properties, csv_path)

    # Print summary
    print(f"\n{'='*70}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"Total properties: {len(properties)}")
    print(f"Successful extractions: {sum(1 for p in properties if p.get('confidence', 0) > 0)}")
    print(f"Errors: {sum(1 for p in properties if 'error' in p)}")
    print(f"Output: {args.output}")
    print(f"{'='*70}\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Universal property scraper for ANY vacation rental website',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with environment variable for API key
  export OPENAI_API_KEY="sk-..."
  python scripts/universal_property_scraper.py \\
      --url "https://www.30aescapes.com/all-rentals" \\
      --company "30A Escapes" \\
      --output 30a_properties.json

  # Limit to first 10 properties for testing
  python scripts/universal_property_scraper.py \\
      --url "https://www.example.com/rentals" \\
      --company "Example Rentals" \\
      --output test.json \\
      --limit 10

  # Save as CSV instead of JSON
  python scripts/universal_property_scraper.py \\
      --url "https://www.example.com/rentals" \\
      --company "Example Rentals" \\
      --output properties.csv \\
      --format csv
        """
    )

    parser.add_argument(
        '--url',
        required=True,
        help='URL of the main rentals/listings page'
    )

    parser.add_argument(
        '--company',
        required=True,
        help='Property management company name'
    )

    parser.add_argument(
        '--output',
        required=True,
        help='Output file path (JSON or CSV)'
    )

    parser.add_argument(
        '--api-key',
        help='OpenAI API key (or set OPENAI_API_KEY env var)'
    )

    parser.add_argument(
        '--model',
        default='gpt-4o-mini',
        help='OpenAI model to use (default: gpt-4o-mini)'
    )

    parser.add_argument(
        '--format',
        choices=['json', 'csv', 'both'],
        default='json',
        help='Output format (default: json)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of properties to process (for testing)'
    )

    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt'
    )

    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )

    args = parser.parse_args()

    try:
        asyncio.run(main_async(args))

    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
