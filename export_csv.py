#!/usr/bin/env python3
"""
CLI script to export scrape results to CSV.

Usage:
    python scripts/export_csv.py --run-id 1 --output output/results.csv
    python scripts/export_csv.py --run-id 1
"""

import argparse
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import Database


def export_to_csv(run_id: int, output_path: str = None):
    """
    Export scrape run results to CSV.
    
    Args:
        run_id: Scrape run ID
        output_path: Output CSV file path
    """
    if not output_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"output/scrape_run_{run_id}_{timestamp}.csv"
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    db = Database()
    
    try:
        results = db.get_scrape_run_results(run_id)
        
        if not results:
            print(f"No results found for run ID: {run_id}")
            return
        
        fieldnames = [
            'manager_name',
            'manager_domain',
            'market_name',
            'listing_url',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'postal_code',
            'country',
            'confidence_score',
            'inference_method',
            'inferred_market',
            'source_page_url',
            'first_seen_at',
            'last_seen_at'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in results:
                filtered_row = {k: v for k, v in row.items() if k in fieldnames}
                writer.writerow(filtered_row)
        
        print(f"✓ Exported {len(results)} records to: {output_path}")
        
    finally:
        db.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Export scrape run results to CSV'
    )
    
    parser.add_argument(
        '--run-id',
        type=int,
        required=True,
        help='Scrape run ID to export'
    )
    
    parser.add_argument(
        '--output',
        help='Output CSV file path (default: output/scrape_run_<id>_<timestamp>.csv)'
    )
    
    args = parser.parse_args()
    
    print(f"Exporting run ID: {args.run_id}")
    
    try:
        export_to_csv(args.run_id, args.output)
    
    except Exception as e:
        print(f"✗ Export failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
