"""API routes module.

Provides RESTful API JSON endpoints for querying news articles, source statistics,
triggering background news scrapers, and retrieving bank financial data.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Tuple

from flask import Blueprint, Response, jsonify, request

from config import Config
from database.database import db
from database.models import News
from scraper.scraper_manager import ScraperManager

logger = logging.getLogger(__name__)

api_bp: Blueprint = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/news", methods=["GET"])
def get_all_news() -> Tuple[Response, int]:
    """Retrieve news articles with pagination, source, country, and search filtering.

    Query Parameters:
        page (int): Page number (default: 1).
        limit (int): Number of items per page (default: 9).
        source (str): Optional filter by source name.
        country (str): Optional filter by country code.
        search / q (str): Optional search pattern matching title or summary.
        sort (str): 'newest' (default) or 'oldest'.

    Returns:
        Tuple[Response, int]: JSON response containing paginated news items and HTTP code.
    """
    try:
        page: int = request.args.get("page", 1, type=int)
        limit: int = request.args.get("limit", Config.ITEMS_PER_PAGE, type=int)
        source: str = request.args.get("source", None, type=str)
        country: str = request.args.get("country", None, type=str)
        search_query: str = (
            request.args.get("search", None, type=str)
            or request.args.get("q", None, type=str)
        )
        sort_order: str = request.args.get("sort", "newest", type=str)

        query = News.query

        # Filter by news source if provided
        if source and source.strip() and source != "all":
            query = query.filter(News.source.ilike(f"%{source.strip()}%"))

        # Filter by country if provided
        if country and country.strip() and country != "all":
            c_code: str = country.strip().upper()
            query = query.filter(News.country == c_code)

        # Search by title or summary if provided
        if search_query and search_query.strip():
            search_pattern: str = f"%{search_query.strip()}%"
            query = query.filter(
                (News.title.ilike(search_pattern))
                | (News.summary.ilike(search_pattern))
            )

        # Sorting
        if sort_order == "oldest":
            query = query.order_by(News.published_date.asc(), News.id.asc())
        else:
            query = query.order_by(News.published_date.desc(), News.id.desc())

        # Pagination using Flask-SQLAlchemy paginate
        pagination = query.paginate(page=page, per_page=limit, error_out=False)

        return (
            jsonify(
                {
                    "success": True,
                    "page": pagination.page,
                    "limit": pagination.per_page,
                    "total_items": pagination.total,
                    "total_pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev,
                    "news": [item.to_dict() for item in pagination.items],
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching news in GET /api/news: {e}", exc_info=True)
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Internal server error fetching news.",
                }
            ),
            500,
        )


@api_bp.route("/news/<int:news_id>", methods=["GET"])
def get_single_news(news_id: int) -> Tuple[Response, int]:
    """Fetch a single detailed article by its primary key ID.

    Args:
        news_id (int): The unique identifier of the news article.

    Returns:
        Tuple[Response, int]: JSON response containing article dictionary and HTTP status.
    """
    try:
        article = db.session.get(News, news_id)
        if not article:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"News item with ID {news_id} not found.",
                    }
                ),
                404,
            )
        return jsonify({"success": True, "news": article.to_dict()}), 200
    except Exception as e:
        logger.error(
            f"Error fetching news item {news_id} in GET /api/news/<id>: {e}",
            exc_info=True,
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Internal server error retrieving news item {news_id}.",
                }
            ),
            500,
        )


@api_bp.route("/source/<string:source_name>", methods=["GET"])
def get_news_by_source(source_name: str) -> Tuple[Response, int]:
    """Fetch all news articles from a specified news source.

    Args:
        source_name (str): The name of the news source.

    Returns:
        Tuple[Response, int]: JSON response containing matching articles and HTTP code.
    """
    try:
        page: int = request.args.get("page", 1, type=int)
        limit: int = request.args.get("limit", Config.ITEMS_PER_PAGE, type=int)

        pagination = (
            News.query.filter(News.source.ilike(f"%{source_name.strip()}%"))
            .order_by(News.published_date.desc())
            .paginate(page=page, per_page=limit, error_out=False)
        )

        return (
            jsonify(
                {
                    "success": True,
                    "source": source_name,
                    "page": pagination.page,
                    "total_items": pagination.total,
                    "total_pages": pagination.pages,
                    "news": [item.to_dict() for item in pagination.items],
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(
            f"Error fetching news for source '{source_name}': {e}",
            exc_info=True,
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Internal server error fetching articles for source '{source_name}'.",
                }
            ),
            500,
        )


@api_bp.route("/sources", methods=["GET"])
def get_sources_list() -> Tuple[Response, int]:
    """Retrieve list of unique available news sources and their article counts.

    Returns:
        Tuple[Response, int]: JSON response containing source statistics and HTTP status.
    """
    try:
        results = (
            db.session.query(News.source, db.func.count(News.id))
            .group_by(News.source)
            .all()
        )
        sources: List[Dict[str, Any]] = [
            {"name": name, "count": count} for name, count in results
        ]
        return jsonify({"success": True, "sources": sources}), 200
    except Exception as e:
        logger.error(
            f"Error retrieving sources list in GET /api/sources: {e}",
            exc_info=True,
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Internal server error fetching sources.",
                }
            ),
            500,
        )


@api_bp.route("/scrape", methods=["POST"])
def trigger_scrape() -> Tuple[Response, int]:
    """Manually trigger news scrapers and return run statistics.

    Returns:
        Tuple[Response, int]: JSON response containing execution summary stats.
    """
    try:
        manager: ScraperManager = ScraperManager()
        stats: Dict[str, Any] = manager.run_all_scrapers()
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Scraping executed successfully.",
                    "stats": stats,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error during POST /api/scrape: {e}", exc_info=True)
        return (
            jsonify(
                {"success": False, "error": f"Scraping failed: {str(e)}"}
            ),
            500,
        )


@api_bp.route("/financials", methods=["GET"])
def get_bank_financials() -> Tuple[Response, int]:
    """Return financial market data for major banking institutions by country.

    Returns:
        Tuple[Response, int]: JSON response containing bank data and status code.
    """
    try:
        country: str = (
            request.args.get("country", "all", type=str).strip().upper()
        )
        financials_by_country: Dict[str, List[Dict[str, Any]]] = (
            Config.FINANCIALS_BY_COUNTRY
        )
        country_names: Dict[str, str] = Config.COUNTRY_NAMES

        if country in financials_by_country:
            selected_banks: List[Dict[str, Any]] = financials_by_country[country]
        else:
            selected_banks = (
                financials_by_country.get("US", [])[:2]
                + financials_by_country.get("IN", [])[:2]
                + financials_by_country.get("UK", [])[:2]
            )

        updated_at_str: str = datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"
        )

        return (
            jsonify(
                {
                    "success": True,
                    "country": country,
                    "country_name": country_names.get(country, "Global 🌍"),
                    "financials": selected_banks,
                    "updated_at": updated_at_str,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error retrieving financials data: {e}", exc_info=True)
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Internal server error retrieving financial data.",
                }
            ),
            500,
        )
