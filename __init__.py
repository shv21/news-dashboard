"""News Aggregator Dashboard Package.

Provides a unified news aggregator web application, REST API, SQLite database,
background scraping manager, and Google Sheets synchronization service.
"""

from config import Config
from exceptions import (
    ConfigurationError,
    DatabaseError,
    GoogleSheetsError,
    NewsDashboardError,
    ScraperError,
    ScraperFetchError,
    ScraperParseError,
)
from utils import (
    classify_category,
    clean_html_text,
    generate_seed_image_url,
    is_valid_url,
    parse_datetime,
)

__all__ = [
    "Config",
    "NewsDashboardError",
    "ConfigurationError",
    "DatabaseError",
    "ScraperError",
    "ScraperFetchError",
    "ScraperParseError",
    "GoogleSheetsError",
    "clean_html_text",
    "parse_datetime",
    "is_valid_url",
    "classify_category",
    "generate_seed_image_url",
]
