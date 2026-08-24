"""Germany news scraper module.

Scrapes European and German news headlines from Deutsche Welle (DW News).
"""

from config import Config
from scraper.base_scraper import BaseNewsScraper


class GermanyNewsScraper(BaseNewsScraper):
    """Scraper implementation for DW News (Deutsche Welle - Germany)."""

    SOURCE_NAME: str = "DW News"
    RSS_URL: str = Config.RSS_URL_DW_GERMANY
    COUNTRY_CODE: str = "DE"

