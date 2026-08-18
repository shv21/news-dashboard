"""Application configuration module for Flask and scrapers.

Loads environment variables from `.env` and defines configuration settings
including database URIs, scraper settings, Google Sheets integration details,
and stock market data configurations.
"""

import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Base directory of application
BASE_DIR: Path = Path(__file__).resolve().parent

# Check if running in Vercel serverless environment
IS_VERCEL: bool = (
    os.environ.get("VERCEL") == "1"
    or os.environ.get("VERCEL_ENV") is not None
)

if IS_VERCEL:
    DATA_DIR: Path = Path("/tmp")
else:
    DATA_DIR = BASE_DIR / "data"

try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    DATA_DIR = Path("/tmp")


class Config:
    """Central configuration class for Flask application and system components."""

    SECRET_KEY: str = os.environ.get(
        "SECRET_KEY", "news-aggregator-secret-key-2026"
    )

    # SQLite Database URI
    DB_FILE: str = (DATA_DIR / "news.db").resolve().as_posix()
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL", f"sqlite:///{DB_FILE}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Scraper general settings
    SCRAPER_REQUEST_TIMEOUT: int = int(
        os.environ.get("SCRAPER_REQUEST_TIMEOUT", "10")
    )
    SCRAPER_MAX_RETRIES: int = int(os.environ.get("SCRAPER_MAX_RETRIES", "3"))
    SCRAPER_USER_AGENT: str = os.environ.get(
        "SCRAPER_USER_AGENT",
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36 (NewsAggregator/1.0)"
        ),
    )

    # Scraper RSS Feed URLs
    RSS_URL_BBC: str = os.environ.get(
        "RSS_URL_BBC", "https://feeds.bbci.co.uk/news/rss.xml"
    )
    RSS_URL_TECHCRUNCH: str = os.environ.get(
        "RSS_URL_TECHCRUNCH", "https://techcrunch.com/feed/"
    )
    RSS_URL_VERGE: str = os.environ.get(
        "RSS_URL_VERGE", "https://www.theverge.com/rss/index.xml"
    )
    RSS_URL_WIRED: str = os.environ.get(
        "RSS_URL_WIRED", "https://www.wired.com/feed/rss"
    )
    RSS_URL_TIMES_OF_INDIA: str = os.environ.get(
        "RSS_URL_TIMES_OF_INDIA",
        "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    )
    RSS_URL_CBC: str = os.environ.get(
        "RSS_URL_CBC", "https://globalnews.ca/feed/"
    )
    RSS_URL_ABC_AUSTRALIA: str = os.environ.get(
        "RSS_URL_ABC_AUSTRALIA", "https://www.abc.net.au/news/feed/51120/rss.xml"
    )
    RSS_URL_DW_GERMANY: str = os.environ.get(
        "RSS_URL_DW_GERMANY", "https://rss.dw.com/xml/rss-en-all"
    )
    RSS_URL_JAPAN_TODAY: str = os.environ.get(
        "RSS_URL_JAPAN_TODAY", "https://japantoday.com/feed"
    )

    # Pagination
    ITEMS_PER_PAGE: int = int(os.environ.get("ITEMS_PER_PAGE", "9"))

    # Google Sheets Integration
    GOOGLE_CREDENTIALS_FILE: str = os.environ.get(
        "GOOGLE_CREDENTIALS_FILE", "credentials.json"
    )
    GOOGLE_SHEET_ID: str = os.environ.get("GOOGLE_SHEET_ID", "").strip()
    GOOGLE_SHEET_NAME: str = os.environ.get(
        "GOOGLE_SHEET_NAME", "My News Data"
    )
    GOOGLE_WORKSHEET_NAME: str = os.environ.get(
        "GOOGLE_WORKSHEET_NAME", "News"
    )

    # Banking Financial Institutions Data Config
    FINANCIALS_BY_COUNTRY: Dict[str, List[Dict[str, Any]]] = {
        "IN": [
            {
                "symbol": "SBIN",
                "name": "State Bank of India",
                "price": 10.15,
                "change_pct": 2.35,
                "market_cap": "₹7.10T ($85.4B)",
                "total_assets": "₹61.2T",
                "net_income": "₹61,077 Cr",
                "cet1_ratio": "13.8%",
                "status": "Strong Buy",
                "logo_icon": "bi-bank",
            },
            {
                "symbol": "HDB",
                "name": "HDFC Bank Ltd.",
                "price": 62.40,
                "change_pct": 1.12,
                "market_cap": "$155.2B",
                "total_assets": "₹36.1T",
                "net_income": "₹60,810 Cr",
                "cet1_ratio": "16.8%",
                "status": "Bullish",
                "logo_icon": "bi-currency-dollar",
            },
            {
                "symbol": "IBN",
                "name": "ICICI Bank Ltd.",
                "price": 28.10,
                "change_pct": 1.85,
                "market_cap": "$98.6B",
                "total_assets": "₹23.6T",
                "net_income": "₹40,888 Cr",
                "cet1_ratio": "14.6%",
                "status": "Bullish",
                "logo_icon": "bi-graph-up-arrow",
            },
            {
                "symbol": "AXISBANK",
                "name": "Axis Bank Ltd.",
                "price": 14.20,
                "change_pct": 0.45,
                "market_cap": "$42.1B",
                "total_assets": "₹14.7T",
                "net_income": "₹24,861 Cr",
                "cet1_ratio": "14.1%",
                "status": "Stable",
                "logo_icon": "bi-building-gear",
            },
            {
                "symbol": "KOTAKBANK",
                "name": "Kotak Mahindra Bank",
                "price": 21.50,
                "change_pct": -0.25,
                "market_cap": "$43.8B",
                "total_assets": "₹6.8T",
                "net_income": "₹13,782 Cr",
                "cet1_ratio": "20.8%",
                "status": "Neutral",
                "logo_icon": "bi-shield-check",
            },
            {
                "symbol": "PNB",
                "name": "Punjab National Bank",
                "price": 1.35,
                "change_pct": 3.10,
                "market_cap": "$14.2B",
                "total_assets": "₹15.6T",
                "net_income": "₹8,245 Cr",
                "cet1_ratio": "11.2%",
                "status": "Stable",
                "logo_icon": "bi-pie-chart-fill",
            },
        ],
        "US": [
            {
                "symbol": "JPM",
                "name": "JPMorgan Chase & Co.",
                "price": 204.85,
                "change_pct": 1.45,
                "market_cap": "$582.4B",
                "total_assets": "$3.87T",
                "net_income": "$49.6B",
                "cet1_ratio": "15.0%",
                "status": "Bullish",
                "logo_icon": "bi-bank",
            },
            {
                "symbol": "BAC",
                "name": "Bank of America Corp.",
                "price": 39.42,
                "change_pct": 0.82,
                "market_cap": "$308.1B",
                "total_assets": "$3.25T",
                "net_income": "$26.5B",
                "cet1_ratio": "11.8%",
                "status": "Stable",
                "logo_icon": "bi-currency-dollar",
            },
            {
                "symbol": "WFC",
                "name": "Wells Fargo & Company",
                "price": 57.65,
                "change_pct": 2.10,
                "market_cap": "$199.5B",
                "total_assets": "$1.93T",
                "net_income": "$19.1B",
                "cet1_ratio": "11.4%",
                "status": "Bullish",
                "logo_icon": "bi-graph-up-arrow",
            },
            {
                "symbol": "C",
                "name": "Citigroup Inc.",
                "price": 64.20,
                "change_pct": 1.15,
                "market_cap": "$122.7B",
                "total_assets": "$2.41T",
                "net_income": "$13.2B",
                "cet1_ratio": "13.5%",
                "status": "Stable",
                "logo_icon": "bi-building-gear",
            },
            {
                "symbol": "GS",
                "name": "The Goldman Sachs Group",
                "price": 482.30,
                "change_pct": 1.95,
                "market_cap": "$158.3B",
                "total_assets": "$1.64T",
                "net_income": "$11.8B",
                "cet1_ratio": "14.9%",
                "status": "Strong Buy",
                "logo_icon": "bi-pie-chart-fill",
            },
            {
                "symbol": "MS",
                "name": "Morgan Stanley",
                "price": 98.50,
                "change_pct": 0.90,
                "market_cap": "$160.2B",
                "total_assets": "$1.19T",
                "net_income": "$9.1B",
                "cet1_ratio": "15.2%",
                "status": "Bullish",
                "logo_icon": "bi-shield-check",
            },
        ],
        "UK": [
            {
                "symbol": "HSBC",
                "name": "HSBC Holdings plc",
                "price": 43.10,
                "change_pct": -0.35,
                "market_cap": "$162.8B",
                "total_assets": "$3.04T",
                "net_income": "$24.1B",
                "cet1_ratio": "14.8%",
                "status": "Neutral",
                "logo_icon": "bi-globe",
            },
            {
                "symbol": "BARC",
                "name": "Barclays PLC",
                "price": 11.45,
                "change_pct": 1.65,
                "market_cap": "$41.2B",
                "total_assets": "£1.52T",
                "net_income": "£5.3B",
                "cet1_ratio": "13.8%",
                "status": "Bullish",
                "logo_icon": "bi-bank",
            },
            {
                "symbol": "LLOY",
                "name": "Lloyds Banking Group",
                "price": 2.85,
                "change_pct": 0.70,
                "market_cap": "$38.6B",
                "total_assets": "£885B",
                "net_income": "£4.9B",
                "cet1_ratio": "13.7%",
                "status": "Stable",
                "logo_icon": "bi-currency-pound",
            },
            {
                "symbol": "NWG",
                "name": "NatWest Group plc",
                "price": 8.60,
                "change_pct": 2.25,
                "market_cap": "$29.4B",
                "total_assets": "£702B",
                "net_income": "£3.6B",
                "cet1_ratio": "13.4%",
                "status": "Strong Buy",
                "logo_icon": "bi-graph-up-arrow",
            },
            {
                "symbol": "STAN",
                "name": "Standard Chartered plc",
                "price": 9.75,
                "change_pct": 1.05,
                "market_cap": "$25.1B",
                "total_assets": "$820B",
                "net_income": "$3.0B",
                "cet1_ratio": "14.1%",
                "status": "Bullish",
                "logo_icon": "bi-building-gear",
            },
        ],
        "CA": [
            {
                "symbol": "RY",
                "name": "Royal Bank of Canada",
                "price": 112.50,
                "change_pct": 0.95,
                "market_cap": "$158.4B",
                "total_assets": "CA$2.01T",
                "net_income": "CA$15.0B",
                "cet1_ratio": "12.8%",
                "status": "Bullish",
                "logo_icon": "bi-bank",
            },
            {
                "symbol": "TD",
                "name": "Toronto-Dominion Bank",
                "price": 61.20,
                "change_pct": -0.45,
                "market_cap": "$107.8B",
                "total_assets": "CA$1.96T",
                "net_income": "CA$10.7B",
                "cet1_ratio": "12.5%",
                "status": "Stable",
                "logo_icon": "bi-building",
            },
            {
                "symbol": "BNS",
                "name": "Bank of Nova Scotia",
                "price": 49.80,
                "change_pct": 1.10,
                "market_cap": "$61.2B",
                "total_assets": "CA$1.40T",
                "net_income": "CA$7.5B",
                "cet1_ratio": "12.2%",
                "status": "Neutral",
                "logo_icon": "bi-shield-check",
            },
            {
                "symbol": "BMO",
                "name": "Bank of Montreal",
                "price": 88.30,
                "change_pct": 0.65,
                "market_cap": "$64.5B",
                "total_assets": "CA$1.29T",
                "net_income": "CA$4.4B",
                "cet1_ratio": "13.1%",
                "status": "Bullish",
                "logo_icon": "bi-currency-dollar",
            },
        ],
        "AU": [
            {
                "symbol": "CBA",
                "name": "Commonwealth Bank of Australia",
                "price": 88.40,
                "change_pct": 1.75,
                "market_cap": "A$148.2B",
                "total_assets": "A$1.25T",
                "net_income": "A$10.2B",
                "cet1_ratio": "12.3%",
                "status": "Strong Buy",
                "logo_icon": "bi-bank",
            },
            {
                "symbol": "NAB",
                "name": "National Australia Bank",
                "price": 23.10,
                "change_pct": 0.85,
                "market_cap": "A$72.4B",
                "total_assets": "A$1.01T",
                "net_income": "A$7.4B",
                "cet1_ratio": "12.2%",
                "status": "Bullish",
                "logo_icon": "bi-building-gear",
            },
            {
                "symbol": "ANZ",
                "name": "ANZ Group Holdings",
                "price": 18.90,
                "change_pct": 0.50,
                "market_cap": "A$56.8B",
                "total_assets": "A$1.06T",
                "net_income": "A$7.1B",
                "cet1_ratio": "13.3%",
                "status": "Stable",
                "logo_icon": "bi-graph-up-arrow",
            },
        ],
        "DE": [
            {
                "symbol": "DB",
                "name": "Deutsche Bank AG",
                "price": 16.80,
                "change_pct": 2.40,
                "market_cap": "€32.5B",
                "total_assets": "€1.31T",
                "net_income": "€4.9B",
                "cet1_ratio": "13.7%",
                "status": "Bullish",
                "logo_icon": "bi-bank",
            },
            {
                "symbol": "CBK",
                "name": "Commerzbank AG",
                "price": 14.25,
                "change_pct": 1.15,
                "market_cap": "€17.2B",
                "total_assets": "€510B",
                "net_income": "€2.2B",
                "cet1_ratio": "14.7%",
                "status": "Strong Buy",
                "logo_icon": "bi-building",
            },
        ],
        "JP": [
            {
                "symbol": "MUFG",
                "name": "Mitsubishi UFJ Financial",
                "price": 10.80,
                "change_pct": 1.95,
                "market_cap": "¥19.2T ($128B)",
                "total_assets": "¥385T",
                "net_income": "¥1.49T",
                "cet1_ratio": "10.9%",
                "status": "Bullish",
                "logo_icon": "bi-bank",
            },
            {
                "symbol": "SMFG",
                "name": "Sumitomo Mitsui Financial",
                "price": 62.50,
                "change_pct": 1.30,
                "market_cap": "¥12.4T ($82B)",
                "total_assets": "¥270T",
                "net_income": "¥960B",
                "cet1_ratio": "10.5%",
                "status": "Strong Buy",
                "logo_icon": "bi-graph-up-arrow",
            },
        ],
    }

    COUNTRY_NAMES: Dict[str, str] = {
        "IN": "India 🇮🇳",
        "US": "United States 🇺🇸",
        "UK": "United Kingdom 🇬🇧",
        "CA": "Canada 🇨🇦",
        "AU": "Australia 🇦🇺",
        "DE": "Germany 🇩🇪",
        "JP": "Japan 🇯🇵",
        "ALL": "Global 🌍",
    }
