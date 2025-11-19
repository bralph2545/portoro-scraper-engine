# 🌐 Universal Property Scraper Guide

## What This Does

A **single script** that can extract property data from ANY vacation rental website, without needing custom configurations.

### Input
- URL of the main "all rentals" or "vacation rentals" page
- Company name
- Your OpenAI API key

### Output
Structured property data including:
- Property management company name
- Property name/title
- Full address (street, city, state, zip, country)
- Listing URL
- Bedrooms, bathrooms, sleeps
- Nightly rate range
- Amenities list
- Description
- Property ID
- Confidence score

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install openai playwright beautifulsoup4 pyyaml lxml
playwright install chromium
```

### 2. Set Your OpenAI API Key

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

Or pass it directly with `--api-key`

### 3. Run the Scraper

```bash
python scripts/universal_property_scraper.py \
    --url "https://www.30aescapes.com/all-rentals" \
    --company "30A Escapes" \
    --output 30a_properties.json
```

That's it! The tool will:
1. Discover all property listings from the index page
2. Extract full data from each property using OpenAI
3. Save to JSON or CSV

## 📊 Example Output

```json
[
  {
    "property_management_company": "30A Escapes",
    "property_name": "Stunning Beachfront Villa",
    "listing_url": "https://www.30aescapes.com/property/beach-villa-123",
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
    "amenities": ["Private Pool", "Hot Tub", "Beach Access", "WiFi", "Grill"],
    "description": "Beautiful beachfront villa with stunning gulf views...",
    "property_id": "beach-villa-123",
    "confidence": 0.95,
    "extraction_method": "llm",
    "model_used": "gpt-4o-mini",
    "extracted_at": "2025-11-19T00:15:30"
  },
  ...
]
```

## 💡 Usage Examples

### Test with 10 Properties First

```bash
python scripts/universal_property_scraper.py \
    --url "https://www.example.com/vacation-rentals" \
    --company "Example Rentals" \
    --output test.json \
    --limit 10
```

### Save as CSV

```bash
python scripts/universal_property_scraper.py \
    --url "https://www.example.com/vacation-rentals" \
    --company "Example Rentals" \
    --output properties.csv \
    --format csv
```

### Save as Both JSON and CSV

```bash
python scripts/universal_property_scraper.py \
    --url "https://www.example.com/vacation-rentals" \
    --company "Example Rentals" \
    --output properties.json \
    --format both
```

### Skip Confirmation Prompt

```bash
python scripts/universal_property_scraper.py \
    --url "https://www.example.com/vacation-rentals" \
    --company "Example Rentals" \
    --output properties.json \
    --yes
```

### Use a Different OpenAI Model

```bash
python scripts/universal_property_scraper.py \
    --url "https://www.example.com/vacation-rentals" \
    --company "Example Rentals" \
    --output properties.json \
    --model gpt-4  # More accurate but more expensive
```

## 💰 Cost Estimate

Using `gpt-4o-mini` (default):
- **~$0.001 - $0.01 per property**
- 100 properties = **$0.10 - $1.00**
- 1000 properties = **$1.00 - $10.00**

Using `gpt-4`:
- **~$0.05 - $0.15 per property**
- 100 properties = **$5.00 - $15.00**
- 1000 properties = **$50.00 - $150.00**

**Recommendation**: Start with `gpt-4o-mini` (default). It's 10-30x cheaper and works great for most sites.

## 🎯 How It Works

### Step 1: Discovery
The crawler visits the main "all rentals" page and:
- Scrolls to load all content
- Clicks "Load More" buttons
- Follows pagination links
- Collects all individual property listing URLs

### Step 2: Extraction
For each property URL:
- Fetches the full HTML page
- Sends the content to OpenAI with a structured prompt
- OpenAI intelligently extracts all property data
- Returns structured JSON

### Step 3: Validation
- Handles missing fields gracefully
- Assigns confidence scores
- Logs errors for failed extractions

## ✅ What Works

- ✅ **Any website structure** - No configs needed
- ✅ **Custom property management sites**
- ✅ **WordPress/Wix/Squarespace sites**
- ✅ **Booking platform integrations**
- ✅ **JavaScript-heavy sites** (uses real browser)
- ✅ **Pagination, infinite scroll, "Load More" buttons**
- ✅ **Missing data** (gracefully returns null)
- ✅ **Diverse address formats** (LLM parses any format)

## ⚠️ Limitations

1. **OpenAI API Required** - You need an OpenAI account and API key
2. **Cost** - Each property costs ~$0.001-$0.01 in API fees
3. **Speed** - ~2-5 seconds per property (API latency + page load)
4. **Rate Limits** - OpenAI has rate limits (usually 60-200 requests/minute)
5. **Network Access** - Won't work on Replit (use locally or VPS)

## 🔧 Troubleshooting

### "OpenAI API key required!"
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### "No property listings discovered!"
- Check that the URL is an index/listings page (not a single property)
- Try adding `--log-level DEBUG` to see what URLs were found
- The site might use unusual URL patterns

### "ModuleNotFoundError: No module named 'openai'"
```bash
pip install openai
```

### "ERR_TUNNEL_CONNECTION_FAILED" (on Replit)
- Replit blocks external HTTPS requests from headless browsers
- Download and run locally, or use a VPS

### Low Confidence Scores
- Some sites don't have complete data on listing pages
- Try the more accurate (but expensive) `--model gpt-4`
- Some properties might only have partial information available

## 📝 Output Fields

| Field | Type | Description |
|-------|------|-------------|
| property_management_company | string | Company name |
| property_name | string | Property title/name |
| listing_url | string | URL of the listing |
| street_address | string | Street address |
| city | string | City name |
| state | string | State (2-letter code for USA) |
| zip_code | string | ZIP/postal code |
| country | string | Country (default: USA) |
| bedrooms | integer | Number of bedrooms |
| bathrooms | float | Number of bathrooms |
| sleeps | integer | Maximum occupancy |
| nightly_rate_min | float | Minimum nightly rate |
| nightly_rate_max | float | Maximum nightly rate |
| amenities | array | List of amenities |
| description | string | Property description (max 500 chars) |
| property_id | string | Listing ID or property code |
| confidence | float | Confidence score (0.0-1.0) |
| extraction_method | string | "llm" or "fallback_regex" |
| model_used | string | OpenAI model used |
| extracted_at | string | ISO timestamp |

## 🎓 Best Practices

1. **Test First** - Use `--limit 10` to test with a small sample
2. **Review One** - Check the first result to ensure quality
3. **Batch Size** - Process 50-100 properties at a time
4. **Save JSON** - JSON preserves all data including amenities arrays
5. **Check Confidence** - Properties with confidence < 0.5 might need manual review
6. **Rate Limits** - If you hit OpenAI rate limits, add delays or process in smaller batches

## 🔄 Processing Multiple Companies

Create a simple batch script:

```bash
#!/bin/bash
# batch_scrape.sh

companies=(
  "https://www.30aescapes.com/all-rentals:30A Escapes"
  "https://www.360blue.com/vacation-rentals:360 Blue"
  "https://realjoy.com/vacation-rentals:RealJoy Vacations"
)

for item in "${companies[@]}"; do
  url="${item%%:*}"
  company="${item##*:}"

  echo "Processing: $company"

  python scripts/universal_property_scraper.py \
    --url "$url" \
    --company "$company" \
    --output "output/${company// /_}.json" \
    --yes

  echo "Waiting 30 seconds before next company..."
  sleep 30
done

echo "All done!"
```

## 📞 Support

For issues or questions:
- Check the main [README.md](./README.md)
- Review the code in `scripts/universal_property_scraper.py`
- Enable debug logging: `--log-level DEBUG`

---

**Ready to extract property data from any vacation rental site!** 🏖️
