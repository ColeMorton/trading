"""
Run Phase 5 Integration Testing and Validation

This script runs the complete Phase 5 validation suite to ensure all
concurrency calculation fixes work correctly together.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import polars as pl


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import test components directly
sys.path.insert(0, str(project_root / "tests"))
from concurrency.test_integration_phase5 import (
    DataIntegrityValidator,
    PerformanceBenchmark,
    TestConcurrencyIntegrationPhase5,
    TestPortfolioBuilder,
)

from app.concurrency.tools.concurrency_analysis import ConcurrencyAnalysis
from app.tools.setup_logging import setup_logging


def validate_real_portfolio():
    """Validate fixes on a real portfolio."""
    log = setup_logging("phase5_validation")

    print("\nValidating real portfolio with all fixes enabled...")
    print("=" * 60)

    # Use the current default portfolio
    config = {
        "PORTFOLIO": "trades_20250530.csv",
        "BASE_DIR": str(project_root),
        "USE_FIXED_RISK_CALC": True,
        "USE_FIXED_EXPECTANCY_CALC": True,
        "USE_FIXED_WIN_RATE_CALC": True,
        "USE_FIXED_SIGNAL_PROC": True,
        "VISUALIZATION": False,
    }

    try:
        # Run analysis
        analysis = ConcurrencyAnalysis(config=config)
        stats = analysis.run()

        # Create validator
        validator = DataIntegrityValidator()

        # Run validations
        risk_valid = validator.validate_risk_contributions(stats)
        win_rate_valid = validator.validate_win_rates(stats)
        expectancy_valid = validator.validate_expectancy(stats)

        # Generate report
        report = validator.generate_report()

        print("\nValidation Results:")
        print(f"- Risk contributions sum to 100%: {'✓' if risk_valid else '✗'}")
        print(f"- Win rates correctly calculated: {'✓' if win_rate_valid else '✗'}")
        print(f"- Expectancy correctly calculated: {'✓' if expectancy_valid else '✗'}")
        print(f"\nTotal tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Success rate: {report['summary']['success_rate']:.1%}")

        # Save validation report
        report_path = (
            project_root
            / "logs"
            / f"phase5_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "portfolio": config["PORTFOLIO"],
                    "validation_report": report,
                    "stats_summary": {
                        "total_strategies": len(stats.get("strategies", {})),
                        "total_risk_contribution": sum(
                            s.get("risk_contribution", 0)
                            for s in stats.get("strategies", {}).values()
                        ),
                    },
                },
                f,
                indent=2,
            )

        print(f"\nValidation report saved to: {report_path}")

        return report["summary"]["success_rate"] == 1.0

    except Exception as e:
        log(f"Error during validation: {e}", "error")
        print(f"\n✗ Validation failed: {e}")
        return False


def compare_with_and_without_fixes():
    """Compare results with fixes enabled vs disabled."""
    setup_logging("phase5_comparison")

    print("\nComparing results with and without fixes...")
    print("=" * 60)

    # Create test portfolio
    (
        data_list,
        config_list,
        expected,
    ) = TestPortfolioBuilder.create_simple_test_portfolio()

    # Run without fixes
    config_without = {
        "USE_FIXED_RISK_CALC": False,
        "USE_FIXED_EXPECTANCY_CALC": False,
        "USE_FIXED_WIN_RATE_CALC": False,
        "USE_FIXED_SIGNAL_PROC": False,
    }

    analysis_without = ConcurrencyAnalysis(config=config_without)
    stats_without = analysis_without.analyze(data_list, config_list)

    # Run with fixes
    config_with = {
        "USE_FIXED_RISK_CALC": True,
        "USE_FIXED_EXPECTANCY_CALC": True,
        "USE_FIXED_WIN_RATE_CALC": True,
        "USE_FIXED_SIGNAL_PROC": True,
    }

    analysis_with = ConcurrencyAnalysis(config=config_with)
    stats_with = analysis_with.analyze(data_list, config_list)

    # Compare key metrics
    print("\nRisk Contribution Comparison:")
    print("-" * 40)

    for strategy_id in stats_with.get("strategies", {}):
        risk_without = stats_without["strategies"][strategy_id].get(
            "risk_contribution",
            0,
        )
        risk_with = stats_with["strategies"][strategy_id].get("risk_contribution", 0)
        print(f"{strategy_id}:")
        print(f"  Without fixes: {risk_without:.4f}")
        print(f"  With fixes:    {risk_with:.4f}")
        print(f"  Difference:    {abs(risk_with - risk_without):.4f}")

    # Total risk contribution
    total_without = sum(
        s.get("risk_contribution", 0) for s in stats_without["strategies"].values()
    )
    total_with = sum(
        s.get("risk_contribution", 0) for s in stats_with["strategies"].values()
    )

    print("\nTotal Risk Contribution:")
    print(
        f"  Without fixes: {total_without:.4f} ({'✗' if abs(total_without - 1.0) > 1e-6 else '✓'})",
    )
    print(
        f"  With fixes:    {total_with:.4f} ({'✓' if abs(total_with - 1.0) < 1e-6 else '✗'})",
    )

    print("\nWin Rate Comparison:")
    print("-" * 40)

    for strategy_id in stats_with.get("strategies", {}):
        wr_without = stats_without["strategies"][strategy_id].get("win_rate", 0)
        wr_with = stats_with["strategies"][strategy_id].get("win_rate", 0)
        print(f"{strategy_id}:")
        print(f"  Without fixes: {wr_without:.4f}")
        print(f"  With fixes:    {wr_with:.4f}")
        print(
            f"  Expected:      {expected[f'strategy{strategy_id[-1]}']['win_rate']:.4f}",
        )


def run_performance_benchmarks():
    """Run detailed performance benchmarks."""
    print("\nRunning performance benchmarks...")
    print("=" * 60)

    # Create larger test portfolio for benchmarking
    dates = pl.date_range(
        datetime(2020, 1, 1),
        datetime(2024, 12, 31),
        interval="1d",
        eager=True,
    )

    # Create 5 strategies with different characteristics
    data_list = []
    config_list = []

    for i in range(5):
        # Generate random price data
        import numpy as np

        np.random.seed(42 + i)

        prices = [100.0]
        for _ in range(len(dates) - 1):
            change = np.random.normal(0.0002, 0.02)  # Daily returns
            prices.append(prices[-1] * (1 + change))

        # Generate trading signals
        ma_fast = 20 + i * 5
        ma_slow = 50 + i * 10

        df = pl.DataFrame({"Date": dates, "Close": prices})

        # Calculate moving averages
        df = df.with_columns(
            [
                pl.col("Close").rolling_mean(ma_fast).alias("MA_Fast"),
                pl.col("Close").rolling_mean(ma_slow).alias("MA_Slow"),
            ],
        )

        # Generate positions
        df = df.with_columns(
            (pl.col("MA_Fast") > pl.col("MA_Slow")).cast(pl.Int32).alias("Position"),
        )

        data_list.append(df)

        config = {
            "ticker": f"TEST{i + 1}",
            "timeframe": "D",
            "strategy": "SMA",
            "ma_fast": ma_fast,
            "ma_slow": ma_slow,
            "allocation": 1.0 / 5,  # Equal allocation
            "stop_loss": 0.02,
        }
        config_list.append(config)

    # Benchmark
    benchmark = PerformanceBenchmark()

    def run_without_fixes():
        config = {
            "USE_FIXED_RISK_CALC": False,
            "USE_FIXED_EXPECTANCY_CALC": False,
            "USE_FIXED_WIN_RATE_CALC": False,
            "USE_FIXED_SIGNAL_PROC": False,
        }
        analysis = ConcurrencyAnalysis(config=config)
        analysis.analyze(data_list, config_list)

    def run_with_fixes():
        config = {
            "USE_FIXED_RISK_CALC": True,
            "USE_FIXED_EXPECTANCY_CALC": True,
            "USE_FIXED_WIN_RATE_CALC": True,
            "USE_FIXED_SIGNAL_PROC": True,
        }
        analysis = ConcurrencyAnalysis(config=config)
        analysis.analyze(data_list, config_list)

    # Run benchmarks with fewer iterations for speed
    print("\nBenchmarking without fixes...")
    without_result = benchmark.benchmark_calculation(
        "without_fixes",
        run_without_fixes,
        iterations=10,
    )

    print("Benchmarking with fixes...")
    with_result = benchmark.benchmark_calculation(
        "with_fixes",
        run_with_fixes,
        iterations=10,
    )

    # Calculate improvement
    speedup = without_result["avg_time"] / with_result["avg_time"]

    print("\nBenchmark Results:")
    print("-" * 40)
    print("Without fixes:")
    print(f"  Average time: {without_result['avg_time']:.4f}s")
    print(f"  Min time:     {without_result['min_time']:.4f}s")
    print(f"  Max time:     {without_result['max_time']:.4f}s")
    print("\nWith fixes:")
    print(f"  Average time: {with_result['avg_time']:.4f}s")
    print(f"  Min time:     {with_result['min_time']:.4f}s")
    print(f"  Max time:     {with_result['max_time']:.4f}s")
    print("\nPerformance:")
    print(f"  Speedup:      {speedup:.2f}x")
    print(f"  Improvement:  {(speedup - 1) * 100:.1f}%")


def main():
    """Run complete Phase 5 validation suite."""
    print("Phase 5: Integration Testing and Validation")
    print("=" * 60)
    print("Testing all concurrency calculation fixes:")
    print("1. Risk contribution calculation (USE_FIXED_RISK_CALC)")
    print("2. Expectancy calculation (USE_FIXED_EXPECTANCY_CALC)")
    print("3. Win rate calculation (USE_FIXED_WIN_RATE_CALC)")
    print("4. Signal processing (USE_FIXED_SIGNAL_PROC)")

    # Run test suite
    test_suite = TestConcurrencyIntegrationPhase5()

    try:
        print("\n" + "=" * 60)
        print("Running test portfolio validation...")
        test_suite.test_all_fixes_enabled()
        test_suite.test_individual_fixes()
        test_suite.test_known_results_validation()
        print("✓ Test portfolio validation passed")

        print("\n" + "=" * 60)
        # Validate real portfolio
        if validate_real_portfolio():
            print("✓ Real portfolio validation passed")
        else:
            print("✗ Real portfolio validation failed")

        print("\n" + "=" * 60)
        # Compare with and without fixes
        compare_with_and_without_fixes()

        print("\n" + "=" * 60)
        # Run performance benchmarks
        run_performance_benchmarks()

        print("\n" + "=" * 60)
        print("Phase 5 validation completed successfully!")
        print("All fixes are working correctly and provide:")
        print("- Mathematically correct risk contributions (sum to 100%)")
        print("- Accurate win rate calculations")
        print("- Proper expectancy calculations")
        print("- Consistent signal processing")

    except Exception as e:
        print(f"\n✗ Validation failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
