"""Financial metrics and institution analysis service module.

Provides clear, beginner-friendly financial calculations and aggregation helper
functions for bank stock prices, percentage changes, and regulatory capital ratios.
"""

import logging
from typing import Any, Dict, List, Optional

from config import Config

logger = logging.getLogger(__name__)


class FinancialService:
    """Service class for processing and calculating banking financial data metrics."""

    @staticmethod
    def get_banks_by_country(country_code: str = "ALL") -> List[Dict[str, Any]]:
        """Retrieve list of banking institutions filtered by country code.

        Args:
            country_code (str): Country ISO code ('IN', 'US', 'UK', 'CA', 'AU', 'DE', 'JP')
                or 'ALL' for a global selection.

        Returns:
            List[Dict[str, Any]]: List of financial institution data dictionaries.
        """
        code: str = (country_code or "ALL").strip().upper()
        financials_db: Dict[str, List[Dict[str, Any]]] = Config.FINANCIALS_BY_COUNTRY

        if code in financials_db:
            return financials_db[code]

        # Global overview fallback: select top 2 institutions from major regions
        global_banks: List[Dict[str, Any]] = (
            financials_db.get("US", [])[:2]
            + financials_db.get("IN", [])[:2]
            + financials_db.get("UK", [])[:2]
        )
        return global_banks

    @staticmethod
    def parse_percentage(pct_str: Optional[str]) -> float:
        """Helper to parse a percentage string (e.g. '14.8%') into a float (14.8).

        Args:
            pct_str (Optional[str]): Percentage string representation.

        Returns:
            float: Numeric float value, or 0.0 on error.
        """
        if not pct_str or not isinstance(pct_str, str):
            return 0.0
        cleaned: str = pct_str.replace("%", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    @classmethod
    def calculate_summary_metrics(
        cls, banks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate summary metrics for a given list of banking institutions.

        Computes:
        - Total number of institutions
        - Average stock price
        - Average percentage daily change
        - Count of positive daily gainers
        - Average CET1 (Common Equity Tier 1) capital ratio percentage

        Args:
            banks (List[Dict[str, Any]]): List of bank data dictionaries.

        Returns:
            Dict[str, Any]: Calculated summary statistics dictionary.
        """
        if not banks:
            return {
                "total_institutions": 0,
                "avg_price": 0.0,
                "avg_change_pct": 0.0,
                "gainers_count": 0,
                "avg_cet1_ratio_pct": 0.0,
            }

        total_price: float = sum(float(b.get("price", 0.0)) for b in banks)
        total_change: float = sum(float(b.get("change_pct", 0.0)) for b in banks)
        gainers_count: int = sum(
            1 for b in banks if float(b.get("change_pct", 0.0)) > 0
        )

        cet1_values: List[float] = [
            cls.parse_percentage(b.get("cet1_ratio"))
            for b in banks
            if b.get("cet1_ratio")
        ]
        avg_cet1: float = (
            sum(cet1_values) / len(cet1_values) if cet1_values else 0.0
        )

        count: int = len(banks)
        return {
            "total_institutions": count,
            "avg_price": round(total_price / count, 2),
            "avg_change_pct": round(total_change / count, 2),
            "gainers_count": gainers_count,
            "avg_cet1_ratio_pct": round(avg_cet1, 2),
        }
