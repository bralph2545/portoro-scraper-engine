"""
LLM-powered universal property data extractor.
Uses OpenAI to intelligently extract property information from any vacation rental website.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

# Check if OpenAI is available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. Install with: pip install openai")


class LLMPropertyExtractor:
    """Extract property data from any vacation rental listing page using LLM."""

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        """
        Initialize the LLM extractor.

        Args:
            api_key: OpenAI API key (or reads from OPENAI_API_KEY env var)
            model: OpenAI model to use (gpt-4o-mini is fast and cheap)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package required. Install with: pip install openai")

        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key parameter")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model

        logger.info(f"Initialized LLM extractor with model: {model}")

    def extract_property_data(self, html_content: str, url: str,
                             company_name: str = None) -> Dict[str, Any]:
        """
        Extract property data from HTML using LLM.

        Args:
            html_content: Raw HTML of the property listing page
            url: URL of the property listing
            company_name: Optional property management company name

        Returns:
            Dictionary with extracted property data
        """
        # Clean and prepare the HTML
        cleaned_text = self._clean_html(html_content)

        # Truncate if too long (LLM context limits)
        if len(cleaned_text) > 15000:
            cleaned_text = cleaned_text[:15000] + "\n\n[Content truncated...]"

        # Build the extraction prompt
        prompt = self._build_extraction_prompt(cleaned_text, url, company_name)

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data extraction specialist. Extract vacation rental property information from webpage content and return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,  # Deterministic output
                response_format={"type": "json_object"}  # Ensure JSON response
            )

            # Parse the response
            extracted_data = json.loads(response.choices[0].message.content)

            # Add metadata
            extracted_data['listing_url'] = url
            extracted_data['extraction_method'] = 'llm'
            extracted_data['model_used'] = self.model

            logger.info(f"Successfully extracted property data from {url}")
            return extracted_data

        except Exception as e:
            logger.error(f"LLM extraction failed for {url}: {str(e)}")
            # Return fallback data
            return self._fallback_extraction(html_content, url, company_name)

    def _clean_html(self, html_content: str) -> str:
        """Clean HTML and extract meaningful text."""
        soup = BeautifulSoup(html_content, 'lxml')

        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        # Get text
        text = soup.get_text(separator='\n', strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)

        return text

    def _build_extraction_prompt(self, content: str, url: str,
                                 company_name: str = None) -> str:
        """Build the prompt for LLM extraction."""

        prompt = f"""Extract vacation rental property information from the following webpage content.

URL: {url}
"""

        if company_name:
            prompt += f"Property Management Company: {company_name}\n"

        prompt += f"""
WEBPAGE CONTENT:
{content}

---

Extract the following information and return as valid JSON:

{{
  "property_management_company": "Company name from the page (or '{company_name}' if provided above)",
  "property_name": "Full property name/title",
  "street_address": "Street address with number",
  "city": "City name",
  "state": "State (2-letter code if USA)",
  "zip_code": "Postal/ZIP code",
  "country": "Country (default to USA if not specified)",
  "bedrooms": <number or null>,
  "bathrooms": <number or null>,
  "sleeps": <number or null>,
  "nightly_rate_min": <number or null>,
  "nightly_rate_max": <number or null>,
  "amenities": ["list", "of", "amenities"],
  "description": "Brief property description (max 500 chars)",
  "property_id": "Any listing ID or property code found",
  "confidence": <0.0 to 1.0 - how confident are you in this extraction>
}}

INSTRUCTIONS:
- If a field is not found or unclear, use null
- For bedrooms/bathrooms/sleeps: extract the number only
- For rates: extract numerical values only (no $ or currency symbols)
- For amenities: extract as an array of strings
- For address: be as complete as possible, parse from any format
- Description should be concise, not the entire listing text
- Confidence should reflect how certain you are about the data quality

Return ONLY valid JSON, no additional text.
"""

        return prompt

    def _fallback_extraction(self, html_content: str, url: str,
                            company_name: str = None) -> Dict[str, Any]:
        """Fallback extraction using regex when LLM fails."""
        logger.info(f"Using fallback extraction for {url}")

        soup = BeautifulSoup(html_content, 'lxml')
        text = soup.get_text()

        # Try to extract basic info with regex
        bedrooms_match = re.search(r'(\d+)\s*(?:bed(?:room)?s?|BR)', text, re.IGNORECASE)
        bathrooms_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath(?:room)?s?|BA)', text, re.IGNORECASE)
        sleeps_match = re.search(r'(?:sleeps?|accommodates?)\s*(\d+)', text, re.IGNORECASE)

        # Extract title
        title = None
        if soup.title:
            title = soup.title.string
        elif soup.h1:
            title = soup.h1.get_text(strip=True)

        return {
            'listing_url': url,
            'property_management_company': company_name,
            'property_name': title,
            'street_address': None,
            'city': None,
            'state': None,
            'zip_code': None,
            'country': 'USA',
            'bedrooms': int(bedrooms_match.group(1)) if bedrooms_match else None,
            'bathrooms': float(bathrooms_match.group(1)) if bathrooms_match else None,
            'sleeps': int(sleeps_match.group(1)) if sleeps_match else None,
            'nightly_rate_min': None,
            'nightly_rate_max': None,
            'amenities': [],
            'description': None,
            'property_id': None,
            'confidence': 0.3,
            'extraction_method': 'fallback_regex',
            'model_used': None
        }


class BatchPropertyExtractor:
    """Extract property data from multiple URLs in batch."""

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        """Initialize batch extractor."""
        self.extractor = LLMPropertyExtractor(api_key=api_key, model=model)
        self.results = []

    async def extract_from_urls(self, urls_with_html: list) -> list:
        """
        Extract property data from multiple URLs.

        Args:
            urls_with_html: List of tuples (url, html_content, company_name)

        Returns:
            List of extracted property data dictionaries
        """
        results = []

        for i, (url, html_content, company_name) in enumerate(urls_with_html, 1):
            logger.info(f"Extracting property data {i}/{len(urls_with_html)}: {url}")

            try:
                data = self.extractor.extract_property_data(
                    html_content=html_content,
                    url=url,
                    company_name=company_name
                )
                results.append(data)

            except Exception as e:
                logger.error(f"Failed to extract data from {url}: {str(e)}")
                results.append({
                    'listing_url': url,
                    'error': str(e),
                    'extraction_method': 'failed'
                })

        return results
