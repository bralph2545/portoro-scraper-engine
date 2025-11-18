"""
Page classification and address extraction from listing pages.
Uses multiple strategies: schema.org JSON-LD, CSS selectors, text heuristics, and map widgets.
"""

import json
import logging
import re
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup

from src.models import AddressCandidate, SiteConfig

logger = logging.getLogger(__name__)


class PageClassifier:
    """Classifies pages as property listings or non-listings."""
    
    LISTING_KEYWORDS = [
        'bedroom', 'bathroom', 'sleeps', 'guests', 'nightly', 'rate',
        'book now', 'check availability', 'calendar', 'reserve',
        'sq ft', 'square feet', 'amenities'
    ]
    
    NON_LISTING_KEYWORDS = [
        'blog', 'article', 'about us', 'contact us', 'careers',
        'privacy policy', 'terms of service', 'faq'
    ]
    
    @staticmethod
    def is_listing_page(html_content: str, url: str) -> Tuple[bool, str]:
        """
        Classify if a page is a property listing.
        
        Args:
            html_content: HTML content of the page
            url: Page URL
            
        Returns:
            Tuple of (is_listing, classification_method)
        """
        if not html_content:
            return False, "empty_content"
        
        soup = BeautifulSoup(html_content, 'lxml')
        text = soup.get_text().lower()
        
        for keyword in PageClassifier.NON_LISTING_KEYWORDS:
            if keyword in url.lower():
                return False, "url_pattern"
        
        listing_score = sum(1 for kw in PageClassifier.LISTING_KEYWORDS if kw in text)
        
        if listing_score >= 3:
            return True, "keyword_heuristic"
        
        if PageClassifier._has_booking_widget(soup):
            return True, "booking_widget"
        
        if PageClassifier._has_schema_lodging(soup):
            return True, "schema_org"
        
        if listing_score >= 2:
            return True, "keyword_heuristic_low_confidence"
        
        return False, "no_listing_indicators"
    
    @staticmethod
    def _has_booking_widget(soup: BeautifulSoup) -> bool:
        """Check for booking widget indicators."""
        booking_selectors = [
            '[class*="booking"]', '[id*="booking"]',
            '[class*="calendar"]', '[id*="calendar"]',
            '[class*="reserve"]', '[class*="availability"]'
        ]
        
        for selector in booking_selectors:
            if soup.select_one(selector):
                return True
        
        return False
    
    @staticmethod
    def _has_schema_lodging(soup: BeautifulSoup) -> bool:
        """Check for schema.org lodging/accommodation types."""
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                schema_type = data.get('@type', '').lower()
                
                if any(t in schema_type for t in ['lodging', 'accommodation', 'house', 'apartment']):
                    return True
            except:
                continue
        
        return False


class AddressExtractor:
    """Extracts address information from listing pages using multiple strategies."""
    
    def __init__(self, config: SiteConfig):
        """
        Initialize extractor with site configuration.
        
        Args:
            config: SiteConfig object
        """
        self.config = config
    
    def extract_addresses(self, html_content: str, url: str) -> List[AddressCandidate]:
        """
        Extract all address candidates from a page.
        
        Args:
            html_content: HTML content
            url: Page URL
            
        Returns:
            List of AddressCandidate objects
        """
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'lxml')
        candidates = []
        
        schema_addresses = self._extract_from_schema(soup)
        candidates.extend(schema_addresses)
        
        # Always try heuristics for 30A Escapes since they have specific patterns
        heuristic_addresses = self._extract_from_heuristics(soup)
        candidates.extend(heuristic_addresses)
        
        # Only use selector extraction if we didn't find good heuristic matches
        # or if we want to supplement the results
        if not any(c.extraction_method == 'address_location_pattern' for c in candidates):
            selector_addresses = self._extract_from_selectors(soup)
            candidates.extend(selector_addresses)
        
        if not candidates:
            map_addresses = self._extract_from_maps(soup)
            candidates.extend(map_addresses)
        
        meta_addresses = self._extract_from_meta_tags(soup)
        candidates.extend(meta_addresses)
        
        logger.info(f"Extracted {len(candidates)} address candidates from {url}")
        
        return candidates
    
    def _extract_from_schema(self, soup: BeautifulSoup) -> List[AddressCandidate]:
        """Extract addresses from schema.org JSON-LD."""
        candidates = []
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                
                address_data = self._find_postal_address(data)
                
                if address_data:
                    address_str = self._format_schema_address(address_data)
                    
                    if address_str:
                        candidates.append(AddressCandidate(
                            address_raw=address_str,
                            extraction_method='schema_ld',
                            html_snippet=str(script)[:500],
                            confidence=0.9
                        ))
                        
            except Exception as e:
                logger.debug(f"Error parsing JSON-LD: {str(e)}")
                continue
        
        return candidates
    
    def _find_postal_address(self, data: dict) -> Optional[dict]:
        """Recursively find PostalAddress in JSON-LD data."""
        if isinstance(data, dict):
            if data.get('@type') == 'PostalAddress':
                return data
            
            if 'address' in data:
                addr = data['address']
                if isinstance(addr, dict) and addr.get('@type') == 'PostalAddress':
                    return addr
            
            for value in data.values():
                if isinstance(value, (dict, list)):
                    result = self._find_postal_address(value)
                    if result:
                        return result
        
        elif isinstance(data, list):
            for item in data:
                result = self._find_postal_address(item)
                if result:
                    return result
        
        return None
    
    def _format_schema_address(self, address_data: dict) -> Optional[str]:
        """Format schema.org address into a string."""
        parts = []
        
        if address_data.get('streetAddress'):
            parts.append(address_data['streetAddress'])
        
        if address_data.get('addressLocality'):
            parts.append(address_data['addressLocality'])
        
        if address_data.get('addressRegion'):
            parts.append(address_data['addressRegion'])
        
        if address_data.get('postalCode'):
            parts.append(address_data['postalCode'])
        
        return ', '.join(parts) if parts else None
    
    def _extract_from_selectors(self, soup: BeautifulSoup) -> List[AddressCandidate]:
        """Extract addresses using configured CSS selectors."""
        candidates = []
        selectors = self.config.listing_page_selectors.address_container_selectors
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                
                for element in elements:
                    text = element.get_text(strip=True)
                    
                    if text and len(text) > 5:
                        candidates.append(AddressCandidate(
                            address_raw=text,
                            extraction_method=f'selector:{selector}',
                            html_snippet=str(element)[:500],
                            confidence=0.8
                        ))
                        
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {str(e)}")
        
        return candidates
    
    def _extract_from_heuristics(self, soup: BeautifulSoup) -> List[AddressCandidate]:
        """Extract addresses using text pattern heuristics."""
        candidates = []
        
        text = soup.get_text()
        
        # First, specifically look for 30aescapes pattern: "Address: [street]" and "Location: [area]"
        # This is the most reliable pattern for this site
        address_match = re.search(r'Address:\s*([^\n]+?)(?:Location:|Type:|$)', text, re.IGNORECASE | re.MULTILINE)
        location_match = re.search(r'Location:\s*([^\n]+?)(?:Type:|$)', text, re.IGNORECASE | re.MULTILINE)
        
        if address_match:
            street_address = address_match.group(1).strip()
            # Clean up the address - remove any trailing "Location:" if it got captured
            if 'Location:' in street_address:
                street_address = street_address[:street_address.index('Location:')].strip()
            
            # Combine with location if found
            full_address = street_address
            if location_match:
                location = location_match.group(1).strip()
                if 'Type:' in location:
                    location = location[:location.index('Type:')].strip()
                full_address = f"{street_address}, {location}"
            
            if len(street_address) > 5:
                candidates.append(AddressCandidate(
                    address_raw=full_address,
                    extraction_method='address_location_pattern',
                    html_snippet=f"Address: {street_address}" + (f", Location: {location}" if location_match else ""),
                    confidence=0.9  # High confidence for this specific pattern
                ))
        
        # Then try general address patterns
        address_patterns = [
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Circle|Cir)',
        ]
        
        for pattern in address_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                address_text = match.group(0)
                address_text = address_text.strip()
                
                # Don't add if we already found this address with the specific pattern
                if not any(address_text in c.address_raw for c in candidates):
                    if 5 < len(address_text) < 200:
                        candidates.append(AddressCandidate(
                            address_raw=address_text,
                            extraction_method='regex_heuristic',
                            html_snippet=address_text,
                            confidence=0.6
                        ))
        
        address_keywords = ['address', 'location', 'where you\'ll be', 'property location']
        
        for keyword in address_keywords:
            elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            
            for element in elements[:3]:
                parent = element.find_parent()
                if parent:
                    text = parent.get_text(strip=True)
                    
                    if 10 < len(text) < 200 and text not in [c.address_raw for c in candidates]:
                        candidates.append(AddressCandidate(
                            address_raw=text,
                            extraction_method=f'keyword:{keyword}',
                            html_snippet=str(parent)[:500],
                            confidence=0.5
                        ))
        
        return candidates[:5]
    
    def _extract_from_maps(self, soup: BeautifulSoup) -> List[AddressCandidate]:
        """Extract addresses from map widgets and iframes."""
        candidates = []
        
        iframes = soup.find_all('iframe')
        
        for iframe in iframes:
            src = iframe.get('src', '')
            
            if 'google.com/maps' in src or 'maps.google' in src:
                q_match = re.search(r'[?&]q=([^&]+)', src)
                if q_match:
                    address = q_match.group(1).replace('+', ' ')
                    candidates.append(AddressCandidate(
                        address_raw=address,
                        extraction_method='google_maps_iframe',
                        html_snippet=str(iframe)[:500],
                        confidence=0.7
                    ))
        
        map_elements = soup.select('[class*="map"], [id*="map"]')
        
        for element in map_elements[:3]:
            data_attrs = element.attrs
            
            for attr, value in data_attrs.items():
                if 'address' in attr.lower() and isinstance(value, str) and len(value) > 5:
                    candidates.append(AddressCandidate(
                        address_raw=value,
                        extraction_method=f'map_data_attr:{attr}',
                        html_snippet=str(element)[:500],
                        confidence=0.6
                    ))
        
        return candidates
    
    def _extract_from_meta_tags(self, soup: BeautifulSoup) -> List[AddressCandidate]:
        """Extract addresses from meta tags as fallback."""
        candidates = []
        
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            content = og_title['content']
            
            if any(kw in content.lower() for kw in ['beach', 'avenue', 'street', 'road', 'drive']):
                candidates.append(AddressCandidate(
                    address_raw=content,
                    extraction_method='og:title',
                    html_snippet=str(og_title),
                    confidence=0.3
                ))
        
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            content = og_desc['content']
            
            address_match = re.search(
                r'\d+\s+[A-Za-z\s]+(?:St|Ave|Rd|Blvd|Dr|Ln|Way)', 
                content
            )
            
            if address_match:
                candidates.append(AddressCandidate(
                    address_raw=address_match.group(0),
                    extraction_method='og:description',
                    html_snippet=content[:200],
                    confidence=0.4
                ))
        
        return candidates
