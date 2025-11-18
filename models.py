"""Pydantic models for API request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ConfigCreate(BaseModel):
    """Request model for creating a new config."""
    name: str = Field(..., min_length=1, max_length=255)
    config_data: Dict[str, Any] = Field(..., description="Site configuration as JSON")
    is_active: bool = True


class ConfigUpdate(BaseModel):
    """Request model for updating a config."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    config_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ConfigResponse(BaseModel):
    """Response model for a config."""
    id: int
    name: str
    config_data: Dict[str, Any]
    is_active: bool
    created_at: str
    updated_at: str


class ScrapeCreate(BaseModel):
    """Request model for starting a new scrape."""
    config_id: Optional[int] = None
    config_name: Optional[str] = None
    max_pages: Optional[int] = None


class ScrapeResponse(BaseModel):
    """Response model for a scrape run."""
    id: int
    site_id: int
    config_id: Optional[int]
    status: str
    start_time: str
    end_time: Optional[str]
    pages_visited: int
    listing_pages_found: int
    addresses_extracted: int
    current_page: Optional[int]
    total_pages_estimate: Optional[int]
    error_message: Optional[str]


class ScrapeDetailResponse(ScrapeResponse):
    """Detailed response model for a scrape run including logs."""
    logs: Optional[str]
    config_snapshot: Optional[str]


class AddressResult(BaseModel):
    """Response model for an address result."""
    listing_url: str
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]
    confidence_score: Optional[float]
    inference_method: Optional[str]


class ResultsResponse(BaseModel):
    """Response model for paginated results."""
    total: int
    page: int
    page_size: int
    results: List[AddressResult]


class StatsResponse(BaseModel):
    """Response model for statistics."""
    total_runs: int = 0
    completed: int = 0
    failed: int = 0
    running: int = 0
    queued: int = 0
    total_pages_visited: int = 0
    total_addresses_extracted: int = 0
    avg_duration_seconds: Optional[float] = None
