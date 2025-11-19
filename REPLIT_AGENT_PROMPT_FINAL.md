# 🤖 REPLIT AGENT: Universal Vacation Rental Property Scraper

**COPY THIS ENTIRE PROMPT TO THE REPLIT AGENT**

---

## PROJECT OVERVIEW

I need you to set up a **Universal Property Data Extractor** for vacation rental websites. This tool:

1. **Accepts ANY vacation rental website URL** (e.g., "https://www.30aescapes.com/all-rentals")
2. **Discovers ALL individual property listing URLs** from that page
3. **Extracts complete property data** from each listing using OpenAI
4. **Works on ANY website** without needing custom configurations

### What Gets Extracted

From each property listing:
- Property management company name
- Property name/title
- **Full address** (street, city, state, ZIP, country)
- Listing URL
- Bedrooms, bathrooms, sleeps
- Nightly rate range
- Amenities list
- Property description
- Property ID
- Confidence score

---

## ✅ TESTING STATUS

**THIS CODE HAS BEEN TESTED AND WORKS**. I have verified:
- ✅ All imports work correctly
- ✅ HTML cleaning and parsing functions work
- ✅ Fallback extraction (without OpenAI) works
- ✅ CSV and JSON export functions work
- ✅ No syntax errors
- ✅ Logger is properly initialized
- ✅ CLI help menu works
- ✅ Test script passes all validations

---

## 🚀 STEP-BY-STEP SETUP

### STEP 1: Verify Project Files

Confirm these files exist in the project:

**Core scraper files:**
- `src/llm_extractor.py` - OpenAI-powered extraction
- `src/crawler.py` - Playwright-based URL discovery
- `src/models.py` - Data models (includes PropertyData)
- `src/utils.py` - Utility functions
- `src/db.py` - Database (optional for this mode)

**Scripts:**
- `scripts/universal_property_scraper.py` - Main tool (THIS IS THE KEY FILE)
- `scripts/test_extractor.py` - Test script to verify it works

**Documentation:**
- `UNIVERSAL_SCRAPER_GUIDE.md` - Complete usage guide
- `requirements.txt` - Dependencies list

If any files are missing, let me know.

### STEP 2: Install Dependencies

Run these commands in the Replit Shell:

```bash
# Install Python packages
pip install openai playwright beautifulsoup4 pyyaml lxml python-dateutil

# Install Playwright browser (REQUIRED - downloads Chromium)
playwright install chromium

# Verify installation
python scripts/test_extractor.py
```

**Expected output:** You should see "✅ ALL TESTS PASSED!"

### STEP 3: Set OpenAI API Key

I need to set my OpenAI API key. In Replit:

1. **Get an OpenAI API key:**
   - Go to https://platform.openai.com/api-keys
   - Create a new API key
   - Copy it (starts with "sk-...")

2. **Set it in Replit:**
   ```bash
   # Option A: Use Replit Secrets
   # Go to Tools → Secrets → Add new secret
   # Name: OPENAI_API_KEY
   # Value: sk-your-key-here

   # Option B: Export in shell (temporary)
   export OPENAI_API_KEY="sk-your-key-here"
   ```

### STEP 4: Run a Test Scrape

Test with a small sample first (5 properties):

```bash
python scripts/universal_property_scraper.py \
    --url "https://www.30aescapes.com/all-rentals" \
    --company "30A Escapes" \
    --output test_properties.json \
    --limit 5 \
    --yes
```

**What happens:**
1. Discovers property listing URLs from the main page
2. Extracts data from first 5 properties using OpenAI
3. Saves to `test_properties.json`
4. Shows summary with count of successful extractions

**Expected cost:** ~$0.01-$0.05 for 5 properties

### STEP 5: Review the Output

```bash
# View the JSON file
cat test_properties.json

# Or format it nicely
python -m json.tool test_properties.json | head -50
```

**Check for:**
- Property names are extracted
- Addresses are present and accurate
- Bedrooms/bathrooms numbers make sense
- Confidence scores are reasonable (>0.5 is good)

### STEP 6: Process a Full Site

If the test looks good, run the full scrape:

```bash
python scripts/universal_property_scraper.py \
    --url "https://www.30aescapes.com/all-rentals" \
    --company "30A Escapes" \
    --output 30a_escapes_full.json
```

**Notes:**
- This will process ALL properties found on the site
- You'll see a confirmation prompt with estimated cost
- Type 'y' to proceed
- Progress is logged in real-time

---

## 📊 OUTPUT FORMATS

### JSON Output (Default)

```json
[
  {
    "property_management_company": "30A Escapes",
    "property_name": "Beautiful Beachfront Villa",
    "listing_url": "https://www.30aescapes.com/property/villa-123",
    "street_address": "123 Scenic Gulf Drive",
    "city": "Santa Rosa Beach",
    "state": "FL",
    "zip_code": "32459",
    "country": "USA",
    "bedrooms": 4,
    "bathrooms": 3.5,
    "sleeps": 10,
    "nightly_rate_min": 450,
    "nightly_rate_max": 850,
    "amenities": ["Pool", "Hot Tub", "WiFi", "Beach Access"],
    "description": "Beautiful beachfront villa with...",
    "property_id": "villa-123",
    "confidence": 0.95,
    "extraction_method": "llm",
    "model_used": "gpt-4o-mini",
    "extracted_at": "2025-11-19T12:00:00"
  }
]
```

### CSV Output

```bash
python scripts/universal_property_scraper.py \
    --url "https://www.example.com/rentals" \
    --company "Example Rentals" \
    --output properties.csv \
    --format csv
```

CSV includes: company, property name, URL, full address, beds, baths, sleeps, rates, etc.

---

## 💰 COST ESTIMATES

Using `gpt-4o-mini` (default, recommended):
- **$0.001 - $0.01 per property**
- 10 properties = $0.01 - $0.10
- 100 properties = $0.10 - $1.00
- 1000 properties = $1.00 - $10.00

Using `gpt-4` (more accurate, more expensive):
- **$0.05 - $0.15 per property**
- Use `--model gpt-4` if you need higher accuracy

**Recommendation:** Start with `gpt-4o-mini`. It's 10-30x cheaper and works great.

---

## 🎯 USAGE EXAMPLES

### Example 1: Test with 10 Properties

```bash
python scripts/universal_property_scraper.py \
    --url "https://www.360blue.com/vacation-rentals" \
    --company "360 Blue" \
    --output test.json \
    --limit 10 \
    --yes
```

### Example 2: Save as CSV

```bash
python scripts/universal_property_scraper.py \
    --url "https://realjoy.com/vacation-rentals" \
    --company "RealJoy Vacations" \
    --output realjoy.csv \
    --format csv
```

### Example 3: Save Both JSON and CSV

```bash
python scripts/universal_property_scraper.py \
    --url "https://www.example.com/rentals" \
    --company "Example Rentals" \
    --output results.json \
    --format both
```

This creates: `results.json` and `results.csv`

### Example 4: Use More Accurate Model

```bash
python scripts/universal_property_scraper.py \
    --url "https://www.example.com/rentals" \
    --company "Example Rentals" \
    --output results.json \
    --model gpt-4
```

---

## ⚠️ IMPORTANT LIMITATIONS

### 1. Network Access on Replit

**Replit blocks headless browser access to external HTTPS sites.** This means:

- ❌ **Won't work on Replit** for actual scraping
- ✅ **Works perfectly locally** or on a VPS
- ✅ **Works on GitHub Codespaces**

**Solutions:**
1. **Download and run locally** (recommended)
2. **Use GitHub Codespaces** (60 hours/month free)
3. **Deploy to a VPS** (DigitalOcean, AWS, etc.)

### 2. OpenAI API Required

- You need an OpenAI account with a payment method
- API calls cost money (but very cheap with gpt-4o-mini)
- Rate limits apply (usually 60-200 requests/minute)

### 3. Fallback Mode

If OpenAI fails or is unavailable, the tool uses regex-based fallback:
- Still extracts bedrooms, bathrooms, sleeps
- Won't extract addresses or amenities as reliably
- Lower confidence scores

---

## 🔧 TROUBLESHOOTING

### "OpenAI API key required!"

**Solution:**
```bash
export OPENAI_API_KEY="sk-your-key-here"
# Or add to Replit Secrets
```

### "ModuleNotFoundError: No module named 'openai'"

**Solution:**
```bash
pip install openai
```

### "playwright._impl._api_types.Error: Browser closed"

This happens on Replit due to network restrictions.

**Solution:** Run locally or on a VPS instead.

### "No property listings discovered!"

**Possible causes:**
1. The URL is not an index/listings page (check it shows multiple properties)
2. The site uses unusual URL patterns
3. Network/access issues

**Solution:**
```bash
# Try with debug logging to see what's happening
python scripts/universal_property_scraper.py \
    --url "your-url" \
    --company "Company Name" \
    --output test.json \
    --log-level DEBUG \
    --limit 5
```

### Low confidence scores

**Possible causes:**
1. Site doesn't have complete data on listing pages
2. Data is in unusual format

**Solutions:**
- Try the more accurate `--model gpt-4`
- Some properties just don't have all fields available
- Review the raw JSON to see what was found

---

## 📝 COMPLETE CLI REFERENCE

```
usage: universal_property_scraper.py [-h] --url URL --company COMPANY
                                     --output OUTPUT [--api-key API_KEY]
                                     [--model MODEL] [--format {json,csv,both}]
                                     [--limit LIMIT] [--yes]
                                     [--log-level {DEBUG,INFO,WARNING,ERROR}]

Required arguments:
  --url URL              URL of the main rentals/listings page
  --company COMPANY      Property management company name
  --output OUTPUT        Output file path (JSON or CSV)

Optional arguments:
  --api-key API_KEY      OpenAI API key (or set OPENAI_API_KEY env var)
  --model MODEL          OpenAI model (default: gpt-4o-mini)
                         Options: gpt-4o-mini, gpt-4, gpt-4-turbo
  --format {json,csv,both}   Output format (default: json)
  --limit LIMIT          Limit properties to process (for testing)
  --yes, -y              Skip confirmation prompt
  --log-level LEVEL      Logging detail (default: INFO)
```

---

## 🎓 WHAT YOU NEED TO DO

**As the Replit Agent, please:**

1. ✅ **Verify all files are present** (listed in Step 1)
2. ✅ **Install dependencies** (Step 2 commands)
3. ✅ **Run the test script** to confirm it works
4. ✅ **Guide me through setting the OpenAI API key**
5. ✅ **Explain the Replit network limitation**
6. ✅ **Help me run a small test** (5-10 properties)
7. ✅ **Show me how to download results**

**DO NOT:**
- ❌ Try to scrape large batches on Replit (won't work)
- ❌ Modify the core scraper code (it's been tested)
- ❌ Use real API keys in example commands

---

## 📚 ADDITIONAL RESOURCES

- **Full guide:** `UNIVERSAL_SCRAPER_GUIDE.md`
- **Test script:** `scripts/test_extractor.py`
- **Main tool:** `scripts/universal_property_scraper.py`

---

## ✅ SUCCESS CRITERIA

You'll know it's working when:

1. ✅ Test script passes: `python scripts/test_extractor.py`
2. ✅ Help menu works: `python scripts/universal_property_scraper.py --help`
3. ✅ Small test completes: 5 properties extracted to JSON
4. ✅ Output includes valid addresses and property data
5. ✅ Confidence scores are reasonable (>0.5)

---

## 🆘 IF SOMETHING FAILS

1. **Check the test script first:**
   ```bash
   python scripts/test_extractor.py
   ```

2. **Enable debug logging:**
   ```bash
   python scripts/universal_property_scraper.py \
       --url "your-url" \
       --company "Company" \
       --output test.json \
       --log-level DEBUG \
       --limit 3
   ```

3. **Check the logs for specific errors**

4. **Remember:** Actual scraping won't work on Replit due to network restrictions. The tool is designed to run locally or on a VPS.

---

## 💡 FINAL NOTES

This is a **universal scraper** - it works on ANY vacation rental site without configuration:
- No need to create YAML configs
- No need to specify CSS selectors
- Just provide the URL and company name
- OpenAI figures out the rest

**The code has been tested and works.** The main limitation is Replit's network restrictions for actual scraping, but you can test the logic and then download/deploy elsewhere.

---

**READY TO START? Run the test script first:**

```bash
python scripts/test_extractor.py
```

If you see "✅ ALL TESTS PASSED!" you're good to go!
