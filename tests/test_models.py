"""Unit tests for database models and serialization.

Tests News model creation, attribute persistence, and dictionary serialization.
"""

from datetime import datetime
from typing import Generator

from flask import Flask
from flask.testing import FlaskClient
import pytest

from app import create_app
from database.database import db
from database.models import News


@pytest.fixture
def app() -> Generator[Flask, None, None]:
    """Create and configure a clean Flask app instance for testing."""
    app_instance = create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
    )

    with app_instance.app_context():
        db.create_all()
        yield app_instance
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Return test client for app instance."""
    return app.test_client()


def test_news_model_creation(app: Flask) -> None:
    """Test News model instantiation, database commit, and to_dict serialization."""
    with app.app_context():
        news = News(
            title="Test Breaking Headline",
            source="Test Source",
            published_date=datetime(2026, 7, 28, 12, 0, 0),
            summary="Test summary content for testing.",
            image_url="https://example.com/image.jpg",
            article_url="https://example.com/test-article",
        )
        db.session.add(news)
        db.session.commit()

        saved = News.query.filter_by(
            article_url="https://example.com/test-article"
        ).first()
        assert saved is not None
        assert saved.title == "Test Breaking Headline"
        assert saved.source == "Test Source"

        # Test to_dict serialization
        data = saved.to_dict()
        assert data["id"] == saved.id
        assert data["title"] == "Test Breaking Headline"
        assert data["source"] == "Test Source"
        assert data["published_date"] == "2026-07-28 12:00:00"
