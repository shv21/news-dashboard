from datetime import datetime, timezone
from database.database import db

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class News(db.Model):
    """SQLAlchemy model representing a news article."""
    __tablename__ = 'news'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    source = db.Column(db.String(100), nullable=False, index=True)
    published_date = db.Column(db.DateTime, nullable=True, default=utc_now, index=True)
    summary = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.Text, nullable=True)
    article_url = db.Column(db.Text, unique=True, nullable=False)
    country = db.Column(db.String(10), nullable=True, default='US', index=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        """Serialize News model to a dictionary for API JSON responses."""
        return {
            'id': self.id,
            'title': self.title,
            'source': self.source,
            'published_date': self.published_date.strftime('%Y-%m-%d %H:%M:%S') if self.published_date else None,
            'summary': self.summary,
            'image_url': self.image_url,
            'article_url': self.article_url,
            'country': self.country or 'US',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f"<News id={self.id} title='{self.title[:30]}' source='{self.source}'>"
