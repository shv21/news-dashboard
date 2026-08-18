"""Shared utility functions for the news-dashboard application.

Contains reusable helper utilities for HTML text cleaning, datetime parsing,
URL validation, article category classification, and seed image generation.
"""

from datetime import datetime, timezone
import hashlib
import re
import time
from typing import Any, Optional

from bs4 import BeautifulSoup
import requests

from config import Config


def clean_html_text(html_content: Optional[str]) -> str:
    """Extract plain text from an HTML snippet using BeautifulSoup.

    Args:
        html_content (Optional[str]): HTML string to strip tags from.

    Returns:
        str: Cleaned plain text, or default string if input is empty.
    """
    if not html_content or not html_content.strip():
        return "No summary available."

    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text().strip()


def parse_datetime(parsed_entry: Any) -> datetime:
    """Extract and parse publication date into a UTC datetime object.

    Args:
        parsed_entry (Any): RSS feed entry object from feedparser.

    Returns:
        datetime: Parsed publication datetime, or current UTC time on fallback.
    """
    if (
        hasattr(parsed_entry, "published_parsed")
        and parsed_entry.published_parsed
    ):
        try:
            return datetime.fromtimestamp(
                time.mktime(parsed_entry.published_parsed)
            )
        except (ValueError, OverflowError, TypeError):
            pass

    if hasattr(parsed_entry, "updated_parsed") and parsed_entry.updated_parsed:
        try:
            return datetime.fromtimestamp(
                time.mktime(parsed_entry.updated_parsed)
            )
        except (ValueError, OverflowError, TypeError):
            pass

    if hasattr(parsed_entry, "published") and parsed_entry.published:
        try:
            from email.utils import parsedate_to_datetime

            return parsedate_to_datetime(parsed_entry.published)
        except Exception:
            pass

    return datetime.now(timezone.utc).replace(tzinfo=None)


def is_valid_url(url: str, timeout: Optional[int] = None) -> bool:
    """Verify whether an article URL is reachable and does not return HTTP 404.

    Args:
        url (str): Target URL to validate via HTTP HEAD request.
        timeout (Optional[int]): Request timeout in seconds. Defaults to Config timeout.

    Returns:
        bool: True if URL is accessible or non-404; False if HTTP 404.
    """
    if not url or not url.strip():
        return False

    req_timeout: int = timeout or Config.SCRAPER_REQUEST_TIMEOUT
    headers: dict[str, str] = {"User-Agent": Config.SCRAPER_USER_AGENT}

    try:
        response = requests.head(
            url, headers=headers, timeout=req_timeout, allow_redirects=True
        )
        return response.status_code != 404
    except Exception:
        # Assume valid on network timeout to prevent dropping live feeds
        return True


def classify_category(title: str, summary: str, url: str) -> str:
    """Classify an article into a news category based on keywords and URL structure.

    Args:
        title (str): Article headline.
        summary (str): Article summary or excerpt text.
        url (str): Article canonical URL.

    Returns:
        str: Category name ('Sports', 'Culture & Arts', 'Technology', 'Business',
            'Politics', or 'General').
    """
    text: str = f"{title} {summary or ''} {url}".lower()

    if re.search(r"/(sport|sports)/", url) or re.search(
        r"\b(sport|sports|football|cricket|match|league|olympics|player|"
        r"stadium|tournament|championship|tennis|golf|f1|premier league)\b",
        text,
    ):
        return "Sports"

    if re.search(r"/(culture|entertainment|lifestyle)/", url) or re.search(
        r"\b(culture|cultural|film|movie|music|art|arts|actor|actress|novel|"
        r"cinema|festival|theater|theatre|fashion|heritage|celebrity)\b",
        text,
    ):
        return "Culture & Arts"

    if re.search(r"/(tech|technology|science)/", url) or re.search(
        r"\b(tech|technology|ai|artificial intelligence|software|hardware|"
        r"robot|robotics|cyber|space|satellite|gadget)\b",
        text,
    ):
        return "Technology"

    if re.search(r"/(business|economy|finance)/", url) or re.search(
        r"\b(business|economy|economic|stock|stocks|market|markets|trade|"
        r"finance|financial|company|inflation|bank|banking|ceo)\b",
        text,
    ):
        return "Business"

    if re.search(r"/(politics|news)/", url) or re.search(
        r"\b(politics|political|minister|election|parliament|government|"
        r"president|pm|vote|court|law|diplomacy|military|war)\b",
        text,
    ):
        return "Politics"

    return "General"


def generate_seed_image_url(
    seed_key: str, width: int = 600, height: int = 400
) -> str:
    """Generate a deterministic seed-based image URL for article image fallbacks.

    Args:
        seed_key (str): Unique string key (e.g. article URL or title).
        width (int): Target image width in pixels. Defaults to 600.
        height (int): Target image height in pixels. Defaults to 400.

    Returns:
        str: Seeded image URL.
    """
    url_hash: str = hashlib.md5(seed_key.encode("utf-8")).hexdigest()
    return f"https://picsum.photos/seed/{url_hash}/{width}/{height}"
