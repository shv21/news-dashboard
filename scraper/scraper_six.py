"""Canadian news scraper module.

Scrapes Canadian news headlines from Global News / CBC.
"""

from config import Config
from scraper.base_scraper import BaseNewsScraper


class CBCNewsScraper(BaseNewsScraper):
    """Scraper implementation for Canadian News (Global News / CBC)."""

    SOURCE_NAME: str = "CBC News"
    RSS_URL: str = Config.RSS_URL_CBC
    COUNTRY_CODE: str = "CA"

