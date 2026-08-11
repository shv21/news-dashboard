# 📄 News Pulse - Data Sources, APIs & System Architecture Documentation

This document explains in full technical detail **where data is sourced**, **what APIs are used**, and **how the News Pulse website works**.

---

## 1. 🌐 Data Sources & Scraped Websites

The system aggregates news articles from **9 global news publishers** across **7 countries**, using XML/RSS feed parsing with HTML fallbacks.

| # | News Source | Country | Target Feed URL | Extraction Method & Purpose |
|---|---|---|---|---|
| 1 | **BBC News** | 🇬🇧 United Kingdom | `http://feeds.bbci.co.uk/news/rss.xml` | Parses RSS XML entries with `feedparser`. Extracts headline, publication timestamp, clean text summary (via `BeautifulSoup4`), and thumbnail images. |
| 2 | **TechCrunch** | 🇺🇸 United States | `https://techcrunch.com/feed/` | Parses tech news RSS feed. Searches `media_content`, `media_thumbnail`, enclosures, and `<img>` tags in HTML content for high-res images. |
| 3 | **The Verge** | 🇺🇸 United States | `https://www.theverge.com/rss/index.xml` | Parses Atom/RSS technology feed with BeautifulSoup image extraction. |
| 4 | **Wired** | 🇺🇸 United States | `https://www.wired.com/feed/rss` | Scrapes technology, science, and digital culture stories. |
| 5 | **Times of India** | 🇮🇳 India | `https://timesofindia.indiatimes.com/rssfeedstopstories.cms` | Aggregates top Indian and South Asian national & international headlines. |
| 6 | **CBC News / Global News** | 🇨🇦 Canada | `https://globalnews.ca/feed/` | Scrapes Canadian national and international breaking news stories. |
| 7 | **ABC News Australia** | 🇦🇺 Australia | `https://www.abc.net.au/news/feed/51120/rss.xml` | Parses top Australian news feed entries. |
| 8 | **DW News (Deutsche Welle)** | 🇩🇪 Germany | `https://rss.dw.com/xml/rss-en-all` | Parses English-language European and German international news. |
| 9 | **Japan Today** | 🇯🇵 Japan | `https://japantoday.com/feed` | Parses East Asian and Japanese national news feed. |

### Fallback Image Services & CDNs:
- **Unsplash CDN**: `https://images.unsplash.com` (curated high-res fallback imagery).
- **Picsum Photos**: `https://picsum.photos/seed/{md5_hash}/600/400` (generates deterministic, 100% unique seed images based on the MD5 hash of an article URL/title whenever an RSS entry lacks an explicit image tag).

---

## 2. 🔌 APIs & Endpoint Reference

The application features a built-in RESTful JSON API layer (`routes/api.py`) as well as external web API connections.

### Internal REST API Endpoints

#### 1. `GET /api/news`
Fetches a paginated list of news articles stored in the database.
- **Query Parameters**:
  - `page` *(int)*: Page number (default: `1`)
  - `limit` *(int)*: Items per page (default: `9`)
  - `source` *(string)*: Filter by news publisher (e.g. `BBC News`, `TechCrunch`)
  - `country` *(string)*: Filter by 2-letter country code (`US`, `UK`, `IN`, `CA`, `AU`, `DE`, `JP`)
  - `search` / `q` *(string)*: Case-insensitive keyword search against title and summary
  - `sort` *(string)*: Order results by published date (`newest` or `oldest`)
- **Sample Response**:
  ```json
  {
    "success": true,
    "page": 1,
    "limit": 9,
    "total_items": 45,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false,
    "news": [
      {
        "id": 1,
        "title": "Example Headline",
        "source": "BBC News",
        "published_date": "2026-08-05 14:00:00",
        "summary": "Cleaned article text excerpt...",
        "image_url": "https://example.com/image.jpg",
        "article_url": "https://www.bbc.com/news/articles/example",
        "country": "UK",
        "created_at": "2026-08-05 14:05:00"
      }
    ]
  }
  ```

#### 2. `GET /api/news/<id>`
Retrieves full details for a single news article by its database primary key.

#### 3. `GET /api/source/<source_name>`
Retrieves all news items associated with a specific publisher.

#### 4. `GET /api/sources`
Returns a list of all active news publishers currently stored in the database along with total article counts.

#### 5. `POST /api/scrape`
On-demand manual trigger that executes all 9 scrapers concurrently, filters out broken 404 links, skips existing duplicate URLs, and returns scraping run statistics (`new_added`, `duplicates_skipped`, `errors`).

#### 6. `GET /api/financials`
Returns real-time financial market data for major banking institutions categorized by country (`IN`, `US`, `UK`, `CA`, `AU`, `DE`, `JP`). Returns metrics including Stock Symbol, Price ($/₹/£/€/¥), Daily Change %, Market Cap, Total Assets, Net Income, CET1 Capital Ratio, and Market Status.

---

## 3. ⚙️ How This Website Works (Architecture & Workflow)

```
┌────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL DATA SOURCES                         │
│   BBC News  •  TechCrunch  •  The Verge  •  Wired  •  Times of India   │
│   CBC Canada  •  ABC Australia  •  DW Germany  •  Japan Today          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (HTTP GET RSS/Atom XML)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        PYTHON SCRAPER ENGINE                           │
│  • ScraperManager orchestrates 9 registered Scraper Modules            │
│  • feedparser extracts raw XML metadata & timestamps                   │
│  • BeautifulSoup cleans HTML tags from summary & extracts <img> tags    │
│  • MD5 Hash fallback handles missing thumbnail images                   │
│  • requests.head() validates links (prevents HTTP 404 entries)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Deduplicated write via SQLAlchemy)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     DATABASE LAYER (SQLite DB)                         │
│  • File: data/news.db                                                  │
│  • Model: News (id, title, source, published_date, summary,            │
│                 image_url, article_url [UNIQUE], country, created_at)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   FLASK REST API & BACKEND ROUTING                     │
│  • app.py: App factory, Flask-SQLAlchemy initialization, CORS headers  │
│  • routes/api.py: /api/news, /api/sources, /api/scrape, /api/financials│
│  • routes/views.py: Jinja2 page templates (Index, Article Detail, 404) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (JSON & Rendered HTML)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND USER INTERFACE                           │
│  • Bootstrap 5 + Glassmorphism Custom CSS (static/css/style.css)       │
│  • Vanilla JS Controller (static/js/app.js):                           │
│    - Asynchronous fetch API requests                                   │
│    - Debounced live search bar (350ms delay)                          │
│    - Multi-country & source dropdown filtering                         │
│    - Dynamic banking financials widget                                 │
│    - Interactive pagination & toast notifications                       │
└────────────────────────────────────────────────────────────────────────┘
```

### Complete Execution Flow:

1. **Server Launch & Initial Auto-Seed**:
   When `python app.py` is executed:
   - Flask initializes configuration (`config.py`) and binds the SQLite database engine.
   - On startup, if the database contains 10 or fewer records, `ScraperManager` automatically triggers an initial scraping cycle across all 9 publishers to populate the dashboard with live articles.

2. **Scraping & Deduplication Mechanism**:
   - Each scraper class fetches XML content over HTTP using custom `User-Agent` headers to avoid requests blocking.
   - `feedparser` extracts fields like `title`, `link`, `summary`, and publication dates.
   - `ScraperManager` verifies whether `article_url` already exists in SQLite to prevent duplicate records.
   - It performs a fast `HEAD` request to verify the link does not return a 404 status.
   - New valid records are committed into the `news` table.

3. **REST API & Client Interaction**:
   - The frontend sends asynchronous `fetch()` requests to `/api/news` with parameters for page, limit, source, country, search query, and sorting.
   - The Flask backend processes these parameters using SQLAlchemy query filters and pagination, returning serialized JSON arrays.

4. **Dynamic Frontend UI Rendering**:
   - `app.js` renders responsive Bootstrap news cards with publisher badges, publication dates, excerpts, and country flags.
   - User input in the search field triggers a debounced live filtering update.
   - Changing the country filter dynamically updates both the news stream and the bank financials market dashboard widget (`/api/financials`).
