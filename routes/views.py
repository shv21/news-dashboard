from flask import Blueprint, render_template, abort
from database.models import News
from database.database import db

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """Renders the main news aggregator dashboard with pre-rendered initial news."""
    try:
        sources = db.session.query(News.source).distinct().all()
        source_list = [s[0] for s in sources if s[0]]
        initial_news = News.query.order_by(News.published_date.desc(), News.id.desc()).limit(9).all()
        total_count = News.query.count()
    except Exception:
        source_list = []
        initial_news = []
        total_count = 0
    return render_template('index.html', sources=source_list, news=initial_news, total_count=total_count)

@views_bp.route('/article/<int:news_id>')
def article_detail(news_id):
    """Renders the full article details view page."""
    article = db.session.get(News, news_id)
    if not article:
        abort(404)
    return render_template('article.html', article=article)
