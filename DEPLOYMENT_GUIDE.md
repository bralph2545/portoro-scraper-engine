# 🚀 DEPLOYMENT GUIDE - After Replit Agent Setup

## THE PROBLEM

**Replit blocks headless browsers from accessing external HTTPS sites.** This means:
- ✅ Testing works on Replit (test scripts, validation)
- ❌ **Actual scraping FAILS on Replit** (ERR_TUNNEL_CONNECTION_FAILED)
- ✅ **Must deploy elsewhere** for production use

---

## 🎯 DEPLOYMENT OPTIONS (RANKED)

### **Option 1: Run Locally on Your Computer** ⭐ RECOMMENDED
**Best for:** Quick results, one-time scrapes, testing
**Cost:** FREE
**Time:** 5 minutes
**Difficulty:** ⭐ Easy

### **Option 2: GitHub Codespaces**
**Best for:** Cloud-based development without VPS setup
**Cost:** FREE (60 hours/month)
**Time:** 10 minutes
**Difficulty:** ⭐ Easy

### **Option 3: Deploy to VPS (DigitalOcean/AWS/Linode)**
**Best for:** Repeated scraping, production use, automation
**Cost:** $6-12/month
**Time:** 20-30 minutes
**Difficulty:** ⭐⭐ Moderate

### **Option 4: GitHub Actions (Automated)**
**Best for:** Scheduled scraping (daily/weekly)
**Cost:** FREE (2000 minutes/month)
**Time:** 30 minutes
**Difficulty:** ⭐⭐⭐ Advanced

---

## 📦 OPTION 1: RUN LOCALLY (RECOMMENDED)

This is the easiest and fastest way to get results.

### Step 1: Download from Replit

**Method A: Download ZIP**
1. In Replit, go to Files panel
2. Click the three dots (⋮) next to the project name
3. Select "Download as zip"
4. Extract the zip file on your computer

**Method B: Clone from GitHub**
```bash
git clone https://github.com/bralph2545/portoro-scraper-engine.git
cd portoro-scraper-engine
```

### Step 2: Install Dependencies

**On Windows:**
```bash
# Open PowerShell or Command Prompt
cd path\to\portoro-scraper-engine

# Install Python packages
pip install openai playwright beautifulsoup4 pyyaml lxml python-dateutil

# Install Playwright browser
playwright install chromium
```

**On Mac/Linux:**
```bash
cd /path/to/portoro-scraper-engine

# Install Python packages
pip3 install openai playwright beautifulsoup4 pyyaml lxml python-dateutil

# Install Playwright browser
playwright install chromium

# On Linux, may need system dependencies:
playwright install-deps
```

### Step 3: Set OpenAI API Key

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY="sk-your-key-here"
```

**Windows Command Prompt:**
```cmd
set OPENAI_API_KEY=sk-your-key-here
```

**Mac/Linux:**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

**Or create a `.env` file:**
```bash
# Create .env file in project root
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### Step 4: Run a Test

```bash
python scripts/test_extractor.py
# Should show: ✅ ALL TESTS PASSED!
```

### Step 5: Scrape Your First Site

```bash
python scripts/universal_property_scraper.py \
    --url "https://www.30aescapes.com/all-rentals" \
    --company "30A Escapes" \
    --output output/30a_escapes.json \
    --limit 10 \
    --yes
```

### Step 6: Check Results

```bash
# View JSON
cat output/30a_escapes.json

# Or open in a text editor
# Windows: notepad output\30a_escapes.json
# Mac: open output/30a_escapes.json
```

### Step 7: Process All Sites

Run the scraper for each of your competitor sites. Results are in `output/` folder.

**Time:** 2-5 minutes per site depending on number of properties
**Cost:** ~$0.50-$5.00 per site with gpt-4o-mini

---

## ☁️ OPTION 2: GITHUB CODESPACES

Free cloud development environment with better network access than Replit.

### Step 1: Open in Codespaces

1. Go to your GitHub repo: `https://github.com/bralph2545/portoro-scraper-engine`
2. Click the green **"Code"** button
3. Click **"Codespaces"** tab
4. Click **"Create codespace on [branch]"**

GitHub creates a cloud VS Code environment (takes ~2 minutes).

### Step 2: Install Dependencies

```bash
# In the Codespaces terminal:
pip install openai playwright beautifulsoup4 pyyaml lxml python-dateutil
playwright install chromium
playwright install-deps
```

### Step 3: Set OpenAI API Key

```bash
# Add to Codespaces secrets
export OPENAI_API_KEY="sk-your-key-here"
```

Or use Codespaces Secrets (persistent):
1. Settings → Secrets → New secret
2. Name: `OPENAI_API_KEY`
3. Value: `sk-your-key-here`

### Step 4: Run the Scraper

```bash
python scripts/universal_property_scraper.py \
    --url "https://www.30aescapes.com/all-rentals" \
    --company "30A Escapes" \
    --output output/30a.json
```

### Step 5: Download Results

1. Navigate to `output/` folder in file explorer
2. Right-click on the JSON/CSV file
3. Select **"Download"**

**Free tier:** 60 hours/month (plenty for your use case)

---

## 🖥️ OPTION 3: DEPLOY TO VPS

For production use, automated scraping, or running multiple sites.

### Best VPS Providers:

**DigitalOcean Droplet** (Recommended)
- Cost: $6/month (1GB RAM)
- Easy setup
- Good documentation

**AWS EC2**
- Cost: ~$10/month (or free tier for 12 months)
- More powerful
- Steeper learning curve

**Linode**
- Cost: $5/month
- Simple interface
- Good performance

### Step 1: Create VPS

**DigitalOcean Example:**

1. Sign up at https://www.digitalocean.com
2. Create a new Droplet:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic ($6/month, 1GB RAM)
   - **Region:** Closest to you
   - **Authentication:** SSH key (recommended) or password
3. Click "Create Droplet"
4. Note the IP address (e.g., `123.45.67.89`)

### Step 2: Connect to VPS

```bash
# SSH into your server
ssh root@123.45.67.89
```

### Step 3: Install Dependencies

```bash
# Update system
apt update && apt upgrade -y

# Install Python and pip
apt install -y python3 python3-pip git

# Install system dependencies for Playwright
apt install -y wget gnupg ca-certificates \
    fonts-liberation libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcups2 libdbus-1-3 libdrm2 \
    libgbm1 libgtk-3-0 libnspr4 libnss3 libx11-xcb1 \
    libxcomposite1 libxdamage1 libxrandr2 xdg-utils

# Clone your project
git clone https://github.com/bralph2545/portoro-scraper-engine.git
cd portoro-scraper-engine

# Install Python packages
pip3 install openai playwright beautifulsoup4 pyyaml lxml python-dateutil

# Install Playwright browser
playwright install chromium
```

### Step 4: Set OpenAI API Key

```bash
# Add to .bashrc for persistence
echo 'export OPENAI_API_KEY="sk-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### Step 5: Run Scraper

```bash
python3 scripts/universal_property_scraper.py \
    --url "https://www.30aescapes.com/all-rentals" \
    --company "30A Escapes" \
    --output output/30a.json \
    --yes
```

### Step 6: Download Results

```bash
# On your local machine:
scp root@123.45.67.89:/root/portoro-scraper-engine/output/*.json ./
```

Or use SFTP client like FileZilla.

### Step 7: Automate (Optional)

Create a script to run all sites:

```bash
#!/bin/bash
# scrape_all.sh

companies=(
  "https://www.30aescapes.com/all-rentals:30A Escapes"
  "https://www.360blue.com/vacation-rentals:360 Blue"
  "https://realjoy.com/vacation-rentals:RealJoy Vacations"
)

for item in "${companies[@]}"; do
  url="${item%%:*}"
  company="${item##*:}"

  echo "Scraping: $company"

  python3 scripts/universal_property_scraper.py \
    --url "$url" \
    --company "$company" \
    --output "output/${company// /_}.json" \
    --yes

  sleep 60  # Wait between sites
done
```

Run it:
```bash
chmod +x scrape_all.sh
./scrape_all.sh
```

### Step 8: Schedule with Cron (Optional)

```bash
# Edit crontab
crontab -e

# Add line to run weekly on Sundays at 2 AM:
0 2 * * 0 cd /root/portoro-scraper-engine && ./scrape_all.sh

# Or monthly on the 1st:
0 2 1 * * cd /root/portoro-scraper-engine && ./scrape_all.sh
```

---

## 🤖 OPTION 4: GITHUB ACTIONS (AUTOMATED)

Run scraping automatically on a schedule using GitHub's free CI/CD.

### Step 1: Create Workflow File

In your repo, create `.github/workflows/scrape.yml`:

```yaml
name: Scrape Vacation Rentals

on:
  # Run manually
  workflow_dispatch:

  # Or on a schedule (every Sunday at 2 AM UTC)
  schedule:
    - cron: '0 2 * * 0'

jobs:
  scrape:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install openai playwright beautifulsoup4 pyyaml lxml python-dateutil
          playwright install chromium
          playwright install-deps

      - name: Run scraper
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python scripts/universal_property_scraper.py \
            --url "https://www.30aescapes.com/all-rentals" \
            --company "30A Escapes" \
            --output output/30a_escapes.json \
            --yes

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: scrape-results
          path: output/*.json
```

### Step 2: Add OpenAI API Key to GitHub Secrets

1. Go to your repo on GitHub
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `OPENAI_API_KEY`
5. Value: `sk-your-key-here`
6. Click "Add secret"

### Step 3: Run the Workflow

1. Go to Actions tab in your repo
2. Select "Scrape Vacation Rentals" workflow
3. Click "Run workflow"
4. Wait for completion (~5-10 minutes)
5. Download artifacts (results)

**Free tier:** 2000 minutes/month

---

## 📊 COST COMPARISON

| Option | Setup Time | Monthly Cost | Best For |
|--------|-----------|--------------|----------|
| **Local** | 5 min | FREE | One-time use, testing |
| **Codespaces** | 10 min | FREE* | Cloud development |
| **VPS** | 30 min | $6-12 | Production, automation |
| **GitHub Actions** | 30 min | FREE* | Scheduled scraping |

*Free tier limits apply

---

## 🎯 RECOMMENDED WORKFLOW

### For Your Use Case (26 Competitors):

1. **Start Local** (Day 1)
   - Download from Replit
   - Test with 2-3 sites
   - Verify data quality
   - Total time: 1-2 hours
   - Cost: ~$2-5

2. **Scale to VPS** (Week 2)
   - Set up DigitalOcean droplet
   - Create automation script
   - Run all 26 sites
   - Total time: 30 min setup + 2-3 hours scraping
   - Cost: $6/month + $10-20 API

3. **Automate** (Ongoing)
   - Set up monthly cron job
   - Scrapes run automatically
   - Download results as needed
   - Cost: $6/month VPS + $10-20/month API

---

## 🔄 COMPLETE DEPLOYMENT PROCESS

### Phase 1: Validation (On Replit)
```
1. Replit Agent sets up project ✓
2. Run test_extractor.py ✓
3. Verify all files present ✓
4. Review documentation ✓
```

### Phase 2: Initial Deployment (Local)
```
1. Download from Replit
2. Install dependencies
3. Test with 1-2 sites
4. Verify output quality
5. Fix any issues
```

### Phase 3: Production (VPS)
```
1. Create VPS (DigitalOcean)
2. Clone from GitHub
3. Install dependencies
4. Create batch script
5. Run all 26 competitors
6. Download results
```

### Phase 4: Automation (Cron/GitHub Actions)
```
1. Set up scheduled runs
2. Configure notifications
3. Auto-download results
4. Monitor for errors
```

---

## 📝 AFTER DEPLOYMENT CHECKLIST

- [ ] Downloaded/cloned project from Replit
- [ ] Installed all dependencies locally
- [ ] Set OpenAI API key
- [ ] Ran test_extractor.py successfully
- [ ] Tested with 1-2 sites
- [ ] Verified output quality
- [ ] Scraped all 26 competitors
- [ ] Saved all JSON/CSV files
- [ ] (Optional) Set up VPS for automation
- [ ] (Optional) Created batch script
- [ ] (Optional) Scheduled recurring scrapes

---

## 🆘 TROUBLESHOOTING DEPLOYMENT

### "Playwright browser not found"
```bash
playwright install chromium
playwright install-deps  # Linux only
```

### "Permission denied" on VPS
```bash
# Run as root or use sudo
sudo pip3 install ...
```

### "Out of memory" on small VPS
```bash
# Process sites one at a time
# Or upgrade to 2GB RAM droplet ($12/month)
```

### "OpenAI rate limit exceeded"
```bash
# Add delays between properties
# Or process in smaller batches
```

---

## 💡 BEST PRACTICES

1. **Start small** - Test with 5 properties first
2. **Verify quality** - Check 1-2 results manually
3. **Save incrementally** - Don't lose data if it crashes
4. **Monitor costs** - Check OpenAI usage dashboard
5. **Backup results** - Save JSON files to cloud storage
6. **Update regularly** - Re-scrape monthly or quarterly

---

## 📞 SUMMARY

**After Replit Agent completes:**

1. **Test on Replit** - Verify it's set up correctly
2. **Download to local** - Fastest way to get results
3. **Run scraper locally** - Process your 26 sites
4. **Optional: Deploy to VPS** - For automation

**Total time from Replit to results:** ~2-4 hours
**Total cost:** $10-30 (API fees) + $0-6 (VPS if used)

---

You'll have complete property data for all 26 competitors in JSON/CSV format, ready for analysis!
