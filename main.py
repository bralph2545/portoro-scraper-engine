"""FastAPI application for the web scraper system."""

import json
import logging
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime
import csv
import io

from src.db import Database
from src.config import ConfigLoader
from src.utils import setup_logging
from api.models import (
    ConfigCreate, ConfigUpdate, ConfigResponse,
    ScrapeCreate, ScrapeResponse, ScrapeDetailResponse,
    ResultsResponse, AddressResult, StatsResponse
)
from api.background import start_scrape_task, cancel_scrape_task, get_active_tasks

setup_logging(level="INFO")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vacation Rental Scraper API",
    description="API for managing site configurations and scrape runs",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_db() -> Database:
    """Get database instance."""
    return Database()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render the main dashboard."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/configs", response_class=HTMLResponse)
async def configs_page(request: Request):
    """Render configurations page."""
    return templates.TemplateResponse("configs.html", {"request": request})


@app.get("/scrapes", response_class=HTMLResponse)
async def scrapes_page(request: Request):
    """Render scrape runs list page."""
    return templates.TemplateResponse("scrapes.html", {"request": request})


@app.get("/scrapes/{run_id}", response_class=HTMLResponse)
async def scrape_detail_page(request: Request, run_id: int):
    """Render scrape run detail page."""
    db = get_db()
    try:
        run = db.get_scrape_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Scrape run not found")
        return templates.TemplateResponse("scrape_detail.html", {"request": request, "run": run})
    finally:
        db.close()


@app.get("/configs-partial", response_class=HTMLResponse)
async def configs_partial(request: Request):
    """Render recent configurations partial for dashboard."""
    db = get_db()
    try:
        configs = db.get_all_configs()[:5]
        return templates.TemplateResponse("partials/configs_partial.html", {
            "request": request,
            "configs": configs
        })
    except Exception as e:
        logger.error(f"Error loading configs partial: {e}")
        return HTMLResponse(
            content='<div class="p-6 text-center text-red-500">Error loading configurations</div>',
            status_code=500
        )
    finally:
        db.close()


@app.get("/scrapes-partial", response_class=HTMLResponse)
async def scrapes_partial(request: Request):
    """Render recent scrape runs partial for dashboard."""
    db = get_db()
    try:
        runs = db.get_scrape_runs_filtered(limit=5)
        return templates.TemplateResponse("partials/scrapes_partial.html", {
            "request": request,
            "runs": runs
        })
    except Exception as e:
        logger.error(f"Error loading scrapes partial: {e}")
        return HTMLResponse(
            content='<div class="p-6 text-center text-red-500">Error loading scrape runs</div>',
            status_code=500
        )
    finally:
        db.close()


@app.get("/stats/config-count", response_class=HTMLResponse)
async def config_count():
    """Return total config count as plain text."""
    db = get_db()
    try:
        configs = db.get_all_configs()
        return str(len(configs))
    except Exception as e:
        logger.error(f"Error loading config count: {e}")
        return HTMLResponse(content="-", status_code=500)
    finally:
        db.close()


@app.get("/stats/active-count", response_class=HTMLResponse)
async def active_count():
    """Return active scrapes count as plain text."""
    db = get_db()
    try:
        stats = db.get_run_statistics()
        count = stats.get('running', 0) + stats.get('queued', 0)
        return str(count)
    except Exception as e:
        logger.error(f"Error loading active count: {e}")
        return HTMLResponse(content="-", status_code=500)
    finally:
        db.close()


@app.get("/stats/address-count", response_class=HTMLResponse)
async def address_count():
    """Return total addresses count as plain text."""
    db = get_db()
    try:
        stats = db.get_run_statistics()
        count = stats.get('total_addresses_extracted', 0)
        return f"{count:,}"
    except Exception as e:
        logger.error(f"Error loading address count: {e}")
        return HTMLResponse(content="-", status_code=500)
    finally:
        db.close()


@app.post("/api/configs", response_model=ConfigResponse, status_code=201)
async def create_config(config: ConfigCreate):
    """Create a new site configuration."""
    db = get_db()
    try:
        config_json = json.dumps(config.config_data)
        config_id = db.insert_config(
            name=config.name,
            config_data=config_json,
            is_active=config.is_active
        )
        
        created_config = db.get_config(config_id=config_id)
        return ConfigResponse(
            id=created_config['id'],
            name=created_config['name'],
            config_data=json.loads(created_config['config_data']),
            is_active=bool(created_config['is_active']),
            created_at=created_config['created_at'],
            updated_at=created_config['updated_at']
        )
    finally:
        db.close()


@app.get("/api/configs", response_model=List[ConfigResponse])
async def list_configs(is_active: Optional[bool] = None):
    """List all configurations."""
    db = get_db()
    try:
        configs = db.get_all_configs(is_active=is_active)
        return [
            ConfigResponse(
                id=c['id'],
                name=c['name'],
                config_data=json.loads(c['config_data']),
                is_active=bool(c['is_active']),
                created_at=c['created_at'],
                updated_at=c['updated_at']
            )
            for c in configs
        ]
    finally:
        db.close()


@app.get("/api/configs/{config_id}", response_model=ConfigResponse)
async def get_config(config_id: int):
    """Get a specific configuration."""
    db = get_db()
    try:
        config = db.get_config(config_id=config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Config not found")
        
        return ConfigResponse(
            id=config['id'],
            name=config['name'],
            config_data=json.loads(config['config_data']),
            is_active=bool(config['is_active']),
            created_at=config['created_at'],
            updated_at=config['updated_at']
        )
    finally:
        db.close()


@app.put("/api/configs/{config_id}", response_model=ConfigResponse)
async def update_config(config_id: int, config: ConfigUpdate):
    """Update a configuration."""
    db = get_db()
    try:
        existing = db.get_config(config_id=config_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Config not found")
        
        config_data_json = None
        if config.config_data is not None:
            config_data_json = json.dumps(config.config_data)
        
        db.update_config(
            config_id=config_id,
            name=config.name,
            config_data=config_data_json,
            is_active=config.is_active
        )
        
        updated_config = db.get_config(config_id=config_id)
        return ConfigResponse(
            id=updated_config['id'],
            name=updated_config['name'],
            config_data=json.loads(updated_config['config_data']),
            is_active=bool(updated_config['is_active']),
            created_at=updated_config['created_at'],
            updated_at=updated_config['updated_at']
        )
    finally:
        db.close()


@app.delete("/api/configs/{config_id}", status_code=204)
async def delete_config(config_id: int):
    """Delete a configuration."""
    db = get_db()
    try:
        existing = db.get_config(config_id=config_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Config not found")
        
        db.delete_config(config_id=config_id)
    finally:
        db.close()


@app.post("/api/scrapes", response_model=ScrapeResponse, status_code=201)
async def create_scrape(scrape: ScrapeCreate, background_tasks: BackgroundTasks):
    """Start a new scrape run."""
    db = get_db()
    try:
        config = None
        if scrape.config_id:
            config = db.get_config(config_id=scrape.config_id)
        elif scrape.config_name:
            config = db.get_config(name=scrape.config_name)
        else:
            raise HTTPException(status_code=400, detail="Must provide config_id or config_name")
        
        if not config:
            raise HTTPException(status_code=404, detail="Config not found")
        
        config_data = json.loads(config['config_data'])
        
        site_id = db.insert_site(
            manager_name=config_data.get('manager_name', 'Unknown'),
            manager_domain=config_data.get('manager_domain', 'unknown.com'),
            market_name=config_data.get('market_name', 'Unknown')
        )
        
        config_snapshot = ConfigLoader.save_config_snapshot(
            type('Config', (), config_data)
        )
        
        run_id = db.create_scrape_run(
            site_id=site_id,
            config_snapshot=config_snapshot,
            config_id=config['id'],
            status='queued'
        )
        
        start_scrape_task(run_id, config_data)
        
        scrape_run = db.get_scrape_run(run_id)
        return ScrapeResponse(
            id=scrape_run['id'],
            site_id=scrape_run['site_id'],
            config_id=scrape_run['config_id'],
            status=scrape_run['status'],
            start_time=scrape_run['start_time'],
            end_time=scrape_run['end_time'],
            pages_visited=scrape_run['pages_visited'],
            listing_pages_found=scrape_run['listing_pages_found'],
            addresses_extracted=scrape_run['addresses_extracted'],
            current_page=scrape_run['current_page'],
            total_pages_estimate=scrape_run['total_pages_estimate'],
            error_message=scrape_run['error_message']
        )
    finally:
        db.close()


@app.get("/api/scrapes", response_model=List[ScrapeResponse])
async def list_scrapes(
    config_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0)
):
    """List scrape runs with optional filters."""
    db = get_db()
    try:
        runs = db.get_scrape_runs_filtered(
            config_id=config_id,
            status=status,
            limit=limit,
            offset=offset
        )
        return [
            ScrapeResponse(
                id=r['id'],
                site_id=r['site_id'],
                config_id=r['config_id'],
                status=r['status'],
                start_time=r['start_time'],
                end_time=r['end_time'],
                pages_visited=r['pages_visited'],
                listing_pages_found=r['listing_pages_found'],
                addresses_extracted=r['addresses_extracted'],
                current_page=r['current_page'],
                total_pages_estimate=r['total_pages_estimate'],
                error_message=r['error_message']
            )
            for r in runs
        ]
    finally:
        db.close()


@app.get("/api/scrapes/{run_id}", response_model=ScrapeDetailResponse)
async def get_scrape(run_id: int):
    """Get details of a specific scrape run."""
    db = get_db()
    try:
        run = db.get_scrape_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Scrape run not found")
        
        return ScrapeDetailResponse(
            id=run['id'],
            site_id=run['site_id'],
            config_id=run['config_id'],
            status=run['status'],
            start_time=run['start_time'],
            end_time=run['end_time'],
            pages_visited=run['pages_visited'],
            listing_pages_found=run['listing_pages_found'],
            addresses_extracted=run['addresses_extracted'],
            current_page=run['current_page'],
            total_pages_estimate=run['total_pages_estimate'],
            error_message=run['error_message'],
            logs=run['logs'],
            config_snapshot=run['config_snapshot']
        )
    finally:
        db.close()


@app.post("/api/scrapes/{run_id}/cancel", status_code=200)
async def cancel_scrape(run_id: int):
    """Cancel a running scrape."""
    db = get_db()
    try:
        run = db.get_scrape_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Scrape run not found")
        
        if run['status'] not in ['queued', 'running']:
            raise HTTPException(status_code=400, detail="Can only cancel queued or running scrapes")
        
        cancelled = cancel_scrape_task(run_id)
        if cancelled:
            db.update_scrape_run(run_id, status='cancelled')
            db.append_run_log(run_id, "Scrape cancelled by user")
        
        return {"message": "Scrape cancelled" if cancelled else "Scrape not actively running"}
    finally:
        db.close()


@app.get("/api/scrapes/{run_id}/results", response_model=ResultsResponse)
async def get_results(
    run_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, le=500)
):
    """Get paginated results for a scrape run."""
    db = get_db()
    try:
        run = db.get_scrape_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Scrape run not found")
        
        all_results = db.get_scrape_run_results(run_id)
        
        total = len(all_results)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_results = all_results[start_idx:end_idx]
        
        return ResultsResponse(
            total=total,
            page=page,
            page_size=page_size,
            results=[
                AddressResult(
                    listing_url=r['listing_url'],
                    address_line1=r['address_line1'],
                    address_line2=r['address_line2'],
                    city=r['city'],
                    state=r['state'],
                    postal_code=r['postal_code'],
                    country=r['country'],
                    confidence_score=r['confidence_score'],
                    inference_method=r['inference_method']
                )
                for r in page_results
            ]
        )
    finally:
        db.close()


@app.get("/api/scrapes/{run_id}/export")
async def export_results(run_id: int):
    """Export scrape results as CSV."""
    db = get_db()
    try:
        run = db.get_scrape_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Scrape run not found")
        
        results = db.get_scrape_run_results(run_id)
        
        if not results:
            raise HTTPException(status_code=404, detail="No results found for this scrape run")
        
        output = io.StringIO()
        fieldnames = list(results[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=scrape_run_{run_id}.csv"
            }
        )
    finally:
        db.close()


@app.get("/api/stats", response_model=StatsResponse)
async def get_statistics(config_id: Optional[int] = None, days: int = 30):
    """Get aggregated statistics."""
    db = get_db()
    try:
        stats = db.get_run_statistics(config_id=config_id, days=days)
        return StatsResponse(**stats)
    finally:
        db.close()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    active = len(get_active_tasks())
    return {
        "status": "healthy",
        "active_scrapes": active
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
