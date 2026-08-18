"""TechCrunch news scraper module.

Scrapes technology news articles and RSS feed entries from TechCrunch.
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


class TechCrunchScraper:
    """Scraper implementation for TechCrunch tech news."""

    SOURCE_NAME: str = "TechCrunch"
    RSS_URL: str = Config.RSS_URL_TECHCRUNCH

    def __init__(self) -> None:
        """Initialize TechCrunchScraper with custom request headers."""
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
        """Fetch feed XML with retry mechanism and custom headers.

        Args:
            url (str): Target RSS feed URL.
            max_retries (Optional[int]): Retry limit.
            timeout (Optional[int]): Timeout in seconds.

        Returns:
            Optional[str]: Feed XML content if successful, None otherwise.
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
                    f"[TechCrunch Scraper] Attempt {attempt}/{retries} failed: {e}"
                )
                if attempt < retries:
                    time.sleep(1 * attempt)
        logger.error(
            f"[TechCrunch Scraper] Failed to fetch after {retries} attempts."
        )
        return None

    def extract_image_url(self, entry: Any, title: str = "") -> str:
        """Extract high quality image URL from RSS media or content HTML.

        Args:
            entry (Any): Feed entry object from feedparser.
            title (str): Article title fallback key.

        Returns:
            str: Resolved image URL or seed fallback image URL.
        """
        if hasattr(entry, "media_content") and entry.media_content:
            for item in entry.media_content:
                if item.get("url"):
                    return item["url"]

        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            for item in entry.media_thumbnail:
                if item.get("url"):
                    return item["url"]

        if hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                if enc.get("type", "").startswith("image"):
                    return enc.get("href") or enc.get("url")

        html_snippets: List[str] = []
        if hasattr(entry, "content") and entry.content:
            for c in entry.content:
                html_snippets.append(c.get("value", ""))
        if hasattr(entry, "summary"):
            html_snippets.append(entry.summary)
        if hasattr(entry, "description"):
            html_snippets.append(entry.description)

        for snippet in html_snippets:
            if not snippet:
                continue
            soup = BeautifulSoup(snippet, "html.parser")
            imgs = soup.find_all("img")
            for img in imgs:
                src = (
                    img.get("src")
                    or img.get("data-src")
                    or img.get("srcset")
                )
                if (
                    src
                    and "gravatar" not in src
                    and "pixel" not in src
                    and "icon" not in src
                ):
                    if " " in src:
                        src = src.split(" ")[0]
                    return src

        seed_key: str = entry.get("link", "") or title
        return generate_seed_image_url(seed_key)

    def scrape(self) -> List[Dict[str, Any]]:
        """Execute news scraping for TechCrunch.

        Returns:
            List[Dict[str, Any]]: List of article dictionaries.
        """
        logger.info(f"[TechCrunch Scraper] Starting scrape from {self.RSS_URL}")
        feed_xml: Optional[str] = self.fetch_feed_content(self.RSS_URL)
        if not feed_xml:
            logger.error(
                "[TechCrunch Scraper] Unable to fetch TechCrunch RSS feed xml."
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
                image_url: str = self.extract_image_url(entry, title)

                articles.append(
                    {
                        "title": title,
                        "source": self.SOURCE_NAME,
                        "published_date": pub_date,
                        "summary": summary_text[:500],
                        "image_url": image_url,
                        "article_url": article_url,
                        "country": "US",
                    }
                )
            except Exception as e:
                logger.error(
                    "[TechCrunch Scraper] Error parsing entry "
                    f"'{getattr(entry, 'title', 'Unknown')}': {e}"
                )
                continue

        logger.info(
            f"[TechCrunch Scraper] Successfully extracted {len(articles)} articles."
        )
        return articles
