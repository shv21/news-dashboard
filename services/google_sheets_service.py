import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """Service to handle appending scraped news articles to Google Sheets."""

    HEADERS = [
        "Source", "Title", "Author", "Published Date", "Category", "URL", "Summary", "Scraped At"
    ]

    def __init__(self):
        self.enabled = False
        self.client = None
        self.sheet = None
        self.worksheet = None
        self._init_sheets()

    def _init_sheets(self):
        credentials_file = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        sheet_id = os.environ.get('GOOGLE_SHEET_ID', '').strip()
        sheet_name = os.environ.get('GOOGLE_SHEET_NAME', 'My News Data')
        worksheet_name = os.environ.get('GOOGLE_WORKSHEET_NAME', 'News')


        # Check if credentials file exists
        if not os.path.exists(credentials_file):
            logger.info(f"[GoogleSheets] Credentials file '{credentials_file}' not found. Google Sheets upload will be skipped.")
            return

        try:
            import gspread
            from google.oauth2.service_account import Credentials

            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
            self.client = gspread.authorize(creds)

            # Open spreadsheet by Name first, or fallback to sheet_id
            try:
                if sheet_name:
                    self.sheet = self.client.open(sheet_name)
                elif sheet_id:
                    self.sheet = self.client.open_by_key(sheet_id)
            except gspread.exceptions.SpreadsheetNotFound:
                if sheet_id:
                    try:
                        self.sheet = self.client.open_by_key(sheet_id)
                    except Exception:
                        logger.error(f"[GoogleSheets] Spreadsheet '{sheet_name}' not found. Please ensure the sheet is shared with Editor access to: {creds.service_account_email}")
                        return
                else:
                    logger.error(f"[GoogleSheets] Spreadsheet '{sheet_name}' not found. Please ensure the sheet is shared with Editor access to: {creds.service_account_email}")
                    return

            except Exception as e:
                err_str = str(e)
                if "drive.googleapis.com" in err_str or "Google Drive API" in err_str:
                    logger.error(f"[GoogleSheets] Google Drive API is disabled in your Google Cloud project. Please enable Google Drive API in Google Cloud Console.")
                else:
                    logger.error(f"[GoogleSheets] Failed to open spreadsheet '{sheet_name}': {e}")
                return


            # Open or create worksheet
            try:
                self.worksheet = self.sheet.worksheet(worksheet_name)
            except gspread.exceptions.WorksheetNotFound:
                logger.info(f"[GoogleSheets] Worksheet '{worksheet_name}' not found. Creating new worksheet...")
                self.worksheet = self.sheet.add_worksheet(title=worksheet_name, rows=1000, cols=len(self.HEADERS))
            except Exception as e:
                logger.error(f"[GoogleSheets] Failed to access worksheet '{worksheet_name}': {e}")
                return

            # Ensure headers exist and are formatted
            try:
                existing_headers = self.worksheet.row_values(1)
                if not existing_headers or existing_headers != self.HEADERS:
                    self.setup_formatted_header()
            except Exception as e:
                logger.warning(f"[GoogleSheets] Could not check/setup header row: {e}")

            self.enabled = True
            logger.info(f"[GoogleSheets] Successfully connected to Google Sheet '{sheet_name}' (Worksheet: '{worksheet_name}').")

        except Exception as e:
            logger.error(f"[GoogleSheets] Connection/Authentication failed: {e}")
            self.enabled = False

    def setup_formatted_header(self):
        """Sets up row 1 with headers, dark navy background, bold white text, and freezes row 1."""
        if not self.worksheet:
            return
        try:
            # Check if row 1 already has headers
            existing = self.worksheet.row_values(1)
            if existing != self.HEADERS:
                self.worksheet.insert_row(self.HEADERS, index=1)
            
            # Freeze header row
            self.worksheet.freeze(rows=1)

            # Apply dark background, bold white text, and left alignment
            self.worksheet.format('A1:H1', {
                'textFormat': {
                    'bold': True,
                    'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}
                },
                'backgroundColor': {'red': 0.12, 'green': 0.16, 'blue': 0.23},
                'horizontalAlignment': 'LEFT'
            })
            logger.info("[GoogleSheets] Formatted header row styling applied successfully.")
        except Exception as e:
            logger.warning(f"[GoogleSheets] Header styling warning: {e}")

    def get_existing_urls(self):
        """Fetch set of URLs currently present in the Google Sheet (Column 6: URL)."""
        if not self.enabled or not self.worksheet:
            return set()
        try:
            urls = self.worksheet.col_values(6)
            return set(u for u in urls if u and u != "URL")
        except Exception as e:
            logger.error(f"[GoogleSheets] Failed to fetch existing URLs for duplicate check: {e}")
            return set()

    def format_article_row(self, art, scraped_at):
        """Clean and format article dictionary into a neat Google Sheet row."""
        url = art.get('article_url', '').strip()
        pub_date = art.get('published_date')
        if isinstance(pub_date, datetime):
            pub_date_str = pub_date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            pub_date_str = str(pub_date or '')

        source = art.get('source', 'Unknown')
        title = art.get('title', 'Untitled').strip()
        summary = art.get('summary', '').strip()
        country = (art.get('country') or '').upper()

        # Clean Category & Author mappings
        if source == 'BBC News' or country == 'UK':
            category = 'UK & World News'
            author = 'BBC Newsroom'
        elif source == 'Times of India' or country == 'IN':
            category = 'India News'
            author = 'TOI Reporter'
        else:
            category = art.get('category') or 'General'
            author = art.get('author') or source

        return [
            source,
            title,
            author,
            pub_date_str,
            category,
            url,
            summary,
            scraped_at
        ]

    def sync_articles(self, articles):
        """Sync list of scraped article dictionaries to Google Sheet."""
        result = {'added': 0, 'skipped': 0, 'errors': 0}

        if not self.enabled or not self.worksheet:
            logger.debug("[GoogleSheets] Sync skipped as Google Sheets service is disabled or uninitialized.")
            return result

        if not articles:
            return result

        try:
            existing_urls = self.get_existing_urls()
            rows_to_add = []
            scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            for art in articles:
                url = art.get('article_url', '').strip()
                if not url:
                    continue

                if url in existing_urls:
                    result['skipped'] += 1
                    continue

                row = self.format_article_row(art, scraped_at)
                rows_to_add.append(row)
                existing_urls.add(url)

            if rows_to_add:
                self.worksheet.append_rows(rows_to_add)
                result['added'] = len(rows_to_add)
                logger.info(f"[GoogleSheets] Appended {result['added']} new organized articles to Google Sheet.")
            else:
                logger.info("[GoogleSheets] All scraped articles already exist in Google Sheet (0 new added).")

        except Exception as e:
            logger.error(f"[GoogleSheets] Error syncing articles to Google Sheet: {e}", exc_info=True)
            result['errors'] += 1

        return result

    def reorganize_sheet(self, articles):
        """Clears raw/unorganized sheet data and populates clean headers and formatted article rows."""
        if not self.enabled or not self.worksheet:
            return False

        try:
            logger.info("[GoogleSheets] Reorganizing sheet with clean headers and formatted rows...")
            self.worksheet.clear()
            self.setup_formatted_header()

            scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            rows = []
            seen_urls = set()

            for art in articles:
                url = art.get('article_url', '').strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                rows.append(self.format_article_row(art, scraped_at))

            if rows:
                self.worksheet.append_rows(rows)
                logger.info(f"[GoogleSheets] Successfully populated {len(rows)} organized rows.")
            return True
        except Exception as e:
            logger.error(f"[GoogleSheets] Failed to reorganize sheet: {e}", exc_info=True)
            return False

