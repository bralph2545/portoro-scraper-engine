# Overview

This is a production-grade web scraping system designed to extract vacation rental property addresses from competitor websites. The system is config-driven, allowing new sites to be added through YAML configuration files without code changes. It uses Playwright for real browser automation to handle JavaScript-heavy sites, implements multi-strategy address extraction (schema.org JSON-LD, CSS selectors, text patterns, map widgets), and stores results in a local SQLite database with CSV export capabilities.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Design Pattern

**Config-Driven Architecture**: The system uses YAML configuration files to define scraping targets, enabling non-technical users to add new sites without modifying code. Each site config specifies manager details, seed URLs, optional CSS selectors, and crawl settings.

**Rationale**: Separating configuration from code allows rapid scaling to new sites and reduces deployment risk.

## Component Architecture

**Orchestrator Pattern** (`src/main.py`): The `ScraperOrchestrator` class coordinates the entire workflow:
1. Config loading and validation
2. Database initialization
3. URL discovery (Crawler)
4. Page classification (PageClassifier)
5. Address extraction (AddressExtractor)
6. Address normalization (AddressNormalizer)
7. Data persistence

**Rationale**: Centralized orchestration provides clear control flow and makes it easy to add monitoring, error handling, and retries at the workflow level.

## Crawler Architecture

**Browser-Based Discovery** (`src/crawler.py`): Uses Playwright's async API with headless Chromium to:
- Handle JavaScript rendering and dynamic content
- Navigate pagination, infinite scroll, and "Load More" buttons
- Discover all property listing URLs from seed pages

**Multi-Level Discovery**: 
- Follows links from index/search pages
- Respects configurable depth limits and concurrency settings
- Deduplicates URLs and tracks visited pages

**Rationale**: Real browser automation is necessary for modern JavaScript-heavy sites where simple HTTP requests would miss dynamically loaded content.

## Extraction Architecture

**Multi-Strategy Extraction** (`src/extractor.py`): Attempts multiple methods to find addresses:
1. **Schema.org JSON-LD**: Parses structured data embedded in `<script>` tags
2. **CSS Selectors**: Uses site-specific selectors from config
3. **Text Heuristics**: Searches for keywords like "Address:", "Location:"
4. **Map Widgets**: Extracts coordinates or addresses from embedded maps

**Page Classification**: Uses keyword heuristics to distinguish property listings from blog posts, contact pages, etc.

**Rationale**: Different sites structure data differently. Multiple strategies maximize extraction success rate across diverse site architectures.

## Normalization Architecture

**Address Parsing and Enrichment** (`src/normalizer.py`): 
- Parses raw address strings into structured components (street, city, state, postal code)
- Uses contextual data (market_name, URL paths, manager location) to infer missing fields
- Assigns confidence scores to indicate data quality

**LLM Integration Stub**: Architecture includes placeholder for optional LLM-based address completion that can be swapped in later.

**Rationale**: Many sites provide incomplete addresses (e.g., "123 Beach Road" without city/state). Context-aware enrichment fills gaps while maintaining transparency through confidence scoring.

## Data Model

**Dataclass-Based Models** (`src/models.py`): Type-safe data structures for:
- `SiteConfig`: Site configuration with selectors and settings
- `AddressCandidate`: Raw extracted address data
- `NormalizedAddress`: Parsed and enriched address components
- `ScrapeMetrics`: Performance tracking

**Rationale**: Dataclasses provide type safety, validation, and clear contracts between components without external dependencies.

## Database Design

**SQLite Schema** (`src/db.py`): Five core tables:
- `configs`: Site configurations stored as JSON for API-driven management
- `sites`: Property manager and market information
- `scrape_runs`: Execution metadata, metrics, status, progress tracking, and logs
- `listing_pages`: Discovered URLs and classification results
- `addresses`: Extracted and normalized address data

**Relationships**: 
- Config-based: One config → Many scrape runs → Many listing pages → Many addresses
- Site-based: One site → Many scrape runs → Many listing pages → Many addresses

**Enhanced Features**:
- **Config Management**: CRUD operations for storing and managing site configurations via API
- **Progress Tracking**: Real-time monitoring of scrape runs with current_page/total_pages_estimate
- **Status States**: Scrape runs support queued, running, completed, failed, and cancelled states
- **Execution Logs**: Timestamped log entries stored directly in scrape_runs for debugging
- **Statistics API**: Aggregated metrics for runs by config, status, and date range

**Rationale**: SQLite provides zero-configuration local storage suitable for single-machine deployments, with clear migration path to PostgreSQL if needed. JSON storage in configs table enables flexible, schema-less configuration management.

## Execution Model

**Async/Await Pattern**: Uses Python's asyncio for:
- Concurrent browser page handling
- Non-blocking I/O operations
- Configurable concurrency limits to avoid overwhelming target sites

**Web Application**: FastAPI-based REST API and web dashboard (`api/main.py`):
- **REST API Endpoints**: Full CRUD for configurations, scrape runs management, results retrieval, and statistics
- **Web Dashboard**: HTMX-powered UI for non-technical users with real-time updates
- **Background Tasks**: Async scrape execution in background workers
- **Security**: XSS-safe HTML rendering with Jinja2 auto-escaping, proper error handling with status codes

**CLI Scripts**: Separate entry points for scraping (`scripts/run_scrape.py`) and export (`scripts/export_csv.py`).

**Rationale**: Web interface enables non-technical users to manage scrapes without command-line knowledge. Background task processing keeps API responsive during long-running scrapes.

# External Dependencies

## Core Technologies

**Playwright** (async_playwright): Headless browser automation
- Provides real Chrome/Chromium instance for JavaScript rendering
- Handles complex interactions (clicks, scrolls, waits)
- Alternative considered: Selenium (rejected due to better async support in Playwright)

**BeautifulSoup4** (lxml parser): HTML parsing and CSS selection
- Lightweight parsing for extracted page content
- Used after Playwright retrieves HTML

**PyYAML**: Configuration file parsing
- Loads and validates YAML site configurations

**SQLite3**: Local database (Python standard library)
- Zero-configuration embedded database
- Note: Architecture supports future migration to PostgreSQL with Drizzle ORM

## Future Integration Points

**Geocoding API Stub**: Placeholder for optional geocoding service (Google Maps, Mapbox, etc.) to validate and complete addresses.

**LLM Completion Stub**: Architecture supports adding OpenAI/Anthropic API calls for intelligent address parsing and completion.

## Development Dependencies

**Logging** (Python standard library): Structured logging with configurable levels

**pathlib** (Python standard library): Cross-platform file path handling

**re** (Python standard library): Regular expression patterns for address parsing and URL matching