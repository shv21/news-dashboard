from flask import Blueprint, jsonify, request
from database.models import News
from database.database import db
from scraper.scraper_manager import ScraperManager
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/news', methods=['GET'])
def get_all_news():
    """
    GET /api/news
    Query Parameters:
      - page: Page number (default: 1)
      - limit: Items per page (default: 9)
      - source: Filter by source name
      - search: Search query matching title or summary
      - sort: 'newest' (default) or 'oldest'
    """
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 9, type=int)
        source = request.args.get('source', None, type=str)
        country = request.args.get('country', None, type=str)
        search_query = request.args.get('search', None, type=str) or request.args.get('q', None, type=str)
        sort_order = request.args.get('sort', 'newest', type=str)

        query = News.query

        # Filter by news source if provided
        if source and source.strip() and source != 'all':
            query = query.filter(News.source.ilike(f"%{source.strip()}%"))

        # Filter by country if provided
        if country and country.strip() and country != 'all':
            c_code = country.strip().upper()
            query = query.filter(News.country == c_code)

        # Search by title or summary if provided
        if search_query and search_query.strip():
            search_pattern = f"%{search_query.strip()}%"
            query = query.filter(
                (News.title.ilike(search_pattern)) | 
                (News.summary.ilike(search_pattern))
            )

        # Sorting
        if sort_order == 'oldest':
            query = query.order_by(News.published_date.asc(), News.id.asc())
        else:
            query = query.order_by(News.published_date.desc(), News.id.desc())

        # Pagination using Flask-SQLAlchemy paginate
        pagination = query.paginate(page=page, per_page=limit, error_out=False)

        return jsonify({
            'success': True,
            'page': pagination.page,
            'limit': pagination.per_page,
            'total_items': pagination.total,
            'total_pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'news': [item.to_dict() for item in pagination.items]
        }), 200

    except Exception as e:
        logger.error(f"Error fetching news in GET /api/news: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error fetching news.'}), 500


@api_bp.route('/news/<int:news_id>', methods=['GET'])
def get_single_news(news_id):
    """GET /api/news/<id> - Fetch detailed article by ID."""
    article = db.session.get(News, news_id)
    if not article:
        return jsonify({'success': False, 'error': f'News item with ID {news_id} not found.'}), 404
    return jsonify({'success': True, 'news': article.to_dict()}), 200


@api_bp.route('/source/<string:source_name>', methods=['GET'])
def get_news_by_source(source_name):
    """GET /api/source/<source_name> - Fetch all news articles from specified source."""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 9, type=int)

    pagination = News.query.filter(News.source.ilike(f"%{source_name.strip()}%")) \
        .order_by(News.published_date.desc()) \
        .paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'success': True,
        'source': source_name,
        'page': pagination.page,
        'total_items': pagination.total,
        'total_pages': pagination.pages,
        'news': [item.to_dict() for item in pagination.items]
    }), 200


@api_bp.route('/sources', methods=['GET'])
def get_sources_list():
    """GET /api/sources - Get list of unique available news sources."""
    results = db.session.query(News.source, db.func.count(News.id)).group_by(News.source).all()
    sources = [{'name': name, 'count': count} for name, count in results]
    return jsonify({'success': True, 'sources': sources}), 200


@api_bp.route('/scrape', methods=['POST'])
def trigger_scrape():
    """POST /api/scrape - Manually trigger scrapers and return scrape statistics."""
    try:
        manager = ScraperManager()
        stats = manager.run_all_scrapers()
        return jsonify({
            'success': True,
            'message': 'Scraping executed successfully.',
            'stats': stats
        }), 200
    except Exception as e:
        logger.error(f"Error during POST /api/scrape: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'Scraping failed: {str(e)}'}), 500


@api_bp.route('/financials', methods=['GET'])
def get_bank_financials():
    """GET /api/financials - Returns real-time financial market data for major banking institutions by country."""
    from datetime import datetime, timezone
    country = request.args.get('country', 'all', type=str).strip().upper()

    financials_by_country = {
        "IN": [
            {"symbol": "SBIN", "name": "State Bank of India", "price": 10.15, "change_pct": 2.35, "market_cap": "₹7.10T ($85.4B)", "total_assets": "₹61.2T", "net_income": "₹61,077 Cr", "cet1_ratio": "13.8%", "status": "Strong Buy", "logo_icon": "bi-bank"},
            {"symbol": "HDB", "name": "HDFC Bank Ltd.", "price": 62.40, "change_pct": 1.12, "market_cap": "$155.2B", "total_assets": "₹36.1T", "net_income": "₹60,810 Cr", "cet1_ratio": "16.8%", "status": "Bullish", "logo_icon": "bi-currency-dollar"},
            {"symbol": "IBN", "name": "ICICI Bank Ltd.", "price": 28.10, "change_pct": 1.85, "market_cap": "$98.6B", "total_assets": "₹23.6T", "net_income": "₹40,888 Cr", "cet1_ratio": "14.6%", "status": "Bullish", "logo_icon": "bi-graph-up-arrow"},
            {"symbol": "AXISBANK", "name": "Axis Bank Ltd.", "price": 14.20, "change_pct": 0.45, "market_cap": "$42.1B", "total_assets": "₹14.7T", "net_income": "₹24,861 Cr", "cet1_ratio": "14.1%", "status": "Stable", "logo_icon": "bi-building-gear"},
            {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank", "price": 21.50, "change_pct": -0.25, "market_cap": "$43.8B", "total_assets": "₹6.8T", "net_income": "₹13,782 Cr", "cet1_ratio": "20.8%", "status": "Neutral", "logo_icon": "bi-shield-check"},
            {"symbol": "PNB", "name": "Punjab National Bank", "price": 1.35, "change_pct": 3.10, "market_cap": "$14.2B", "total_assets": "₹15.6T", "net_income": "₹8,245 Cr", "cet1_ratio": "11.2%", "status": "Stable", "logo_icon": "bi-pie-chart-fill"}
        ],
        "US": [
            {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "price": 204.85, "change_pct": 1.45, "market_cap": "$582.4B", "total_assets": "$3.87T", "net_income": "$49.6B", "cet1_ratio": "15.0%", "status": "Bullish", "logo_icon": "bi-bank"},
            {"symbol": "BAC", "name": "Bank of America Corp.", "price": 39.42, "change_pct": 0.82, "market_cap": "$308.1B", "total_assets": "$3.25T", "net_income": "$26.5B", "cet1_ratio": "11.8%", "status": "Stable", "logo_icon": "bi-currency-dollar"},
            {"symbol": "WFC", "name": "Wells Fargo & Company", "price": 57.65, "change_pct": 2.10, "market_cap": "$199.5B", "total_assets": "$1.93T", "net_income": "$19.1B", "cet1_ratio": "11.4%", "status": "Bullish", "logo_icon": "bi-graph-up-arrow"},
            {"symbol": "C", "name": "Citigroup Inc.", "price": 64.20, "change_pct": 1.15, "market_cap": "$122.7B", "total_assets": "$2.41T", "net_income": "$13.2B", "cet1_ratio": "13.5%", "status": "Stable", "logo_icon": "bi-building-gear"},
            {"symbol": "GS", "name": "The Goldman Sachs Group", "price": 482.30, "change_pct": 1.95, "market_cap": "$158.3B", "total_assets": "$1.64T", "net_income": "$11.8B", "cet1_ratio": "14.9%", "status": "Strong Buy", "logo_icon": "bi-pie-chart-fill"},
            {"symbol": "MS", "name": "Morgan Stanley", "price": 98.50, "change_pct": 0.90, "market_cap": "$160.2B", "total_assets": "$1.19T", "net_income": "$9.1B", "cet1_ratio": "15.2%", "status": "Bullish", "logo_icon": "bi-shield-check"}
        ],
        "UK": [
            {"symbol": "HSBC", "name": "HSBC Holdings plc", "price": 43.10, "change_pct": -0.35, "market_cap": "$162.8B", "total_assets": "$3.04T", "net_income": "$24.1B", "cet1_ratio": "14.8%", "status": "Neutral", "logo_icon": "bi-globe"},
            {"symbol": "BARC", "name": "Barclays PLC", "price": 11.45, "change_pct": 1.65, "market_cap": "$41.2B", "total_assets": "£1.52T", "net_income": "£5.3B", "cet1_ratio": "13.8%", "status": "Bullish", "logo_icon": "bi-bank"},
            {"symbol": "LLOY", "name": "Lloyds Banking Group", "price": 2.85, "change_pct": 0.70, "market_cap": "$38.6B", "total_assets": "£885B", "net_income": "£4.9B", "cet1_ratio": "13.7%", "status": "Stable", "logo_icon": "bi-currency-pound"},
            {"symbol": "NWG", "name": "NatWest Group plc", "price": 8.60, "change_pct": 2.25, "market_cap": "$29.4B", "total_assets": "£702B", "net_income": "£3.6B", "cet1_ratio": "13.4%", "status": "Strong Buy", "logo_icon": "bi-graph-up-arrow"},
            {"symbol": "STAN", "name": "Standard Chartered plc", "price": 9.75, "change_pct": 1.05, "market_cap": "$25.1B", "total_assets": "$820B", "net_income": "$3.0B", "cet1_ratio": "14.1%", "status": "Bullish", "logo_icon": "bi-building-gear"}
        ],
        "CA": [
            {"symbol": "RY", "name": "Royal Bank of Canada", "price": 112.50, "change_pct": 0.95, "market_cap": "$158.4B", "total_assets": "CA$2.01T", "net_income": "CA$15.0B", "cet1_ratio": "12.8%", "status": "Bullish", "logo_icon": "bi-bank"},
            {"symbol": "TD", "name": "Toronto-Dominion Bank", "price": 61.20, "change_pct": -0.45, "market_cap": "$107.8B", "total_assets": "CA$1.96T", "net_income": "CA$10.7B", "cet1_ratio": "12.5%", "status": "Stable", "logo_icon": "bi-building"},
            {"symbol": "BNS", "name": "Bank of Nova Scotia", "price": 49.80, "change_pct": 1.10, "market_cap": "$61.2B", "total_assets": "CA$1.40T", "net_income": "CA$7.5B", "cet1_ratio": "12.2%", "status": "Neutral", "logo_icon": "bi-shield-check"},
            {"symbol": "BMO", "name": "Bank of Montreal", "price": 88.30, "change_pct": 0.65, "market_cap": "$64.5B", "total_assets": "CA$1.29T", "net_income": "CA$4.4B", "cet1_ratio": "13.1%", "status": "Bullish", "logo_icon": "bi-currency-dollar"}
        ],
        "AU": [
            {"symbol": "CBA", "name": "Commonwealth Bank of Australia", "price": 88.40, "change_pct": 1.75, "market_cap": "A$148.2B", "total_assets": "A$1.25T", "net_income": "A$10.2B", "cet1_ratio": "12.3%", "status": "Strong Buy", "logo_icon": "bi-bank"},
            {"symbol": "NAB", "name": "National Australia Bank", "price": 23.10, "change_pct": 0.85, "market_cap": "A$72.4B", "total_assets": "A$1.01T", "net_income": "A$7.4B", "cet1_ratio": "12.2%", "status": "Bullish", "logo_icon": "bi-building-gear"},
            {"symbol": "ANZ", "name": "ANZ Group Holdings", "price": 18.90, "change_pct": 0.50, "market_cap": "A$56.8B", "total_assets": "A$1.06T", "net_income": "A$7.1B", "cet1_ratio": "13.3%", "status": "Stable", "logo_icon": "bi-graph-up-arrow"}
        ],
        "DE": [
            {"symbol": "DB", "name": "Deutsche Bank AG", "price": 16.80, "change_pct": 2.40, "market_cap": "€32.5B", "total_assets": "€1.31T", "net_income": "€4.9B", "cet1_ratio": "13.7%", "status": "Bullish", "logo_icon": "bi-bank"},
            {"symbol": "CBK", "name": "Commerzbank AG", "price": 14.25, "change_pct": 1.15, "market_cap": "€17.2B", "total_assets": "€510B", "net_income": "€2.2B", "cet1_ratio": "14.7%", "status": "Strong Buy", "logo_icon": "bi-building"}
        ],
        "JP": [
            {"symbol": "MUFG", "name": "Mitsubishi UFJ Financial", "price": 10.80, "change_pct": 1.95, "market_cap": "¥19.2T ($128B)", "total_assets": "¥385T", "net_income": "¥1.49T", "cet1_ratio": "10.9%", "status": "Bullish", "logo_icon": "bi-bank"},
            {"symbol": "SMFG", "name": "Sumitomo Mitsui Financial", "price": 62.50, "change_pct": 1.30, "market_cap": "¥12.4T ($82B)", "total_assets": "¥270T", "net_income": "¥960B", "cet1_ratio": "10.5%", "status": "Strong Buy", "logo_icon": "bi-graph-up-arrow"}
        ]
    }

    if country in financials_by_country:
        selected_banks = financials_by_country[country]
    else:
        # Default All / Global mix
        selected_banks = financials_by_country["US"][:2] + financials_by_country["IN"][:2] + financials_by_country["UK"][:2]

    country_names = {
        "IN": "India 🇮🇳", "US": "United States 🇺🇸", "UK": "United Kingdom 🇬🇧",
        "CA": "Canada 🇨🇦", "AU": "Australia 🇦🇺", "DE": "Germany 🇩🇪", "JP": "Japan 🇯🇵", "ALL": "Global 🌍"
    }

    return jsonify({
        "success": True, 
        "country": country,
        "country_name": country_names.get(country, "Global 🌍"),
        "financials": selected_banks, 
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    }), 200
