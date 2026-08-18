"""Australia news scraper module.

Scrapes Australian news headlines from ABC News Australia.
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


class AustraliaNewsScraper:
    """Scraper implementation for ABC News (Australia)."""

    SOURCE_NAME: str = "ABC News Australia"
    RSS_URL: str = Config.RSS_URL_ABC_AUSTRALIA

    def __init__(self) -> None:
        """Initialize AustraliaNewsScraper with request headers."""
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
                    f"[ABC Australia Scraper] Attempt {attempt}/{retries} failed: {e}"
                )
                if attempt < retries:
                    time.sleep(1 * attempt)
        return None

    def extract_image_url(
        self, entry: Any, summary_html: str = "", title: str = ""
    ) -> str:
        """Extract image URL from feed enclosures, media content or HTML summary.

        Args:
            entry (Any): Feed entry object from feedparser.
            summary_html (str): Summary HTML text.
            title (str): Article title fallback key.

        Returns:
            str: Resolved image URL or seed fallback.
        """
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            return entry.media_thumbnail[0].get("url")
        if hasattr(entry, "media_content") and entry.media_content:
            return entry.media_content[0].get("url")
        if hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                if enc.get("type", "").startswith("image"):
                    return enc.get("href") or enc.get("url")

        if summary_html:
            soup = BeautifulSoup(summary_html, "html.parser")
            img_tag = soup.find("img")
            if img_tag and img_tag.get("src"):
                return img_tag["src"]

        seed_key: str = entry.get("link", "") or title
        return generate_seed_image_url(seed_key)

    def scrape(self) -> List[Dict[str, Any]]:
        """Execute news scraping for ABC News Australia.

        Returns:
            List[Dict[str, Any]]: List of article dictionaries.
        """
        logger.info(
            f"[ABC Australia Scraper] Starting scrape from {self.RSS_URL}"
        )
        feed_xml: Optional[str] = self.fetch_feed_content(self.RSS_URL)
        if not feed_xml:
            logger.error(
                "[ABC Australia Scraper] Unable to fetch ABC RSS feed xml."
            )
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
                image_url: str = self.extract_image_url(entry, summary, title)

                articles.append(
                    {
                        "title": title,
                        "source": self.SOURCE_NAME,
                        "published_date": pub_date,
                        "summary": summary_text[:500],
                        "image_url": image_url,
                        "article_url": article_url,
                        "country": "AU",
                    }
                )
            except Exception as e:
                logger.error(f"[ABC Australia Scraper] Error parsing entry: {e}")
                continue

        logger.info(
            f"[ABC Australia Scraper] Successfully extracted {len(articles)} articles."
        )
        return articles
