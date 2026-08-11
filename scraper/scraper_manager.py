import logging
import requests
from database.database import db
from database.models import News
from scraper.scraper_one import BBCNewsScraper
from scraper.scraper_five import IndiaNewsScraper
from services.google_sheets_service import GoogleSheetsService


logger = logging.getLogger(__name__)

class ScraperManager:
    """Orchestrates news scrapers, handles database persistence and duplicate prevention."""

    def __init__(self):
        # Register only the two requested scrapers: BBC News (UK) and Times of India (IN)
        self.scrapers = [
            BBCNewsScraper(),        # BBC News (UK)
            IndiaNewsScraper()       # Times of India (IN)
        ]
        self.sheets_service = GoogleSheetsService()


    def is_valid_url(self, url):
        """Verifies if the article URL does not return HTTP 404."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
            }
            res = requests.head(url, headers=headers, timeout=3, allow_redirects=True)
            if res.status_code == 404:
                return False
            return True
        except Exception:
            return True  # If timeout occurs, assume valid to avoid dropping network-throttled feeds

    def run_all_scrapers(self):
        """
        Executes all registered scrapers and saves non-duplicate articles to SQLite DB and Google Sheets.
        
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

                    # Validate URL is not returning 404
                    if not self.is_valid_url(art_data['article_url']):
                        logger.warning(f"[ScraperManager] Skipping article with 404 URL: {art_data['article_url']}")
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

                # Sync scraped articles to Google Sheets (non-blocking, failure will not affect website/DB)
                try:
                    if articles:
                        self.sheets_service.sync_articles(articles)
                except Exception as sheet_err:
                    logger.error(f"[ScraperManager] Google Sheets sync error for {source_name}: {sheet_err}")

            except Exception as e:
                db.session.rollback()
                logger.error(f"[ScraperManager] Error executing scraper for {source_name}: {e}", exc_info=True)
                stats['errors'] += 1

        logger.info(f"[ScraperManager] Scraping finished. Total Added: {stats['new_added']}, Total Skipped: {stats['duplicates_skipped']}")
        return stats

