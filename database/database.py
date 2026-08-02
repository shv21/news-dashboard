import os
import shutil
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

def init_db(app):
    """Binds SQLAlchemy to the Flask app, ensures directory exists, and initializes tables/seed db."""
    db.init_app(app)
    with app.app_context():
        try:
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if db_uri.startswith('sqlite:///') and not db_uri.startswith('sqlite:///:memory:'):
                db_path = db_uri.replace('sqlite:///', '')
                db_dir = os.path.dirname(os.path.abspath(db_path))
                if db_dir:
                    os.makedirs(db_dir, exist_ok=True)
                
                # Copy packaged seed database if present and target is missing or 0 bytes
                if not app.config.get('TESTING'):
                    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
                        root = Path(app.root_path) if hasattr(app, 'root_path') else Path.cwd()
                        seed_db = root / 'data' / 'news.db'
                        if seed_db.exists() and seed_db.resolve().as_posix() != Path(db_path).resolve().as_posix():
                            try:
                                shutil.copy2(seed_db, db_path)
                            except Exception as e:
                                app.logger.warning(f"Could not copy seed database: {e}")
        except Exception as err:
            app.logger.warning(f"Database directory setup error: {err}")

        # Create tables
        db.create_all()

        # Fallback seed if DB remains empty and not in testing mode
        if not app.config.get('TESTING'):
            seed_fallback_articles(app)

def seed_fallback_articles(app):
    """Executes scrapers to populate initial live news articles if DB is empty."""
    try:
        from database.models import News
        if News.query.count() == 0:
            app.logger.info("Empty database detected. Running live news scrapers for initial seed...")
            from scraper.scraper_manager import ScraperManager
            manager = ScraperManager()
            manager.run_all_scrapers()
    except Exception as e:
        app.logger.warning(f"Initial live article scraping failed: {e}")
