import logging
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import time
import hashlib
from config import Config

logger = logging.getLogger(__name__)

class VergeScraper:
    """Scraper implementation for The Verge tech news feed."""

    SOURCE_NAME = "The Verge"
    RSS_URL = "https://www.theverge.com/rss/index.xml"

    FALLBACK_IMAGES = [
        "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=600&q=80"
    ]

    def __init__(self):
        self.headers = {
            'User-Agent': Config.SCRAPER_USER_AGENT,
            'Accept': 'application/rss+xml, application/atom+xml, text/xml, */*'
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
                logger.warning(f"[The Verge Scraper] Attempt {attempt}/{max_retries} failed: {e}")
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
        if hasattr(parsed_entry, 'updated_parsed') and parsed_entry.updated_parsed:
            try:
                return datetime.fromtimestamp(time.mktime(parsed_entry.updated_parsed))
            except Exception:
                pass
        return datetime.now(timezone.utc).replace(tzinfo=None)

    def extract_image_url(self, entry, title=""):
        """Extract featured image URL."""
        if hasattr(entry, 'media_content') and entry.media_content:
            for item in entry.media_content:
                if item.get('url'):
                    return item['url']

        html_content = ""
        if hasattr(entry, 'content') and entry.content:
            html_content = entry.content[0].get('value', '')
        elif hasattr(entry, 'summary'):
            html_content = entry.summary

        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            img = soup.find('img')
            if img and (img.get('src') or img.get('srcset')):
                src = img.get('src') or img.get('srcset')
                if ' ' in src:
                    src = src.split(' ')[0]
                return src

        url_hash = hashlib.md5((entry.get('link', '') or title).encode('utf-8')).hexdigest()
        return f"https://picsum.photos/seed/{url_hash}/600/400"

    def scrape(self):
        """Scrape articles from The Verge."""
        logger.info(f"[The Verge Scraper] Starting scrape from {self.RSS_URL}")
        feed_xml = self.fetch_feed_content(self.RSS_URL)
        if not feed_xml:
            logger.error("[The Verge Scraper] Unable to fetch feed.")
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
                logger.error(f"[The Verge Scraper] Error parsing entry: {e}")
                continue

        logger.info(f"[The Verge Scraper] Successfully extracted {len(articles)} articles.")
        return articles
