import logging
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import time
import hashlib
from config import Config

logger = logging.getLogger(__name__)

class JapanNewsScraper:
    """Scraper implementation for Japan Today (Japan)."""

    SOURCE_NAME = "Japan Today"
    RSS_URL = "https://japantoday.com/feed"

    def __init__(self):
        self.headers = {
            'User-Agent': Config.SCRAPER_USER_AGENT,
            'Accept': 'application/rss+xml, application/xml, text/xml, */*'
        }

    def fetch_feed_content(self, url, max_retries=None, timeout=None):
        """Fetch feed XML with retry mechanism."""
        max_retries = max_retries or Config.SCRAPER_MAX_RETRIES
        timeout = timeout or Config.SCRAPER_REQUEST_TIMEOUT

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, headers=self.headers, timeout=timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.warning(f"[Japan Today Scraper] Attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    time.sleep(1 * attempt)
        return None

    def parse_published_date(self, parsed_entry):
        """Extract and parse publication date into a datetime object."""
        if hasattr(parsed_entry, 'published_parsed') and parsed_entry.published_parsed:
            try:
                return datetime.fromtimestamp(time.mktime(parsed_entry.published_parsed))
            except Exception:
                pass
        return datetime.now(timezone.utc).replace(tzinfo=None)

    def extract_image_url(self, entry, summary_html="", title=""):
        """Extract image URL from feed enclosures or HTML summary."""
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            return entry.media_thumbnail[0].get('url')
        if hasattr(entry, 'media_content') and entry.media_content:
            return entry.media_content[0].get('url')
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enc in entry.enclosures:
                if enc.get('type', '').startswith('image'):
                    return enc.get('href') or enc.get('url')

        if summary_html:
            soup = BeautifulSoup(summary_html, 'html.parser')
            img_tag = soup.find('img')
            if img_tag and img_tag.get('src'):
                return img_tag['src']

        url_hash = hashlib.md5((entry.get('link', '') or title).encode('utf-8')).hexdigest()
        return f"https://picsum.photos/seed/{url_hash}/600/400"

    def scrape(self):
        """Execute news scraping for Japan Today."""
        logger.info(f"[Japan Today Scraper] Starting scrape from {self.RSS_URL}")
        feed_xml = self.fetch_feed_content(self.RSS_URL)
        if not feed_xml:
            logger.error("[Japan Today Scraper] Unable to fetch Japan Today RSS feed xml.")
            return []

        parsed_feed = feedparser.parse(feed_xml)
        articles = []

        for entry in parsed_feed.entries:
            try:
                title = getattr(entry, 'title', '').strip()
                article_url = getattr(entry, 'link', '').strip()
                summary = getattr(entry, 'summary', '').strip()

                if not title or not article_url:
                    continue

                if summary:
                    summary_soup = BeautifulSoup(summary, 'html.parser')
                    summary_text = summary_soup.get_text().strip()
                else:
                    summary_text = "No summary available."

                pub_date = self.parse_published_date(entry)
                image_url = self.extract_image_url(entry, summary, title)

                articles.append({
                    'title': title,
                    'source': self.SOURCE_NAME,
                    'published_date': pub_date,
                    'summary': summary_text[:500],
                    'image_url': image_url,
                    'article_url': article_url,
                    'country': 'JP'
                })
            except Exception as e:
                logger.error(f"[Japan Today Scraper] Error parsing entry: {e}")
                continue

        logger.info(f"[Japan Today Scraper] Successfully extracted {len(articles)} articles.")
        return articles
