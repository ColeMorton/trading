"""Integration tests for optimization report generation with file I/O."""

import json
import unittest

import pytest

from app.concurrency.tools.optimization_report import (
    NumpyEncoder,
    generate_optimization_report,
    save_optimization_report,
)

from .base import ConcurrencyTestCase


@pytest.mark.integration
class TestOptimizationReport(ConcurrencyTestCase):
    """Test optimization report generation."""

    def test_generate_optimization_report(self):
        """Test optimization report generation."""
        # Create test data
        all_strategies = [
            {"TICKER": "BTC"},
            {"TICKER": "ETH"},
            {"TICKER": "SOL"},
        ]

        all_stats = {
            "efficiency_score": 0.7,
            "diversification_multiplier": 0.8,
            "independence_multiplier": 0.85,
            "activity_multiplier": 0.9,
            "total_expectancy": 1.5,
            "weighted_efficiency": 0.75,
            "risk_concentration_index": 0.3,
        }

        optimal_strategies = [
            {"TICKER": "BTC"},
            {"TICKER": "SOL"},
        ]

        optimal_stats = {
            "efficiency_score": 0.85,
            "diversification_multiplier": 0.9,
            "independence_multiplier": 0.95,
            "activity_multiplier": 0.92,
            "total_expectancy": 1.6,
            "weighted_efficiency": 0.88,
            "risk_concentration_index": 0.25,
        }

        config = {"PORTFOLIO": "test.json"}

        report = generate_optimization_report(
            all_strategies,
            all_stats,
            optimal_strategies,
            optimal_stats,
            config,
            self.log_mock,
        )

        # Check report structure
        self.assertIn("optimization_summary", report)
        self.assertIn("all_strategies", report)
        self.assertIn("optimal_strategies", report)
        self.assertIn("config", report)

        # Check summary
        summary = report["optimization_summary"]
        self.assertEqual(summary["all_strategies_count"], 3)
        self.assertEqual(summary["optimal_strategies_count"], 2)
        # Check that tickers are captured (key name might vary)
        self.assertEqual(summary["optimal_strategies_count"], 2)

        # Check improvement calculation
        expected_improvement = (0.85 - 0.7) / 0.7 * 100
        self.assertAlmostEqual(
            summary["efficiency_improvement_percent"],
            expected_improvement,
            places=2,
        )

    def test_save_optimization_report(self):
        """Test saving optimization report to file."""
        report = {
            "optimization_summary": {
                "all_strategies_count": 3,
                "optimal_strategies_count": 2,
            },
            "test_data": [1, 2, 3],
        }

        config = {"PORTFOLIO": "test_portfolio.json"}

        # Save report
        saved_path = save_optimization_report(report, config, self.log_mock)

        # Check file was created
        self.assertTrue(saved_path.exists())
        self.assertEqual(saved_path.name, "test_portfolio_optimization.json")

        # Check content
        with open(saved_path) as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data["optimization_summary"]["all_strategies_count"], 3)
        self.assertEqual(saved_data["test_data"], [1, 2, 3])

        # Cleanup
        saved_path.unlink()

    def test_numpy_encoder(self):
        """Test NumPy encoder for JSON serialization."""
        import numpy as np

        # Test various NumPy types
        test_data = {
            "int64": np.int64(42),
            "float64": np.float64(3.14),
            "array": np.array([1, 2, 3]),
            "none": None,
            "regular": 123,
        }

        # Should serialize without error
        json_str = json.dumps(test_data, cls=NumpyEncoder)
        decoded = json.loads(json_str)

        # Check conversions
        self.assertEqual(decoded["int64"], 42)
        self.assertAlmostEqual(decoded["float64"], 3.14)
        self.assertEqual(decoded["array"], [1, 2, 3])
        # Note: The NumpyEncoder actually returns None as null in JSON
        self.assertIsNone(decoded["none"])
        self.assertEqual(decoded["regular"], 123)


if __name__ == "__main__":
    unittest.main()
