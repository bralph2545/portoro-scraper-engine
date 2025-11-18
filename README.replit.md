# 🏖️ Vacation Rental Address Scraper - Replit Quick Start

Welcome! This tool scrapes vacation rental websites to extract property addresses.

## 🚀 Quick Start (2 minutes)

### First Time Setup

1. **Install Playwright browsers** (one-time only):
   ```bash
   playwright install chromium
   ```

2. **Test the scraper** with a quick URL:
   ```bash
   python scripts/run_scrape.py \
       --url https://www.30aescapes.com/search/for-rent \
       --manager-name "30A Escapes" \
       --manager-domain 30aescapes.com \
       --market-name "30A / Destin, FL"
   ```

3. **Export your results**:
   ```bash
   python scripts/export_csv.py --run-id 1 --output output/my_results.csv
   ```

4. **View the CSV** - Check the `output/` folder!

## 📋 Two Ways to Use This Tool

### Option A: Quick "Paste URL" Mode ⚡
Perfect for one-off scrapes - no config file needed!

```bash
python scripts/run_scrape.py \
    --url https://example.com/vacation-rentals \
    --manager-name "Manager Name" \
    --manager-domain example.com \
    --market-name "City, State"
```

### Option B: Config File Mode 📝
Better for repeated scraping - create a YAML config:

```bash
# Edit configs/my_site.yaml first, then:
python scripts/run_scrape.py --config configs/my_site.yaml
```

See `configs/example_site.yaml` for a template.

## 📊 What You'll Get

The scraper will:
- ✅ Discover all listing pages (handles pagination, infinite scroll)
- ✅ Extract addresses using multiple strategies (JSON-LD, selectors, patterns)
- ✅ Normalize addresses into structured fields (street, city, state, zip)
- ✅ Export clean CSV with one row per property

## 🗄️ Database

All data is stored in `data/scraper.db` (SQLite). You can:
- Run multiple scrapes (each gets a unique run ID)
- Export any previous scrape using its run ID
- Keep full history of all scraping sessions

## 🛠️ Useful Commands

```bash
# See all options
python scripts/run_scrape.py --help

# Debug mode (verbose logging)
python scripts/run_scrape.py --config configs/my_site.yaml --log-level DEBUG

# Export with custom filename
python scripts/export_csv.py --run-id 2 --output output/beach_properties.csv
```

## 📁 Project Structure

```
├── scripts/
│   ├── run_scrape.py    # Main scraping script
│   └── export_csv.py    # CSV export utility
├── configs/
│   └── *.yaml           # Site configurations
├── data/
│   └── scraper.db       # SQLite database
├── output/
│   └── *.csv            # Exported results
└── src/                 # Core scraping logic
```

## 💡 Tips

- **Start small**: Test with 1-2 pages before scraping entire sites
- **Be polite**: Use delays (configured in YAML) to avoid overwhelming servers
- **Check robots.txt**: Make sure you're allowed to scrape the target site
- **Network issues**: If scraping fails, it might be network/proxy issues in Replit

## 🔧 Troubleshooting

**"Module not found" error?**
```bash
pip install -r requirements.txt
playwright install chromium
```

**"net::ERR_TUNNEL_CONNECTION_FAILED"?**
- This is a Replit network restriction (can't access external HTTPS sites from headless browser)
- Run the scraper locally or on a server instead

**No addresses extracted?**
- Check if the site has addresses visible on listing pages
- Try adding specific CSS selectors in your config file
- Use `--log-level DEBUG` to see what's being extracted

## 📚 Full Documentation

See the main [README.md](./README.md) for complete documentation.

---

**Ready to scrape?** Start with the Quick Start commands above! 🚀
