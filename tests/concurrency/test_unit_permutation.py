"""Unit tests for permutation analysis and optimization.

Pure unit tests with no I/O, no external dependencies, using mocks only.
"""

import unittest
from unittest.mock import Mock

import pytest

from app.concurrency.tools.permutation import (
    analyze_permutation,
    find_optimal_permutation,
    generate_strategy_permutations,
)

from .base import ConcurrencyTestCase, MockDataMixin


@pytest.mark.unit
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

        # Should have C(3,2) = 3 permutations (default: exact size only)
        self.assertEqual(len(perms), 3)

        # Check all permutations have exactly min_strategies
        for perm in perms:
            self.assertEqual(len(perm), 2)

    @pytest.mark.error_handling
    def test_generate_strategy_permutations_minimum_validation(self):
        """Test validation of minimum strategies."""
        strategies = [{"ticker": "BTC"}]

        # Should raise ValueError when min_strategies > available
        with pytest.raises(ValueError) as cm:
            generate_strategy_permutations(strategies, min_strategies=2)

        self.assertIn("cannot be greater than", str(cm.value))

        # Should raise ValueError when min_strategies < 2
        with pytest.raises(ValueError) as cm:
            generate_strategy_permutations(strategies, min_strategies=1)

        self.assertIn("must be at least 2", str(cm.value))

    def test_generate_strategy_permutations_sizes(self):
        """Test generating permutations with max_strategies specified."""
        strategies = [
            {"ticker": "A"},
            {"ticker": "B"},
            {"ticker": "C"},
            {"ticker": "D"},
        ]

        # Generate with min_strategies=2, max_strategies=4
        perms = generate_strategy_permutations(
            strategies, min_strategies=2, max_strategies=4
        )

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


@pytest.mark.unit
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

        _stats, _aligned = analyze_permutation(
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
        # With 3 strategies and min_strategies=2, we get C(3,2) = 3 permutations
        efficiency_scores = [0.7, 0.85, 0.6]  # Second one is best
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

        best_perm, best_stats, _best_aligned = find_optimal_permutation(
            strategies,
            mock_process,
            mock_analyze,
            self.log_mock,
            min_strategies=2,
        )

        # Should find the permutation with 0.85 efficiency (highest of the 3)
        self.assertEqual(best_stats["efficiency_score"], 0.85)
        self.assertIsNotNone(best_perm)

    @pytest.mark.error_handling
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
        _best_perm, best_stats, _best_aligned = find_optimal_permutation(
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


if __name__ == "__main__":
    unittest.main()
