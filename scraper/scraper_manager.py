"""Scraper manager orchestration module.

Manages execution of registered news scrapers, handles article deduplication,
database persistence, and triggers Google Sheets synchronization.
"""

import logging
from typing import Any, Dict, List

from database.database import db
from database.models import News
from exceptions import DatabaseError, ScraperError
from scraper.scraper_five import IndiaNewsScraper
from scraper.scraper_one import BBCNewsScraper
from services.google_sheets_service import GoogleSheetsService
from utils import is_valid_url

logger = logging.getLogger(__name__)


class ScraperManager:
    """Orchestrates news scrapers, handles DB persistence and duplicate prevention."""

    def __init__(self) -> None:
        """Initialize ScraperManager with active scrapers and Google Sheets service."""
        self.scrapers: List[Any] = [
            BBCNewsScraper(),  # BBC News (UK)
            IndiaNewsScraper(),  # Times of India (IN)
        ]
        self.sheets_service: GoogleSheetsService = GoogleSheetsService()

    def validate_article_url(self, url: str) -> bool:
        """Verify whether an article URL is reachable via utility helper.

        Args:
            url (str): Article canonical URL.

        Returns:
            bool: True if reachable, False if HTTP 404.
        """
        return is_valid_url(url)

    def run_all_scrapers(self) -> Dict[str, Any]:
        """Execute all registered scrapers and persist new articles to DB and Sheets.

        Returns:
            Dict[str, Any]: Summary statistics of the scraping run.
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
            source_name: str = getattr(scraper, "SOURCE_NAME", "Unknown")
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
                    # Deduplication check by article_url
                    existing: News = News.query.filter_by(
                        article_url=art_data["article_url"]
                    ).first()
                    if existing:
                        if art_data.get("image_url") and (
                            "default" in existing.image_url
                            or "logo" in existing.image_url
                            or existing.image_url == art_data["image_url"]
                        ):
                            existing.image_url = art_data["image_url"]
                        duplicate_count += 1
                        continue

                    # Validate URL is not returning 404
                    if not self.validate_article_url(art_data["article_url"]):
                        logger.warning(
                            f"[ScraperManager] Skipping 404 URL: {art_data['article_url']}"
                        )
                        continue

                    new_news: News = News(
                        title=art_data["title"],
                        source=art_data["source"],
                        published_date=art_data["published_date"],
                        summary=art_data["summary"],
                        image_url=art_data["image_url"],
                        article_url=art_data["article_url"],
                        country=art_data.get("country", "US"),
                    )
                    db.session.add(new_news)
                    added_count += 1

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
                try:
                    if articles:
                        self.sheets_service.sync_articles(articles)
                except Exception as sheet_err:
                    logger.error(
                        f"[ScraperManager] Google Sheets sync error for {source_name}: {sheet_err}"
                    )

            except Exception as e:
                db.session.rollback()
                logger.error(
                    f"[ScraperManager] Error executing scraper for {source_name}: {e}",
                    exc_info=True,
                )
                stats["errors"] += 1

        logger.info(
            "[ScraperManager] Scraping finished. Total Added: "
            f"{stats['new_added']}, Total Skipped: {stats['duplicates_skipped']}"
        )
        return stats
