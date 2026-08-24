"""Japan news scraper module.

Scrapes Japanese & East Asian news headlines from Japan Today.
"""

from config import Config
from scraper.base_scraper import BaseNewsScraper


class JapanNewsScraper(BaseNewsScraper):
    """Scraper implementation for Japan Today (Japan)."""

    SOURCE_NAME: str = "Japan Today"
    RSS_URL: str = Config.RSS_URL_JAPAN_TODAY
    COUNTRY_CODE: str = "JP"

