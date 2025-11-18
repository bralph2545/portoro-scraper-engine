"""
Playwright-based web crawler for discovering property listing URLs.
Handles pagination, infinite scroll, and "Load More" buttons.
"""

import asyncio
import logging
import time
from typing import Set, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from src.models import SiteConfig, ListingPage
from src.utils import (
    normalize_url, 
    is_same_domain, 
    is_likely_listing_url,
    deduplicate_urls
)

logger = logging.getLogger(__name__)


class Crawler:
    """Playwright-based crawler for discovering listing pages."""
    
    def __init__(self, config: SiteConfig):
        """
        Initialize crawler with site configuration.
        
        Args:
            config: SiteConfig object
        """
        self.config = config
        self.discovered_urls: Set[str] = set()
        self.visited_urls: Set[str] = set()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
    
    async def start(self):
        """Start the browser and create context."""
        self.playwright = await async_playwright().start()
        
        logger.info("Launching Playwright browser (headless mode)")
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        self.context = await self.browser.new_context(
            user_agent=self.config.crawl_settings.user_agent,
            viewport={'width': 1920, 'height': 1080}
        )
        
        logger.info("Browser started successfully")
    
    async def close(self):
        """Close browser and clean up."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")
    
    async def discover_listing_urls(self) -> List[str]:
        """
        Discover all listing URLs from the configured seed URLs.
        
        Returns:
            List of discovered listing page URLs
        """
        await self.start()
        
        try:
            for seed_url in self.config.seed_urls:
                logger.info(f"Processing seed URL: {seed_url}")
                await self._crawl_index_page(seed_url)
            
            for directory_url in self.config.property_directory_urls:
                logger.info(f"Processing directory URL: {directory_url}")
                await self._crawl_index_page(directory_url)
            
            listing_urls = [
                url for url in self.discovered_urls 
                if is_likely_listing_url(
                    url, 
                    self.config.listing_url_patterns,
                    self.config.excluded_url_patterns
                )
            ]
            
            logger.info(f"Total listing URLs discovered: {len(listing_urls)}")
            return deduplicate_urls(listing_urls)
            
        finally:
            await self.close()
    
    async def _crawl_index_page(self, url: str):
        """
        Crawl an index/search page to discover listing links.
        Enhanced to handle JavaScript navigation and SPAs.
        
        Args:
            url: Index page URL to crawl
        """
        if url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        page = await self.context.new_page()
        
        try:
            logger.info(f"Loading page: {url}")
            
            # Set up navigation listener to detect redirects
            navigation_occurred = False
            def on_navigation(frame):
                nonlocal navigation_occurred
                navigation_occurred = True
                logger.debug(f"Navigation detected to: {page.url}")
            
            page.on('framenavigated', on_navigation)
            
            # Initial page load with more lenient wait strategy
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for potential redirects or SPA navigation
            await asyncio.sleep(3.0)
            
            # Check if we were redirected
            final_url = page.url
            if final_url != url:
                logger.info(f"Redirected from {url} to {final_url}")
                # Update visited URLs with the final URL
                self.visited_urls.add(final_url)
            
            # Wait for key content to appear (if selector configured)
            if self.config.index_page_selectors.listing_link_selector:
                try:
                    await page.wait_for_selector(
                        self.config.index_page_selectors.listing_link_selector,
                        timeout=5000
                    )
                except:
                    logger.debug("Listing selector not found, continuing anyway")
            
            await self._handle_infinite_scroll(page)
            
            await self._click_load_more_buttons(page)
            
            links = await self._extract_links(page, final_url)
            
            for link in links:
                if is_same_domain(link, self.config.manager_domain):
                    self.discovered_urls.add(link)
            
            logger.info(f"Found {len(links)} links on {final_url}")
            
            await self._handle_pagination(page, final_url)
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
        
        finally:
            await page.close()
            await asyncio.sleep(self.config.crawl_settings.min_delay_ms / 1000.0)
    
    async def _handle_infinite_scroll(self, page: Page):
        """
        Handle infinite scroll by scrolling to bottom multiple times.
        More resilient to JavaScript navigation and SPA reloads.
        
        Args:
            page: Playwright page object
        """
        scroll_attempts = self.config.crawl_settings.scroll_attempts
        
        # Skip scrolling if disabled
        if scroll_attempts <= 0:
            return
        
        for i in range(scroll_attempts):
            try:
                # Get initial element count for comparison
                initial_count = await page.locator('a').count()
                
                # Use mouse wheel for scrolling (more resilient than evaluate)
                await page.mouse.wheel(0, 10000)
                
                # Alternative: scroll to bottom element if exists
                bottom_elements = await page.locator('body').all()
                if bottom_elements:
                    await bottom_elements[-1].scroll_into_view_if_needed()
                
                await asyncio.sleep(1.5)
                
                # Check if new content loaded
                new_count = await page.locator('a').count()
                
                if new_count == initial_count:
                    logger.debug(f"No new content after scroll attempt {i+1}")
                    break
                
                logger.debug(f"Scroll attempt {i+1}: found {new_count - initial_count} new links")
                
            except Exception as e:
                # Handle execution context destruction gracefully
                if "execution context was destroyed" in str(e).lower():
                    logger.warning(f"Page navigated during scroll, stopping scroll attempts")
                    break
                else:
                    logger.debug(f"Error during scroll attempt {i+1}: {str(e)}")
                    # Try to continue with next scroll attempt
                    continue
    
    async def _click_load_more_buttons(self, page: Page):
        """
        Click "Load More" or "Show More" buttons repeatedly.
        
        Args:
            page: Playwright page object
        """
        load_more_patterns = [
            'text=Load More',
            'text=Show More',
            'text=View More',
            'button:has-text("Load")',
            'button:has-text("More")',
            '.load-more',
            '.show-more'
        ]
        
        if self.config.index_page_selectors.load_more_selector:
            load_more_patterns.insert(0, self.config.index_page_selectors.load_more_selector)
        
        max_clicks = 20
        clicks = 0
        
        for pattern in load_more_patterns:
            while clicks < max_clicks:
                try:
                    button = page.locator(pattern).first
                    
                    if await button.is_visible(timeout=1000):
                        logger.debug(f"Clicking Load More button: {pattern}")
                        await button.click()
                        await asyncio.sleep(1.5)
                        clicks += 1
                    else:
                        break
                        
                except Exception:
                    break
        
        if clicks > 0:
            logger.info(f"Clicked Load More button {clicks} times")
    
    async def _handle_pagination(self, page: Page, current_url: str):
        """
        Handle pagination by finding and following "Next" links.
        
        Args:
            page: Playwright page object
            current_url: Current page URL
        """
        next_selectors = [
            'a:has-text("Next")',
            'a[rel="next"]',
            '.pagination a:has-text("Next")',
            'button:has-text("Next")'
        ]
        
        if self.config.index_page_selectors.pagination_next_selector:
            next_selectors.insert(0, self.config.index_page_selectors.pagination_next_selector)
        
        for selector in next_selectors:
            try:
                next_link = page.locator(selector).first
                
                if await next_link.is_visible(timeout=1000):
                    next_url = await next_link.get_attribute('href')
                    
                    if next_url:
                        next_url = urljoin(current_url, next_url)
                        
                        if next_url not in self.visited_urls:
                            logger.info(f"Following pagination to: {next_url}")
                            await self._crawl_index_page(next_url)
                    
                    return
                    
            except Exception:
                continue
    
    async def _extract_links(self, page: Page, base_url: str) -> List[str]:
        """
        Extract all links from a page.
        
        Args:
            page: Playwright page object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of absolute URLs
        """
        links = []
        
        try:
            if self.config.index_page_selectors.listing_link_selector:
                elements = await page.locator(
                    self.config.index_page_selectors.listing_link_selector
                ).all()
                
                for element in elements:
                    href = await element.get_attribute('href')
                    if href:
                        absolute_url = urljoin(base_url, href)
                        links.append(normalize_url(absolute_url))
            
            else:
                all_links = await page.locator('a[href]').all()
                
                for link in all_links:
                    href = await link.get_attribute('href')
                    if href and not href.startswith('#') and not href.startswith('javascript:'):
                        absolute_url = urljoin(base_url, href)
                        links.append(normalize_url(absolute_url))
        
        except Exception as e:
            logger.error(f"Error extracting links: {str(e)}")
        
        return deduplicate_urls(links)
    
    async def fetch_page_content(self, url: str) -> Tuple[Optional[str], bool]:
        """
        Fetch HTML content of a single page.
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (html_content, success)
        """
        if not self.browser:
            await self.start()
        
        page = await self.context.new_page()
        
        try:
            logger.debug(f"Fetching content: {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            await asyncio.sleep(1.0)
            
            html_content = await page.content()
            
            return html_content, True
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None, False
            
        finally:
            await page.close()
            await asyncio.sleep(self.config.crawl_settings.min_delay_ms / 1000.0)
