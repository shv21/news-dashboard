"""The Verge news scraper module.

Scrapes technology and pop culture news from The Verge.
"""

from config import Config
from scraper.base_scraper import BaseNewsScraper


class VergeScraper(BaseNewsScraper):
    """Scraper implementation for The Verge tech news (US)."""

    SOURCE_NAME: str = "The Verge"
    RSS_URL: str = Config.RSS_URL_VERGE
    COUNTRY_CODE: str = "US"

