import logging
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import time
import hashlib
from config import Config

logger = logging.getLogger(__name__)

class TechCrunchScraper:
    """Scraper implementation for TechCrunch with distinct image extraction."""

    SOURCE_NAME = "TechCrunch"
    RSS_URL = "https://techcrunch.com/feed/"

    # Fallback curated tech image set to ensure distinct visuals
    TECH_FALLBACK_IMAGES = [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=600&q=80"
    ]

    def __init__(self):
        self.headers = {
            'User-Agent': Config.SCRAPER_USER_AGENT,
            'Accept': 'application/rss+xml, application/xml, text/xml, */*'
        }

    def fetch_feed_content(self, url, max_retries=None, timeout=None):
        """Fetch content from URL with retry mechanism and custom headers."""
        max_retries = max_retries or Config.SCRAPER_MAX_RETRIES
        timeout = timeout or Config.SCRAPER_REQUEST_TIMEOUT

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, headers=self.headers, timeout=timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.warning(f"[TechCrunch Scraper] Attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    time.sleep(1 * attempt)
        logger.error(f"[TechCrunch Scraper] Failed to fetch after {max_retries} attempts.")
        return None

    def parse_published_date(self, parsed_entry):
        """Extract and parse publication date into a datetime object."""
        if hasattr(parsed_entry, 'published_parsed') and parsed_entry.published_parsed:
            try:
                return datetime.fromtimestamp(time.mktime(parsed_entry.published_parsed))
            except Exception as e:
                logger.debug(f"[TechCrunch Scraper] Date parsing error: {e}")

        if hasattr(parsed_entry, 'published') and parsed_entry.published:
            try:
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(parsed_entry.published)
            except Exception:
                pass

        return datetime.now(timezone.utc).replace(tzinfo=None)

    def extract_image_url(self, entry, title=""):
        """Extract high quality image URL from RSS media, enclosures, or content HTML."""
        # 1. Check media_content
        if hasattr(entry, 'media_content') and entry.media_content:
            for item in entry.media_content:
                if item.get('url'):
                    return item['url']

        # 2. Check media_thumbnail
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            for item in entry.media_thumbnail:
                if item.get('url'):
                    return item['url']

        # 3. Check enclosures
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enc in entry.enclosures:
                if enc.get('type', '').startswith('image'):
                    return enc.get('href') or enc.get('url')

        # 4. Search BeautifulSoup in entry.content or summary HTML
        html_snippets = []
        if hasattr(entry, 'content') and entry.content:
            for c in entry.content:
                html_snippets.append(c.get('value', ''))
        if hasattr(entry, 'summary'):
            html_snippets.append(entry.summary)
        if hasattr(entry, 'description'):
            html_snippets.append(entry.description)

        for snippet in html_snippets:
            if not snippet:
                continue
            soup = BeautifulSoup(snippet, 'html.parser')
            imgs = soup.find_all('img')
            for img in imgs:
                src = img.get('src') or img.get('data-src') or img.get('srcset')
                if src and 'gravatar' not in src and 'pixel' not in src and 'icon' not in src:
                    if ' ' in src: # handling srcset
                        src = src.split(' ')[0]
                    return src

        # 5. Deterministic 100% unique seed image based on article title and URL
        url_hash = hashlib.md5((entry.get('link', '') or title).encode('utf-8')).hexdigest()
        return f"https://picsum.photos/seed/{url_hash}/600/400"

    def scrape(self):
        """Execute news scraping for TechCrunch."""
        logger.info(f"[TechCrunch Scraper] Starting scrape from {self.RSS_URL}")
        feed_xml = self.fetch_feed_content(self.RSS_URL)
        if not feed_xml:
            logger.error("[TechCrunch Scraper] Unable to fetch TechCrunch RSS feed xml.")
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
                image_url = self.extract_image_url(entry, title)

                articles.append({
                    'title': title,
                    'source': self.SOURCE_NAME,
                    'published_date': pub_date,
                    'summary': summary_text[:500],
                    'image_url': image_url,
                    'article_url': article_url,
                    'country': 'US'
                })
            except Exception as e:
                logger.error(f"[TechCrunch Scraper] Error processing entry '{getattr(entry, 'title', 'Unknown')}': {e}")
                continue

        logger.info(f"[TechCrunch Scraper] Successfully extracted {len(articles)} articles.")
        return articles
