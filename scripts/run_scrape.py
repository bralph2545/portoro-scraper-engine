#!/usr/bin/env python3
"""
CLI script to run a scrape using a site configuration file.

Usage:
    python scripts/run_scrape.py --config configs/example_site.yaml
    python scripts/run_scrape.py --config configs/example_site.yaml --log-level DEBUG
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import run_scrape_from_config


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Run a web scraping job using a site configuration file'
    )
    
    parser.add_argument(
        '--config',
        required=True,
        help='Path to the YAML configuration file'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    config_file = Path(args.config)
    
    if not config_file.exists():
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)
    
    print(f"Starting scrape with config: {args.config}")
    print(f"Log level: {args.log_level}")
    print("-" * 60)
    
    try:
        run_id = asyncio.run(run_scrape_from_config(
            config_path=str(config_file),
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
        sys.exit(1)


if __name__ == '__main__':
    main()
