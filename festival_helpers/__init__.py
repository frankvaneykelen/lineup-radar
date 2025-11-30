"""
Festival Helpers Library

Shared utilities for festival lineup tracking and HTML generation.
Supports multiple festivals and years.
"""

from .slug import artist_name_to_slug
from .ai_client import get_azure_openai_client, translate_text
from .scraper import FestivalScraper
from .config import FestivalConfig, get_festival_config

__all__ = [
    'artist_name_to_slug',
    'get_azure_openai_client',
    'translate_text',
    'FestivalScraper',
    'FestivalConfig',
    'get_festival_config',
]

__version__ = '1.0.0'
