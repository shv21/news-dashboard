"""Australia news scraper module.

Scrapes Australian news headlines from ABC News Australia.
"""

from config import Config
from scraper.base_scraper import BaseNewsScraper


class AustraliaNewsScraper(BaseNewsScraper):
    """Scraper implementation for ABC News (Australia)."""

    SOURCE_NAME: str = "ABC News Australia"
    RSS_URL: str = Config.RSS_URL_ABC_AUSTRALIA
    COUNTRY_CODE: str = "AU"

