"""Database initialization and management module.

Provides functions to bind SQLAlchemy to the Flask app, set up database files,
create schema tables, and execute fallback seed scraping.
"""

import logging
import os
from pathlib import Path
import shutil
from typing import Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from exceptions import DatabaseError

logger = logging.getLogger(__name__)

# Global SQLAlchemy database instance
db: SQLAlchemy = SQLAlchemy()


def _ensure_sqlite_directory(db_uri: str) -> Optional[str]:
    """Ensure directory exists for SQLite database file path.

    Args:
        db_uri (str): SQLAlchemy database connection string.

    Returns:
        Optional[str]: Resolved file path string if file-based SQLite; None otherwise.
    """
    if db_uri.startswith("sqlite:///") and not db_uri.startswith(
        "sqlite:///:memory:"
    ):
        db_path: str = db_uri.replace("sqlite:///", "")
        db_dir: str = os.path.dirname(os.path.abspath(db_path))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        return db_path
    return None


def _copy_packaged_seed_db(app: Flask, db_path: str) -> None:
    """Copy packaged seed database to target db_path if target is missing or 0 bytes.

    Args:
        app (Flask): Flask application instance.
        db_path (str): Target SQLite database file path.
    """
    if app.config.get("TESTING"):
        return

    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        root: Path = (
            Path(app.root_path) if hasattr(app, "root_path") else Path.cwd()
        )
        seed_db: Path = root / "data" / "news.db"
        target_db: Path = Path(db_path).resolve()

        if seed_db.exists() and seed_db.resolve().as_posix() != target_db.as_posix():
            try:
                shutil.copy2(seed_db, db_path)
                logger.info(f"Copied packaged seed database to {db_path}")
            except Exception as copy_err:
                logger.warning(f"Could not copy seed database: {copy_err}")


def init_db(app: Flask) -> None:
    """Bind SQLAlchemy to the Flask application and initialize database.

    Ensures target directory exists, copies packaged seed database if target is
    missing/empty, creates database tables, and executes initial seed if empty.

    Args:
        app (Flask): The Flask application instance.

    Raises:
        DatabaseError: If database table creation fails.
    """
    db.init_app(app)

    with app.app_context():
        try:
            db_uri: str = app.config.get("SQLALCHEMY_DATABASE_URI", "")
            db_path: Optional[str] = _ensure_sqlite_directory(db_uri)
            if db_path:
                _copy_packaged_seed_db(app, db_path)
        except Exception as err:
            logger.warning(f"Database setup warning: {err}")

        try:
            db.create_all()
        except Exception as create_err:
            logger.error(f"Failed to create database tables: {create_err}")
            raise DatabaseError(
                "Database table creation failed", details=str(create_err)
            ) from create_err

        # Execute fallback live article scraping if database remains empty
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
    except Exception as exc:
        logger.warning(f"Initial live article seed scraping failed: {exc}")

