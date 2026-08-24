"""TechCrunch news scraper module.

Scrapes technology news articles and RSS feed entries from TechCrunch.
"""

from config import Config
from scraper.base_scraper import BaseNewsScraper


class TechCrunchScraper(BaseNewsScraper):
    """Scraper implementation for TechCrunch tech news (US)."""

    SOURCE_NAME: str = "TechCrunch"
    RSS_URL: str = Config.RSS_URL_TECHCRUNCH
    COUNTRY_CODE: str = "US"

