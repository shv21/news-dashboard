"""Database models module for News Aggregator.

Defines SQLAlchemy ORM models and dictionary serialization helpers for news articles.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from database.database import db


def utc_now() -> datetime:
    """Return current naive UTC timestamp.

    Returns:
        datetime: Current UTC datetime without timezone offset.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class News(db.Model):
    """SQLAlchemy model representing a scraped news article stored in SQLite."""

    __tablename__ = "news"

    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title: str = db.Column(db.String(255), nullable=False)
    source: str = db.Column(db.String(100), nullable=False, index=True)
    published_date: Optional[datetime] = db.Column(
        db.DateTime, nullable=True, default=utc_now, index=True
    )
    summary: Optional[str] = db.Column(db.Text, nullable=True)
    image_url: Optional[str] = db.Column(db.Text, nullable=True)
    article_url: str = db.Column(db.Text, unique=True, nullable=False)
    country: Optional[str] = db.Column(
        db.String(10), nullable=True, default="US", index=True
    )
    created_at: Optional[datetime] = db.Column(db.DateTime, default=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize News model instance to a dictionary for API JSON responses.

        Returns:
            Dict[str, Any]: Dictionary containing all article attributes.
        """
        pub_date_str: Optional[str] = (
            self.published_date.strftime("%Y-%m-%d %H:%M:%S")
            if self.published_date
            else None
        )
        created_str: Optional[str] = (
            self.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if self.created_at
            else None
        )

        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "published_date": pub_date_str,
            "summary": self.summary,
            "image_url": self.image_url,
            "article_url": self.article_url,
            "country": self.country or "US",
            "created_at": created_str,
        }

    def __repr__(self) -> str:
        """Return developer-friendly string representation of News object."""
        title_snippet: str = self.title[:30] if self.title else "Untitled"
        return f"<News id={self.id} title='{title_snippet}' source='{self.source}'>"

