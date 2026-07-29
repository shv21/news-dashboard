# 📰 News Pulse - Full-Stack News Aggregator

A modular, scalable, full-stack web application built with **Python 3.12+**, **Flask**, **SQLAlchemy**, **BeautifulSoup4**, **Feedparser**, **SQLite**, **Bootstrap 5**, and **Vanilla JavaScript**. 

The application automatically collects news articles from multiple news sources (BBC News, TechCrunch), prevents duplicate entries using unique article URLs, persists the news in SQLite, provides RESTful API endpoints, and presents a responsive, modern web interface.

---

## ✨ Features

- **Multi-Source News Scraping**: Automatically parses news feeds from BBC News and TechCrunch using BeautifulSoup4 & Feedparser.
- **Duplicate Prevention**: Enforces database-level URL uniqueness constraints to prevent duplicate entries.
- **RESTful API**: Exposes JSON endpoints for fetching news, filtering by source, searching by keyword, and manually triggering scrapers.
- **Modern Responsive Frontend**: Built with Bootstrap 5 and custom CSS featuring glassmorphism headers, card hover animations, and toast notifications.
- **Live Search & Filter**: Instant keyword search, news source dropdown filtering, and sorting (Newest / Oldest).
- **Pagination**: Client and server-side pagination support.
- **Manual Scrape Trigger**: Web UI button to trigger scraping on demand with live progress spinners.
- **Unit Testing Suite**: Comprehensive unit tests covering database models, scrapers, and REST endpoints.

---

## 📁 Project Structure

```
news-aggregator/
├── app.py                     # Main Flask application initialization & error handlers
├── config.py                  # Central configuration (DB URI, scraper timeouts, page size)
├── requirements.txt           # Python project dependencies
├── README.md                  # Project documentation
├── .gitignore                 # Git ignore configuration
├── database/
│   ├── models.py              # SQLAlchemy News model definition
│   └── database.py            # SQLAlchemy database engine and session binding
├── scraper/
│   ├── scraper_one.py         # BBC News RSS & HTML scraper
│   ├── scraper_two.py         # TechCrunch RSS & HTML scraper
│   └── scraper_manager.py     # Central orchestrator for scrapers, retry logic, & deduplication
├── routes/
│   ├── api.py                 # REST API endpoints (/api/news, /api/source/<source>, /api/scrape)
│   └── views.py               # HTML template view routes
├── templates/
│   ├── base.html              # Base Jinja2 layout (Navbar, Footer, Toasts)
│   ├── index.html             # Homepage dashboard (Cards grid, search, filter, pagination)
│   ├── article.html           # Full article detail view
│   └── 404.html               # Custom 404 error page
├── static/
│   ├── css/
│   │   └── style.css          # Custom visual styles & responsive tweaks
│   └── js/
│       └── app.js             # Client JavaScript controller (API calls, UI updates)
├── data/
│   └── news.db                # SQLite database file (generated automatically)
└── tests/
    ├── test_models.py         # Unit tests for ORM models
    ├── test_api.py            # Unit tests for REST API endpoints
    └── test_scrapers.py       # Unit tests for scraper module
```

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- Python 3.12+ installed on your system
- Git

### 2. Virtual Environment Setup

Clone or open the repository, then create and activate a Python virtual environment:

#### Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Install all required Python packages via `pip`:

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Application

### Launch the Flask Web Server

Run `app.py` directly from the project root:

```bash
python app.py
```

Upon launching:
1. SQLite database `data/news.db` will be initialized automatically.
2. An initial news scrape will be executed automatically if the database is empty.
3. Open your browser and navigate to:

👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔌 REST API Documentation

The application exposes the following JSON REST API endpoints:

| Endpoint | Method | Description | Example Query Params |
| :--- | :--- | :--- | :--- |
| `/api/news` | `GET` | Fetch paginated list of news articles | `?page=1&limit=9&source=BBC%20News&search=AI&sort=newest` |
| `/api/news/<id>` | `GET` | Get detailed information for a single news item | `/api/news/1` |
| `/api/source/<source>` | `GET` | Get news articles by source name | `/api/source/BBC%20News` |
| `/api/sources` | `GET` | List all available news sources & item counts | `/api/sources` |
| `/api/scrape` | `POST` | Trigger manual news scraping on all registered scrapers | None |

### Example Response (`GET /api/news`):

```json
{
  "success": true,
  "page": 1,
  "limit": 9,
  "total_items": 25,
  "total_pages": 3,
  "has_next": true,
  "has_prev": false,
  "news": [
    {
      "id": 1,
      "title": "Example News Title",
      "source": "BBC News",
      "published_date": "2026-07-28 14:30:00",
      "summary": "Sample summary text extracted from the RSS news feed...",
      "image_url": "https://example.com/image.jpg",
      "article_url": "https://www.bbc.com/news/articles/example",
      "created_at": "2026-07-28 15:00:00"
    }
  ]
}
```

---

## 🧪 Running Unit Tests

To run the automated test suite with `pytest`:

```bash
pytest -v
```

---

## 🔮 Future Improvements

- Add asynchronous background scraping using Celery or APScheduler.
- Add user account authentication & saved favorite articles.
- Add additional news source scrapers (CNN, Reuters, Hacker News API).
- Implement Natural Language Processing (NLP) sentiment analysis and topic categorization.
