# Complete Specification: Universal Vacation Rental Property Scraper Web Application

## 📋 Table of Contents

1. [Overview](#overview)
2. [Technical Stack](#technical-stack)
3. [System Architecture](#system-architecture)
4. [File Structure](#file-structure)
5. [Detailed Component Specifications](#detailed-component-specifications)
6. [API Endpoints](#api-endpoints)
7. [Data Models](#data-models)
8. [Frontend Specifications](#frontend-specifications)
9. [Backend Logic](#backend-logic)
10. [Deployment Configuration](#deployment-configuration)
11. [Environment Variables](#environment-variables)
12. [User Flows](#user-flows)
13. [Implementation Steps](#implementation-steps)

---

## Overview

### Purpose
Build a web application that allows non-technical users to scrape property data from ANY vacation rental website through a simple web form interface. No coding or terminal knowledge required.

### Core Functionality
1. **Universal Web Scraping**: Accept any vacation rental website URL
2. **Intelligent Discovery**: Find all individual property listing URLs from an index page
3. **AI-Powered Extraction**: Use OpenAI GPT-4o-mini to extract complete property data from any HTML structure
4. **Real-Time Progress**: Show live progress updates via AJAX polling
5. **Data Export**: Download results as JSON or CSV
6. **History Tracking**: Save all scrapes to SQLite database with permanent download links
7. **Authentication**: Password-protected access using HTTP Basic Auth

### Key Requirements
- **No configuration needed**: Works on any vacation rental site without YAML configs
- **Non-technical interface**: Web form only, no CLI
- **Password protected**: Secure access
- **Persistent storage**: SQLite database for scrape history
- **Background processing**: Long-running scrapes don't block UI
- **Real-time updates**: Progress bar updates every 2 seconds

---

## Technical Stack

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **ASGI Server**: Uvicorn
- **Template Engine**: Jinja2 (for serving HTML)
- **Authentication**: HTTP Basic Auth (fastapi.security.HTTPBasic)
- **Database**: SQLite3 (built-in Python)
- **Async**: asyncio for background tasks

### Web Scraping
- **Browser Automation**: Playwright (async version)
- **HTML Parsing**: BeautifulSoup4
- **LLM Integration**: OpenAI Python SDK (gpt-4o-mini model)

### Frontend
- **Pure JavaScript** (no frameworks - vanilla JS)
- **AJAX**: Fetch API for polling
- **CSS**: Inline styles with gradient design
- **No build process**: Everything in single HTML files

### Deployment
- **Platform**: Railway.app
- **Process Manager**: Uvicorn (specified in Procfile)
- **Python Version**: 3.9+ (specified in railway.json or detected automatically)

---

## System Architecture

### High-Level Flow

```
User Browser
    ↓
[HTTP Basic Auth]
    ↓
FastAPI Application
    ↓
POST /scrape → Background Task Started
    ↓
[Playwright Crawler]
    ├─→ Discover property URLs (crawler.py)
    └─→ Extract data with OpenAI (llm_extractor.py)
    ↓
Store in SQLite Database
    ↓
User polls GET /status/{job_id}
    ↓
Returns: {status, message, progress, total}
    ↓
User downloads GET /download/{scrape_id}
```

### Component Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (HTML/JS)              │
│  - Form submission                      │
│  - AJAX status polling (2 sec interval) │
│  - Progress bar rendering               │
│  - Download button management           │
└─────────────┬───────────────────────────┘
              │
              ↓ HTTP Requests
┌─────────────────────────────────────────┐
│       FastAPI Backend (Python)          │
│  - Route handling                       │
│  - HTTP Basic Auth                      │
│  - Background task management           │
│  - In-memory job status tracking        │
│  - SQLite database operations           │
└─────────────┬───────────────────────────┘
              │
              ↓ Delegates to
┌─────────────────────────────────────────┐
│    Scraping Engine (Async)              │
│  ┌────────────────────────────────┐    │
│  │ 1. Playwright Crawler          │    │
│  │    - Launch browser             │    │
│  │    - Navigate to seed URL       │    │
│  │    - Discover listing URLs      │    │
│  │    - Handle pagination/scroll   │    │
│  └────────────────────────────────┘    │
│  ┌────────────────────────────────┐    │
│  │ 2. OpenAI Extractor             │    │
│  │    - Fetch each listing page    │    │
│  │    - Clean HTML content         │    │
│  │    - Send to OpenAI API         │    │
│  │    - Parse JSON response        │    │
│  └────────────────────────────────┘    │
└─────────────┬───────────────────────────┘
              │
              ↓ Stores to
┌─────────────────────────────────────────┐
│        SQLite Database                  │
│  - scrapes table                        │
│  - properties table (JSON blob)         │
└─────────────────────────────────────────┘
```

---

## File Structure

### Required Directory Structure

```
portoro-scraper-engine/
├── api/
│   └── scraper_app.py              # Main FastAPI application
├── src/
│   ├── __init__.py
│   ├── crawler.py                  # Playwright-based URL discovery
│   ├── llm_extractor.py           # OpenAI-powered data extraction
│   ├── models.py                   # Data classes (PropertyData)
│   └── db.py                       # Database operations (optional helper)
├── templates/
│   └── scraper/
│       ├── index.html              # Main scraping form page
│       └── history.html            # Scrape history page
├── data/                           # Created at runtime
│   └── scraper.db                  # SQLite database (auto-created)
├── requirements.txt                # Python dependencies
├── Procfile                        # Railway start command
├── railway.json                    # Railway build configuration
├── .gitignore
└── README.md
```

### Files to Create

You need to create these files:

1. **`api/scraper_app.py`** - Main FastAPI application (~400 lines)
2. **`templates/scraper/index.html`** - Main scraping form (~250 lines)
3. **`templates/scraper/history.html`** - History page (~200 lines)
4. **`Procfile`** - Single line deployment config
5. **`railway.json`** - Railway build configuration (~15 lines)

**Note**: Files `src/crawler.py`, `src/llm_extractor.py`, and `src/models.py` already exist in the project and should be imported.

---

## Detailed Component Specifications

### 1. FastAPI Backend (`api/scraper_app.py`)

#### Imports Required

```python
from fastapi import FastAPI, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi import Request
import secrets
import asyncio
import os
import json
import csv
import sqlite3
from datetime import datetime
from typing import Dict, Optional, List
import uuid
from pathlib import Path

# Import from existing scraper modules
from src.crawler import PlaywrightCrawler
from src.llm_extractor import LLMPropertyExtractor
from src.models import PropertyData
```

#### Application Initialization

```python
app = FastAPI(title="Universal Property Scraper")
security = HTTPBasic()
templates = Jinja2Templates(directory="templates/scraper")

# In-memory job tracking
jobs: Dict[str, dict] = {}

# Database setup
DB_PATH = "data/scraper.db"
```

#### Authentication Configuration

**Environment Variables:**
- `SCRAPER_USERNAME` - default: "admin"
- `SCRAPER_PASSWORD` - default: "portoro2024"

**Implementation:**

```python
def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify HTTP Basic Auth credentials"""
    correct_username = secrets.compare_digest(
        credentials.username,
        os.getenv("SCRAPER_USERNAME", "admin")
    )
    correct_password = secrets.compare_digest(
        credentials.password,
        os.getenv("SCRAPER_PASSWORD", "portoro2024")
    )
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
```

#### Database Schema

**Table: `scrapes`**

```sql
CREATE TABLE IF NOT EXISTS scrapes (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    company TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'processing', 'completed', 'failed'
    property_count INTEGER DEFAULT 0,
    properties_json TEXT,  -- JSON array of PropertyData objects
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
)
```

**Initialize database function:**

```python
def init_db():
    """Create database and tables if they don't exist"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scrapes (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            company TEXT NOT NULL,
            status TEXT NOT NULL,
            property_count INTEGER DEFAULT 0,
            properties_json TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Call on startup
@app.on_event("startup")
async def startup_event():
    init_db()
```

#### API Routes

##### 1. GET `/` - Main Page

```python
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, username: str = Depends(get_current_username)):
    """Render main scraping form"""
    return templates.TemplateResponse("index.html", {"request": request})
```

##### 2. POST `/scrape` - Start Scraping Job

**Parameters:**
- `url` (Form field) - The vacation rental website URL
- `company` (Form field) - Company name

**Returns:**
```json
{
    "job_id": "uuid-string",
    "message": "Scraping started"
}
```

**Implementation:**

```python
@app.post("/scrape")
async def start_scrape(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    company: str = Form(...),
    username: str = Depends(get_current_username)
):
    """Start a new scraping job"""
    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Initialize job status
    jobs[job_id] = {
        "status": "processing",
        "message": "Starting scraper...",
        "progress": 0,
        "total": 0,
        "scrape_id": None,
        "url": url,
        "company": company
    }

    # Create database record
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO scrapes (id, url, company, status) VALUES (?, ?, ?, ?)",
        (job_id, url, company, "processing")
    )
    conn.commit()
    conn.close()

    # Start background scraping task
    background_tasks.add_task(run_scrape, job_id, url, company)

    return {"job_id": job_id, "message": "Scraping started"}
```

##### 3. GET `/status/{job_id}` - Check Job Status

**Returns:**
```json
{
    "status": "processing|completed|failed",
    "message": "Current status message",
    "progress": 15,
    "total": 47,
    "scrape_id": "job-uuid"  // Only present when completed
}
```

**Implementation:**

```python
@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Get real-time status of a scraping job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs[job_id]
```

##### 4. GET `/history` - Get All Scrapes

**Returns:**
```json
[
    {
        "id": "uuid",
        "url": "https://example.com",
        "company": "Example Rentals",
        "status": "completed",
        "property_count": 47,
        "created_at": "2025-01-15 10:30:00"
    },
    ...
]
```

**Implementation:**

```python
@app.get("/history")
async def get_history(username: str = Depends(get_current_username)):
    """Get all scrape history"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, url, company, status, property_count, created_at "
        "FROM scrapes ORDER BY created_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]
```

##### 5. GET `/history-page` - History HTML Page

```python
@app.get("/history-page", response_class=HTMLResponse)
async def history_page(request: Request, username: str = Depends(get_current_username)):
    """Render history page"""
    return templates.TemplateResponse("history.html", {"request": request})
```

##### 6. GET `/download/{scrape_id}` - Download JSON

**Implementation:**

```python
@app.get("/download/{scrape_id}")
async def download_json(scrape_id: str, username: str = Depends(get_current_username)):
    """Download scrape results as JSON"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT properties_json, company FROM scrapes WHERE id = ?",
        (scrape_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Scrape not found or no data")

    properties_json = row[0]
    company = row[1]

    # Return as downloadable file
    filename = f"{company.replace(' ', '_')}_{scrape_id[:8]}.json"

    return JSONResponse(
        content=json.loads(properties_json),
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
```

##### 7. GET `/download/{scrape_id}/csv` - Download CSV

**Implementation:**

```python
@app.get("/download/{scrape_id}/csv")
async def download_csv(scrape_id: str, username: str = Depends(get_current_username)):
    """Download scrape results as CSV"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT properties_json, company FROM scrapes WHERE id = ?",
        (scrape_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Scrape not found or no data")

    properties = json.loads(row[0])
    company = row[1]

    # Convert to CSV
    csv_path = f"/tmp/{scrape_id}.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        if properties:
            writer = csv.DictWriter(f, fieldnames=properties[0].keys())
            writer.writeheader()
            writer.writerows(properties)

    filename = f"{company.replace(' ', '_')}_{scrape_id[:8]}.csv"

    return FileResponse(
        csv_path,
        media_type="text/csv",
        filename=filename
    )
```

#### Background Scraping Task

**Main scraping function:**

```python
async def run_scrape(job_id: str, url: str, company: str):
    """
    Background task that performs the actual scraping
    Updates job status in real-time
    """
    try:
        # Update status: Discovering properties
        jobs[job_id]["message"] = "Discovering property listings..."

        # Step 1: Discover property URLs using Playwright crawler
        from src.crawler import PlaywrightCrawler

        crawler = PlaywrightCrawler()

        # Extract domain from URL for filtering
        from urllib.parse import urlparse
        domain = urlparse(url).netloc

        # Discover all property listing URLs
        discovered_urls = await crawler.discover_urls(
            seed_url=url,
            url_pattern_filter=domain  # Only keep URLs from same domain
        )

        total_properties = len(discovered_urls)
        jobs[job_id]["total"] = total_properties
        jobs[job_id]["message"] = f"Found {total_properties} properties"

        await asyncio.sleep(2)  # Brief pause

        # Step 2: Extract data from each property page using OpenAI
        jobs[job_id]["message"] = "Extracting property data..."

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY environment variable not set")

        extractor = LLMPropertyExtractor(api_key=api_key, model="gpt-4o-mini")

        properties = []
        for idx, prop_url in enumerate(discovered_urls):
            try:
                # Fetch HTML
                async with crawler.browser.new_page() as page:
                    await page.goto(prop_url, wait_until="networkidle")
                    html_content = await page.content()

                # Extract property data using OpenAI
                property_data = await extractor.extract_property_data(
                    html_content=html_content,
                    url=prop_url,
                    company_name=company
                )

                properties.append(property_data)

                # Update progress
                jobs[job_id]["progress"] = idx + 1
                jobs[job_id]["message"] = f"Extracting data... {idx + 1} / {total_properties}"

            except Exception as e:
                # Log error but continue with other properties
                print(f"Error extracting {prop_url}: {str(e)}")
                continue

        # Step 3: Save to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE scrapes
               SET status = ?, property_count = ?, properties_json = ?, completed_at = ?
               WHERE id = ?""",
            ("completed", len(properties), json.dumps(properties), datetime.now(), job_id)
        )
        conn.commit()
        conn.close()

        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["message"] = f"Complete! Extracted {len(properties)} properties"
        jobs[job_id]["scrape_id"] = job_id

    except Exception as e:
        # Handle errors
        error_message = str(e)

        # Update database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE scrapes SET status = ?, error_message = ? WHERE id = ?",
            ("failed", error_message, job_id)
        )
        conn.commit()
        conn.close()

        # Update job status
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Error: {error_message}"

    finally:
        # Cleanup
        if 'crawler' in locals():
            await crawler.close()
```

**Note on crawler.discover_urls():**

This function should be in `src/crawler.py`. If it doesn't exist, here's the specification:

```python
class PlaywrightCrawler:
    async def discover_urls(self, seed_url: str, url_pattern_filter: str = None) -> List[str]:
        """
        Discover all property listing URLs from a seed URL

        Args:
            seed_url: Starting URL (e.g., https://example.com/rentals)
            url_pattern_filter: Domain to filter URLs (e.g., 'example.com')

        Returns:
            List of discovered property listing URLs

        Algorithm:
            1. Navigate to seed_url
            2. Scroll page to trigger lazy loading
            3. Extract all <a> links
            4. Filter to keep only listing URLs (heuristic: longer paths, not /about, /contact, etc.)
            5. Remove duplicates
            6. Return list
        """
        # Implementation here
```

---

### 2. Frontend: Main Page (`templates/scraper/index.html`)

#### HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Universal Property Scraper</title>
    <style>
        /* Styles here - see full specification below */
    </style>
</head>
<body>
    <div class="container">
        <h1>🏖️ Universal Property Scraper</h1>
        <p class="subtitle">Extract property data from any vacation rental website</p>

        <form id="scrapeForm">
            <div class="form-group">
                <label for="url">Website URL</label>
                <input type="url" id="url" name="url" required
                       placeholder="https://www.example.com/vacation-rentals">
                <small>Paste the URL of the vacation rental listings page</small>
            </div>

            <div class="form-group">
                <label for="company">Company Name</label>
                <input type="text" id="company" name="company" required
                       placeholder="Example Rentals">
                <small>Enter the property management company name</small>
            </div>

            <button type="submit" id="submitBtn">Start Scraping</button>
        </form>

        <div id="progressContainer" style="display: none;">
            <div class="progress-bar">
                <div id="progressBar" class="progress-fill"></div>
            </div>
            <p id="statusMessage">Initializing...</p>
            <p id="progressText">0 / 0</p>
        </div>

        <div id="resultsContainer" style="display: none;">
            <h2>✅ Scraping Complete!</h2>
            <p id="resultsMessage"></p>
            <div class="button-group">
                <a id="downloadJsonBtn" class="download-btn" download>Download JSON</a>
                <a id="downloadCsvBtn" class="download-btn" download>Download CSV</a>
            </div>
        </div>

        <div class="footer">
            <a href="/history-page">View Scrape History →</a>
        </div>
    </div>

    <script>
        /* JavaScript here - see full specification below */
    </script>
</body>
</html>
```

#### CSS Styles

**Design Requirements:**
- Gradient purple background (from `#667eea` to `#764ba2`)
- White container with rounded corners and shadow
- Clean, modern form inputs
- Animated progress bar
- Responsive design (mobile-friendly)

**Full styles:**

```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.container {
    background: white;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    max-width: 600px;
    width: 100%;
    padding: 40px;
}

h1 {
    color: #333;
    margin-bottom: 10px;
    font-size: 28px;
}

.subtitle {
    color: #666;
    margin-bottom: 30px;
    font-size: 14px;
}

.form-group {
    margin-bottom: 20px;
}

label {
    display: block;
    margin-bottom: 8px;
    color: #333;
    font-weight: 600;
    font-size: 14px;
}

input[type="url"],
input[type="text"] {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 14px;
    transition: border-color 0.3s;
}

input:focus {
    outline: none;
    border-color: #667eea;
}

small {
    display: block;
    margin-top: 4px;
    color: #888;
    font-size: 12px;
}

button[type="submit"] {
    width: 100%;
    padding: 14px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
}

#progressContainer {
    margin-top: 30px;
    padding-top: 30px;
    border-top: 2px solid #f0f0f0;
}

.progress-bar {
    width: 100%;
    height: 30px;
    background: #f0f0f0;
    border-radius: 15px;
    overflow: hidden;
    margin-bottom: 15px;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #10b981 0%, #059669 100%);
    width: 0%;
    transition: width 0.5s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 12px;
}

#statusMessage {
    color: #333;
    font-weight: 600;
    margin-bottom: 5px;
}

#progressText {
    color: #666;
    font-size: 14px;
}

#resultsContainer {
    margin-top: 30px;
    padding: 20px;
    background: #d4edda;
    border-radius: 10px;
    text-align: center;
}

#resultsContainer h2 {
    color: #155724;
    margin-bottom: 10px;
}

#resultsMessage {
    color: #155724;
    margin-bottom: 20px;
}

.button-group {
    display: flex;
    gap: 10px;
    justify-content: center;
    flex-wrap: wrap;
}

.download-btn {
    display: inline-block;
    padding: 12px 24px;
    background: #10b981;
    color: white;
    text-decoration: none;
    border-radius: 8px;
    font-weight: 600;
    transition: background 0.3s;
}

.download-btn:hover {
    background: #059669;
}

.footer {
    margin-top: 30px;
    text-align: center;
}

.footer a {
    color: #667eea;
    text-decoration: none;
    font-size: 14px;
}

.footer a:hover {
    text-decoration: underline;
}
```

#### JavaScript Logic

**Requirements:**
1. Intercept form submission
2. Send POST to `/scrape` endpoint
3. Start polling `/status/{job_id}` every 2 seconds
4. Update progress bar and status messages
5. When complete, show download buttons
6. Handle errors gracefully

**Full implementation:**

```javascript
let currentJobId = null;
let pollInterval = null;

// Handle form submission
document.getElementById('scrapeForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const url = document.getElementById('url').value;
    const company = document.getElementById('company').value;

    // Disable form
    document.getElementById('submitBtn').disabled = true;
    document.getElementById('submitBtn').textContent = 'Starting...';

    // Hide results if previously shown
    document.getElementById('resultsContainer').style.display = 'none';

    try {
        // Start scraping
        const response = await fetch('/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `url=${encodeURIComponent(url)}&company=${encodeURIComponent(company)}`
        });

        if (!response.ok) {
            throw new Error('Failed to start scraping');
        }

        const data = await response.json();
        currentJobId = data.job_id;

        // Show progress container
        document.getElementById('progressContainer').style.display = 'block';

        // Start polling for status
        startPolling();

    } catch (error) {
        alert('Error starting scrape: ' + error.message);
        resetForm();
    }
});

function startPolling() {
    // Poll every 2 seconds
    pollInterval = setInterval(checkStatus, 2000);

    // Also check immediately
    checkStatus();
}

async function checkStatus() {
    try {
        const response = await fetch(`/status/${currentJobId}`);

        if (!response.ok) {
            throw new Error('Failed to get status');
        }

        const status = await response.json();

        // Update UI
        document.getElementById('statusMessage').textContent = status.message;

        if (status.total > 0) {
            const percentage = (status.progress / status.total) * 100;
            document.getElementById('progressBar').style.width = percentage + '%';
            document.getElementById('progressBar').textContent = Math.round(percentage) + '%';
            document.getElementById('progressText').textContent = `${status.progress} / ${status.total}`;
        }

        // Check if completed or failed
        if (status.status === 'completed') {
            clearInterval(pollInterval);
            showResults(status);
        } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            showError(status.message);
        }

    } catch (error) {
        console.error('Error checking status:', error);
    }
}

function showResults(status) {
    // Hide progress
    document.getElementById('progressContainer').style.display = 'none';

    // Show results
    const resultsContainer = document.getElementById('resultsContainer');
    resultsContainer.style.display = 'block';

    const count = status.total;
    document.getElementById('resultsMessage').textContent =
        `Successfully extracted data from ${count} properties!`;

    // Set download links
    document.getElementById('downloadJsonBtn').href = `/download/${status.scrape_id}`;
    document.getElementById('downloadCsvBtn').href = `/download/${status.scrape_id}/csv`;

    // Reset form
    resetForm();
}

function showError(message) {
    alert('Scraping failed: ' + message);
    document.getElementById('progressContainer').style.display = 'none';
    resetForm();
}

function resetForm() {
    document.getElementById('submitBtn').disabled = false;
    document.getElementById('submitBtn').textContent = 'Start Scraping';
}
```

---

### 3. Frontend: History Page (`templates/scraper/history.html`)

#### HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scrape History</title>
    <style>
        /* Similar base styles to index.html */
        /* Plus table-specific styles - see below */
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 Scrape History</h1>
        <p class="subtitle">View and download your past property scrapes</p>

        <a href="/" class="nav-link">← Back to Scraper</a>

        <div id="historyContent">
            <div class="empty-state">
                <h2>Loading...</h2>
            </div>
        </div>
    </div>

    <script>
        /* JavaScript to load and display history */
    </script>
</body>
</html>
```

#### Additional CSS for History Page

```css
.nav-link {
    display: inline-block;
    margin-bottom: 20px;
    color: #667eea;
    text-decoration: none;
    font-size: 14px;
}

.nav-link:hover {
    text-decoration: underline;
}

.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #666;
}

.table-container {
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}

thead {
    background: #f8f9fa;
}

th {
    padding: 12px 16px;
    text-align: left;
    font-weight: 600;
    color: #333;
    border-bottom: 2px solid #e0e0e0;
    font-size: 14px;
}

td {
    padding: 12px 16px;
    border-bottom: 1px solid #f0f0f0;
    font-size: 14px;
    color: #555;
}

tr:hover {
    background: #f8f9fa;
}

.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}

.status-completed {
    background: #d4edda;
    color: #155724;
}

.status-failed {
    background: #f8d7da;
    color: #721c24;
}

.status-processing {
    background: #fff3cd;
    color: #856404;
}

.download-btn-small {
    display: inline-block;
    padding: 6px 12px;
    margin-right: 5px;
    background: #10b981;
    color: white;
    text-decoration: none;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
}

.download-btn-small:hover {
    background: #059669;
}
```

#### JavaScript for History Page

```javascript
async function loadHistory() {
    try {
        const response = await fetch('/history');
        const scrapes = await response.json();

        const container = document.getElementById('historyContent');

        if (scrapes.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h2>No scrapes yet</h2>
                    <p>Start your first scrape from the <a href="/">main page</a></p>
                </div>
            `;
            return;
        }

        // Build table
        let html = `
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Company</th>
                            <th>Website</th>
                            <th>Properties</th>
                            <th>Status</th>
                            <th>Date</th>
                            <th>Downloads</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        scrapes.forEach(scrape => {
            const statusClass = scrape.status === 'completed' ? 'status-completed' :
                              scrape.status === 'failed' ? 'status-failed' : 'status-processing';
            const statusText = scrape.status === 'completed' ? '✅ Complete' :
                             scrape.status === 'failed' ? '❌ Failed' : '⏳ Processing';

            const date = new Date(scrape.created_at).toLocaleString();

            html += `
                <tr>
                    <td><strong>${escapeHtml(scrape.company)}</strong></td>
                    <td>
                        <a href="${escapeHtml(scrape.url)}" target="_blank">
                            ${escapeHtml(scrape.url)}
                        </a>
                    </td>
                    <td>${scrape.property_count}</td>
                    <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                    <td>${date}</td>
                    <td>
                        ${scrape.status === 'completed' && scrape.property_count > 0 ? `
                            <a href="/download/${scrape.id}" class="download-btn-small">JSON</a>
                            <a href="/download/${scrape.id}/csv" class="download-btn-small">CSV</a>
                        ` : '-'}
                    </td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = html;

    } catch (error) {
        console.error('Failed to load history:', error);
        document.getElementById('historyContent').innerHTML = `
            <div class="empty-state">
                <h2>Error loading history</h2>
                <p>${error.message}</p>
            </div>
        `;
    }
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Load history on page load
loadHistory();
```

---

### 4. Deployment Files

#### `Procfile`

```
web: uvicorn api.scraper_app:app --host 0.0.0.0 --port $PORT
```

**Explanation:**
- `web:` - Tells Railway this is a web service
- `uvicorn` - ASGI server
- `api.scraper_app:app` - Path to FastAPI app object
- `--host 0.0.0.0` - Listen on all interfaces
- `--port $PORT` - Use Railway's provided port

#### `railway.json`

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt && playwright install chromium && playwright install-deps chromium"
  },
  "deploy": {
    "startCommand": "uvicorn api.scraper_app:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Explanation:**
- `buildCommand` - Install Python deps and Playwright browser
- `startCommand` - Same as Procfile
- `healthcheckPath` - Railway will check `/` to verify app is running
- `restartPolicyType` - Restart on failures

#### `requirements.txt`

```
# Core dependencies
playwright>=1.40.0
beautifulsoup4>=4.12.0
pyyaml>=6.0
lxml>=4.9.0
python-dateutil>=2.8.0

# LLM-powered extraction
openai>=1.0.0

# Web API
fastapi>=0.100.0
uvicorn>=0.23.0
jinja2>=3.1.0
python-multipart>=0.0.6
aiofiles>=23.0.0

# Optional: advanced text extraction
trafilatura>=1.6.0
```

---

## Data Models

### PropertyData (from `src/models.py`)

```python
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class PropertyData:
    """Complete property information extracted from a listing page"""
    listing_url: str
    property_management_company: Optional[str] = None
    property_name: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "USA"
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sleeps: Optional[int] = None
    nightly_rate_min: Optional[float] = None
    nightly_rate_max: Optional[float] = None
    amenities: List[str] = field(default_factory=list)
    description: Optional[str] = None
    property_id: Optional[str] = None
    confidence: float = 0.0
    extraction_method: str = "unknown"
    model_used: Optional[str] = None
```

**When serializing to JSON for database storage:**

```python
import json
from dataclasses import asdict

# Convert to dict
property_dict = asdict(property_data)

# Store in database
properties_json = json.dumps([property_dict for property_data in properties])
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o-mini | `sk-proj-abc123...` |

### Optional (with defaults)

| Variable | Description | Default |
|----------|-------------|---------|
| `SCRAPER_USERNAME` | Login username | `admin` |
| `SCRAPER_PASSWORD` | Login password | `portoro2024` |
| `PORT` | Server port | `8000` (Railway sets this) |

---

## User Flows

### Flow 1: First-Time User Scrapes a Site

1. User navigates to Railway URL (e.g., `https://app.railway.app`)
2. Browser shows HTTP Basic Auth prompt
3. User enters username/password (from env vars)
4. User sees main scraping form
5. User pastes URL: `https://www.30aescapes.com/all-rentals`
6. User types company: `30A Escapes`
7. User clicks "Start Scraping"
8. Button becomes disabled, shows "Starting..."
9. Progress container appears, shows "Discovering property listings..."
10. After 5-10 seconds: "Found 47 properties"
11. Progress bar starts updating: "Extracting data... 1 / 47"
12. Progress bar updates every 2 seconds
13. After 5-10 minutes: "✅ Complete! Extracted 47 properties"
14. Green success box appears with two download buttons
15. User clicks "Download CSV"
16. Browser downloads `30A_Escapes_abc123.csv`
17. User opens in Excel, sees 47 rows with complete property data

### Flow 2: User Views History

1. From main page, user clicks "View Scrape History →"
2. New page loads showing table of all past scrapes
3. User sees: Company | Website | Properties | Status | Date | Downloads
4. User sees their previous scrape: "30A Escapes | ... | 47 | ✅ Complete | Jan 15 10:30 | [JSON] [CSV]"
5. User clicks "CSV" button
6. Browser downloads the same file again
7. User clicks "← Back to Scraper"
8. Returns to main form

### Flow 3: Scraping Fails

1. User enters URL of a password-protected site
2. Clicks "Start Scraping"
3. Progress shows "Discovering property listings..."
4. After 30 seconds: Alert "Scraping failed: Unable to access site - may require login"
5. Form resets to enabled state
6. User can try different URL

---

## Implementation Steps

### Step 1: Set Up Project Structure

```bash
mkdir -p api templates/scraper data
touch api/__init__.py
touch api/scraper_app.py
touch templates/scraper/index.html
touch templates/scraper/history.html
touch Procfile
touch railway.json
```

### Step 2: Implement Backend (`api/scraper_app.py`)

1. Add all imports
2. Initialize FastAPI app
3. Set up authentication function
4. Create database initialization
5. Implement all 7 API routes
6. Implement background scraping task
7. Add startup event to init database

**Order of implementation:**
1. `/` route (just return "Hello World" first)
2. Authentication dependency
3. Database init
4. `/scrape` route (without background task first - just return job_id)
5. `/status/{job_id}` route (return dummy status first)
6. Background task `run_scrape()` (implement fully)
7. `/history` route
8. `/download/{scrape_id}` routes
9. `/history-page` route

### Step 3: Create Frontend - Main Page

1. Create `templates/scraper/index.html`
2. Add HTML structure (form, progress, results containers)
3. Add CSS styles (copy from specification above)
4. Add JavaScript:
   - Form submission handler
   - POST to `/scrape`
   - Status polling loop
   - Progress bar updates
   - Result display

### Step 4: Create Frontend - History Page

1. Create `templates/scraper/history.html`
2. Add HTML structure (table container, empty state)
3. Add CSS styles
4. Add JavaScript:
   - Fetch `/history` on load
   - Build table dynamically
   - Handle empty state

### Step 5: Add Deployment Files

1. Create `Procfile` with single line
2. Create `railway.json` with build/deploy config
3. Verify `requirements.txt` has all dependencies

### Step 6: Test Locally

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Set environment variables
export OPENAI_API_KEY="sk-your-key"
export SCRAPER_USERNAME="admin"
export SCRAPER_PASSWORD="test123"

# Run server
uvicorn api.scraper_app:app --reload --port 8000

# Test in browser
# Open http://localhost:8000
# Try scraping a small site (5-10 properties)
```

### Step 7: Deploy to Railway

1. Push code to GitHub
2. Create Railway project
3. Connect GitHub repo
4. Add environment variables in Railway dashboard
5. Wait for deployment
6. Test with Railway URL

---

## Testing Checklist

### Manual Testing

- [ ] Can access main page (authentication works)
- [ ] Form validation works (required fields)
- [ ] Submitting form starts scraping
- [ ] Progress bar appears and updates
- [ ] Status messages are readable
- [ ] Progress percentage is accurate
- [ ] Completion shows download buttons
- [ ] JSON download works
- [ ] CSV download works
- [ ] CSV opens in Excel correctly
- [ ] History page loads
- [ ] History shows correct data
- [ ] History download links work
- [ ] Can scrape multiple sites
- [ ] Can scrape same site twice (both saved in history)
- [ ] Errors are handled gracefully

### Test Sites (Small)

Use these for testing (they have 5-20 properties):

1. Any vacation rental company with "View All" page
2. Filter to small number of results if possible
3. Test on at least 3 different site structures

---

## Common Issues and Solutions

### Issue: Playwright won't install on Railway

**Solution:** Make sure `railway.json` includes:
```json
"buildCommand": "pip install -r requirements.txt && playwright install chromium && playwright install-deps chromium"
```

### Issue: OpenAI API rate limits

**Solution:** Add retry logic with exponential backoff in `llm_extractor.py`

### Issue: Scraping takes too long (timeouts)

**Solution:**
- Reduce concurrency in crawler
- Add timeout to individual property extractions
- Show partial results if some properties fail

### Issue: Can't access password-protected sites

**Expected:** This is a limitation. Show clear error message to user.

### Issue: CSV encoding issues (special characters)

**Solution:** Use `encoding='utf-8'` when writing CSV:
```python
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
```

### Issue: Database locked errors

**Solution:** Use connection pooling or serialize database writes:
```python
# Add timeout
conn = sqlite3.connect(DB_PATH, timeout=10.0)
```

---

## Performance Considerations

### Backend

- **Database**: SQLite is fine for <1000 scrapes. Migrate to PostgreSQL if scaling.
- **Job Storage**: In-memory dict is fine for Railway (single instance). Use Redis for multi-instance.
- **Concurrency**: Limit Playwright concurrent pages to 3-5 to avoid memory issues.

### Frontend

- **Polling Interval**: 2 seconds is good balance between responsiveness and server load.
- **Long Scrapes**: Consider websocket for scrapes >100 properties (optional enhancement).

### Costs

- **Railway**: Free tier includes $5/month credits, ~500 hours. Should cover typical use.
- **OpenAI**: gpt-4o-mini is ~$0.15/1M input tokens. Typical property page = 5K tokens = $0.0008. Very cheap.
- **Bandwidth**: Minimal costs for small-medium usage.

---

## Security Considerations

1. **HTTP Basic Auth**: Simple but sufficient for private tool. For production with many users, use JWT or session-based auth.

2. **Input Validation**:
   - Validate URL format
   - Sanitize company name (prevent XSS)
   - Limit URL length

3. **Rate Limiting**: Consider adding rate limits to prevent abuse:
```python
from fastapi_limiter import FastAPILimiter

@app.post("/scrape")
@limiter.limit("10/hour")  # Max 10 scrapes per hour
async def start_scrape(...):
```

4. **OpenAI API Key**: Keep in environment variable, never commit to git.

5. **Error Messages**: Don't expose internal paths or sensitive info in error messages.

---

## Optional Enhancements

### Enhancement 1: Email Notifications

Add email when scrape completes:

```python
import smtplib
from email.mime.text import MIMEText

def send_completion_email(email, scrape_id, property_count):
    msg = MIMEText(f"Your scrape completed! {property_count} properties extracted.")
    msg['Subject'] = 'Scrape Complete'
    msg['From'] = 'noreply@yourapp.com'
    msg['To'] = email

    # Send via SMTP
    # ... implementation
```

### Enhancement 2: Scrape Scheduling

Allow users to schedule recurring scrapes (weekly, monthly):

```python
# Add scheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@app.post("/schedule-scrape")
async def schedule_scrape(url: str, company: str, frequency: str):
    # Add recurring job
    scheduler.add_job(
        run_scrape,
        'cron',
        week=1,  # Weekly
        args=[uuid.uuid4(), url, company]
    )
```

### Enhancement 3: Export to Google Sheets

Add button to export directly to Google Sheets via API.

### Enhancement 4: Comparison View

Show side-by-side comparison of two scrapes (detect changes in rates, new properties, etc.).

---

## Summary

This specification provides complete details for implementing a universal vacation rental property scraper web application. Key points:

1. **Backend**: FastAPI with HTTP Basic Auth, SQLite database, background tasks
2. **Frontend**: Pure HTML/CSS/JS with AJAX polling for real-time updates
3. **Scraping**: Playwright for discovery + OpenAI for extraction
4. **Deployment**: Railway.app with Procfile and railway.json
5. **User Experience**: Simple form → real-time progress → download results

All code snippets, file structures, and implementation steps are provided above. Follow the implementation steps in order, test locally, then deploy to Railway.

**Total implementation time estimate:** 4-6 hours for experienced developer, including testing.

**Files to create:** 5 main files (scraper_app.py, index.html, history.html, Procfile, railway.json)

**Dependencies:** All listed in requirements.txt (already exists in project)

**Result:** A production-ready web application that non-technical users can use to scrape any vacation rental website with zero coding knowledge.
