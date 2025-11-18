"""Background task processing for running scrapes asynchronously."""

import asyncio
import logging
from typing import Dict
from datetime import datetime

from src.main import ScraperOrchestrator
from src.config import ConfigLoader
from src.db import Database
from src.models import SiteConfig

logger = logging.getLogger(__name__)

active_tasks: Dict[int, asyncio.Task] = {}


async def run_scrape_background(run_id: int, config_data: dict, db_path: str = "data/scraper.db"):
    """
    Run a scrape in the background and update the database with progress.
    
    Args:
        run_id: Scrape run ID
        config_data: Site configuration dictionary
        db_path: Path to database
    """
    db = Database(db_path)
    
    try:
        db.update_scrape_run(run_id, status='running')
        db.append_run_log(run_id, "Scrape started")
        
        site_config = SiteConfig.from_dict(config_data)
        
        orchestrator = ScraperOrchestrator(site_config, db)
        orchestrator.run_id = run_id
        
        site_id = db.get_scrape_run(run_id)['site_id']
        orchestrator.site_id = site_id
        
        orchestrator.metrics.start_time = datetime.now()
        
        db.append_run_log(run_id, f"Starting discovery for {site_config.manager_name}")
        listing_urls = await orchestrator._discover_listings()
        
        db.update_run_progress(run_id, 0, len(listing_urls))
        db.append_run_log(run_id, f"Discovered {len(listing_urls)} potential listings")
        
        await orchestrator._process_listings(listing_urls)
        
        db.append_run_log(run_id, "Starting address normalization")
        orchestrator._normalize_addresses()
        
        orchestrator._finalize_run('completed')
        db.append_run_log(run_id, f"Scrape completed successfully - {orchestrator.metrics.addresses_extracted} addresses extracted")
        
        logger.info(f"Scrape run {run_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Scrape run {run_id} failed: {str(e)}", exc_info=True)
        db.update_scrape_run(run_id, status='failed', error_message=str(e))
        db.append_run_log(run_id, f"ERROR: {str(e)}")
        
    finally:
        db.close()
        if run_id in active_tasks:
            del active_tasks[run_id]


def start_scrape_task(run_id: int, config_data: dict, db_path: str = "data/scraper.db") -> None:
    """
    Start a scrape task in the background.
    
    Args:
        run_id: Scrape run ID
        config_data: Site configuration dictionary
        db_path: Path to database
    """
    task = asyncio.create_task(run_scrape_background(run_id, config_data, db_path))
    active_tasks[run_id] = task
    logger.info(f"Started background scrape task for run {run_id}")


def cancel_scrape_task(run_id: int) -> bool:
    """
    Cancel a running scrape task.
    
    Args:
        run_id: Scrape run ID
        
    Returns:
        True if cancelled, False if not found
    """
    if run_id in active_tasks:
        active_tasks[run_id].cancel()
        del active_tasks[run_id]
        logger.info(f"Cancelled scrape task {run_id}")
        return True
    return False


def get_active_tasks() -> Dict[int, asyncio.Task]:
    """Get all active scrape tasks."""
    return active_tasks.copy()
