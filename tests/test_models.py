import pytest
from datetime import datetime
from app import create_app
from database.database import db
from database.models import News

@pytest.fixture
def app():
    """Create and configure a clean Flask app instance for testing."""
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_news_model_creation(app):
    """Test News model creation and serialization."""
    with app.app_context():
        news = News(
            title="Test Breaking Headline",
            source="Test Source",
            published_date=datetime(2026, 7, 28, 12, 0, 0),
            summary="Test summary content for testing.",
            image_url="https://example.com/image.jpg",
            article_url="https://example.com/test-article"
        )
        db.session.add(news)
        db.session.commit()

        saved = News.query.filter_by(article_url="https://example.com/test-article").first()
        assert saved is not None
        assert saved.title == "Test Breaking Headline"
        assert saved.source == "Test Source"
        
        # Test to_dict serialization
        data = saved.to_dict()
        assert data['id'] == saved.id
        assert data['title'] == "Test Breaking Headline"
        assert data['source'] == "Test Source"
        assert data['published_date'] == "2026-07-28 12:00:00"
