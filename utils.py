"""Shared utility functions for the news-dashboard application.

Contains reusable helper utilities for HTML text cleaning, datetime parsing,
URL validation, article category classification, and seed image generation.
"""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import re
import time
from typing import Any, Dict, Optional, Tuple

from bs4 import BeautifulSoup
import requests

from config import Config

# Category classification regex rules: (URL Pattern, Keyword Pattern, Category Name)
CATEGORY_RULES: Tuple[Tuple[str, str, str], ...] = (
    (
        r"/(sport|sports)/",
        r"\b(sport|sports|football|cricket|match|league|olympics|player|"
        r"stadium|tournament|championship|tennis|golf|f1|premier league)\b",
        "Sports",
    ),
    (
        r"/(culture|entertainment|lifestyle)/",
        r"\b(culture|cultural|film|movie|music|art|arts|actor|actress|novel|"
        r"cinema|festival|theater|theatre|fashion|heritage|celebrity)\b",
        "Culture & Arts",
    ),
    (
        r"/(tech|technology|science)/",
        r"\b(tech|technology|ai|artificial intelligence|software|hardware|"
        r"robot|robotics|cyber|space|satellite|gadget)\b",
        "Technology",
    ),
    (
        r"/(business|economy|finance)/",
        r"\b(business|economy|economic|stock|stocks|market|markets|trade|"
        r"finance|financial|company|inflation|bank|banking|ceo)\b",
        "Business",
    ),
    (
        r"/(politics|news)/",
        r"\b(politics|political|minister|election|parliament|government|"
        r"president|pm|vote|court|law|diplomacy|military|war)\b",
        "Politics",
    ),
)


def clean_html_text(html_content: Optional[str]) -> str:
    """Extract clean plain text from an HTML snippet using BeautifulSoup.

    Args:
        html_content (Optional[str]): HTML markup or text string.

    Returns:
        str: Stripped plain text string, or default fallback if empty.
    """
    if not html_content or not html_content.strip():
        return "No summary available."

    soup: BeautifulSoup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text().strip()


def parse_datetime(parsed_entry: Any) -> datetime:
    """Extract and convert publication timestamp from an RSS feed entry into UTC.

    Checks `published_parsed`, `updated_parsed`, and RFC date strings in order.
    Returns current naive UTC datetime as a safe fallback.

    Args:
        parsed_entry (Any): RSS feed entry dictionary/object from feedparser.

    Returns:
        datetime: Parsed naive UTC datetime object.
    """
    # 1. Try structured time tuples (published_parsed or updated_parsed)
    for attr in ("published_parsed", "updated_parsed"):
        time_struct = getattr(parsed_entry, attr, None)
        if time_struct:
            try:
                return datetime.fromtimestamp(time.mktime(time_struct))
            except (ValueError, OverflowError, TypeError):
                continue

    # 2. Try raw string dates (e.g. published attribute)
    published_str = getattr(parsed_entry, "published", None)
    if published_str and isinstance(published_str, str):
        try:
            return parsedate_to_datetime(published_str)
        except Exception:
            pass

    # 3. Fallback to current UTC time
    return datetime.now(timezone.utc).replace(tzinfo=None)


def is_valid_url(url: str, timeout: Optional[int] = None) -> bool:
    """Verify whether an article URL is accessible via HTTP HEAD request.

    Args:
        url (str): Target URL string.
        timeout (Optional[int]): Request timeout in seconds. Defaults to Config timeout.

    Returns:
        bool: False if URL returns HTTP 404; True otherwise (assumed valid on timeout).
    """
    if not url or not url.strip():
        return False

    req_timeout: int = timeout or Config.SCRAPER_REQUEST_TIMEOUT
    headers: Dict[str, str] = {"User-Agent": Config.SCRAPER_USER_AGENT}

    try:
        response: requests.Response = requests.head(
            url, headers=headers, timeout=req_timeout, allow_redirects=True
        )
        return response.status_code != 404
    except Exception:
        # Preserve live feeds on network timeout or connection reset
        return True


def classify_category(title: str, summary: str, url: str) -> str:
    """Classify a news article into a category based on URL and text keywords.

    Args:
        title (str): Article headline text.
        summary (str): Article summary excerpt.
        url (str): Article canonical URL.

    Returns:
        str: Category string ('Sports', 'Culture & Arts', 'Technology',
            'Business', 'Politics', or 'General').
    """
    search_text: str = f"{title} {summary or ''} {url}".lower()

    for url_pattern, text_pattern, category_name in CATEGORY_RULES:
        if re.search(url_pattern, url) or re.search(text_pattern, search_text):
            return category_name

    return "General"


def generate_seed_image_url(
    seed_key: str, width: int = 600, height: int = 400
) -> str:
    """Generate a deterministic image URL based on MD5 hash of seed string.

    Args:
        seed_key (str): Unique seed key (e.g. article URL or headline).
        width (int): Image width in pixels. Defaults to 600.
        height (int): Image height in pixels. Defaults to 400.

    Returns:
        str: Deterministic Picsum image URL.
    """
    url_hash: str = hashlib.md5(seed_key.encode("utf-8")).hexdigest()
    return f"https://picsum.photos/seed/{url_hash}/{width}/{height}"

