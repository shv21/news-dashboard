"""Unit tests for Flask API endpoints.

Tests fetching paginated news, source filtering, searching, and 404 responses.
"""

from datetime import datetime
from typing import Generator

from flask.testing import FlaskClient
import pytest

from app import create_app
from database.database import db
from database.models import News


@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    """Create a clean Flask test client fixture initialized with in-memory database."""
    app = create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
    )

    with app.app_context():
        db.create_all()

        # Seed sample data for API tests
        n1 = News(
            title="BBC News Sample",
            source="BBC News",
            published_date=datetime(2026, 7, 28, 10, 0, 0),
            summary="BBC summary text",
            image_url="https://example.com/bbc.jpg",
            article_url="https://example.com/bbc-1",
        )
        n2 = News(
            title="TechCrunch Sample AI Article",
            source="TechCrunch",
            published_date=datetime(2026, 7, 28, 11, 0, 0),
            summary="TechCrunch AI news summary",
            image_url="https://example.com/tc.jpg",
            article_url="https://example.com/tc-1",
        )
        db.session.add_all([n1, n2])
        db.session.commit()

        yield app.test_client()

        db.session.remove()
        db.drop_all()


def test_get_news_endpoint(client: FlaskClient) -> None:
    """Test GET /api/news returns JSON array with correct count."""
    res = client.get("/api/news")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["total_items"] == 2
    assert len(data["news"]) == 2


def test_get_news_filter_by_source(client: FlaskClient) -> None:
    """Test GET /api/news filtering by news source name."""
    res = client.get("/api/news?source=BBC%20News")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_items"] == 1
    assert data["news"][0]["source"] == "BBC News"


def test_get_news_search(client: FlaskClient) -> None:
    """Test GET /api/news search query matching title or summary."""
    res = client.get("/api/news?search=AI")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_items"] == 1
    assert "TechCrunch" in data["news"][0]["source"]


def test_get_single_news(client: FlaskClient) -> None:
    """Test GET /api/news/<id> retrieving valid item by ID."""
    res = client.get("/api/news/1")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["news"]["id"] == 1


def test_get_single_news_404(client: FlaskClient) -> None:
    """Test GET /api/news/999 returns HTTP 404 for missing ID."""
    res = client.get("/api/news/999")
    assert res.status_code == 404
    data = res.get_json()
    assert data["success"] is False
