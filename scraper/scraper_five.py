"""Times of India news scraper module.

Scrapes Indian & South Asian top news stories from Times of India.
"""

from config import Config
from scraper.base_scraper import BaseNewsScraper


class IndiaNewsScraper(BaseNewsScraper):
    """Scraper implementation for Times of India (India news)."""

    SOURCE_NAME: str = "Times of India"
    RSS_URL: str = Config.RSS_URL_TIMES_OF_INDIA
    COUNTRY_CODE: str = "IN"

