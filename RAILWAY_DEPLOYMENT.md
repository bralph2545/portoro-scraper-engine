# 🚂 Railway Deployment Guide

## Quick Deploy (5 Minutes)

This guide will help you deploy your Universal Property Scraper to Railway.app - a free hosting service that supports web scraping.

---

## Prerequisites

1. **GitHub Account** - Your code needs to be on GitHub
2. **Railway Account** - Free at https://railway.app (sign up with GitHub)
3. **OpenAI API Key** - Get from https://platform.openai.com/api-keys

---

## Step 1: Push to GitHub

If you haven't already pushed this code to GitHub:

```bash
git add .
git commit -m "Add Railway web app"
git push -u origin claude/cleanup-for-github-01SHmdx9mt3X7xpbWnc77ffn
```

---

## Step 2: Deploy to Railway

1. **Go to Railway.app**
   - Visit https://railway.app
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"

2. **Connect GitHub Repository**
   - Authorize Railway to access your GitHub
   - Select your repository: `bralph2545/portoro-scraper-engine`
   - Select branch: `claude/cleanup-for-github-01SHmdx9mt3X7xpbWnc77ffn`

3. **Railway Will Auto-Detect**
   - It will see the `Procfile` and `railway.json`
   - It will automatically start building

---

## Step 3: Add Environment Variables

In the Railway dashboard:

1. Click on your deployed service
2. Go to **"Variables"** tab
3. Click **"New Variable"**

Add these variables:

| Variable Name | Value | Description |
|--------------|-------|-------------|
| `OPENAI_API_KEY` | `sk-your-key-here` | Your OpenAI API key |
| `SCRAPER_USERNAME` | `admin` | Login username (choose any) |
| `SCRAPER_PASSWORD` | `your-password` | Login password (choose any) |

**IMPORTANT**: Save these credentials somewhere safe - you'll need them to log in!

---

## Step 4: Wait for Deployment

Railway will:
1. Install Python dependencies (~2-3 minutes)
2. Install Playwright browser (~1-2 minutes)
3. Start the web server

You'll see a URL like: `https://your-app.railway.app`

---

## Step 5: Test Your Deployment

1. **Open the URL** (e.g., `https://your-app.railway.app`)
2. **Login** with the username/password you set
3. **Test with a small scrape:**
   - URL: `https://www.30aescapes.com/all-rentals`
   - Company: `30A Escapes`
   - Click "Start Scraping"
4. **Watch the progress bar** - it should update in real-time
5. **Download the results** when complete

---

## Step 6: View History

Click "View Scrape History →" to see all your past scrapes with download links.

---

## Costs

### Railway (Free Tier)
- **$5 free credits/month**
- **500 hours execution time**
- More than enough for typical use
- No credit card required initially

### OpenAI API
- **~$0.01 - $0.10 per property** (using gpt-4o-mini)
- 10 properties = $0.10
- 100 properties = $1.00
- Very affordable!

**Estimated total cost**: $0-5/month for most use cases

---

## Troubleshooting

### "Application Error" on Railway

**Check the logs:**
1. Go to Railway dashboard
2. Click your service
3. Click "Deployments"
4. Click the latest deployment
5. View logs for error messages

**Common issues:**
- Missing environment variables (add OPENAI_API_KEY)
- Playwright installation failed (check build logs)

### "Unauthorized" when accessing the site

- Make sure you set `SCRAPER_USERNAME` and `SCRAPER_PASSWORD` in Railway variables
- Use those exact credentials to log in

### Scraping fails

**Check:**
1. OpenAI API key is correct (starts with `sk-`)
2. You have credits in your OpenAI account
3. The URL you're scraping is publicly accessible
4. Check Railway logs for specific error messages

### Slow deployment

- First deployment takes 5-10 minutes (installing Playwright browser)
- Subsequent deployments are faster (2-3 minutes)

---

## Updating Your Deployment

To update the code after making changes:

```bash
# Make your changes
git add .
git commit -m "Description of changes"
git push

# Railway will automatically redeploy!
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | Your OpenAI API key for property extraction |
| `SCRAPER_USERNAME` | Yes | - | Username for basic auth login |
| `SCRAPER_PASSWORD` | Yes | - | Password for basic auth login |
| `PORT` | No | 8000 | Railway sets this automatically |

---

## Alternative: Use Default Credentials

If you don't want to set environment variables, the app has defaults:
- Username: `admin`
- Password: `portoro2024`

**⚠️ WARNING**: Change these immediately after deployment for security!

---

## Next Steps

Once deployed:

1. **Save your Railway URL** - bookmark it
2. **Save your login credentials** - store them securely
3. **Test with 5-10 properties first** - verify output quality
4. **Then scrape full sites** - download results as JSON/CSV

---

## Getting Help

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **This Project**: Check the logs in Railway dashboard

---

## Summary

✅ **5-minute setup**
✅ **Free hosting** (up to $5/month credits)
✅ **No coding required** - just click and scrape
✅ **Password protected**
✅ **History tracking**
✅ **JSON & CSV downloads**

Your property scraper is ready to use! 🎉
