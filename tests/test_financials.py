"""Unit tests for FinancialService financial calculations and metric aggregations.

Tests metric calculations, percentage parsing, and bank filtering by country.
"""

from typing import Any, Dict, List
import unittest

from services.financial_service import FinancialService


class TestFinancialService(unittest.TestCase):
    """Test suite for FinancialService calculations."""

    def test_parse_percentage(self) -> None:
        """Test parsing percentage string values into floats."""
        self.assertEqual(FinancialService.parse_percentage("14.8%"), 14.8)
        self.assertEqual(FinancialService.parse_percentage("  12.3% "), 12.3)
        self.assertEqual(FinancialService.parse_percentage(None), 0.0)
        self.assertEqual(FinancialService.parse_percentage("invalid"), 0.0)

    def test_get_banks_by_country(self) -> None:
        """Test retrieving bank financial institution data by country code."""
        us_banks = FinancialService.get_banks_by_country("US")
        self.assertTrue(len(us_banks) > 0)
        self.assertEqual(us_banks[0]["symbol"], "JPM")

        in_banks = FinancialService.get_banks_by_country("IN")
        self.assertTrue(len(in_banks) > 0)

        global_banks = FinancialService.get_banks_by_country("ALL")
        self.assertTrue(len(global_banks) > 0)

    def test_calculate_summary_metrics(self) -> None:
        """Test summary metric calculations across financial institutions."""
        sample_banks: List[Dict[str, Any]] = [
            {
                "symbol": "BANK1",
                "price": 100.0,
                "change_pct": 2.0,
                "cet1_ratio": "15.0%",
            },
            {
                "symbol": "BANK2",
                "price": 200.0,
                "change_pct": -1.0,
                "cet1_ratio": "13.0%",
            },
        ]

        metrics = FinancialService.calculate_summary_metrics(sample_banks)
        self.assertEqual(metrics["total_institutions"], 2)
        self.assertEqual(metrics["avg_price"], 150.0)
        self.assertEqual(metrics["avg_change_pct"], 0.5)
        self.assertEqual(metrics["gainers_count"], 1)
        self.assertEqual(metrics["avg_cet1_ratio_pct"], 14.0)


if __name__ == "__main__":
    unittest.main()
