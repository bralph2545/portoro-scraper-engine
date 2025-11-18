"""
Address normalization and enrichment module.
Parses raw addresses into components and uses context to infer missing fields.
Includes a stub for LLM-based address completion.
"""

import logging
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

from src.models import AddressCandidate, NormalizedAddress, SiteConfig

logger = logging.getLogger(__name__)


class AddressNormalizer:
    """Normalizes and enriches address data."""
    
    STATE_ABBREVIATIONS = {
        'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
        'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
        'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
        'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
        'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
        'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
        'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
        'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
        'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
        'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
        'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
        'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
        'wisconsin': 'WI', 'wyoming': 'WY'
    }
    
    def __init__(self, config: SiteConfig):
        """
        Initialize normalizer with site configuration.
        
        Args:
            config: SiteConfig object
        """
        self.config = config
    
    def normalize_address(self, candidate: AddressCandidate, 
                         url: str = None) -> NormalizedAddress:
        """
        Normalize an address candidate into structured components.
        
        Args:
            candidate: AddressCandidate object
            url: Optional listing page URL for context
            
        Returns:
            NormalizedAddress object
        """
        address_raw = candidate.address_raw.strip()
        
        parsed = self._parse_address_components(address_raw)
        
        if self._is_complete(parsed):
            parsed['confidence_score'] = 0.9
            parsed['inference_method'] = 'parser'
        else:
            parsed = self._enrich_with_context(parsed, address_raw, url)
        
        parsed['address_raw'] = address_raw
        
        return NormalizedAddress(**parsed)
    
    def _parse_address_components(self, address_raw: str) -> Dict[str, Any]:
        """
        Parse address string into components using regex patterns.
        
        Args:
            address_raw: Raw address string
            
        Returns:
            Dictionary of parsed components
        """
        components = {
            'address_line1': None,
            'address_line2': None,
            'city': None,
            'state': None,
            'postal_code': None,
            'country': 'USA',
            'confidence_score': 0.5,
            'inference_method': 'parser'
        }
        
        zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', address_raw)
        if zip_match:
            components['postal_code'] = zip_match.group(1)
        
        state_pattern = r'\b(' + '|'.join(self.STATE_ABBREVIATIONS.values()) + r')\b'
        state_match = re.search(state_pattern, address_raw, re.IGNORECASE)
        if state_match:
            components['state'] = state_match.group(1).upper()
        else:
            for full_name, abbrev in self.STATE_ABBREVIATIONS.items():
                if full_name in address_raw.lower():
                    components['state'] = abbrev
                    break
        
        street_match = re.match(
            r'^(\d+\s+[A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Circle|Cir|Highway|Hwy)\.?)',
            address_raw,
            re.IGNORECASE
        )
        if street_match:
            components['address_line1'] = street_match.group(1).strip()
        
        parts = [p.strip() for p in address_raw.split(',')]
        
        if len(parts) >= 2:
            if not components['address_line1']:
                components['address_line1'] = parts[0]
            
            if len(parts) >= 2 and not components['city']:
                city_candidate = parts[-2] if len(parts) > 2 else parts[-1]
                
                city_candidate = re.sub(r'\b[A-Z]{2}\b', '', city_candidate)
                city_candidate = re.sub(r'\b\d{5}(?:-\d{4})?\b', '', city_candidate)
                city_candidate = city_candidate.strip()
                
                if city_candidate and len(city_candidate) > 2:
                    components['city'] = city_candidate
        
        return components
    
    def _is_complete(self, parsed: Dict[str, Any]) -> bool:
        """Check if parsed address has all essential components."""
        return all([
            parsed.get('address_line1'),
            parsed.get('city'),
            parsed.get('state')
        ])
    
    def _enrich_with_context(self, parsed: Dict[str, Any], 
                            address_raw: str, url: str = None) -> Dict[str, Any]:
        """
        Enrich incomplete address using context from config and URL.
        
        Args:
            parsed: Partially parsed address components
            address_raw: Raw address string
            url: Listing page URL
            
        Returns:
            Enriched address components
        """
        enriched = parsed.copy()
        
        if not enriched.get('city') or not enriched.get('state'):
            city, state = self._extract_from_market_name()
            
            if not enriched.get('city') and city:
                enriched['city'] = city
                enriched['inferred_market'] = self.config.market_name
            
            if not enriched.get('state') and state:
                enriched['state'] = state
                enriched['inferred_market'] = self.config.market_name
        
        if url and not enriched.get('city'):
            url_city = self._extract_city_from_url(url)
            if url_city:
                enriched['city'] = url_city
                enriched['inference_method'] = 'url_path'
        
        if self._is_complete(enriched):
            enriched['confidence_score'] = 0.7
            enriched['inference_method'] = 'context_enrichment'
        else:
            enriched = self._llm_enrich_stub(enriched, address_raw, url)
        
        return enriched
    
    def _extract_from_market_name(self) -> tuple:
        """
        Extract city and state from market_name.
        
        Returns:
            Tuple of (city, state)
        """
        market = self.config.market_name
        if not market:
            return None, None
        
        for state_name, abbrev in self.STATE_ABBREVIATIONS.items():
            if state_name in market.lower() or abbrev in market.upper():
                state = abbrev
                
                city = market.replace(state_name, '').replace(abbrev, '')
                city = re.sub(r'[/,]', ' ', city)
                city = city.strip()
                
                if city:
                    return city, state
                
                return None, state
        
        parts = [p.strip() for p in re.split(r'[/,]', market)]
        if parts:
            return parts[0], None
        
        return None, None
    
    def _extract_city_from_url(self, url: str) -> Optional[str]:
        """Extract potential city name from URL path."""
        try:
            path = urlparse(url).path
            parts = [p for p in path.split('/') if p]
            
            city_keywords = ['destin', 'miami', 'orlando', 'tampa', 'beach', 'bay', 'island']
            
            for part in parts:
                part_clean = part.replace('-', ' ').replace('_', ' ')
                
                if any(kw in part_clean.lower() for kw in city_keywords):
                    return part_clean.title()
        
        except:
            pass
        
        return None
    
    def _llm_enrich_stub(self, parsed: Dict[str, Any], 
                        address_raw: str, url: str = None) -> Dict[str, Any]:
        """
        Stub for LLM-based address enrichment.
        
        This is where you would integrate an LLM API (OpenAI, Anthropic, etc.)
        to intelligently fill in missing address components.
        
        Args:
            parsed: Partially parsed address
            address_raw: Raw address string
            url: Listing page URL
            
        Returns:
            Enriched address components
        """
        enriched = parsed.copy()
        
        logger.info(f"LLM enrichment stub called for: {address_raw}")
        
        if not self._is_complete(enriched):
            enriched['confidence_score'] = 0.4
            enriched['inference_method'] = 'incomplete'
        else:
            enriched['confidence_score'] = 0.6
            enriched['inference_method'] = 'llm_stub'
        
        return enriched
    
    def deduplicate_addresses(self, addresses: List[NormalizedAddress]) -> List[NormalizedAddress]:
        """
        Deduplicate addresses based on similarity.
        
        Args:
            addresses: List of NormalizedAddress objects
            
        Returns:
            Deduplicated list
        """
        if not addresses:
            return []
        
        unique = []
        seen_keys = set()
        
        for addr in addresses:
            key = (
                addr.address_line1 or '',
                addr.city or '',
                addr.state or '',
                addr.postal_code or ''
            )
            
            key_normalized = tuple(k.lower().strip() for k in key)
            
            if key_normalized not in seen_keys and any(key):
                seen_keys.add(key_normalized)
                unique.append(addr)
        
        unique.sort(key=lambda a: a.confidence_score, reverse=True)
        
        return unique


def integrate_llm_enrichment(api_key: str, model: str = "gpt-4"):
    """
    INTEGRATION POINT: Replace the stub with actual LLM API calls.
    
    Example integration with OpenAI:
    
    ```python
    import openai
    
    def _llm_enrich_stub(self, parsed, address_raw, url):
        prompt = f'''
        Given this incomplete address: {address_raw}
        
        Context:
        - Market: {self.config.market_name}
        - URL: {url}
        - Current parsed: {parsed}
        
        Fill in missing fields (city, state, postal_code) and return JSON:
        {{
            "address_line1": "...",
            "city": "...",
            "state": "...",
            "postal_code": "...",
            "confidence_score": 0.0-1.0
        }}
        '''
        
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = json.loads(response.choices[0].message.content)
        result['inference_method'] = 'llm_enrichment'
        return result
    ```
    
    Args:
        api_key: API key for LLM service
        model: Model name to use
    """
    pass
