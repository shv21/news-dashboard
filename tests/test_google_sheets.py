import unittest
from unittest.mock import MagicMock, patch
import sys

# Pre-mock gspread and google libraries if not installed in current environment
try:
    import gspread
    import google.oauth2.service_account
except ImportError:
    mock_gspread = MagicMock()
    mock_google = MagicMock()
    sys.modules['gspread'] = mock_gspread
    sys.modules['google'] = mock_google
    sys.modules['google.oauth2'] = mock_google
    sys.modules['google.oauth2.service_account'] = mock_google

from services.google_sheets_service import GoogleSheetsService
from datetime import datetime, timezone

class TestGoogleSheetsService(unittest.TestCase):

    def test_service_disabled_when_credentials_missing(self):
        with patch('os.path.exists', return_value=False):
            service = GoogleSheetsService()
            self.assertFalse(service.enabled)
            res = service.sync_articles([{'article_url': 'https://example.com/1'}])
            self.assertEqual(res['added'], 0)
            self.assertEqual(res['skipped'], 0)

    @patch('os.path.exists', return_value=True)
    def test_duplicate_filtering_and_sync(self, mock_exists):
        service = GoogleSheetsService()

        # Setup mock client & worksheet
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_worksheet = MagicMock()

        service.client = mock_client
        service.sheet = mock_sheet
        service.worksheet = mock_worksheet
        service.enabled = True

        # Existing URL in sheet: https://example.com/existing
        mock_worksheet.col_values.return_value = ["URL", "https://example.com/existing"]
        mock_worksheet.row_values.return_value = ["Source", "Title"]

        articles = [
            {
                'title': 'Existing News',
                'source': 'BBC News',
                'published_date': datetime.now(timezone.utc),
                'summary': 'Summary 1',
                'article_url': 'https://example.com/existing',
                'country': 'UK'
            },
            {
                'title': 'New Unique News',
                'source': 'Times of India',
                'published_date': datetime.now(timezone.utc),
                'summary': 'Summary 2',
                'article_url': 'https://example.com/new-article',
                'country': 'IN'
            }
        ]

        result = service.sync_articles(articles)
        self.assertEqual(result['added'], 1)
        self.assertEqual(result['skipped'], 1)
        mock_worksheet.append_rows.assert_called_once()

if __name__ == '__main__':
    unittest.main()
