"""BBC News scraper module.

Scrapes UK news headlines and RSS feed entries from BBC News.
"""

from config import Config
from scraper.base_scraper import BaseNewsScraper


class BBCNewsScraper(BaseNewsScraper):
    """Scraper implementation for BBC News (UK)."""

    SOURCE_NAME: str = "BBC News"
    RSS_URL: str = Config.RSS_URL_BBC
    COUNTRY_CODE: str = "UK"

