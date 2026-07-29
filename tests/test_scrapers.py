import pytest
from scraper.scraper_one import BBCNewsScraper
from scraper.scraper_two import TechCrunchScraper

def test_bbc_scraper_instantiation():
    """Test BBC Scraper configuration."""
    scraper = BBCNewsScraper()
    assert scraper.SOURCE_NAME == "BBC News"
    assert "bbci.co.uk" in scraper.RSS_URL

def test_techcrunch_scraper_instantiation():
    """Test TechCrunch Scraper configuration."""
    scraper = TechCrunchScraper()
    assert scraper.SOURCE_NAME == "TechCrunch"
    assert "techcrunch.com" in scraper.RSS_URL

def test_bbc_date_fallback():
    """Test scraper date parser with mock data."""
    scraper = BBCNewsScraper()
    class DummyEntry:
        published_parsed = None
        published = None

    dt = scraper.parse_published_date(DummyEntry())
    assert dt is not None
