import logging
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import time
import hashlib
from config import Config

logger = logging.getLogger(__name__)

class IndiaNewsScraper:
    """Scraper implementation for Indian & South Asian news (Times of India / NDTV)."""

    SOURCE_NAME = "Times of India"
    RSS_URL = "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"

    FALLBACK_IMAGES = [
        "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1532375810709-75b1da00537c?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1506461883276-594a12b11cf3?auto=format&fit=crop&w=600&q=80"
    ]

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
                logger.warning(f"[India Scraper] Attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    time.sleep(1 * attempt)
        return None

    def parse_published_date(self, parsed_entry):
        """Parse publication date."""
        if hasattr(parsed_entry, 'published_parsed') and parsed_entry.published_parsed:
            try:
                return datetime.fromtimestamp(time.mktime(parsed_entry.published_parsed))
            except Exception:
                pass
        return datetime.now(timezone.utc).replace(tzinfo=None)

    def extract_image_url(self, entry, title=""):
        """Extract image URL or return unique seed fallback."""
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            for item in entry.media_thumbnail:
                if item.get('url'):
                    return item['url']
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enc in entry.enclosures:
                if enc.get('type', '').startswith('image/') and enc.get('href'):
                    return enc['href']

        if hasattr(entry, 'summary'):
            soup = BeautifulSoup(entry.summary, 'html.parser')
            img = soup.find('img')
            if img and img.get('src'):
                return img['src']

        url_hash = hashlib.md5((entry.get('link', '') or title).encode('utf-8')).hexdigest()
        return f"https://picsum.photos/seed/{url_hash}/600/400"

    def scrape(self):
        """Scrape articles from Times of India."""
        logger.info(f"[India Scraper] Starting scrape from {self.RSS_URL}")
        feed_xml = self.fetch_feed_content(self.RSS_URL)
        if not feed_xml:
            logger.error("[India Scraper] Unable to fetch Times of India feed.")
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
                    'country': 'IN'
                })
            except Exception as e:
                logger.error(f"[India Scraper] Error parsing entry: {e}")
                continue

        logger.info(f"[India Scraper] Successfully extracted {len(articles)} articles.")
        return articles
