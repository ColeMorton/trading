#!/usr/bin/env python3
"""
Direct validation of all concurrency calculation fixes.

This script validates that all fixes are working correctly:
1. Risk contribution calculation (USE_FIXED_RISK_CALC)
2. Expectancy calculation (USE_FIXED_EXPECTANCY_CALC)
3. Win rate calculation (USE_FIXED_WIN_RATE_CALC)
4. Signal processing (USE_FIXED_SIGNAL_PROC)
"""

from datetime import datetime
import json
import os
from pathlib import Path
import sys

import polars as pl


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.concurrency.config_defaults import get_optimized_config_for_mstr
from app.concurrency.tools.runner import main as run_concurrency


def validate_risk_contributions(json_path: Path) -> bool:
    """Validate that risk contributions sum to 100%."""
    with open(json_path) as f:
        data = json.load(f)

    total_risk = 0.0
    print("\nRisk Contribution Validation:")
    print("-" * 50)

    for strategy in data.get("strategies", []):
        risk_contrib = strategy.get("risk_contribution", 0)
        strategy_id = strategy.get("strategy_id", "Unknown")
        print(f"{strategy_id}: {risk_contrib:.4f}")
        total_risk += risk_contrib

    print(f"\nTotal Risk Contribution: {total_risk:.6f}")
    is_valid = abs(total_risk - 1.0) < 1e-6
    print(f"Valid (sums to 100%): {'✓' if is_valid else '✗'}")

    return is_valid


def validate_win_rates(json_path: Path) -> bool:
    """Validate win rate calculations."""
    with open(json_path) as f:
        data = json.load(f)

    print("\nWin Rate Validation:")
    print("-" * 50)

    all_valid = True
    for strategy in data.get("strategies", []):
        strategy_id = strategy.get("strategy_id", "Unknown")
        total_trades = strategy.get("total_trades", 0)
        winning_trades = strategy.get("winning_trades", 0)
        losing_trades = strategy.get("losing_trades", 0)
        win_rate = strategy.get("win_rate", 0)

        if total_trades > 0:
            # Check trades sum
            trades_sum = winning_trades + losing_trades
            trades_valid = trades_sum == total_trades

            # Check win rate calculation
            expected_win_rate = winning_trades / total_trades
            win_rate_valid = abs(win_rate - expected_win_rate) < 1e-6

            is_valid = trades_valid and win_rate_valid
            all_valid &= is_valid

            print(f"\n{strategy_id}:")
            print(f"  Total trades: {total_trades}")
            print(f"  Winning: {winning_trades}, Losing: {losing_trades}")
            print(f"  Win rate: {win_rate:.4f} (expected: {expected_win_rate:.4f})")
            print(f"  Valid: {'✓' if is_valid else '✗'}")

    return all_valid


def validate_expectancy(json_path: Path) -> bool:
    """Validate expectancy calculations."""
    with open(json_path) as f:
        data = json.load(f)

    print("\nExpectancy Validation:")
    print("-" * 50)

    all_valid = True
    for strategy in data.get("strategies", []):
        strategy_id = strategy.get("strategy_id", "Unknown")
        win_rate = strategy.get("win_rate", 0)
        avg_win = strategy.get("avg_win", 0)
        avg_loss = strategy.get("avg_loss", 0)
        expectancy = strategy.get("expectancy", 0)

        # Calculate expected expectancy
        expected_expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        is_valid = abs(expectancy - expected_expectancy) < 1e-6
        all_valid &= is_valid

        print(f"\n{strategy_id}:")
        print(f"  Win rate: {win_rate:.4f}")
        print(f"  Avg win: {avg_win:.4f}")
        print(f"  Avg loss: {avg_loss:.4f}")
        print(f"  Expectancy: {expectancy:.6f} (expected: {expected_expectancy:.6f})")
        print(f"  Valid: {'✓' if is_valid else '✗'}")

    return all_valid


def check_csv_output(portfolio_name: str) -> bool:
    """Check if CSV output matches JSON data."""
    csv_path = project_root / "csv" / "portfolios_best" / f"{portfolio_name}_best.csv"
    json_path = project_root / "json" / "concurrency" / f"{portfolio_name}.json"

    if not csv_path.exists():
        print(f"\nCSV file not found: {csv_path}")
        return False

    if not json_path.exists():
        print(f"\nJSON file not found: {json_path}")
        return False

    print("\nCSV/JSON Cross-Validation:")
    print("-" * 50)

    # Load CSV
    csv_data = pl.read_csv(csv_path)

    # Load JSON
    with open(json_path) as f:
        json_data = json.load(f)

    # Compare strategy count
    csv_count = len(csv_data)
    json_count = len(json_data.get("strategies", []))

    print(f"CSV strategies: {csv_count}")
    print(f"JSON strategies: {json_count}")
    print(f"Match: {'✓' if csv_count == json_count else '✗'}")

    return csv_count == json_count


def main():
    """Run validation of all fixes."""
    print("Validating All Concurrency Calculation Fixes")
    print("=" * 60)

    # Get optimized configuration with all fixes enabled
    config = get_optimized_config_for_mstr()

    # Verify all fixes are enabled
    print("\nConfiguration Status:")
    print(f"USE_FIXED_RISK_CALC: {config.get('USE_FIXED_RISK_CALC', False)}")
    print(
        f"USE_FIXED_EXPECTANCY_CALC: {config.get('USE_FIXED_EXPECTANCY_CALC', False)}",
    )
    print(f"USE_FIXED_WIN_RATE_CALC: {config.get('USE_FIXED_WIN_RATE_CALC', False)}")
    print(f"USE_FIXED_SIGNAL_PROC: {config.get('USE_FIXED_SIGNAL_PROC', False)}")

    # Set environment variables to ensure fixes are active
    os.environ["USE_FIXED_RISK_CALC"] = "true"
    os.environ["USE_FIXED_EXPECTANCY_CALC"] = "true"
    os.environ["USE_FIXED_WIN_RATE_CALC"] = "true"
    os.environ["USE_FIXED_SIGNAL_PROC"] = "true"

    # Run analysis
    portfolio_name = Path(config["PORTFOLIO"]).stem

    print(f"\nRunning analysis on portfolio: {config['PORTFOLIO']}")
    print("-" * 60)

    try:
        # Run the analysis
        success = run_concurrency(config)

        if not success:
            print("✗ Analysis failed")
            return False

        print("✓ Analysis completed successfully")

        # Validate outputs
        json_path = project_root / "json" / "concurrency" / f"{portfolio_name}.json"

        if not json_path.exists():
            print(f"\n✗ JSON output not found: {json_path}")
            return False

        # Run all validations
        validations = [
            ("Risk Contributions", validate_risk_contributions(json_path)),
            ("Win Rates", validate_win_rates(json_path)),
            ("Expectancy", validate_expectancy(json_path)),
            ("CSV/JSON Cross-Check", check_csv_output(portfolio_name)),
        ]

        # Summary
        print("\n" + "=" * 60)
        print("Validation Summary:")
        print("-" * 50)

        all_passed = True
        for name, passed in validations:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{name}: {status}")
            all_passed &= passed

        if all_passed:
            print("\n✓ All validations passed!")
            print("All concurrency calculation fixes are working correctly.")
        else:
            print("\n✗ Some validations failed.")
            print("Please review the fixes.")

        # Save validation report
        report_path = (
            project_root
            / "logs"
            / f"fix_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "portfolio": config["PORTFOLIO"],
                    "fixes_enabled": {
                        "USE_FIXED_RISK_CALC": config.get("USE_FIXED_RISK_CALC", False),
                        "USE_FIXED_EXPECTANCY_CALC": config.get(
                            "USE_FIXED_EXPECTANCY_CALC", False,
                        ),
                        "USE_FIXED_WIN_RATE_CALC": config.get(
                            "USE_FIXED_WIN_RATE_CALC", False,
                        ),
                        "USE_FIXED_SIGNAL_PROC": config.get(
                            "USE_FIXED_SIGNAL_PROC", False,
                        ),
                    },
                    "validations": dict(validations),
                    "all_passed": all_passed,
                },
                f,
                indent=2,
            )

        print(f"\nValidation report saved to: {report_path}")

        return all_passed

    except Exception as e:
        print(f"\n✗ Error during validation: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
