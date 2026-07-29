import os
from pathlib import Path

# Base directory of application
BASE_DIR = Path(__file__).resolve().parent

# Check if running in Vercel serverless environment
IS_VERCEL = os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL_ENV') is not None

if IS_VERCEL:
    DATA_DIR = Path('/tmp/data')
else:
    DATA_DIR = BASE_DIR / 'data'

try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    DATA_DIR = Path('/tmp')

class Config:
    """Central configuration class for Flask and Application modules."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'news-aggregator-secret-key-2026')
    
    # SQLite Database URI (Absolute posix path)
    DB_FILE = (DATA_DIR / "news.db").resolve().as_posix()
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', f'sqlite:///{DB_FILE}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Scraper settings
    SCRAPER_REQUEST_TIMEOUT = 10  # seconds
    SCRAPER_MAX_RETRIES = 3
    SCRAPER_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36 (NewsAggregator/1.0)"
    )
    
    # Pagination
    ITEMS_PER_PAGE = 9
