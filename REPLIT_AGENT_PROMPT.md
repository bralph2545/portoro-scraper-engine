# REPLIT AGENT SETUP PROMPT

Copy and paste this entire prompt to the Replit Agent to set up and run the vacation rental scraper:

---

I need you to help me set up and run a vacation rental property address scraper. This tool will scrape 26 competitor websites to extract property addresses for my vacation rental business in Destin/30A, Florida.

## PROJECT OVERVIEW

This is a production-grade web scraper that:
- Uses Playwright (real browser) to handle JavaScript-heavy websites
- Discovers all rental listing URLs from index pages (handles pagination, infinite scroll, "Load More" buttons)
- Extracts addresses using multiple strategies (JSON-LD, CSS selectors, regex patterns, map widgets)
- Normalizes addresses into structured components (street, city, state, zip)
- Stores everything in SQLite database
- Exports clean CSV files with one row per property

## STEP 1: INSTALL DEPENDENCIES

Run these commands in the Replit shell:

```bash
# Install Python packages
pip install playwright beautifulsoup4 pyyaml lxml python-dateutil

# Install Playwright browser (IMPORTANT - this downloads Chromium)
playwright install chromium
```

## STEP 2: VERIFY THE PROJECT STRUCTURE

The project should have this structure:

```
portoro-scraper-engine/
├── src/                    # Core scraping logic
│   ├── main.py            # Orchestrator
│   ├── crawler.py         # Playwright-based crawler
│   ├── extractor.py       # Address extraction
│   ├── normalizer.py      # Address normalization
│   ├── db.py              # SQLite database
│   ├── config.py          # Config loader
│   ├── models.py          # Data models
│   └── utils.py           # Utilities
├── scripts/
│   ├── run_scrape.py              # Main scraping script
│   ├── export_csv.py              # CSV export
│   └── batch_scrape_competitors.py # NEW: Batch scraper for all 26 competitors
├── configs/
│   ├── competitors_list.csv       # NEW: List of 26 competitors
│   ├── example_site.yaml
│   └── test_30aescapes.yaml
├── data/                  # SQLite database (created on first run)
├── output/                # CSV exports
├── requirements.txt
├── pyproject.toml
└── README.md
```

## STEP 3: TEST WITH A SINGLE COMPETITOR

Before scraping all 26 competitors, test with one site:

```bash
python scripts/run_scrape.py \
    --url https://www.30aescapes.com/all-rentals \
    --manager-name "30A Escapes" \
    --manager-domain 30aescapes.com \
    --market-name "30A / Destin, FL" \
    --log-level INFO
```

This will output a Run ID (e.g., "Run ID: 1").

Export the results:

```bash
python scripts/export_csv.py --run-id 1 --output output/test_30a_escapes.csv
```

Check the `output/` folder for the CSV file.

## STEP 4: BATCH SCRAPE ALL 26 COMPETITORS

⚠️ **IMPORTANT NETWORK LIMITATION**:

Replit's environment blocks headless browser access to external HTTPS sites (you'll see `ERR_TUNNEL_CONNECTION_FAILED` errors). This is a Replit network security restriction.

**SOLUTIONS**:
1. **Run locally** - Download the zip file and run on your local machine
2. **Use GitHub Codespaces** - Better network access than Replit
3. **Deploy to a VPS** - DigitalOcean, AWS, Linode, etc.

If you want to try anyway on Replit (it likely won't work for external sites):

```bash
# Scrape all 26 competitors with 60-second delay between each
python scripts/batch_scrape_competitors.py \
    --input configs/competitors_list.csv \
    --delay 60 \
    --log-level INFO
```

The batch scraper will:
- Process all 26 competitors one by one
- Wait 60 seconds between each scrape (to be polite to servers)
- Store each scrape in the database with a unique Run ID
- Print a summary at the end with all Run IDs

## STEP 5: EXPORT ALL RESULTS

After the batch scrape completes, it will print export commands for each successful scrape.

Example:
```bash
python scripts/export_csv.py --run-id 1 --output output/30a_escapes.csv
python scripts/export_csv.py --run-id 2 --output output/pelican_beach.csv
# ... etc for all 26
```

Or create a master export script that combines all runs.

## STEP 6: DOWNLOAD THE RESULTS

1. Go to the Replit Files panel
2. Navigate to the `output/` folder
3. Download each CSV file
4. Or compress all CSVs: `zip -r all_addresses.zip output/*.csv`

## THE 26 COMPETITORS TO SCRAPE

The scraper will process these companies (all in `configs/competitors_list.csv`):

1. Pelican Beach Management
2. Destin West Vacations
3. Beach Condos in Destin
4. Dune Allen Realty Vacation Rentals
5. Ocean Reef Vacation Rentals & Real Estate
6. Mara Lee Vacation Rentals
7. Holiday Isle Properties
8. Kimberly Lang Vacation Rental Properties
9. Sea Star Vacations
10. Sunset Resort Rentals
11. Forever Destin Beach Rentals
12. Oversee
13. Brooks and Shorey Resorts
14. 30A Escapes
15. 360 Blue
16. Benchmark Management
17. Scenic Stays
18. RealJoy Vacations
19. Destin Dreamers
20. Five Star Properties
21. Gibson Beach Rentals
22. Harmony Beach Vacations
23. Panhandle Getaways
24. Beach Blue Properties
25. Dune Vacation Rentals
26. Gulf Tide Vacations

## EXPECTED OUTPUT

Each CSV export will have these columns:
- `manager_name` - Company name
- `manager_domain` - Website domain
- `market_name` - Geographic market
- `listing_url` - URL of the property listing
- `address_line1` - Street address
- `address_line2` - Apartment/unit number (if any)
- `city` - City name
- `state` - State abbreviation
- `postal_code` - ZIP code
- `country` - Country (default: USA)
- `confidence_score` - How confident the parser is (0.0-1.0)
- `inference_method` - How the address was extracted

## TROUBLESHOOTING

**"Module not found" errors?**
```bash
pip install -r requirements.txt
playwright install chromium
```

**"ERR_TUNNEL_CONNECTION_FAILED" errors?**
- This is Replit's network restriction
- Download the project and run locally instead
- Or use GitHub Codespaces, a VPS, or your own computer

**"No addresses extracted"?**
- Some sites might not have addresses visible on listing pages
- Some sites might be JavaScript-heavy and need custom selectors
- Check the database to see if listings were discovered but addresses weren't found
- Use `--log-level DEBUG` to see detailed extraction attempts

**Want to customize extraction for a specific site?**
- Create a YAML config file in `configs/` (see `example_site.yaml`)
- Add custom CSS selectors for that site's specific HTML structure
- Use config mode: `python scripts/run_scrape.py --config configs/custom_site.yaml`

## ALTERNATIVE: RUN LOCALLY (RECOMMENDED)

Since Replit has network limitations, the recommended approach is:

1. **Download the zip file** from this Repl
2. **Extract on your local machine**
3. **Install dependencies**: `pip install -r requirements.txt && playwright install chromium`
4. **Run the batch scraper**: `python scripts/batch_scrape_competitors.py --input configs/competitors_list.csv --delay 60`
5. **Wait** - This will take ~30 minutes (26 sites × 60 seconds + scrape time)
6. **Export all CSVs** - The script will print the commands

## QUESTIONS OR ISSUES?

Check these files for detailed documentation:
- `README.md` - Full project documentation
- `README.replit.md` - Replit-specific quick start
- `src/*.py` - Inline code documentation

---

## SUMMARY FOR REPLIT AGENT

Please help me:
1. Verify all files are in place
2. Install dependencies (`pip install -r requirements.txt && playwright install chromium`)
3. Test with one site first
4. Explain the Replit network limitation and recommend running locally
5. Show me how to download the project as a zip if needed
6. If possible on Replit, run the batch scraper for all 26 competitors
7. Export all results to CSV files in the `output/` folder

Thank you!
