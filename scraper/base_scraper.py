"""Base scraper module for news feeds.

Provides a unified base class for fetching and parsing RSS feeds,
extracting image links, handling network retries, and formatting articles.
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


class BaseNewsScraper:
    """Base class for all RSS-based news scrapers."""

    SOURCE_NAME: str = "Base Source"
    RSS_URL: str = ""
    COUNTRY_CODE: str = "US"

    def __init__(self) -> None:
        """Initialize scraper with default HTTP request headers."""
        self.headers: Dict[str, str] = {
            "User-Agent": Config.SCRAPER_USER_AGENT,
            "Accept": (
                "application/rss+xml, application/atom+xml, "
                "application/xml, text/xml, */*"
            ),
        }

    def fetch_feed_content(
        self,
        url: str,
        max_retries: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> Optional[str]:
        """Fetch RSS feed XML text from URL with retry logic.

        Args:
            url (str): Target RSS feed URL.
            max_retries (Optional[int]): Max retry attempts. Defaults to Config value.
            timeout (Optional[int]): Request timeout in seconds. Defaults to Config value.

        Returns:
            Optional[str]: Feed XML text string if successful, None otherwise.
        """
        retries: int = max_retries or Config.SCRAPER_MAX_RETRIES
        req_timeout: int = timeout or Config.SCRAPER_REQUEST_TIMEOUT

        for attempt in range(1, retries + 1):
            try:
                response: requests.Response = requests.get(
                    url, headers=self.headers, timeout=req_timeout
                )
                response.raise_for_status()
                return response.text
            except requests.RequestException as exc:
                logger.warning(
                    f"[{self.SOURCE_NAME} Scraper] Fetch attempt {attempt}/{retries} failed: {exc}"
                )
                if attempt < retries:
                    time.sleep(1 * attempt)

        logger.error(
            f"[{self.SOURCE_NAME} Scraper] Failed to fetch feed after {retries} attempts: {url}"
        )
        return None

    def extract_image_url(
        self, entry: Any, summary_html: str = "", title: str = ""
    ) -> str:
        """Extract article image URL from media tags, enclosures, or HTML summary.

        Args:
            entry (Any): Parsed feed entry object from feedparser.
            summary_html (str): Raw summary HTML string.
            title (str): Article title fallback key.

        Returns:
            str: Resolved image URL or seed fallback image URL.
        """
        # 1. Media thumbnails or content
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            for item in entry.media_thumbnail:
                if isinstance(item, dict) and item.get("url"):
                    return item["url"]

        if hasattr(entry, "media_content") and entry.media_content:
            for item in entry.media_content:
                if isinstance(item, dict) and item.get("url"):
                    return item["url"]

        # 2. Feed enclosures
        if hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                if isinstance(enc, dict):
                    enc_type = enc.get("type", "")
                    if enc_type.startswith("image"):
                        return enc.get("href") or enc.get("url", "")

        # 3. HTML image tags in content/summary
        html_candidates: List[str] = [summary_html]
        if hasattr(entry, "content") and entry.content:
            for c in entry.content:
                if isinstance(c, dict) and c.get("value"):
                    html_candidates.append(c["value"])

        for html_text in html_candidates:
            if not html_text:
                continue
            soup = BeautifulSoup(html_text, "html.parser")
            img_tag = soup.find("img")
            if img_tag:
                src = (
                    img_tag.get("src")
                    or img_tag.get("data-src")
                    or img_tag.get("srcset")
                )
                if src:
                    if " " in src:
                        src = src.split(" ")[0]
                    if not any(
                        bad in src for bad in ("gravatar", "pixel", "icon")
                    ):
                        return src

        # 4. Fallback seed image
        seed_key: str = (
            getattr(entry, "link", "") or title or getattr(entry, "title", "")
        )
        return generate_seed_image_url(seed_key)

    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape articles from the configured RSS feed URL.

        Returns:
            List[Dict[str, Any]]: List of article dictionaries.
        """
        if not self.RSS_URL:
            logger.error(f"[{self.SOURCE_NAME} Scraper] Missing RSS feed URL.")
            return []

        logger.info(f"[{self.SOURCE_NAME} Scraper] Starting scrape from {self.RSS_URL}")
        feed_xml: Optional[str] = self.fetch_feed_content(self.RSS_URL)
        if not feed_xml:
            logger.error(f"[{self.SOURCE_NAME} Scraper] Unable to retrieve feed XML.")
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
                        "country": self.COUNTRY_CODE,
                    }
                )
            except Exception as exc:
                entry_title = getattr(entry, "title", "Unknown")
                logger.error(
                    f"[{self.SOURCE_NAME} Scraper] Error parsing entry '{entry_title}': {exc}"
                )
                continue

        logger.info(
            f"[{self.SOURCE_NAME} Scraper] Successfully extracted {len(articles)} articles."
        )
        return articles
