# 📦 DELIVERY INSTRUCTIONS - Vacation Rental Scraper

## 🎯 What You Have

A complete, production-ready vacation rental address scraper that can extract property addresses from all 26 of your Destin/30A competitors.

## 📥 TWO WAYS TO GET THE FILES

### Option 1: Download the Zip File (57KB)
**Location**: `portoro-scraper-engine.zip` (in this Repl's root folder)

**Contains**:
- All source code (src/, scripts/, configs/)
- Dependencies lists (requirements.txt, pyproject.toml)
- Documentation (README.md, README.replit.md)
- Replit config files (.replit, replit.nix)
- 26 competitor URLs ready to scrape (configs/competitors_list.csv)
- Batch scraping script (scripts/batch_scrape_competitors.py)

**What's NOT included** (by design):
- No .git folder
- No cached data or databases
- No __pycache__ files
- No generated CSVs

### Option 2: Clone from GitHub
```bash
git clone https://github.com/bralph2545/portoro-scraper-engine.git
# or
# Import into Replit: https://replit.com/github/bralph2545/portoro-scraper-engine
```

## 🤖 FOR THE REPLIT AGENT

**File**: `REPLIT_AGENT_PROMPT.md`

Copy the entire contents of this file and paste it to the Replit Agent. It contains:
- Complete setup instructions
- Dependency installation commands
- Single-site test procedure
- Batch scraping all 26 competitors
- CSV export instructions
- Troubleshooting guide
- Expected output format

## 🚀 QUICK START (Manual)

If you want to do it yourself without the Replit Agent:

### 1. Install Dependencies
```bash
pip install playwright beautifulsoup4 pyyaml lxml python-dateutil
playwright install chromium
```

### 2. Test with One Site
```bash
python scripts/run_scrape.py \
    --url https://www.30aescapes.com/all-rentals \
    --manager-name "30A Escapes" \
    --manager-domain 30aescapes.com \
    --market-name "30A / Destin, FL"
```

### 3. Scrape All 26 Competitors
```bash
python scripts/batch_scrape_competitors.py \
    --input configs/competitors_list.csv \
    --delay 60 \
    --log-level INFO
```

This will take ~30-45 minutes (26 sites × 60 seconds between each + scraping time).

### 4. Export Results
The batch script will print export commands for each successful scrape:
```bash
python scripts/export_csv.py --run-id 1 --output output/30a_escapes.csv
python scripts/export_csv.py --run-id 2 --output output/pelican_beach.csv
# ... etc
```

## ⚠️ IMPORTANT: NETWORK LIMITATIONS

**Replit blocks headless browser access to external HTTPS sites.**

You'll see: `ERR_TUNNEL_CONNECTION_FAILED`

### Solutions:
1. ✅ **Download the zip and run locally** (recommended)
2. ✅ **Use GitHub Codespaces** (better network access)
3. ✅ **Deploy to a VPS** (DigitalOcean, AWS, Linode)
4. ❌ **Won't work well on Replit** (network restrictions)

## 📋 THE 26 COMPETITORS

All listed in `configs/competitors_list.csv`:

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

## 📊 WHAT YOU'LL GET

CSV files with these columns for each property:
- manager_name, manager_domain, market_name
- listing_url (link to the property)
- address_line1, address_line2
- city, state, postal_code, country
- confidence_score (0.0-1.0)
- inference_method (how it was extracted)

## 🗂️ FILE STRUCTURE

```
portoro-scraper-engine/
├── 📄 REPLIT_AGENT_PROMPT.md      ← Copy this to Replit Agent
├── 📄 DELIVERY_INSTRUCTIONS.md    ← You are here
├── 📦 portoro-scraper-engine.zip  ← Download this
│
├── scripts/
│   ├── run_scrape.py              ← Single site scraper
│   ├── batch_scrape_competitors.py ← Batch scrape all 26
│   └── export_csv.py              ← Export to CSV
│
├── configs/
│   ├── competitors_list.csv       ← 26 competitor URLs
│   ├── example_site.yaml          ← Config template
│   └── test_30aescapes.yaml       ← Test config
│
├── src/                           ← Core scraping logic
│   ├── main.py, crawler.py
│   ├── extractor.py, normalizer.py
│   └── db.py, models.py, utils.py
│
├── data/                          ← SQLite database (created on first run)
├── output/                        ← CSV exports go here
│
└── 📚 Documentation
    ├── README.md                  ← Full project docs
    └── README.replit.md           ← Replit quick start
```

## 🎬 NEXT STEPS

**CHOICE A: Use Replit Agent**
1. Open `REPLIT_AGENT_PROMPT.md`
2. Copy the entire file
3. Paste to Replit Agent
4. Follow its guidance

**CHOICE B: Run Locally (Recommended)**
1. Download `portoro-scraper-engine.zip`
2. Extract on your computer
3. Install dependencies
4. Run batch scraper
5. Collect 26 CSV files from `output/` folder

**CHOICE C: Deploy to VPS**
1. Rent a VPS (DigitalOcean droplet, AWS EC2, etc.)
2. Upload the zip file
3. Extract and install dependencies
4. Run batch scraper
5. Download CSV files via SCP/SFTP

## 💰 COST ESTIMATE

- **Free**: Running locally on your computer
- **~$6/month**: DigitalOcean Basic Droplet
- **~$10/month**: AWS t2.micro EC2 instance
- **Free tier**: GitHub Codespaces (60 hours/month free)

## ⏱️ TIME ESTIMATE

- Setup: 5-10 minutes
- Batch scraping 26 sites: 30-45 minutes
- Total: **~1 hour** from zero to CSV files

## ✅ WHAT'S BEEN COMPLETED

✅ Full scraper implementation (all 9 source files)
✅ Config-based and quick URL modes
✅ Batch scraper for processing multiple sites
✅ CSV with all 26 competitors
✅ Complete documentation
✅ Replit configuration files
✅ Clean downloadable zip
✅ Comprehensive agent prompt
✅ All code pushed to GitHub

## 📞 QUESTIONS?

Check these files:
- `README.md` - Complete documentation
- `REPLIT_AGENT_PROMPT.md` - Setup instructions
- `src/*.py` - Code has inline documentation

---

**Ready to scrape!** 🚀

Choose your path (Replit Agent, local, or VPS) and start collecting addresses.
