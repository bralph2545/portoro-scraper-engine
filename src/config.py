"""
Configuration loading and validation from YAML files.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from src.models import SiteConfig

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and validates site configuration from YAML files."""
    
    @staticmethod
    def load_config(config_path: str) -> SiteConfig:
        """
        Load configuration from a YAML file.
        
        Args:
            config_path: Path to the YAML config file
            
        Returns:
            SiteConfig object
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        logger.info(f"Loading config from: {config_path}")
        
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data:
            raise ValueError(f"Empty config file: {config_path}")
        
        ConfigLoader.validate_config(data)
        
        site_config = SiteConfig.from_dict(data)
        logger.info(f"Config loaded: {site_config.manager_name} ({site_config.manager_domain})")
        
        return site_config
    
    @staticmethod
    def validate_config(data: Dict[str, Any]) -> None:
        """
        Validate required config fields.
        
        Args:
            data: Config dictionary
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ['manager_name', 'manager_domain', 'market_name', 'seed_urls']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required config field: {field}")
        
        if not isinstance(data['seed_urls'], list) or len(data['seed_urls']) == 0:
            raise ValueError("seed_urls must be a non-empty list")
        
        logger.debug("Config validation passed")
    
    @staticmethod
    def save_config_snapshot(site_config) -> str:
        """
        Convert config to YAML string for storage.
        
        Args:
            site_config: SiteConfig object or dict-like object
            
        Returns:
            YAML string representation
        """
        # Handle both SiteConfig objects and dict-like objects
        if hasattr(site_config, '__dict__'):
            # It's an object with attributes
            config_dict = {}
            for key in ['manager_name', 'manager_domain', 'market_name', 'seed_urls',
                       'sitemap_urls', 'property_directory_urls', 'listing_url_patterns',
                       'excluded_url_patterns', 'address_selectors', 'listing_url_pattern',
                       'max_depth', 'max_concurrent_requests']:
                if hasattr(site_config, key):
                    config_dict[key] = getattr(site_config, key)
        else:
            # It's already a dict
            config_dict = dict(site_config)
        
        return yaml.dump(config_dict, default_flow_style=False)
