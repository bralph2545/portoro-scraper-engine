"""
Utility functions for logging, URL handling, and common operations.
"""

import logging
import re
from urllib.parse import urlparse, urljoin, urlunparse
from typing import Set, List, Optional
import sys


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path to write logs
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def normalize_url(url: str, base_url: str = None) -> str:
    """
    Normalize a URL by removing fragments and query parameters (optional).
    
    Args:
        url: URL to normalize
        base_url: Base URL for resolving relative URLs
        
    Returns:
        Normalized absolute URL
    """
    if base_url:
        url = urljoin(base_url, url)
    
    parsed = urlparse(url)
    
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        parsed.query,
        ''
    ))
    
    return normalized.rstrip('/')


def is_same_domain(url: str, domain: str) -> bool:
    """
    Check if URL belongs to the specified domain.
    
    Args:
        url: URL to check
        domain: Domain to match against
        
    Returns:
        True if URL is from the same domain
    """
    try:
        parsed = urlparse(url)
        url_domain = parsed.netloc.lower()
        target_domain = domain.lower()
        
        return url_domain == target_domain or url_domain.endswith(f'.{target_domain}')
    except:
        return False


def matches_url_pattern(url: str, patterns: List[str]) -> bool:
    """
    Check if URL matches any of the given patterns.
    
    Args:
        url: URL to check
        patterns: List of regex patterns or substring patterns
        
    Returns:
        True if URL matches any pattern
    """
    if not patterns:
        return False
    
    url_lower = url.lower()
    
    for pattern in patterns:
        if pattern in url_lower:
            return True
        
        try:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        except re.error:
            pass
    
    return False


def is_likely_listing_url(url: str, listing_patterns: List[str] = None, 
                          excluded_patterns: List[str] = None) -> bool:
    """
    Heuristically determine if a URL is likely a property listing page.
    
    Args:
        url: URL to check
        listing_patterns: Patterns that indicate listing pages
        excluded_patterns: Patterns that indicate non-listing pages
        
    Returns:
        True if URL is likely a listing page
    """
    url_lower = url.lower()
    
    excluded_keywords = [
        '/blog', '/about', '/contact', '/faq', '/careers', '/news',
        '/search', '/filter', '/category', '/tag', '/author',
        '.pdf', '.jpg', '.png', '.gif', '.css', '.js',
        '/login', '/signup', '/register', '/cart', '/checkout'
    ]
    
    if excluded_patterns:
        excluded_keywords.extend(excluded_patterns)
    
    for keyword in excluded_keywords:
        if keyword in url_lower:
            return False
    
    if listing_patterns and matches_url_pattern(url, listing_patterns):
        return True
    
    listing_indicators = [
        '/property/', '/rental/', '/listing/', '/vacation-rental/',
        '/home/', '/unit/', '/condo/', '/house/', '/villa/'
    ]
    
    for indicator in listing_indicators:
        if indicator in url_lower:
            return True
    
    path = urlparse(url).path
    parts = [p for p in path.split('/') if p]
    
    if len(parts) >= 2:
        last_part = parts[-1]
        if re.match(r'^[a-z0-9-]{10,}$', last_part) or last_part.isdigit():
            return True
    
    return False


def deduplicate_urls(urls: List[str]) -> List[str]:
    """
    Remove duplicate URLs while preserving order.
    
    Args:
        urls: List of URLs
        
    Returns:
        Deduplicated list
    """
    seen = set()
    result = []
    
    for url in urls:
        normalized = normalize_url(url)
        if normalized not in seen:
            seen.add(normalized)
            result.append(url)
    
    return result


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL to parse
        
    Returns:
        Domain name
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return ""


def truncate_text(text: str, max_length: int = 500) -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
