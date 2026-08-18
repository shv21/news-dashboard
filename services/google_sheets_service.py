"""Google Sheets synchronization service module.

Handles authenticating with Google Drive / Sheets API, formatting worksheet headers,
classifying news article categories, and appending non-duplicate scraped articles.
"""

from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict, List, Optional, Set

from config import Config
from exceptions import GoogleSheetsError
from utils import classify_category

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """Service to handle appending scraped news articles to Google Sheets."""

    HEADERS: List[str] = [
        "Source",
        "Title",
        "Author",
        "Published Date",
        "Category",
        "URL",
        "Summary",
        "Scraped At",
    ]

    def __init__(self) -> None:
        """Initialize GoogleSheetsService and attempt Google API connection."""
        self.enabled: bool = False
        self.client: Optional[Any] = None
        self.sheet: Optional[Any] = None
        self.worksheet: Optional[Any] = None
        self._init_sheets()

    def _init_sheets(self) -> None:
        """Initialize connection to Google Sheets API using service account credentials."""
        credentials_file: str = Config.GOOGLE_CREDENTIALS_FILE
        sheet_id: str = Config.GOOGLE_SHEET_ID
        sheet_name: str = Config.GOOGLE_SHEET_NAME
        worksheet_name: str = Config.GOOGLE_WORKSHEET_NAME

        if not os.path.exists(credentials_file):
            logger.info(
                f"[GoogleSheets] Credentials file '{credentials_file}' not found. "
                "Google Sheets upload will be skipped."
            )
            return

        try:
            import gspread
            from google.oauth2.service_account import Credentials

            scopes: List[str] = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(
                credentials_file, scopes=scopes
            )
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
                    except Exception as err:
                        logger.error(
                            f"[GoogleSheets] Spreadsheet '{sheet_name}' not found: {err}"
                        )
                        return
                else:
                    logger.error(
                        f"[GoogleSheets] Spreadsheet '{sheet_name}' not found."
                    )
                    return
            except Exception as e:
                err_str: str = str(e)
                if (
                    "drive.googleapis.com" in err_str
                    or "Google Drive API" in err_str
                ):
                    logger.error(
                        "[GoogleSheets] Google Drive API is disabled in Google Cloud."
                    )
                else:
                    logger.error(
                        f"[GoogleSheets] Failed to open spreadsheet '{sheet_name}': {e}"
                    )
                return

            # Open or create worksheet
            try:
                self.worksheet = self.sheet.worksheet(worksheet_name)
            except gspread.exceptions.WorksheetNotFound:
                logger.info(
                    f"[GoogleSheets] Worksheet '{worksheet_name}' missing. Creating..."
                )
                self.worksheet = self.sheet.add_worksheet(
                    title=worksheet_name, rows=1000, cols=len(self.HEADERS)
                )
            except Exception as e:
                logger.error(
                    f"[GoogleSheets] Failed to access worksheet '{worksheet_name}': {e}"
                )
                return

            # Ensure headers exist and are formatted
            try:
                existing_headers = self.worksheet.row_values(1)
                if not existing_headers or existing_headers != self.HEADERS:
                    self.setup_formatted_header()
            except Exception as e:
                logger.warning(
                    f"[GoogleSheets] Could not check header row: {e}"
                )

            self.enabled = True
            logger.info(
                f"[GoogleSheets] Connected to Sheet '{sheet_name}' "
                f"(Worksheet: '{worksheet_name}')."
            )

        except Exception as e:
            logger.error(f"[GoogleSheets] Authentication failed: {e}")
            self.enabled = False

    def setup_formatted_header(self) -> None:
        """Set up row 1 with headers, dark navy background, bold white text, and freeze row 1."""
        if not self.worksheet:
            return
        try:
            existing: List[str] = self.worksheet.row_values(1)
            if existing != self.HEADERS:
                self.worksheet.insert_row(self.HEADERS, index=1)

            self.worksheet.freeze(rows=1)
            self.worksheet.format(
                "A1:H1",
                {
                    "textFormat": {
                        "bold": True,
                        "foregroundColor": {
                            "red": 1.0,
                            "green": 1.0,
                            "blue": 1.0,
                        },
                    },
                    "backgroundColor": {
                        "red": 0.12,
                        "green": 0.16,
                        "blue": 0.23,
                    },
                    "horizontalAlignment": "LEFT",
                },
            )
            logger.info("[GoogleSheets] Formatted header row styling applied.")
        except Exception as e:
            logger.warning(f"[GoogleSheets] Header styling warning: {e}")

    def get_existing_urls(self) -> Set[str]:
        """Fetch set of URLs currently present in the Google Sheet (Column 6: URL).

        Returns:
            Set[str]: Set of article URLs existing in worksheet.
        """
        if not self.enabled or not self.worksheet:
            return set()
        try:
            urls: List[str] = self.worksheet.col_values(6)
            return set(u for u in urls if u and u != "URL")
        except Exception as e:
            logger.error(
                f"[GoogleSheets] Failed to fetch existing URLs for deduplication: {e}"
            )
            return set()

    def classify_article_category(
        self, title: str, summary: str, url: str
    ) -> str:
        """Automatically classify article into categories using utility helper.

        Args:
            title (str): Article title.
            summary (str): Article summary text.
            url (str): Article URL.

        Returns:
            str: Category string.
        """
        return classify_category(title, summary, url)

    def format_article_row(
        self, art: Dict[str, Any], scraped_at: str
    ) -> List[str]:
        """Clean and format article dictionary into a Google Sheet row list.

        Args:
            art (Dict[str, Any]): Article attributes dictionary.
            scraped_at (str): ISO formatted timestamp string.

        Returns:
            List[str]: Formatted row column values.
        """
        url: str = art.get("article_url", "").strip()
        pub_date: Any = art.get("published_date")
        if isinstance(pub_date, datetime):
            pub_date_str: str = pub_date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            pub_date_str = str(pub_date or "")

        source: str = art.get("source", "Unknown")
        title: str = art.get("title", "Untitled").strip()
        summary: str = art.get("summary", "").strip()

        category: str = art.get(
            "category"
        ) or self.classify_article_category(title, summary, url)

        # Author mapping
        if source == "BBC News":
            author: str = art.get("author") or "BBC Newsroom"
        elif source == "Times of India":
            author = art.get("author") or "TOI Reporter"
        else:
            author = art.get("author") or source

        return [
            source,
            title,
            author,
            pub_date_str,
            category,
            url,
            summary,
            scraped_at,
        ]

    def sync_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """Sync list of scraped article dictionaries to Google Sheet.

        Args:
            articles (List[Dict[str, Any]]): List of scraped article dicts.

        Returns:
            Dict[str, int]: Result statistics ('added', 'skipped', 'errors').
        """
        result: Dict[str, int] = {"added": 0, "skipped": 0, "errors": 0}

        if not self.enabled or not self.worksheet:
            logger.debug(
                "[GoogleSheets] Sync skipped (service disabled or missing)."
            )
            return result

        if not articles:
            return result

        try:
            existing_urls: Set[str] = self.get_existing_urls()
            rows_to_add: List[List[str]] = []
            scraped_at: str = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            for art in articles:
                url: str = art.get("article_url", "").strip()
                if not url:
                    continue

                if url in existing_urls:
                    result["skipped"] += 1
                    continue

                row: List[str] = self.format_article_row(art, scraped_at)
                rows_to_add.append(row)
                existing_urls.add(url)

            if rows_to_add:
                self.worksheet.append_rows(rows_to_add)
                result["added"] = len(rows_to_add)
                logger.info(
                    f"[GoogleSheets] Appended {result['added']} articles to Sheet."
                )
            else:
                logger.info("[GoogleSheets] All articles already exist in Sheet.")

        except Exception as e:
            logger.error(
                f"[GoogleSheets] Error syncing articles to Google Sheet: {e}",
                exc_info=True,
            )
            result["errors"] += 1

        return result

    def reorganize_sheet(self, articles: List[Dict[str, Any]]) -> bool:
        """Clear raw sheet data and populate formatted headers and article rows.

        Args:
            articles (List[Dict[str, Any]]): List of article dicts.

        Returns:
            bool: True if reorganization succeeded, False otherwise.
        """
        if not self.enabled or not self.worksheet:
            return False

        try:
            logger.info("[GoogleSheets] Reorganizing sheet content...")
            self.worksheet.clear()
            self.setup_formatted_header()

            scraped_at: str = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            rows: List[List[str]] = []
            seen_urls: Set[str] = set()

            for art in articles:
                url: str = art.get("article_url", "").strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                rows.append(self.format_article_row(art, scraped_at))

            if rows:
                self.worksheet.append_rows(rows)
                logger.info(
                    f"[GoogleSheets] Successfully populated {len(rows)} rows."
                )
            return True
        except Exception as e:
            logger.error(
                f"[GoogleSheets] Failed to reorganize sheet: {e}", exc_info=True
            )
            return False
