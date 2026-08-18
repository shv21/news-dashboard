"""Unit tests for scraper configurations and date parsers.

Tests instantiation, feed URL values, and date parsing fallbacks.
"""

from typing import Any

from scraper.scraper_one import BBCNewsScraper
from scraper.scraper_two import TechCrunchScraper


def test_bbc_scraper_instantiation() -> None:
    """Test BBC Scraper configuration and source name."""
    scraper = BBCNewsScraper()
    assert scraper.SOURCE_NAME == "BBC News"
    assert "bbci.co.uk" in scraper.RSS_URL


def test_techcrunch_scraper_instantiation() -> None:
    """Test TechCrunch Scraper configuration and source name."""
    scraper = TechCrunchScraper()
    assert scraper.SOURCE_NAME == "TechCrunch"
    assert "techcrunch.com" in scraper.RSS_URL


def test_bbc_date_fallback() -> None:
    """Test scraper date parser with dummy feed entry."""
    from utils import parse_datetime

    class DummyEntry:
        published_parsed: Any = None
        published: Any = None

    dt = parse_datetime(DummyEntry())
    assert dt is not None
