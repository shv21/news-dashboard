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

            # Ensure headers exist
            try:
                existing_headers = self.worksheet.row_values(1)
                if not existing_headers:
                    self.worksheet.append_row(self.HEADERS)
                    logger.info("[GoogleSheets] Header row initialized.")
            except Exception as e:
                logger.warning(f"[GoogleSheets] Could not check header row: {e}")

            self.enabled = True
            logger.info(f"[GoogleSheets] Successfully connected to Google Sheet '{sheet_name}' (Worksheet: '{worksheet_name}').")

        except Exception as e:
            logger.error(f"[GoogleSheets] Connection/Authentication failed: {e}")
            self.enabled = False

    def get_existing_urls(self):
        """Fetch set of URLs currently present in the Google Sheet (Column 6: URL)."""
        if not self.enabled or not self.worksheet:
            return set()
        try:
            # URL is column 6 (1-indexed)
            urls = self.worksheet.col_values(6)
            return set(u for u in urls if u and u != "URL")
        except Exception as e:
            logger.error(f"[GoogleSheets] Failed to fetch existing URLs for duplicate check: {e}")
            return set()

    def sync_articles(self, articles):
        """
        Sync list of scraped article dictionaries to Google Sheet.
        
        Args:
            articles (list[dict]): Scraped article dictionaries containing keys:
                title, source, published_date, summary, article_url, country, etc.

        Returns:
            dict: Summary count of added and skipped articles.
        """
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

                # Format publication date
                pub_date = art.get('published_date')
                if isinstance(pub_date, datetime):
                    pub_date_str = pub_date.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    pub_date_str = str(pub_date or '')

                author = art.get('author') or art.get('source', 'Unknown')
                category = art.get('category') or art.get('country', 'General')
                title = art.get('title', 'Untitled')
                source = art.get('source', 'Unknown')
                summary = art.get('summary', '')

                row = [
                    source,
                    title,
                    author,
                    pub_date_str,
                    category,
                    url,
                    summary,
                    scraped_at
                ]
                rows_to_add.append(row)
                existing_urls.add(url)

            if rows_to_add:
                self.worksheet.append_rows(rows_to_add)
                result['added'] = len(rows_to_add)
                logger.info(f"[GoogleSheets] Appended {result['added']} new articles to Google Sheet.")
            else:
                logger.info("[GoogleSheets] All scraped articles already exist in Google Sheet (0 new added).")

        except Exception as e:
            logger.error(f"[GoogleSheets] Error syncing articles to Google Sheet: {e}", exc_info=True)
            result['errors'] += 1

        return result
