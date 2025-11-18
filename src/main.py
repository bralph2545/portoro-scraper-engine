"""
Main orchestration module for the scraping system.
Coordinates crawler, extractor, and normalizer components.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Optional

from src.config import ConfigLoader
from src.db import Database
from src.crawler import Crawler
from src.extractor import PageClassifier, AddressExtractor
from src.normalizer import AddressNormalizer
from src.models import SiteConfig, ScrapeMetrics
from src.utils import setup_logging

logger = logging.getLogger(__name__)


class ScraperOrchestrator:
    """Orchestrates the entire scraping process."""
    
    def __init__(self, config: SiteConfig, db: Database):
        """
        Initialize orchestrator.
        
        Args:
            config: SiteConfig object
            db: Database instance
        """
        self.config = config
        self.db = db
        self.metrics = ScrapeMetrics()
        self.run_id: Optional[int] = None
        self.site_id: Optional[int] = None
    
    async def run_scrape(self) -> int:
        """
        Execute the complete scraping workflow.
        
        Returns:
            scrape_run_id
        """
        self.metrics.start_time = datetime.now()
        
        try:
            self._initialize_run()
            
            logger.info("=" * 60)
            logger.info(f"Starting scrape run #{self.run_id}")
            logger.info(f"Site: {self.config.manager_name}")
            logger.info(f"Domain: {self.config.manager_domain}")
            logger.info(f"Market: {self.config.market_name}")
            logger.info("=" * 60)
            
            listing_urls = await self._discover_listings()
            
            await self._process_listings(listing_urls)
            
            self._normalize_addresses()
            
            self._finalize_run('completed')
            
            logger.info("=" * 60)
            logger.info(f"Scrape run #{self.run_id} completed successfully")
            logger.info(f"Total pages visited: {self.metrics.pages_visited}")
            logger.info(f"Valid listings found: {self.metrics.listing_pages_found}")
            logger.info(f"Addresses extracted: {self.metrics.addresses_extracted}")
            logger.info(f"Duration: {self.metrics.duration_seconds():.2f} seconds")
            logger.info("=" * 60)
            
            return self.run_id
            
        except Exception as e:
            logger.error(f"Scrape run failed: {str(e)}", exc_info=True)
            self._finalize_run('failed', error_message=str(e))
            raise
    
    def _initialize_run(self):
        """Initialize database records for this scrape run."""
        self.site_id = self.db.insert_site(
            manager_name=self.config.manager_name,
            manager_domain=self.config.manager_domain,
            market_name=self.config.market_name
        )
        
        config_snapshot = ConfigLoader.save_config_snapshot(self.config)
        
        self.run_id = self.db.create_scrape_run(
            site_id=self.site_id,
            config_snapshot=config_snapshot
        )
        
        logger.info(f"Initialized scrape run: site_id={self.site_id}, run_id={self.run_id}")
    
    async def _discover_listings(self) -> list:
        """
        Discover all listing URLs using the crawler.
        
        Returns:
            List of listing URLs
        """
        logger.info("Phase 1: Discovering listing URLs")
        
        crawler = Crawler(self.config)
        listing_urls = await crawler.discover_listing_urls()
        
        logger.info(f"Discovery complete: {len(listing_urls)} potential listings found")
        
        return listing_urls
    
    async def _process_listings(self, listing_urls: list):
        """
        Fetch and process each listing page.
        
        Args:
            listing_urls: List of URLs to process
        """
        logger.info(f"Phase 2: Processing {len(listing_urls)} listing pages")
        
        crawler = Crawler(self.config)
        await crawler.start()
        
        try:
            extractor = AddressExtractor(self.config)
            
            for i, url in enumerate(listing_urls, 1):
                try:
                    logger.info(f"Processing {i}/{len(listing_urls)}: {url}")
                    
                    html_content, success = await crawler.fetch_page_content(url)
                    
                    if not success:
                        logger.warning(f"Failed to fetch: {url}")
                        continue
                    
                    self.metrics.pages_visited += 1
                    
                    page_id = self.db.insert_listing_page(
                        scrape_run_id=self.run_id,
                        url=url,
                        html_content=html_content
                    )
                    
                    is_listing, method = PageClassifier.is_listing_page(html_content, url)
                    
                    self.db.update_listing_page(
                        page_id=page_id,
                        is_valid_listing=is_listing,
                        classification_method=method
                    )
                    
                    if is_listing:
                        self.metrics.listing_pages_found += 1
                        
                        candidates = extractor.extract_addresses(html_content, url)
                        
                        for candidate in candidates:
                            self.db.insert_address_candidate(
                                listing_page_id=page_id,
                                address_raw=candidate.address_raw,
                                extraction_method=candidate.extraction_method,
                                html_snippet=candidate.html_snippet
                            )
                            self.metrics.addresses_extracted += 1
                        
                        logger.info(f"  ✓ Valid listing - {len(candidates)} addresses extracted")
                    else:
                        logger.debug(f"  ✗ Not a listing page ({method})")
                    
                    self.db.update_scrape_run(
                        run_id=self.run_id,
                        pages_visited=self.metrics.pages_visited,
                        listing_pages_found=self.metrics.listing_pages_found,
                        addresses_extracted=self.metrics.addresses_extracted
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing {url}: {str(e)}")
                    self.metrics.errors_count += 1
                    continue
        
        finally:
            await crawler.close()
        
        logger.info(f"Processing complete: {self.metrics.listing_pages_found} valid listings")
    
    def _normalize_addresses(self):
        """Normalize all extracted address candidates."""
        logger.info("Phase 3: Normalizing addresses")
        
        normalizer = AddressNormalizer(self.config)
        
        listing_pages = self.db.get_listing_pages_for_run(
            scrape_run_id=self.run_id,
            is_valid_listing=True
        )
        
        normalized_count = 0
        
        for page in listing_pages:
            candidates = self.db.get_address_candidates_for_page(page['id'])
            
            if not candidates:
                continue
            
            from src.models import AddressCandidate
            
            candidate_objects = [
                AddressCandidate(
                    address_raw=c['address_raw'],
                    extraction_method=c['extraction_method'],
                    html_snippet=c['html_snippet']
                )
                for c in candidates
            ]
            
            normalized_addresses = [
                normalizer.normalize_address(cand, page['url'])
                for cand in candidate_objects
            ]
            
            unique_addresses = normalizer.deduplicate_addresses(normalized_addresses)
            
            for i, norm_addr in enumerate(unique_addresses[:1]):
                address_data = {
                    'address_candidate_id': candidates[i]['id'] if i < len(candidates) else None,
                    'address_raw': norm_addr.address_raw,
                    'address_line1': norm_addr.address_line1,
                    'address_line2': norm_addr.address_line2,
                    'city': norm_addr.city,
                    'state': norm_addr.state,
                    'postal_code': norm_addr.postal_code,
                    'country': norm_addr.country,
                    'inferred_market': norm_addr.inferred_market,
                    'inference_method': norm_addr.inference_method,
                    'confidence_score': norm_addr.confidence_score
                }
                
                self.db.insert_address(
                    listing_page_id=page['id'],
                    address_data=address_data
                )
                normalized_count += 1
        
        logger.info(f"Normalization complete: {normalized_count} addresses normalized")
    
    def _finalize_run(self, status: str, error_message: str = None):
        """Finalize the scrape run."""
        self.metrics.end_time = datetime.now()
        
        self.db.update_scrape_run(
            run_id=self.run_id,
            status=status,
            pages_visited=self.metrics.pages_visited,
            listing_pages_found=self.metrics.listing_pages_found,
            addresses_extracted=self.metrics.addresses_extracted,
            error_message=error_message
        )


async def run_scrape_from_config(config_path: str, log_level: str = "INFO") -> int:
    """
    Main entry point for running a scrape from a config file.
    
    Args:
        config_path: Path to YAML config file
        log_level: Logging level
        
    Returns:
        scrape_run_id
    """
    setup_logging(level=log_level)
    
    config = ConfigLoader.load_config(config_path)
    
    db = Database()
    
    orchestrator = ScraperOrchestrator(config, db)
    
    run_id = await orchestrator.run_scrape()
    
    db.close()
    
    return run_id
