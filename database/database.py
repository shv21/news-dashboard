"""Database initialization and management module.

Provides functions to bind SQLAlchemy to the Flask app, set up database files,
create schema tables, and execute fallback seed scraping.
"""

import logging
import os
from pathlib import Path
import shutil
from typing import Any

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from exceptions import DatabaseError

logger = logging.getLogger(__name__)

# Initialize SQLAlchemy instance
db: SQLAlchemy = SQLAlchemy()


def init_db(app: Flask) -> None:
    """Bind SQLAlchemy to the Flask application and initialize database.

    Ensures target directory exists, copies packaged seed database if target is
    missing/empty, creates database tables, and executes initial seed if empty.

    Args:
        app (Flask): The Flask application instance.

    Raises:
        DatabaseError: If database directory creation or initialization fails.
    """
    db.init_app(app)
    with app.app_context():
        try:
            db_uri: str = app.config.get("SQLALCHEMY_DATABASE_URI", "")
            if db_uri.startswith("sqlite:///") and not db_uri.startswith(
                "sqlite:///:memory:"
            ):
                db_path: str = db_uri.replace("sqlite:///", "")
                db_dir: str = os.path.dirname(os.path.abspath(db_path))
                if db_dir:
                    os.makedirs(db_dir, exist_ok=True)

                # Copy packaged seed database if present and target missing/0 bytes
                if not app.config.get("TESTING"):
                    if (
                        not os.path.exists(db_path)
                        or os.path.getsize(db_path) == 0
                    ):
                        root: Path = (
                            Path(app.root_path)
                            if hasattr(app, "root_path")
                            else Path.cwd()
                        )
                        seed_db: Path = root / "data" / "news.db"
                        target_db: Path = Path(db_path).resolve()
                        if (
                            seed_db.exists()
                            and seed_db.resolve().as_posix()
                            != target_db.as_posix()
                        ):
                            try:
                                shutil.copy2(seed_db, db_path)
                                logger.info(
                                    f"Copied seed database to {db_path}"
                                )
                            except Exception as copy_err:
                                logger.warning(
                                    f"Could not copy seed database: {copy_err}"
                                )
        except Exception as err:
            logger.warning(f"Database directory setup error: {err}")

        try:
            db.create_all()
        except Exception as create_err:
            logger.error(f"Failed to create database tables: {create_err}")
            raise DatabaseError(
                "Database table creation failed", details=str(create_err)
            ) from create_err

        # Fallback seed if DB remains empty and not in testing mode
        if not app.config.get("TESTING"):
            seed_fallback_articles(app)


def seed_fallback_articles(app: Flask) -> None:
    """Execute news scrapers to populate initial news articles if DB is empty.

    Args:
        app (Flask): The Flask application instance.
    """
    try:
        from database.models import News

        if News.query.count() == 0:
            logger.info(
                "Empty database detected. Running news scrapers for seed..."
            )
            from scraper.scraper_manager import ScraperManager

            manager: ScraperManager = ScraperManager()
            manager.run_all_scrapers()
    except Exception as e:
        logger.warning(f"Initial live article seed scraping failed: {e}")
