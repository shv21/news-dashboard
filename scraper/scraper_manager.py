"""Scraper manager orchestration module.

Manages execution of registered news scrapers, handles article deduplication,
database persistence, and triggers Google Sheets synchronization.
"""

import logging
from typing import Any, Dict, List, Optional

from database.database import db
from database.models import News
from scraper.base_scraper import BaseNewsScraper
from scraper.scraper_five import IndiaNewsScraper
from scraper.scraper_one import BBCNewsScraper
from services.google_sheets_service import GoogleSheetsService
from utils import is_valid_url

logger = logging.getLogger(__name__)


class ScraperManager:
    """Orchestrates news scrapers, handles DB persistence and duplicate prevention."""

    def __init__(self) -> None:
        """Initialize ScraperManager with registered scrapers and Google Sheets service."""
        self.scrapers: List[BaseNewsScraper] = [
            BBCNewsScraper(),
            IndiaNewsScraper(),
        ]
        self.sheets_service: GoogleSheetsService = GoogleSheetsService()

    def validate_article_url(self, url: str) -> bool:
        """Verify whether an article URL is reachable via utility helper.

        Args:
            url (str): Article canonical URL string.

        Returns:
            bool: True if reachable, False if HTTP 404.
        """
        return is_valid_url(url)

    def _save_or_update_article(self, art_data: Dict[str, Any]) -> bool:
        """Insert a new article or update existing article image URL if needed.

        Args:
            art_data (Dict[str, Any]): Article attributes dictionary.

        Returns:
            bool: True if a new article was added to DB session; False if skipped/duplicate.
        """
        article_url: str = art_data.get("article_url", "").strip()
        if not article_url:
            return False

        existing: Optional[News] = News.query.filter_by(
            article_url=article_url
        ).first()

        if existing:
            # Update image URL if current image is a generic placeholder
            new_img: str = art_data.get("image_url", "")
            if new_img and existing.image_url and any(
                ph in existing.image_url for ph in ("default", "logo")
            ):
                existing.image_url = new_img
            return False

        # Check reachability before persisting new article
        if not self.validate_article_url(article_url):
            logger.warning(
                f"[ScraperManager] Skipping unreachable 404 URL: {article_url}"
            )
            return False

        new_news = News(
            title=art_data["title"],
            source=art_data["source"],
            published_date=art_data.get("published_date"),
            summary=art_data.get("summary"),
            image_url=art_data.get("image_url"),
            article_url=article_url,
            country=art_data.get("country", "US"),
        )
        db.session.add(new_news)
        return True

    def run_all_scrapers(self) -> Dict[str, Any]:
        """Execute all registered scrapers and persist new articles to DB and Sheets.

        Returns:
            Dict[str, Any]: Summary statistics dictionary of the scraping run.
        """
        stats: Dict[str, Any] = {
            "total_extracted": 0,
            "new_added": 0,
            "duplicates_skipped": 0,
            "errors": 0,
            "sources": {},
        }

        logger.info("[ScraperManager] Initiating news scraping cycle...")

        for scraper in self.scrapers:
            source_name: str = scraper.SOURCE_NAME
            stats["sources"][source_name] = {
                "extracted": 0,
                "added": 0,
                "duplicates": 0,
            }

            try:
                articles: List[Dict[str, Any]] = scraper.scrape()
                stats["sources"][source_name]["extracted"] = len(articles)
                stats["total_extracted"] += len(articles)

                added_count: int = 0
                duplicate_count: int = 0

                for art_data in articles:
                    if self._save_or_update_article(art_data):
                        added_count += 1
                    else:
                        duplicate_count += 1

                db.session.commit()

                stats["sources"][source_name]["added"] = added_count
                stats["sources"][source_name]["duplicates"] = duplicate_count
                stats["new_added"] += added_count
                stats["duplicates_skipped"] += duplicate_count

                logger.info(
                    f"[ScraperManager] {source_name}: Added {added_count} new "
                    f"articles ({duplicate_count} duplicates skipped)."
                )

                # Sync scraped articles to Google Sheets
                if articles:
                    try:
                        self.sheets_service.sync_articles(articles)
                    except Exception as sheet_err:
                        logger.error(
                            f"[ScraperManager] Google Sheets sync error for {source_name}: {sheet_err}"
                        )

            except Exception as exc:
                db.session.rollback()
                logger.error(
                    f"[ScraperManager] Scraper error for {source_name}: {exc}",
                    exc_info=True,
                )
                stats["errors"] += 1

        logger.info(
            "[ScraperManager] Scraping cycle finished. "
            f"Total Added: {stats['new_added']}, Skipped: {stats['duplicates_skipped']}"
        )
        return stats

