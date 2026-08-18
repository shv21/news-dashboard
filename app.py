"""Main application entrypoint module for Flask News Aggregator.

Initializes Flask application, binds extensions, configures CORS, registers
blueprints, and spawns the background news scraper thread.
"""

import logging
import os
import threading
import time
from typing import Any, Dict, Optional

from flask import Flask, jsonify, render_template

from config import Config
from database.database import init_db
from routes.api import api_bp
from routes.views import views_bp
from scraper.scraper_manager import ScraperManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def start_background_scraper(
    app: Flask, interval_seconds: int = 3600
) -> threading.Thread:
    """Spawn a background daemon thread to scrape news periodically.

    Args:
        app (Flask): Flask application instance.
        interval_seconds (int): Sleep duration between scrape cycles in seconds.

    Returns:
        threading.Thread: Started background scraper thread object.
    """

    def run_loop() -> None:
        time.sleep(3)  # Wait 3 seconds after startup for app context initialization
        while True:
            try:
                with app.app_context():
                    logger.info("[BackgroundScraper] Executing news update cycle...")
                    manager: ScraperManager = ScraperManager()
                    stats: Dict[str, Any] = manager.run_all_scrapers()
                    logger.info(
                        "[BackgroundScraper] Cycle complete: "
                        f"{stats['new_added']} new articles added to DB & Sheets."
                    )
            except Exception as e:
                logger.error(
                    f"[BackgroundScraper] Unexpected error during update: {e}"
                )

            time.sleep(interval_seconds)

    thread: threading.Thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    return thread


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """Application factory for Flask News Aggregator dashboard.

    Args:
        test_config (Optional[Dict[str, Any]]): Optional testing configuration.

    Returns:
        Flask: Configured Flask application instance.
    """
    app: Flask = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    # Initialize Database
    init_db(app)

    # Register Blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)

    # Enable CORS headers for API access
    @app.after_request
    def add_cors_headers(response: Any) -> Any:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization"
        )
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

    # Custom Error Handlers
    @app.errorhandler(404)
    def page_not_found(e: Any) -> Any:
        if app.debug:
            logger.warning(f"404 Error: {e}")
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e: Any) -> Any:
        logger.error(f"500 Internal Error: {e}")
        return (
            jsonify({"success": False, "error": "Internal server error"}),
            500,
        )

    # Start automatic background scraper if not in TESTING or VERCEL mode
    is_vercel: bool = (
        os.environ.get("VERCEL") == "1"
        or os.environ.get("VERCEL_ENV") is not None
    )
    if not app.config.get("TESTING") and not is_vercel:
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
            logger.info("Initializing automatic background news scraper...")
            start_background_scraper(app, interval_seconds=3600)

    return app


app: Flask = create_app()

if __name__ == "__main__":
    logger.info("Starting News Aggregator web application at http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
