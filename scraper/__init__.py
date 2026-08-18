"""Scraper Package.

Provides news scraper orchestration manager and individual news source scrapers.
"""

from scraper.scraper_eight import GermanyNewsScraper
from scraper.scraper_five import IndiaNewsScraper
from scraper.scraper_four import WiredScraper
from scraper.scraper_manager import ScraperManager
from scraper.scraper_nine import JapanNewsScraper
from scraper.scraper_one import BBCNewsScraper
from scraper.scraper_seven import AustraliaNewsScraper
from scraper.scraper_six import CBCNewsScraper
from scraper.scraper_three import VergeScraper
from scraper.scraper_two import TechCrunchScraper

__all__ = [
    "ScraperManager",
    "BBCNewsScraper",
    "TechCrunchScraper",
    "VergeScraper",
    "WiredScraper",
    "IndiaNewsScraper",
    "CBCNewsScraper",
    "AustraliaNewsScraper",
    "GermanyNewsScraper",
    "JapanNewsScraper",
]
