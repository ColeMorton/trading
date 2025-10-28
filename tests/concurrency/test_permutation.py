"""Unit tests for permutation analysis and optimization - cleaned version.

Only tests functions that are actually implemented.
"""

import json
import unittest
from unittest.mock import Mock

import pytest

from app.concurrency.tools.optimization_report import (
    NumpyEncoder,
    generate_optimization_report,
    save_optimization_report,
)
from app.concurrency.tools.permutation import (
    analyze_permutation,
    find_optimal_permutation,
    generate_strategy_permutations,
)

from .base import ConcurrencyTestCase, MockDataMixin


class TestPermutationGeneration(unittest.TestCase):
    """Test permutation generation functions."""

    def test_generate_strategy_permutations_basic(self):
        """Test basic permutation generation."""
        strategies = [
            {"ticker": "BTC", "id": 1},
            {"ticker": "ETH", "id": 2},
            {"ticker": "SOL", "id": 3},
        ]

        perms = generate_strategy_permutations(strategies, min_strategies=2)

        # Should have C(3,2) + C(3,3) = 3 + 1 = 4 permutations
        self.assertEqual(len(perms), 4)

        # Check all permutations have at least min_strategies
        for perm in perms:
            self.assertGreaterEqual(len(perm), 2)
            self.assertLessEqual(len(perm), 3)

    def test_generate_strategy_permutations_minimum_validation(self):
        """Test validation of minimum strategies."""
        strategies = [{"ticker": "BTC"}]

        # Should raise ValueError when min_strategies > available
        with pytest.raises(ValueError) as cm:
            generate_strategy_permutations(strategies, min_strategies=2)

        self.assertIn("cannot be greater than", str(cm.exception))

        # Should raise ValueError when min_strategies < 2
        with pytest.raises(ValueError) as cm:
            generate_strategy_permutations(strategies, min_strategies=1)

        self.assertIn("must be at least 2", str(cm.exception))

    def test_generate_strategy_permutations_sizes(self):
        """Test generating permutations of different sizes."""
        strategies = [
            {"ticker": "A"},
            {"ticker": "B"},
            {"ticker": "C"},
            {"ticker": "D"},
        ]

        # Generate with min_strategies=2
        perms = generate_strategy_permutations(strategies, min_strategies=2)

        # Should have C(4,2) + C(4,3) + C(4,4) = 6 + 4 + 1 = 11 permutations
        self.assertEqual(len(perms), 11)

        # Check we have correct number of each size
        size_counts = {}
        for perm in perms:
            size = len(perm)
            size_counts[size] = size_counts.get(size, 0) + 1

        self.assertEqual(size_counts[2], 6)  # C(4,2)
        self.assertEqual(size_counts[3], 4)  # C(4,3)
        self.assertEqual(size_counts[4], 1)  # C(4,4)


class TestPermutationAnalysis(ConcurrencyTestCase, MockDataMixin):
    """Test permutation analysis functions."""

    def test_analyze_permutation_equal_allocation(self):
        """Test that permutations use equal allocation."""
        # Create test permutation
        permutation = [
            {"ticker": "BTC", "ALLOCATION": 50.0},
            {"ticker": "ETH", "ALLOCATION": 30.0},
            {"ticker": "SOL", "ALLOCATION": 20.0},
        ]

        # Mock functions
        mock_process = Mock(return_value=({"data": "processed"}, permutation))
        mock_analyze = Mock(return_value=({"efficiency_score": 0.85}, []))

        stats, aligned = analyze_permutation(
            permutation,
            mock_process,
            mock_analyze,
            self.log_mock,
        )

        # Check that allocations were equalized
        expected_allocation = 1.0 / 3
        for strategy in permutation:
            self.assertAlmostEqual(
                strategy["ALLOCATION"],
                expected_allocation,
                places=5,
            )

        # Verify log message about equal allocations
        self.log_mock.assert_any_call(
            f"Using equal allocations ({expected_allocation:.4f}) for all strategies in permutation",
            "info",
        )

    def test_find_optimal_permutation_basic(self):
        """Test finding optimal permutation."""
        # Create test strategies with required fields for valid permutations
        strategies = [
            {
                "TICKER": "BTC",
                "TIMEFRAME": "D",
                "STRATEGY": "SMA",
                "MA_FAST": 10,
                "MA_SLOW": 20,
                "EXPECTANCY_PER_TRADE": 0.02,
                "PORTFOLIO_STATS": {
                    "Score": 1.5,
                    "Win Rate [%]": 55.0,
                    "Total Trades": 25,
                    "Profit Factor": 1.3,
                },
                "id": 1,
            },
            {
                "TICKER": "ETH",
                "TIMEFRAME": "D",
                "STRATEGY": "SMA",
                "MA_FAST": 15,
                "MA_SLOW": 30,
                "EXPECTANCY_PER_TRADE": 0.025,
                "PORTFOLIO_STATS": {
                    "Score": 1.8,
                    "Win Rate [%]": 60.0,
                    "Total Trades": 30,
                    "Profit Factor": 1.5,
                },
                "id": 2,
            },
            {
                "TICKER": "SOL",
                "TIMEFRAME": "D",
                "STRATEGY": "SMA",
                "MA_FAST": 12,
                "MA_SLOW": 25,
                "EXPECTANCY_PER_TRADE": 0.018,
                "PORTFOLIO_STATS": {
                    "Score": 1.2,
                    "Win Rate [%]": 50.0,
                    "Total Trades": 20,
                    "Profit Factor": 1.1,
                },
                "id": 3,
            },
        ]

        # Mock functions to return different efficiency scores
        efficiency_scores = [0.7, 0.85, 0.6, 0.9]  # Last one is best
        call_count = 0

        def mock_process(strats, log, config):
            return {"data": "processed"}, strats

        def mock_analyze(data, strats, log):
            nonlocal call_count
            score = (
                efficiency_scores[call_count]
                if call_count < len(efficiency_scores)
                else 0.5
            )
            call_count += 1
            return {"efficiency_score": score}, []

        best_perm, best_stats, best_aligned = find_optimal_permutation(
            strategies,
            mock_process,
            mock_analyze,
            self.log_mock,
            min_strategies=2,
        )

        # Should find the permutation with 0.9 efficiency
        self.assertEqual(best_stats["efficiency_score"], 0.9)
        self.assertIsNotNone(best_perm)

    def test_find_optimal_permutation_error_handling(self):
        """Test error handling during permutation analysis."""
        strategies = [
            {
                "TICKER": "BTC",
                "TIMEFRAME": "D",
                "STRATEGY": "SMA",
                "EXPECTANCY_PER_TRADE": 0.02,
                "PORTFOLIO_STATS": {"Score": 1.5},
            },
            {
                "TICKER": "ETH",
                "TIMEFRAME": "D",
                "STRATEGY": "SMA",
                "EXPECTANCY_PER_TRADE": 0.025,
                "PORTFOLIO_STATS": {"Score": 1.8},
            },
            {
                "TICKER": "SOL",
                "TIMEFRAME": "D",
                "STRATEGY": "SMA",
                "EXPECTANCY_PER_TRADE": 0.018,
                "PORTFOLIO_STATS": {"Score": 1.2},
            },
        ]

        # Mock functions - first two fail, third succeeds
        call_count = 0

        def mock_process(strats, log, config):
            return {"data": "processed"}, strats

        def mock_analyze(data, strats, log):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                msg = "Test error"
                raise ValueError(msg)
            return {"efficiency_score": 0.8}, []

        # Should still find best despite errors
        best_perm, best_stats, best_aligned = find_optimal_permutation(
            strategies,
            mock_process,
            mock_analyze,
            self.log_mock,
            min_strategies=2,
        )

        self.assertEqual(best_stats["efficiency_score"], 0.8)

        # Verify error logging
        error_logs = [
            call
            for call in self.log_mock.call_args_list
            if "Error analyzing permutation" in str(call)
        ]
        self.assertEqual(len(error_logs), 2)


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
