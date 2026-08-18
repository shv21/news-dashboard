"""Times of India news scraper module.

Scrapes Indian & South Asian top news stories from Times of India.
"""

from datetime import datetime
import logging
import time
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
import feedparser
import requests

from config import Config
from utils import clean_html_text, generate_seed_image_url, parse_datetime

logger = logging.getLogger(__name__)


class IndiaNewsScraper:
    """Scraper implementation for Times of India (India news)."""

    SOURCE_NAME: str = "Times of India"
    RSS_URL: str = Config.RSS_URL_TIMES_OF_INDIA

    def __init__(self) -> None:
        """Initialize IndiaNewsScraper with request headers."""
        self.headers: Dict[str, str] = {
            "User-Agent": Config.SCRAPER_USER_AGENT,
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        }

    def fetch_feed_content(
        self,
        url: str,
        max_retries: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> Optional[str]:
        """Fetch feed XML with retry mechanism.

        Args:
            url (str): Target RSS feed URL.
            max_retries (Optional[int]): Retry limit.
            timeout (Optional[int]): Request timeout in seconds.

        Returns:
            Optional[str]: Feed XML text if successful, None otherwise.
        """
        retries: int = max_retries or Config.SCRAPER_MAX_RETRIES
        req_timeout: int = timeout or Config.SCRAPER_REQUEST_TIMEOUT

        for attempt in range(1, retries + 1):
            try:
                response = requests.get(
                    url, headers=self.headers, timeout=req_timeout
                )
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.warning(
                    f"[India Scraper] Attempt {attempt}/{retries} failed: {e}"
                )
                if attempt < retries:
                    time.sleep(1 * attempt)
        return None

    def extract_image_url(self, entry: Any, title: str = "") -> str:
        """Extract image URL or return unique seed fallback.

        Args:
            entry (Any): Feed entry object from feedparser.
            title (str): Article title fallback key.

        Returns:
            str: Resolved image URL or seed fallback image.
        """
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            for item in entry.media_thumbnail:
                if item.get("url"):
                    return item["url"]
        if hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                if enc.get("type", "").startswith("image/") and enc.get("href"):
                    return enc["href"]

        if hasattr(entry, "summary"):
            soup = BeautifulSoup(entry.summary, "html.parser")
            img = soup.find("img")
            if img and img.get("src"):
                return img["src"]

        seed_key: str = entry.get("link", "") or title
        return generate_seed_image_url(seed_key)

    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape articles from Times of India.

        Returns:
            List[Dict[str, Any]]: List of article dictionaries.
        """
        logger.info(f"[India Scraper] Starting scrape from {self.RSS_URL}")
        feed_xml: Optional[str] = self.fetch_feed_content(self.RSS_URL)
        if not feed_xml:
            logger.error("[India Scraper] Unable to fetch Times of India feed.")
            return []

        parsed_feed = feedparser.parse(feed_xml)
        articles: List[Dict[str, Any]] = []

        for entry in parsed_feed.entries:
            try:
                title: str = getattr(entry, "title", "").strip()
                article_url: str = getattr(entry, "link", "").strip()
                summary: str = getattr(entry, "summary", "").strip()

                if not title or not article_url:
                    continue

                summary_text: str = clean_html_text(summary)
                pub_date: datetime = parse_datetime(entry)
                image_url: str = self.extract_image_url(entry, title)

                articles.append(
                    {
                        "title": title,
                        "source": self.SOURCE_NAME,
                        "published_date": pub_date,
                        "summary": summary_text[:500],
                        "image_url": image_url,
                        "article_url": article_url,
                        "country": "IN",
                    }
                )
            except Exception as e:
                logger.error(f"[India Scraper] Error parsing entry: {e}")
                continue

        logger.info(
            f"[India Scraper] Successfully extracted {len(articles)} articles."
        )
        return articles
