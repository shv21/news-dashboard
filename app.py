import logging
from flask import Flask, render_template, jsonify
from config import Config
from database.database import init_db, db
from database.models import News
from routes.api import api_bp
from routes.views import views_bp
from scraper.scraper_manager import ScraperManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(test_config=None):
    """Application factory for Flask News Aggregator."""
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    # Initialize Database
    init_db(app)

    # Register Blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)

    # Enable CORS headers for API access from Live Server or external clients
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response

    # Custom 404 Error Handler
    @app.errorhandler(404)
    def page_not_found(e):
        if app.debug:
            logger.warning(f"404 Error: {e}")
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"500 Internal Error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

    # Auto-seed initial news data if DB is empty and not in TESTING/VERCEL mode
    with app.app_context():
        try:
            import os
            is_vercel = os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL_ENV') is not None
            if not app.config.get('TESTING') and not is_vercel and News.query.count() == 0:
                logger.info("Database is empty. Performing initial news scrape on app startup...")
                manager = ScraperManager()
                manager.run_all_scrapers()
        except Exception as err:
            logger.warning(f"Initial DB check/scrape failed: {err}")

    return app

app = create_app()

if __name__ == '__main__':
    logger.info("Starting News Aggregator web application at http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
