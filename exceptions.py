"""Custom exceptions for the news-dashboard application.

Provides a structured hierarchy of exception classes for handling errors across
configuration, database, scraping, and service operations.
"""

from typing import Optional


class NewsDashboardError(Exception):
    """Base exception class for all news-dashboard errors."""

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        """Initialize NewsDashboardError.

        Args:
            message (str): High-level human readable error message.
            details (Optional[str]): Detailed technical or context info.
        """
        super().__init__(message)
        self.message: str = message
        self.details: Optional[str] = details

    def __str__(self) -> str:
        """Return formatted string representation of the error."""
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class ConfigurationError(NewsDashboardError):
    """Raised when there is a missing or invalid configuration setting."""

    pass


class DatabaseError(NewsDashboardError):
    """Raised when a database query, connection, or transaction fails."""

    pass


class ScraperError(NewsDashboardError):
    """Base exception for errors encountered during web news scraping."""

    pass


class ScraperFetchError(ScraperError):
    """Raised when fetching an RSS feed or web page content fails."""

    pass


class ScraperParseError(ScraperError):
    """Raised when parsing XML, RSS feed entries, or HTML fails."""

    pass


class GoogleSheetsError(NewsDashboardError):
    """Raised when authentication, opening, or syncing to Google Sheets fails."""

    pass
