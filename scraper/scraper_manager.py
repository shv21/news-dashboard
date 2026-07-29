import logging
from database.database import db
from database.models import News
from scraper.scraper_one import BBCNewsScraper
from scraper.scraper_two import TechCrunchScraper
from scraper.scraper_three import VergeScraper
from scraper.scraper_four import WiredScraper
from scraper.scraper_five import IndiaNewsScraper

logger = logging.getLogger(__name__)

class ScraperManager:
    """Orchestrates news scrapers, handles database persistence and duplicate prevention."""

    def __init__(self):
        # Register all active scrapers here
        self.scrapers = [
            BBCNewsScraper(),
            TechCrunchScraper(),
            VergeScraper(),
            WiredScraper(),
            IndiaNewsScraper()
        ]

    def run_all_scrapers(self):
        """
        Executes all registered scrapers and saves non-duplicate articles to SQLite DB.
        
        Returns:
            dict: Summary statistics of the scraping run.
        """
        stats = {
            'total_extracted': 0,
            'new_added': 0,
            'duplicates_skipped': 0,
            'errors': 0,
            'sources': {}
        }

        logger.info("[ScraperManager] Initiating news scraping cycle across all sources...")

        for scraper in self.scrapers:
            source_name = scraper.SOURCE_NAME
            stats['sources'][source_name] = {'extracted': 0, 'added': 0, 'duplicates': 0}

            try:
                articles = scraper.scrape()
                stats['sources'][source_name]['extracted'] = len(articles)
                stats['total_extracted'] += len(articles)

                added_count = 0
                duplicate_count = 0

                for art_data in articles:
                    # Deduplication check by article_url
                    existing = News.query.filter_by(article_url=art_data['article_url']).first()
                    if existing:
                        # Update image_url if existing had fallback or default
                        if art_data.get('image_url') and ('default' in existing.image_url or 'logo' in existing.image_url or existing.image_url == art_data['image_url']):
                            existing.image_url = art_data['image_url']
                        duplicate_count += 1
                        continue

                    new_news = News(
                        title=art_data['title'],
                        source=art_data['source'],
                        published_date=art_data['published_date'],
                        summary=art_data['summary'],
                        image_url=art_data['image_url'],
                        article_url=art_data['article_url'],
                        country=art_data.get('country', 'US')
                    )
                    db.session.add(new_news)
                    added_count += 1

                db.session.commit()

                stats['sources'][source_name]['added'] = added_count
                stats['sources'][source_name]['duplicates'] = duplicate_count
                stats['new_added'] += added_count
                stats['duplicates_skipped'] += duplicate_count

                logger.info(f"[ScraperManager] {source_name}: Added {added_count} new articles ({duplicate_count} duplicates skipped).")

            except Exception as e:
                db.session.rollback()
                logger.error(f"[ScraperManager] Error executing scraper for {source_name}: {e}", exc_info=True)
                stats['errors'] += 1

        logger.info(f"[ScraperManager] Scraping finished. Total Added: {stats['new_added']}, Total Skipped: {stats['duplicates_skipped']}")
        return stats
