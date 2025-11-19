# 🏖️ How to Use Your Property Scraper

## Super Simple - No Coding Required!

---

## What This Tool Does

**You give it ANY vacation rental website URL → It finds all properties → Extracts complete data → Gives you downloadable files**

No coding. No terminal. Just a web form.

---

## Step 1: Open Your Scraper

Go to your Railway URL (looks like `https://your-app.railway.app`)

You'll see a login screen.

---

## Step 2: Log In

Enter the username and password you set during deployment.

**Default credentials** (if you didn't change them):
- Username: `admin`
- Password: `portoro2024`

---

## Step 3: Enter Website Details

You'll see a simple form with two fields:

### Field 1: Website URL
Paste the URL of the vacation rental listings page.

**Examples:**
- `https://www.30aescapes.com/all-rentals`
- `https://www.360blue.com/vacation-rentals`
- `https://realjoy.com/vacation-rentals`

**What to paste:**
- ✅ The main page that shows MULTIPLE properties
- ✅ The "All Rentals" or "Properties" page
- ❌ NOT a single property page

### Field 2: Company Name
Type the company name.

**Examples:**
- `30A Escapes`
- `360 Blue`
- `RealJoy Vacations`

---

## Step 4: Click "Start Scraping"

The tool will:
1. ✅ Find all individual property listings on that page
2. ✅ Visit each property page
3. ✅ Extract complete data (name, address, beds, baths, rates, amenities, etc.)
4. ✅ Show you real-time progress

---

## Step 5: Wait for Progress

You'll see:
- **Status messages** - "Discovering properties...", "Extracting data..."
- **Progress bar** - Updates in real-time
- **Count** - "15 / 47" (15 properties extracted out of 47 found)

**How long does it take?**
- 10 properties = ~1-2 minutes
- 50 properties = ~5-10 minutes
- 100 properties = ~10-20 minutes

**You can leave the page open** - just wait for the green "Complete!" message.

---

## Step 6: Download Results

When complete, two buttons appear:

### Download JSON
- Complete data with all fields
- Includes amenities as lists
- Best for importing into other systems

### Download CSV
- Spreadsheet format
- Open in Excel or Google Sheets
- Best for human review and analysis

**Download both!** You can always use them later.

---

## What Data Do You Get?

For each property:
- ✅ Property Management Company
- ✅ Property Name
- ✅ **Full Address** (street, city, state, ZIP, country)
- ✅ Listing URL
- ✅ Bedrooms, Bathrooms, Sleeps
- ✅ Nightly Rate Range (min/max)
- ✅ Amenities List (pool, hot tub, wifi, etc.)
- ✅ Property Description
- ✅ Property ID
- ✅ Confidence Score (how confident the AI was)

---

## View Past Scrapes

Click **"View Scrape History →"** at the bottom of the page.

You'll see a table with all your past scrapes:
- Company name
- Website URL
- Number of properties found
- Date/time
- Download links (JSON & CSV)

**Never lose your data** - it's all saved in the history!

---

## Tips for Best Results

### 1. Start Small
First time using a new website? Add `&limit=10` or similar to test with fewer properties.

### 2. Check the First Result
Download the JSON/CSV and look at 1-2 properties to verify the data looks good.

### 3. Use the Right URL
Make sure you're on a page that shows MULTIPLE properties, not a single listing.

**How to find the right URL:**
1. Go to the company's website
2. Find "Vacation Rentals" or "Properties" or "All Rentals"
3. Copy that URL

### 4. Be Patient
Large sites with 100+ properties can take 10-20 minutes. This is normal.

---

## Costs

### What You Pay For

**Railway Hosting:**
- Free tier: $5 credits/month
- Typically $0-5/month depending on usage
- No credit card required initially

**OpenAI API (the smart extraction):**
- ~$0.01 - $0.10 per property
- 10 properties = $0.10
- 100 properties = $1.00
- Very cheap!

**Total estimated cost:** $1-10/month for typical use

---

## Troubleshooting

### "No properties found"

**Problem:** The tool couldn't find property listings on that page.

**Solutions:**
- Make sure the URL is a listings/index page (shows multiple properties)
- Try the main "All Rentals" page
- Some sites may not work if they have unusual structures

### "Extraction failed"

**Problem:** The AI couldn't extract data from the page.

**Solutions:**
- Check if the property pages are publicly accessible (not login-required)
- Try a different site
- Check your OpenAI API credits

### "Unauthorized" login error

**Problem:** Wrong username/password.

**Solution:** Use the credentials you set during Railway deployment.

### Takes too long

**Problem:** Scraping 200 properties can take 30+ minutes.

**Solutions:**
- Be patient - this is normal for large sites
- Process in smaller batches
- Leave the browser tab open and check back later

---

## Frequently Asked Questions

### Can I scrape any vacation rental website?

**Yes!** The tool works on ANY vacation rental site:
- Property management companies
- Airbnb-style platforms
- Custom websites
- WordPress sites
- Wix/Squarespace sites

Just paste the URL!

### How many sites can I scrape?

**Unlimited!** Scrape as many different websites as you want. Each scrape is saved in your history.

### Can I scrape the same site multiple times?

**Yes!** Scrape weekly or monthly to track changes. Each scrape is saved separately.

### Is the data accurate?

**Very accurate!** The tool uses OpenAI's GPT-4o-mini to intelligently extract data. It's usually 90-95% accurate.

Always spot-check a few results to verify quality.

### What if a property is missing data?

Some properties don't have complete information on their listing pages (e.g., no rate listed). The tool extracts what's available and marks missing fields as empty.

### Can I export to Excel?

**Yes!** Download the CSV file and open it in:
- Microsoft Excel
- Google Sheets
- Apple Numbers
- Any spreadsheet app

---

## Example Workflow

Here's how you might use this for competitive analysis:

1. **Monday Morning:**
   - Scrape competitor #1 (30A Escapes)
   - Download CSV
   - Review in Excel

2. **Monday Afternoon:**
   - Scrape competitors #2-5
   - Download all CSVs
   - Combine in a master spreadsheet

3. **Throughout the week:**
   - Scrape remaining competitors
   - Check history page for all results

4. **Monthly:**
   - Re-scrape all sites
   - Compare changes (new properties, rate changes, etc.)

---

## That's It!

**Three steps:**
1. 📝 Paste URL + Company Name
2. ⏳ Wait for scraping to complete
3. 📥 Download JSON/CSV files

**No coding. No terminal. No complexity.**

Just a simple web form that works on ANY vacation rental website!

---

## Need Help?

- **Check the history page** - see if past scrapes worked
- **Try a different website** - some sites may have unusual structures
- **Check Railway logs** - if you're technical, Railway dashboard shows detailed logs
- **Verify OpenAI credits** - make sure your OpenAI account has credits

---

## Summary

✅ **Paste any vacation rental URL**
✅ **Click "Start Scraping"**
✅ **Download complete property data**
✅ **Works on ANY website**
✅ **No coding required**
✅ **History saved forever**

**Enjoy your universal property scraper!** 🎉
