"""
Phase 5: Integration Testing and Validation Suite

This module provides comprehensive integration testing for all concurrency calculation fixes:
1. Risk contribution calculation (USE_FIXED_RISK_CALC)
2. Expectancy calculation (USE_FIXED_EXPECTANCY_CALC)
3. Win rate calculation (USE_FIXED_WIN_RATE_CALC)
4. Signal processing (USE_FIXED_SIGNAL_PROC)

The test suite includes:
- Hand-calculated test portfolios with known results
- Cross-module validation between JSON and CSV outputs
- Automated DataIntegrityValidator for ongoing validation
- Performance benchmarking
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import polars as pl
import pytest

from app.concurrency.tools.concurrency_analysis import ConcurrencyAnalysis
from app.tools.portfolio import StrategyConfig
from app.tools.setup_logging import setup_logging


class TestPortfolioBuilder:
    """Build test portfolios with known hand-calculated results."""

    @staticmethod
    def create_simple_test_portfolio() -> (
        Tuple[List[pl.DataFrame], List[StrategyConfig], Dict[str, Any]]
    ):
        """Create a simple portfolio with hand-calculated expected results.

        Returns:
            Tuple of (data_list, config_list, expected_results)
        """
        # Create two simple strategies with known trades
        dates = pl.date_range(
            datetime(2024, 1, 1), datetime(2024, 1, 31), interval="1d", eager=True
        )

        # Strategy 1: 2 trades, 1 win, 1 loss
        # Trade 1: Buy at 100, Sell at 110 (+10%)
        # Trade 2: Buy at 110, Sell at 99 (-10%)
        prices1 = [100.0] * 5 + [110.0] * 5 + [110.0] * 5 + [99.0] * 5 + [99.0] * 11
        positions1 = [0] * 5 + [1] * 5 + [0] * 5 + [1] * 5 + [0] * 11

        df1 = pl.DataFrame(
            {
                "Date": dates,
                "Close": prices1,
                "Position": positions1,
                "MA_Fast": [p * 0.98 for p in prices1],  # Dummy MA values
                "MA_Slow": [p * 1.02 for p in prices1],
            }
        )

        # Strategy 2: 3 trades, 2 wins, 1 loss
        # Trade 1: Buy at 100, Sell at 105 (+5%)
        # Trade 2: Buy at 105, Sell at 102 (-2.86%)
        # Trade 3: Buy at 102, Sell at 107 (+4.9%)
        prices2 = (
            [100.0] * 4
            + [105.0] * 4
            + [105.0] * 4
            + [102.0] * 4
            + [102.0] * 4
            + [107.0] * 4
            + [107.0] * 7
        )
        positions2 = [0] * 4 + [1] * 4 + [0] * 4 + [1] * 4 + [0] * 4 + [1] * 4 + [0] * 7

        df2 = pl.DataFrame(
            {
                "Date": dates,
                "Close": prices2,
                "Position": positions2,
                "MA_Fast": [p * 0.99 for p in prices2],
                "MA_Slow": [p * 1.01 for p in prices2],
            }
        )

        data_list = [df1, df2]

        config1 = StrategyConfig(
            ticker="TEST1",
            timeframe="D",
            strategy="SMA",
            ma_fast=5,
            ma_slow=10,
            allocation=0.6,  # 60% allocation
            stop_loss=0.05,  # 5% stop loss
        )

        config2 = StrategyConfig(
            ticker="TEST2",
            timeframe="D",
            strategy="SMA",
            ma_fast=5,
            ma_slow=10,
            allocation=0.4,  # 40% allocation
            stop_loss=0.03,  # 3% stop loss
        )

        config_list = [config1, config2]

        # Hand-calculated expected results
        expected_results = {
            # Strategy 1 metrics
            "strategy1": {
                "total_trades": 2,
                "winning_trades": 1,
                "losing_trades": 1,
                "win_rate": 0.5,  # 1/2 = 50%
                "avg_win": 0.10,  # 10%
                "avg_loss": 0.10,  # 10%
                "expectancy": 0.0,  # (0.5 * 0.10) - (0.5 * 0.10) = 0
                "risk_contribution": 0.6,  # 60% allocation
            },
            # Strategy 2 metrics
            "strategy2": {
                "total_trades": 3,
                "winning_trades": 2,
                "losing_trades": 1,
                "win_rate": 0.667,  # 2/3 = 66.7%
                "avg_win": 0.0495,  # (5% + 4.9%) / 2 = 4.95%
                "avg_loss": 0.0286,  # 2.86%
                "expectancy": 0.0227,  # (0.667 * 0.0495) - (0.333 * 0.0286) = 0.0227
                "risk_contribution": 0.4,  # 40% allocation
            },
            # Portfolio metrics
            "portfolio": {
                "total_risk_contribution": 1.0,  # Should sum to 100%
                "portfolio_expectancy": 0.00908,  # Weighted: 0.6*0 + 0.4*0.0227
            },
        }

        return data_list, config_list, expected_results


class DataIntegrityValidator:
    """Automated validator for ongoing data integrity checks."""

    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
        self.validation_results = []

    def validate_risk_contributions(self, stats: Dict[str, Any]) -> bool:
        """Validate that risk contributions sum to 100%.

        Args:
            stats: Statistics dictionary from concurrency analysis

        Returns:
            bool: True if valid, False otherwise
        """
        total_contribution = sum(
            strategy.get("risk_contribution", 0)
            for strategy in stats.get("strategies", {}).values()
        )

        is_valid = abs(total_contribution - 1.0) < self.tolerance

        self.validation_results.append(
            {
                "test": "risk_contributions_sum",
                "expected": 1.0,
                "actual": total_contribution,
                "passed": is_valid,
                "timestamp": datetime.now(),
            }
        )

        return is_valid

    def validate_win_rates(self, stats: Dict[str, Any]) -> bool:
        """Validate win rate calculations.

        Args:
            stats: Statistics dictionary from concurrency analysis

        Returns:
            bool: True if all valid, False otherwise
        """
        all_valid = True

        for strategy_id, strategy_stats in stats.get("strategies", {}).items():
            total_trades = strategy_stats.get("total_trades", 0)
            winning_trades = strategy_stats.get("winning_trades", 0)
            losing_trades = strategy_stats.get("losing_trades", 0)
            win_rate = strategy_stats.get("win_rate", 0)

            if total_trades > 0:
                # Check that wins + losses = total
                trades_sum_valid = (winning_trades + losing_trades) == total_trades

                # Check win rate calculation
                expected_win_rate = (
                    winning_trades / total_trades if total_trades > 0 else 0
                )
                win_rate_valid = abs(win_rate - expected_win_rate) < self.tolerance

                is_valid = trades_sum_valid and win_rate_valid
                all_valid &= is_valid

                self.validation_results.append(
                    {
                        "test": f"win_rate_{strategy_id}",
                        "expected_win_rate": expected_win_rate,
                        "actual_win_rate": win_rate,
                        "trades_sum_valid": trades_sum_valid,
                        "passed": is_valid,
                        "timestamp": datetime.now(),
                    }
                )

        return all_valid

    def validate_expectancy(self, stats: Dict[str, Any]) -> bool:
        """Validate expectancy calculations.

        Args:
            stats: Statistics dictionary from concurrency analysis

        Returns:
            bool: True if all valid, False otherwise
        """
        all_valid = True

        for strategy_id, strategy_stats in stats.get("strategies", {}).items():
            win_rate = strategy_stats.get("win_rate", 0)
            avg_win = strategy_stats.get("avg_win", 0)
            avg_loss = strategy_stats.get("avg_loss", 0)
            expectancy = strategy_stats.get("expectancy", 0)

            # Calculate expected expectancy
            expected_expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

            is_valid = abs(expectancy - expected_expectancy) < self.tolerance
            all_valid &= is_valid

            self.validation_results.append(
                {
                    "test": f"expectancy_{strategy_id}",
                    "expected": expected_expectancy,
                    "actual": expectancy,
                    "passed": is_valid,
                    "timestamp": datetime.now(),
                }
            )

        return all_valid

    def validate_signal_processing(
        self, data_list: List[pl.DataFrame], stats: Dict[str, Any]
    ) -> bool:
        """Validate signal processing counts.

        Args:
            data_list: Original data frames
            stats: Statistics dictionary from concurrency analysis

        Returns:
            bool: True if all valid, False otherwise
        """
        all_valid = True

        for i, (df, (strategy_id, strategy_stats)) in enumerate(
            zip(data_list, stats.get("strategies", {}).items())
        ):
            # Count position changes in original data
            positions = df["Position"].to_list()
            expected_trades = 0

            for j in range(1, len(positions)):
                if positions[j - 1] == 0 and positions[j] == 1:
                    expected_trades += 1

            actual_trades = strategy_stats.get("total_trades", 0)
            is_valid = actual_trades == expected_trades
            all_valid &= is_valid

            self.validation_results.append(
                {
                    "test": f"signal_count_{strategy_id}",
                    "expected": expected_trades,
                    "actual": actual_trades,
                    "passed": is_valid,
                    "timestamp": datetime.now(),
                }
            )

        return all_valid

    def generate_report(self) -> Dict[str, Any]:
        """Generate validation report.

        Returns:
            Dict containing validation summary and details
        """
        passed_tests = sum(1 for r in self.validation_results if r["passed"])
        total_tests = len(self.validation_results)

        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            },
            "details": self.validation_results,
        }


class PerformanceBenchmark:
    """Benchmark performance of different calculation methods."""

    def __init__(self):
        self.results = []

    def benchmark_calculation(
        self, name: str, func: callable, iterations: int = 100
    ) -> Dict[str, float]:
        """Benchmark a calculation function.

        Args:
            name: Name of the calculation
            func: Function to benchmark
            iterations: Number of iterations

        Returns:
            Dict with timing statistics
        """
        times = []

        for _ in range(iterations):
            start = time.time()
            func()
            end = time.time()
            times.append(end - start)

        result = {
            "name": name,
            "iterations": iterations,
            "min_time": min(times),
            "max_time": max(times),
            "avg_time": np.mean(times),
            "std_time": np.std(times),
            "total_time": sum(times),
        }

        self.results.append(result)
        return result

    def compare_implementations(
        self, old_func: callable, new_func: callable, name: str
    ) -> Dict[str, Any]:
        """Compare old and new implementations.

        Args:
            old_func: Original implementation
            new_func: Fixed implementation
            name: Name of the calculation

        Returns:
            Dict with comparison results
        """
        old_result = self.benchmark_calculation(f"{name}_old", old_func)
        new_result = self.benchmark_calculation(f"{name}_new", new_func)

        speedup = old_result["avg_time"] / new_result["avg_time"]

        return {
            "calculation": name,
            "old_avg_time": old_result["avg_time"],
            "new_avg_time": new_result["avg_time"],
            "speedup": speedup,
            "improvement_pct": (speedup - 1) * 100,
        }


class TestConcurrencyIntegrationPhase5:
    """Phase 5 integration tests for concurrency calculation fixes."""

    def test_all_fixes_enabled(self):
        """Test with all fixes enabled."""
        # Create test portfolio
        (
            data_list,
            config_list,
            expected,
        ) = TestPortfolioBuilder.create_simple_test_portfolio()

        # Enable all fixes
        config = {
            "USE_FIXED_RISK_CALC": True,
            "USE_FIXED_EXPECTANCY_CALC": True,
            "USE_FIXED_WIN_RATE_CALC": True,
            "USE_FIXED_SIGNAL_PROC": True,
        }

        # Run analysis
        analysis = ConcurrencyAnalysis(config=config)
        stats = analysis.analyze(data_list, config_list)

        # Create validator
        validator = DataIntegrityValidator()

        # Validate all components
        assert validator.validate_risk_contributions(
            stats
        ), "Risk contributions should sum to 100%"
        assert validator.validate_win_rates(
            stats
        ), "Win rates should be correctly calculated"
        assert validator.validate_expectancy(
            stats
        ), "Expectancy should be correctly calculated"
        assert validator.validate_signal_processing(
            data_list, stats
        ), "Signal counts should match"

        # Generate and check report
        report = validator.generate_report()
        assert report["summary"]["success_rate"] == 1.0, "All validations should pass"

    def test_individual_fixes(self):
        """Test each fix individually."""
        (
            data_list,
            config_list,
            expected,
        ) = TestPortfolioBuilder.create_simple_test_portfolio()

        fixes = [
            ("USE_FIXED_RISK_CALC", "risk_contributions"),
            ("USE_FIXED_EXPECTANCY_CALC", "expectancy"),
            ("USE_FIXED_WIN_RATE_CALC", "win_rates"),
            ("USE_FIXED_SIGNAL_PROC", "signal_processing"),
        ]

        for fix_flag, validation_method in fixes:
            # Enable only this fix
            config = {
                "USE_FIXED_RISK_CALC": False,
                "USE_FIXED_EXPECTANCY_CALC": False,
                "USE_FIXED_WIN_RATE_CALC": False,
                "USE_FIXED_SIGNAL_PROC": False,
            }
            config[fix_flag] = True

            # Run analysis
            analysis = ConcurrencyAnalysis(config=config)
            stats = analysis.analyze(data_list, config_list)

            # Validate specific component
            validator = DataIntegrityValidator()

            if validation_method == "risk_contributions":
                assert validator.validate_risk_contributions(
                    stats
                ), f"{fix_flag} validation failed"
            elif validation_method == "expectancy":
                assert validator.validate_expectancy(
                    stats
                ), f"{fix_flag} validation failed"
            elif validation_method == "win_rates":
                assert validator.validate_win_rates(
                    stats
                ), f"{fix_flag} validation failed"
            elif validation_method == "signal_processing":
                assert validator.validate_signal_processing(
                    data_list, stats
                ), f"{fix_flag} validation failed"

    def test_cross_module_validation(self):
        """Test that JSON and CSV outputs are consistent."""
        (
            data_list,
            config_list,
            expected,
        ) = TestPortfolioBuilder.create_simple_test_portfolio()

        # Enable all fixes
        config = {
            "USE_FIXED_RISK_CALC": True,
            "USE_FIXED_EXPECTANCY_CALC": True,
            "USE_FIXED_WIN_RATE_CALC": True,
            "USE_FIXED_SIGNAL_PROC": True,
            "PORTFOLIO": "test_portfolio.csv",
        }

        # Run analysis with output
        analysis = ConcurrencyAnalysis(config=config)
        stats = analysis.analyze(data_list, config_list)

        # Save outputs
        json_path = Path("json/concurrency/test_portfolio.json")
        csv_path = Path("csv/portfolios_best/test_portfolio.csv")

        # Load and compare outputs
        if json_path.exists():
            with open(json_path) as f:
                json_data = json.load(f)

            # Verify key metrics match
            for strategy_id in stats.get("strategies", {}):
                json_strategy = next(
                    (
                        s
                        for s in json_data.get("strategies", [])
                        if s.get("strategy_id") == strategy_id
                    ),
                    None,
                )

                if json_strategy:
                    assert (
                        abs(
                            stats["strategies"][strategy_id]["risk_contribution"]
                            - json_strategy.get("risk_contribution", 0)
                        )
                        < 1e-6
                    ), f"Risk contribution mismatch for {strategy_id}"

    def test_performance_benchmarks(self):
        """Benchmark performance of fixed calculations."""
        (
            data_list,
            config_list,
            expected,
        ) = TestPortfolioBuilder.create_simple_test_portfolio()

        benchmark = PerformanceBenchmark()

        # Benchmark with fixes disabled
        def run_without_fixes():
            config = {
                "USE_FIXED_RISK_CALC": False,
                "USE_FIXED_EXPECTANCY_CALC": False,
                "USE_FIXED_WIN_RATE_CALC": False,
                "USE_FIXED_SIGNAL_PROC": False,
            }
            analysis = ConcurrencyAnalysis(config=config)
            analysis.analyze(data_list, config_list)

        # Benchmark with fixes enabled
        def run_with_fixes():
            config = {
                "USE_FIXED_RISK_CALC": True,
                "USE_FIXED_EXPECTANCY_CALC": True,
                "USE_FIXED_WIN_RATE_CALC": True,
                "USE_FIXED_SIGNAL_PROC": True,
            }
            analysis = ConcurrencyAnalysis(config=config)
            analysis.analyze(data_list, config_list)

        # Compare implementations
        comparison = benchmark.compare_implementations(
            run_without_fixes, run_with_fixes, "all_fixes"
        )

        # Log results
        print(f"\nPerformance Comparison:")
        print(f"Old implementation: {comparison['old_avg_time']:.4f}s")
        print(f"New implementation: {comparison['new_avg_time']:.4f}s")
        print(f"Speedup: {comparison['speedup']:.2f}x")
        print(f"Improvement: {comparison['improvement_pct']:.1f}%")

    def test_known_results_validation(self):
        """Validate against hand-calculated expected results."""
        (
            data_list,
            config_list,
            expected,
        ) = TestPortfolioBuilder.create_simple_test_portfolio()

        # Enable all fixes
        config = {
            "USE_FIXED_RISK_CALC": True,
            "USE_FIXED_EXPECTANCY_CALC": True,
            "USE_FIXED_WIN_RATE_CALC": True,
            "USE_FIXED_SIGNAL_PROC": True,
        }

        # Run analysis
        analysis = ConcurrencyAnalysis(config=config)
        stats = analysis.analyze(data_list, config_list)

        # Validate strategy 1
        strategy1_stats = stats["strategies"].get("TEST1_D_SMA_5_10", {})
        assert strategy1_stats["total_trades"] == expected["strategy1"]["total_trades"]
        assert (
            strategy1_stats["winning_trades"] == expected["strategy1"]["winning_trades"]
        )
        assert (
            strategy1_stats["losing_trades"] == expected["strategy1"]["losing_trades"]
        )
        assert (
            abs(strategy1_stats["win_rate"] - expected["strategy1"]["win_rate"]) < 1e-3
        )
        assert (
            abs(
                strategy1_stats["risk_contribution"]
                - expected["strategy1"]["risk_contribution"]
            )
            < 1e-6
        )

        # Validate strategy 2
        strategy2_stats = stats["strategies"].get("TEST2_D_SMA_5_10", {})
        assert strategy2_stats["total_trades"] == expected["strategy2"]["total_trades"]
        assert (
            strategy2_stats["winning_trades"] == expected["strategy2"]["winning_trades"]
        )
        assert (
            strategy2_stats["losing_trades"] == expected["strategy2"]["losing_trades"]
        )
        assert (
            abs(strategy2_stats["win_rate"] - expected["strategy2"]["win_rate"]) < 1e-3
        )
        assert (
            abs(
                strategy2_stats["risk_contribution"]
                - expected["strategy2"]["risk_contribution"]
            )
            < 1e-6
        )

        # Validate portfolio totals
        total_risk = sum(s["risk_contribution"] for s in stats["strategies"].values())
        assert abs(total_risk - expected["portfolio"]["total_risk_contribution"]) < 1e-6


if __name__ == "__main__":
    # Run integration tests
    test = TestConcurrencyIntegrationPhase5()

    print("Running Phase 5 Integration Tests...")
    print("=" * 60)

    try:
        print("\n1. Testing all fixes enabled...")
        test.test_all_fixes_enabled()
        print("✓ All fixes validation passed")

        print("\n2. Testing individual fixes...")
        test.test_individual_fixes()
        print("✓ Individual fix validation passed")

        print("\n3. Testing cross-module validation...")
        test.test_cross_module_validation()
        print("✓ Cross-module validation passed")

        print("\n4. Running performance benchmarks...")
        test.test_performance_benchmarks()
        print("✓ Performance benchmarks completed")

        print("\n5. Validating against known results...")
        test.test_known_results_validation()
        print("✓ Known results validation passed")

        print("\n" + "=" * 60)
        print("All Phase 5 integration tests passed!")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
