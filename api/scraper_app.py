"""
FastAPI web application for universal property scraping.
Password-protected web interface with scrape history.
"""

from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crawler import Crawler
from src.llm_extractor import LLMPropertyExtractor
from src.models import SiteConfig, CrawlSettings
from src.utils import setup_logging
from urllib.parse import urlparse

# Setup logging
setup_logging(level="INFO")
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Universal Property Scraper")

# Security
security = HTTPBasic()

# Simple password authentication
USERNAME = os.getenv("SCRAPER_USERNAME", "admin")
PASSWORD = os.getenv("SCRAPER_PASSWORD", "changeme123")  # Change this!

# Templates
templates = Jinja2Templates(directory="templates/scraper")

# Ensure directories exist
Path("data/scrapes").mkdir(parents=True, exist_ok=True)
Path("static").mkdir(parents=True, exist_ok=True)

# In-memory storage for scrape status (in production, use Redis)
scrape_jobs = {}


def verify_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify username and password."""
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, username: str = Depends(verify_auth)):
    """Home page with scraping form."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "username": username
    })


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request, username: str = Depends(verify_auth)):
    """View scrape history."""
    # Load all completed scrapes
    scrapes = []
    scrape_dir = Path("data/scrapes")

    if scrape_dir.exists():
        for scrape_file in sorted(scrape_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(scrape_file, 'r') as f:
                    metadata_file = scrape_file.parent / f"{scrape_file.stem}_metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as mf:
                            metadata = json.load(mf)
                            metadata['scrape_id'] = scrape_file.stem
                            scrapes.append(metadata)
            except Exception as e:
                logger.error(f"Error loading scrape {scrape_file}: {e}")

    return templates.TemplateResponse("history.html", {
        "request": request,
        "scrapes": scrapes,
        "username": username
    })


@app.post("/scrape")
async def start_scrape(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    company: str = Form(...),
    username: str = Depends(verify_auth)
):
    """Start a new scraping job."""

    # Generate job ID
    job_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Initialize job status
    scrape_jobs[job_id] = {
        "status": "starting",
        "url": url,
        "company": company,
        "started_at": datetime.now().isoformat(),
        "progress": 0,
        "total": 0,
        "message": "Initializing scraper..."
    }

    # Start background task
    background_tasks.add_task(run_scrape, job_id, url, company)

    return JSONResponse({
        "job_id": job_id,
        "message": "Scraping started"
    })


async def run_scrape(job_id: str, url: str, company: str):
    """Background task to run the scraping."""

    try:
        # Update status
        scrape_jobs[job_id]["status"] = "discovering"
        scrape_jobs[job_id]["message"] = "Discovering property listings..."

        # Extract domain
        domain = urlparse(url).netloc.replace('www.', '')

        # Create config
        config = SiteConfig(
            manager_name=company,
            manager_domain=domain,
            market_name="Unknown",
            seed_urls=[url],
            listing_url_patterns=["/property/", "/rental/", "/vacation-rental/", "/unit/"],
            excluded_url_patterns=["/blog", "/about", "/contact", "/cart", "/checkout", "/search"],
            crawl_settings=CrawlSettings(
                max_concurrency=2,
                min_delay_ms=1000,
                scroll_attempts=3,
                max_depth=2
            )
        )

        # Discover URLs
        crawler = Crawler(config)
        listing_urls = await crawler.discover_listing_urls()

        scrape_jobs[job_id]["total"] = len(listing_urls)
        scrape_jobs[job_id]["message"] = f"Found {len(listing_urls)} properties. Extracting data..."
        scrape_jobs[job_id]["status"] = "extracting"

        # Get OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            scrape_jobs[job_id]["status"] = "failed"
            scrape_jobs[job_id]["message"] = "OpenAI API key not configured"
            return

        # Extract property data
        extractor = LLMPropertyExtractor(api_key=api_key, model="gpt-4o-mini")
        properties = []

        await crawler.start()

        try:
            for i, listing_url in enumerate(listing_urls, 1):
                try:
                    # Update progress
                    scrape_jobs[job_id]["progress"] = i
                    scrape_jobs[job_id]["message"] = f"Processing property {i}/{len(listing_urls)}..."

                    # Fetch page
                    html_content, success = await crawler.fetch_page_content(listing_url)

                    if not success:
                        continue

                    # Extract data
                    property_data = extractor.extract_property_data(
                        html_content=html_content,
                        url=listing_url,
                        company_name=company
                    )

                    property_data['extracted_at'] = datetime.now().isoformat()
                    properties.append(property_data)

                except Exception as e:
                    logger.error(f"Error processing {listing_url}: {e}")
                    continue

        finally:
            await crawler.close()

        # Save results
        output_file = Path(f"data/scrapes/{job_id}.json")
        with open(output_file, 'w') as f:
            json.dump(properties, f, indent=2)

        # Save metadata
        metadata = {
            "job_id": job_id,
            "url": url,
            "company": company,
            "started_at": scrape_jobs[job_id]["started_at"],
            "completed_at": datetime.now().isoformat(),
            "total_properties": len(properties),
            "total_discovered": len(listing_urls),
            "success_rate": f"{len(properties) / len(listing_urls) * 100:.1f}%" if listing_urls else "0%"
        }

        metadata_file = Path(f"data/scrapes/{job_id}_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Update final status
        scrape_jobs[job_id]["status"] = "completed"
        scrape_jobs[job_id]["message"] = f"Completed! Extracted {len(properties)} properties"
        scrape_jobs[job_id]["properties_count"] = len(properties)

    except Exception as e:
        logger.error(f"Scrape job {job_id} failed: {str(e)}", exc_info=True)
        scrape_jobs[job_id]["status"] = "failed"
        scrape_jobs[job_id]["message"] = f"Error: {str(e)}"


@app.get("/status/{job_id}")
async def get_status(job_id: str, username: str = Depends(verify_auth)):
    """Get status of a scraping job."""
    if job_id not in scrape_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return JSONResponse(scrape_jobs[job_id])


@app.get("/download/{scrape_id}")
async def download_results(scrape_id: str, username: str = Depends(verify_auth)):
    """Download scrape results as JSON."""
    file_path = Path(f"data/scrapes/{scrape_id}.json")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Results not found")

    return FileResponse(
        file_path,
        filename=f"{scrape_id}.json",
        media_type="application/json"
    )


@app.get("/download/{scrape_id}/csv")
async def download_csv(scrape_id: str, username: str = Depends(verify_auth)):
    """Download scrape results as CSV."""
    json_file = Path(f"data/scrapes/{scrape_id}.json")

    if not json_file.exists():
        raise HTTPException(status_code=404, detail="Results not found")

    # Convert JSON to CSV
    import csv
    import tempfile

    with open(json_file, 'r') as f:
        properties = json.load(f)

    if not properties:
        raise HTTPException(status_code=404, detail="No properties in results")

    # Create temporary CSV file
    csv_file = Path(f"data/scrapes/{scrape_id}.csv")

    fieldnames = [
        'property_management_company', 'property_name', 'listing_url',
        'street_address', 'city', 'state', 'zip_code', 'country',
        'bedrooms', 'bathrooms', 'sleeps',
        'nightly_rate_min', 'nightly_rate_max',
        'property_id', 'description',
        'confidence', 'extraction_method', 'model_used', 'extracted_at'
    ]

    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(properties)

    return FileResponse(
        csv_file,
        filename=f"{scrape_id}.csv",
        media_type="text/csv"
    )


@app.get("/health")
async def health_check():
    """Health check endpoint (no auth required)."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
