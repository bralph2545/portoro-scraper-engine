"""
Data models using dataclasses for type safety and validation.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class CrawlSettings:
    """Settings for crawler behavior."""
    max_concurrency: int = 3
    min_delay_ms: int = 500
    max_depth: int = 4
    scroll_attempts: int = 5
    wait_for_selector_timeout: int = 5000
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


@dataclass
class IndexPageSelectors:
    """Selectors for extracting links from index/search pages."""
    listing_link_selector: Optional[str] = None
    pagination_next_selector: Optional[str] = None
    load_more_selector: Optional[str] = None
    total_count_selector: Optional[str] = None


@dataclass
class ListingPageSelectors:
    """Selectors for extracting data from listing detail pages."""
    address_container_selectors: List[str] = field(default_factory=list)
    property_name_selector: Optional[str] = None
    bedrooms_selector: Optional[str] = None
    map_container_selector: Optional[str] = None


@dataclass
class SiteConfig:
    """Complete configuration for a scraping target site."""
    manager_name: str
    manager_domain: str
    market_name: str
    seed_urls: List[str]
    
    sitemap_urls: List[str] = field(default_factory=list)
    property_directory_urls: List[str] = field(default_factory=list)
    listing_url_patterns: List[str] = field(default_factory=list)
    excluded_url_patterns: List[str] = field(default_factory=list)
    
    index_page_selectors: IndexPageSelectors = field(default_factory=IndexPageSelectors)
    listing_page_selectors: ListingPageSelectors = field(default_factory=ListingPageSelectors)
    crawl_settings: CrawlSettings = field(default_factory=CrawlSettings)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SiteConfig':
        """Create SiteConfig from dictionary."""
        index_selectors = data.get('index_page_selectors', {})
        listing_selectors = data.get('listing_page_selectors', {})
        crawl_settings = data.get('crawl_settings', {})
        
        return cls(
            manager_name=data['manager_name'],
            manager_domain=data['manager_domain'],
            market_name=data['market_name'],
            seed_urls=data['seed_urls'],
            sitemap_urls=data.get('sitemap_urls', []),
            property_directory_urls=data.get('property_directory_urls', []),
            listing_url_patterns=data.get('listing_url_patterns', []),
            excluded_url_patterns=data.get('excluded_url_patterns', []),
            index_page_selectors=IndexPageSelectors(**index_selectors),
            listing_page_selectors=ListingPageSelectors(**listing_selectors),
            crawl_settings=CrawlSettings(**crawl_settings)
        )


@dataclass
class AddressCandidate:
    """A raw address extracted from a page."""
    address_raw: str
    extraction_method: str
    html_snippet: Optional[str] = None
    confidence: float = 0.5


@dataclass
class NormalizedAddress:
    """A parsed and normalized address."""
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "USA"
    inferred_market: Optional[str] = None
    inference_method: str = "parser"
    confidence_score: float = 0.0
    address_raw: Optional[str] = None


@dataclass
class ListingPage:
    """Represents a property listing page."""
    url: str
    discovered_from_url: Optional[str] = None
    is_valid_listing: Optional[bool] = None
    html_content: Optional[str] = None
    classification_method: Optional[str] = None
    page_type: Optional[str] = None
    fetch_time: Optional[datetime] = None


@dataclass
class ScrapeMetrics:
    """Metrics for a scrape run."""
    pages_visited: int = 0
    listing_pages_found: int = 0
    addresses_extracted: int = 0
    errors_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def duration_seconds(self) -> Optional[float]:
        """Calculate duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
