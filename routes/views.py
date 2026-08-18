"""View routes module.

Provides Flask Blueprints for serving HTML frontend web pages.
"""

import logging
from typing import List, Union

from flask import Blueprint, Response, abort, render_template

from database.database import db
from database.models import News

logger = logging.getLogger(__name__)

views_bp: Blueprint = Blueprint("views", __name__)


@views_bp.route("/")
@views_bp.route("/index.html")
@views_bp.route("/api/index")
def index() -> Union[str, Response]:
    """Render the main news aggregator dashboard with pre-rendered initial news.

    Returns:
        Union[str, Response]: Rendered HTML dashboard template string.
    """
    try:
        sources = db.session.query(News.source).distinct().all()
        source_list: List[str] = [s[0] for s in sources if s[0]]
        initial_news: List[News] = (
            News.query.order_by(News.published_date.desc(), News.id.desc())
            .limit(9)
            .all()
        )
        total_count: int = News.query.count()
    except Exception as e:
        logger.error(f"Error querying database for dashboard view: {e}")
        source_list = []
        initial_news = []
        total_count = 0

    return render_template(
        "index.html",
        sources=source_list,
        news=initial_news,
        total_count=total_count,
    )


@views_bp.route("/article/<int:news_id>")
def article_detail(news_id: int) -> Union[str, Response]:
    """Render the full article details view page for a given news item.

    Args:
        news_id (int): Primary key ID of the news article.

    Returns:
        Union[str, Response]: Rendered HTML template or HTTP 404 response.
    """
    try:
        article: Union[News, None] = db.session.get(News, news_id)
        if not article:
            logger.warning(f"Article detail requested for non-existent ID {news_id}")
            abort(404)
        return render_template("article.html", article=article)
    except Exception as e:
        logger.error(f"Error serving article detail for ID {news_id}: {e}")
        abort(404)
