"""Wired news scraper module.

Scrapes technology news headlines from Wired Magazine.
"""

from config import Config
from scraper.base_scraper import BaseNewsScraper


class WiredScraper(BaseNewsScraper):
    """Scraper implementation for Wired technology news (US)."""

    SOURCE_NAME: str = "Wired"
    RSS_URL: str = Config.RSS_URL_WIRED
    COUNTRY_CODE: str = "US"

