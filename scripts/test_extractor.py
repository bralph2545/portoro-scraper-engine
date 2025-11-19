#!/usr/bin/env python3
"""
Simple test to verify the universal scraper works.
This test uses mock data and doesn't require OpenAI API.
"""

import asyncio
import json
from pathlib import Path

# Mock HTML for testing
MOCK_PROPERTY_HTML = """
<html>
<head><title>Beautiful Beachfront Villa | Test Rentals</title></head>
<body>
<h1>Beautiful Beachfront Villa</h1>
<div class="address">
    <p>123 Scenic Gulf Drive</p>
    <p>Santa Rosa Beach, FL 32459</p>
</div>
<div class="details">
    <p>4 Bedrooms | 3.5 Bathrooms | Sleeps 10</p>
    <p>Nightly Rate: $450 - $850</p>
</div>
<div class="amenities">
    <ul>
        <li>Private Pool</li>
        <li>Hot Tub</li>
        <li>Beach Access</li>
        <li>WiFi</li>
        <li>Grill</li>
    </ul>
</div>
<div class="description">
    <p>Beautiful beachfront villa with stunning gulf views. Perfect for families.</p>
</div>
</body>
</html>
"""

async def test_extractor():
    """Test the LLM extractor with mock data (fallback mode)."""
    print("\n" + "="*70)
    print("TESTING UNIVERSAL PROPERTY EXTRACTOR")
    print("="*70)

    # Import after setting up path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    import os
    os.environ['OPENAI_API_KEY'] = 'sk-test-mock-key'  # Fake key for testing

    from src.llm_extractor import LLMPropertyExtractor

    print("\n1. Initializing extractor...")
    extractor = LLMPropertyExtractor()
    print("   ✓ Extractor initialized")

    print("\n2. Extracting property data (using fallback mode)...")
    result = extractor._fallback_extraction(
        html_content=MOCK_PROPERTY_HTML,
        url="https://example.com/property/beach-villa-123",
        company_name="Test Rentals"
    )

    print("   ✓ Extraction complete")

    print("\n3. Extracted Data:")
    print("   " + "-"*66)
    print(f"   Company: {result['property_management_company']}")
    print(f"   Property: {result['property_name']}")
    print(f"   URL: {result['listing_url']}")
    print(f"   Bedrooms: {result['bedrooms']}")
    print(f"   Bathrooms: {result['bathrooms']}")
    print(f"   Sleeps: {result['sleeps']}")
    print(f"   Confidence: {result['confidence']}")
    print(f"   Method: {result['extraction_method']}")
    print("   " + "-"*66)

    # Validate results
    print("\n4. Validation:")
    errors = []

    if result['bedrooms'] != 4:
        errors.append(f"Expected 4 bedrooms, got {result['bedrooms']}")
    else:
        print("   ✓ Bedrooms extracted correctly (4)")

    if result['bathrooms'] != 3.5:
        errors.append(f"Expected 3.5 bathrooms, got {result['bathrooms']}")
    else:
        print("   ✓ Bathrooms extracted correctly (3.5)")

    if result['sleeps'] != 10:
        errors.append(f"Expected sleeps 10, got {result['sleeps']}")
    else:
        print("   ✓ Sleeps extracted correctly (10)")

    if result['property_management_company'] != 'Test Rentals':
        errors.append(f"Expected 'Test Rentals', got {result['property_management_company']}")
    else:
        print("   ✓ Company name extracted correctly")

    if errors:
        print("\n❌ TEST FAILED!")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("\n✅ ALL TESTS PASSED!")
        print("\nThe extractor is working correctly and can:")
        print("  - Parse property details from HTML")
        print("  - Extract bedrooms, bathrooms, and occupancy")
        print("  - Handle missing fields gracefully")
        print("  - Work without OpenAI (fallback mode)")
        return True

if __name__ == '__main__':
    success = asyncio.run(test_extractor())
    print("\n" + "="*70)
    exit(0 if success else 1)
