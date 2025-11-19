# 🏖️ Universal Vacation Rental Property Scraper

A smart web scraper that extracts **complete property data** from ANY vacation rental website - no coding required!

## 🚀 Two Ways to Use This Tool

### Option 1: Web App (Recommended - No Coding!) ⭐

Deploy to Railway.app and use a simple web form:
- ✅ **No terminal or Python needed** - just a web browser
- ✅ **Works on ANY vacation rental website** - paste any URL
- ✅ **Password protected** with scrape history
- ✅ **Download JSON/CSV** results with one click
- ✅ **Free hosting** (Railway free tier)

👉 **[See Web App Deployment Guide](RAILWAY_DEPLOYMENT.md)**
👉 **[See User Guide](USER_GUIDE.md)**

### Option 2: Command Line (Advanced Users)

Use the CLI tool for batch processing or automation:
- Run from terminal with `python scripts/universal_property_scraper.py`
- Works locally, on VPS, or GitHub Codespaces
- Great for scheduled scraping or processing multiple sites

👉 **[See CLI Deployment Guide](DEPLOYMENT_GUIDE.md)**

---

## What This Tool Does

**Input:** Any vacation rental website URL (e.g., `https://www.30aescapes.com/all-rentals`)

**Process:**
1. Discovers ALL individual property listings from that page
2. Visits each property page
3. Uses OpenAI to intelligently extract complete property data
4. Works on ANY website structure - no configuration needed

**Output:** JSON or CSV with complete property information:
- Property management company
- Property name
- **Full address** (street, city, state, ZIP, country)
- Bedrooms, bathrooms, sleeps
- Nightly rate range
- Amenities list
- Description
- Property ID
- Confidence score

---

## Features

- **Universal**: Works on ANY vacation rental website without custom configs
- **AI-Powered**: Uses OpenAI GPT-4o-mini for intelligent data extraction
- **Complete Data**: Extracts full property details, not just addresses
- **Real Browser**: Uses Playwright for JavaScript-heavy sites
- **Smart Discovery**: Handles pagination, infinite scroll, and "Load More" buttons
- **No Coding Required**: Web interface for non-technical users
- **History Tracking**: Saves all past scrapes with download links
- **Password Protected**: Secure access to your scraper
- **JSON & CSV Export**: Choose your preferred format

---

## 🎯 Quick Start (Web App)

**For non-technical users - get started in 5 minutes:**

1. **Deploy to Railway** - Follow [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)
2. **Set your OpenAI API key** in Railway environment variables
3. **Set a password** for your scraper
4. **Open your Railway URL** and log in
5. **Paste any vacation rental URL** and click "Start Scraping"
6. **Download JSON/CSV** when complete

**That's it!** No coding, no terminal, no complexity.

👉 **[Full User Guide](USER_GUIDE.md)**

---

## 💰 Costs

### Railway Hosting (Free Tier)
- **$5 free credits/month**
- **500 hours execution time**
- More than enough for typical use
- No credit card required initially

### OpenAI API
- **~$0.01 - $0.10 per property** (using gpt-4o-mini)
- 10 properties = $0.10
- 100 properties = $1.00
- Very affordable!

**Total estimated cost:** $1-10/month for typical use

---

## 📚 Documentation

- **[Railway Deployment Guide](RAILWAY_DEPLOYMENT.md)** - Deploy the web app (5 minutes)
- **[User Guide](USER_GUIDE.md)** - How to use the web interface
- **[CLI Deployment Guide](DEPLOYMENT_GUIDE.md)** - Advanced deployment options
- **[Universal Scraper Guide](UNIVERSAL_SCRAPER_GUIDE.md)** - CLI tool documentation

---

## Architecture

```
┌─────────────┐
│   Config    │ YAML configuration for each site
└──────┬──────┘
       │
┌──────▼──────────┐
│   Crawler       │ Playwright-based discovery
│  (crawler.py)   │ - Infinite scroll
│                 │ - Pagination
│                 │ - Load More buttons
└──────┬──────────┘
       │
┌──────▼──────────┐
│  Classifier     │ Identify listing pages
│ (extractor.py)  │ - Keyword heuristics
└──────┬──────────┘
       │
┌──────▼──────────┐
│   Extractor     │ Multi-strategy address extraction
│ (extractor.py)  │ - schema.org JSON-LD
│                 │ - CSS selectors
│                 │ - Text patterns
│                 │ - Map widgets
└──────┬──────────┘
       │
┌──────▼──────────┐
│  Normalizer     │ Parse and enrich addresses
│(normalizer.py)  │ - Component parsing
│                 │ - Context enrichment
│                 │ - LLM stub (optional)
└──────┬──────────┘
       │
┌──────▼──────────┐
│   Database      │ SQLite storage
│   (db.py)       │ - sites
│                 │ - scrape_runs
│                 │ - listing_pages
│                 │ - addresses
└──────┬──────────┘
       │
┌──────▼──────────┐
│  CSV Export     │ Clean output
└─────────────────┘
```

## Installation

### On Replit

The environment is already configured! Just run:

```bash
python scripts/run_scrape.py --config configs/example_site.yaml
```

### On Local Machine

```bash
# Install Python dependencies
pip install playwright beautifulsoup4 pyyaml lxml python-dateutil

# Install Playwright browsers
playwright install chromium

# Run a scrape
python scripts/run_scrape.py --config configs/example_site.yaml
```

## Usage

### 1. Run a Scrape

#### Option A: Config-Based Mode (Recommended)

Create a YAML config file and run:

```bash
python scripts/run_scrape.py --config configs/example_site.yaml
```

#### Option B: Quick "Paste URL" Mode

No config file needed - just provide the URL and basic info:

```bash
python scripts/run_scrape.py \
    --url https://example.com/vacation-rentals \
    --manager-name "Example Rentals" \
    --manager-domain example.com \
    --market-name "Miami Beach, FL"
```

Both modes will:
- Discover all listing pages from the seed URLs
- Classify pages as listings or non-listings
- Extract address candidates using multiple strategies
- Normalize and enrich addresses
- Store everything in the SQLite database

### 2. Export Results to CSV

```bash
python scripts/export_csv.py --run-id 1 --output output/my_results.csv
```

Or use the auto-generated filename:

```bash
python scripts/export_csv.py --run-id 1
```

### 3. View Results

The CSV will contain:
- manager_name
- manager_domain
- market_name
- listing_url
- address_line1, address_line2
- city, state, postal_code, country
- confidence_score
- inference_method

## Adding a New Site

Create a new YAML config file in `configs/`:

```yaml
# configs/my_new_site.yaml

manager_name: "Beach Rentals Inc"
manager_domain: "beachrentals.com"
market_name: "Miami Beach"

seed_urls:
  - "https://www.beachrentals.com/properties"

listing_url_patterns:
  - "/properties/"
  - "/rental/"

listing_page_selectors:
  address_container_selectors:
    - ".property-location"
    - ".address"

crawl_settings:
  max_concurrency: 3
  min_delay_ms: 500
```

Then run:

```bash
python scripts/run_scrape.py --config configs/my_new_site.yaml
```

## Configuration Reference

### Required Fields

- `manager_name`: Name of the property manager
- `manager_domain`: Domain name (e.g., "example.com")
- `market_name`: Geographic market (e.g., "Destin / 30A")
- `seed_urls`: List of starting URLs for crawling

### Optional Fields

- `sitemap_urls`: List of sitemap URLs
- `property_directory_urls`: Additional directory pages
- `listing_url_patterns`: Patterns to identify listing URLs
- `excluded_url_patterns`: Patterns to exclude from crawling
- `index_page_selectors`: CSS selectors for index pages
- `listing_page_selectors`: CSS selectors for listing pages
- `crawl_settings`: Crawler behavior configuration

## Database Schema

### Tables

- **sites**: Manager/site information
- **scrape_runs**: Metadata for each scrape run
- **listing_pages**: Discovered listing pages with classification
- **address_candidates**: Raw extracted addresses
- **addresses**: Normalized and enriched addresses

## Extending the System

### Adding LLM Integration

The normalizer includes a stub for LLM-based address enrichment. To integrate:

1. Install your LLM client library (openai, anthropic, etc.)
2. Edit `src/normalizer.py` - replace `_llm_enrich_stub()` method
3. Add API key via environment variable

Example OpenAI integration:

```python
import openai

def _llm_enrich_stub(self, parsed, address_raw, url):
    prompt = f"Complete this address: {address_raw}\nMarket: {self.config.market_name}"
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Parse and return enriched address
```

### Adding Geocoding

Integrate a geocoding API in `normalizer.py` to validate addresses and get coordinates.

## Logging

Control log verbosity:

```bash
# Default: INFO level
python scripts/run_scrape.py --config configs/example_site.yaml

# Debug mode
python scripts/run_scrape.py --config configs/example_site.yaml --log-level DEBUG

# Minimal output
python scripts/run_scrape.py --config configs/example_site.yaml --log-level WARNING
```

## Troubleshooting

### Playwright Errors

If you see browser launch errors:

```bash
playwright install chromium
playwright install-deps  # Linux only, requires sudo
```

### No Listings Found

1. Check the `listing_url_patterns` in your config
2. Enable DEBUG logging to see discovered URLs
3. Verify the site isn't blocking automated access

### Incomplete Addresses

1. Add more specific `address_container_selectors`
2. Check if addresses are in schema.org JSON-LD
3. Implement LLM enrichment for better inference

## Project Structure

```
.
├── src/
│   ├── __init__.py
│   ├── main.py          # Orchestrator
│   ├── config.py        # Config loader
│   ├── crawler.py       # Playwright crawler
│   ├── extractor.py     # Page classification & extraction
│   ├── normalizer.py    # Address normalization
│   ├── db.py            # Database schema
│   ├── models.py        # Data models
│   └── utils.py         # Utilities
├── scripts/
│   ├── run_scrape.py    # CLI to run scrapes
│   └── export_csv.py    # CLI to export CSVs
├── configs/
│   └── example_site.yaml
├── data/
│   └── scraper.db       # SQLite database (created on first run)
├── output/
│   └── *.csv            # Exported results
└── README.md
```

## License

MIT License - feel free to use and modify for your needs.

## Support

For questions or issues, please refer to the inline documentation in the source code.
