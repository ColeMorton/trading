#!/usr/bin/env python3
"""
Phase 5: Complete Integration Validation

This script validates all concurrency calculation fixes are working together correctly.
"""

from datetime import datetime
import json
import os
from pathlib import Path
import sys


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables BEFORE imports
os.environ["USE_FIXED_RISK_CALC"] = "true"
os.environ["USE_FIXED_EXPECTANCY_CALC"] = "true"
os.environ["USE_FIXED_WIN_RATE_CALC"] = "true"
os.environ["USE_FIXED_SIGNAL_PROC"] = "true"

from app.concurrency.config_defaults import get_optimized_config_for_mstr
from app.concurrency.tools.runner import main as run_concurrency


class IntegrationValidator:
    """Validates all calculation fixes work together correctly."""

    def __init__(self):
        self.results = {}
        self.log = self._setup_logging()

    def _setup_logging(self):
        """Set up logging."""

        def log_func(msg, level="info"):
            print(f"[{level.upper()}] {msg}")

        return log_func

    def validate_json_output(self, json_path: Path) -> dict:
        """Validate JSON output from concurrency analysis."""
        if not json_path.exists():
            return {"valid": False, "error": f"JSON file not found: {json_path}"}

        with open(json_path) as f:
            data = json.load(f)

        results = {"valid": True, "checks": {}}

        # Check 1: Risk contributions sum to 100%
        total_risk = 0.0
        risk_contribs = []

        # Get strategies from JSON structure
        strategies = data.get("strategies", [])
        if not strategies:
            # Try alternative structure
            strategy_metrics = data.get("strategy_metrics", {})
            if strategy_metrics:
                strategies = list(strategy_metrics.values())

        for strategy in strategies:
            risk_contrib = strategy.get("risk_contribution", 0)
            risk_contribs.append(risk_contrib)
            total_risk += risk_contrib

        risk_valid = abs(total_risk - 1.0) < 1e-6 if total_risk > 0 else False
        results["checks"]["risk_contributions"] = {
            "valid": risk_valid,
            "total": total_risk,
            "individual": risk_contribs,
            "message": f"Total risk: {total_risk:.6f}",
        }

        # Check 2: Win rates are correctly calculated
        win_rate_issues = []
        for strategy in strategies:
            strategy_id = strategy.get("strategy_id", "Unknown")
            total_trades = strategy.get("total_trades", 0)
            winning_trades = strategy.get("winning_trades", 0)
            strategy.get("losing_trades", 0)
            win_rate = strategy.get("win_rate", 0)

            if total_trades > 0:
                expected_win_rate = winning_trades / total_trades
                if abs(win_rate - expected_win_rate) > 1e-6:
                    win_rate_issues.append(
                        {
                            "strategy": strategy_id,
                            "actual": win_rate,
                            "expected": expected_win_rate,
                        },
                    )

        results["checks"]["win_rates"] = {
            "valid": len(win_rate_issues) == 0,
            "issues": win_rate_issues,
        }

        # Check 3: Expectancy calculations
        expectancy_issues = []
        for strategy in strategies:
            strategy_id = strategy.get("strategy_id", "Unknown")
            win_rate = strategy.get("win_rate", 0)
            avg_win = strategy.get("avg_win", 0)
            avg_loss = strategy.get("avg_loss", 0)
            expectancy = strategy.get("expectancy", 0)

            expected_expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
            if abs(expectancy - expected_expectancy) > 1e-6:
                expectancy_issues.append(
                    {
                        "strategy": strategy_id,
                        "actual": expectancy,
                        "expected": expected_expectancy,
                    },
                )

        results["checks"]["expectancy"] = {
            "valid": len(expectancy_issues) == 0,
            "issues": expectancy_issues,
        }

        # Check 4: Signal counts are reasonable
        signal_issues = []
        for strategy in strategies:
            strategy_id = strategy.get("strategy_id", "Unknown")
            total_trades = strategy.get("total_trades", 0)

            # Basic sanity check - trades should be positive
            if total_trades < 0:
                signal_issues.append(
                    {
                        "strategy": strategy_id,
                        "issue": f"Negative trade count: {total_trades}",
                    },
                )

        results["checks"]["signals"] = {
            "valid": len(signal_issues) == 0,
            "issues": signal_issues,
        }

        # Overall validation
        results["valid"] = all(check["valid"] for check in results["checks"].values())

        return results

    def run_full_validation(self, portfolio_name: str = "trades_20250530.csv"):
        """Run full validation suite."""
        print("\nPhase 5: Integration Testing and Validation")
        print("=" * 60)

        # Get configuration
        config = get_optimized_config_for_mstr()
        config["PORTFOLIO"] = portfolio_name

        # Verify fixes are enabled
        print("\nConfiguration Status:")
        for fix in [
            "USE_FIXED_RISK_CALC",
            "USE_FIXED_EXPECTANCY_CALC",
            "USE_FIXED_WIN_RATE_CALC",
            "USE_FIXED_SIGNAL_PROC",
        ]:
            value = config.get(fix, False)
            env_value = os.environ.get(fix, "").lower() == "true"
            print(f"{fix}: Config={value}, Env={env_value}")

        # Run analysis
        print(f"\nRunning analysis on: {portfolio_name}")
        print("-" * 60)

        try:
            success = run_concurrency(config)

            if not success:
                print("✗ Analysis failed")
                return False

            print("✓ Analysis completed")

            # Validate output
            json_path = (
                project_root
                / "json"
                / "concurrency"
                / f"{Path(portfolio_name).stem}.json"
            )
            validation_results = self.validate_json_output(json_path)

            # Print validation results
            print("\nValidation Results:")
            print("-" * 60)

            for check_name, check_results in validation_results["checks"].items():
                status = "✓" if check_results["valid"] else "✗"
                print(f"\n{check_name.replace('_', ' ').title()}: {status}")

                if not check_results["valid"]:
                    if "message" in check_results:
                        print(f"  {check_results['message']}")
                    if check_results.get("issues"):
                        for issue in check_results["issues"][:5]:  # Show first 5 issues
                            print(f"  - {issue}")
                        if len(check_results["issues"]) > 5:
                            print(f"  ... and {len(check_results['issues']) - 5} more")

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
                        "portfolio": portfolio_name,
                        "config": {
                            k: v
                            for k, v in config.items()
                            if k.startswith("USE_FIXED_")
                        },
                        "validation_results": validation_results,
                        "success": validation_results["valid"],
                    },
                    f,
                    indent=2,
                )

            print(f"\nValidation report saved to: {report_path}")

            if validation_results["valid"]:
                print("\n✓ All validation checks passed!")
                print("\nIntegration Summary:")
                print("- Risk contributions correctly sum to 100%")
                print("- Win rates are accurately calculated")
                print("- Expectancy values are mathematically correct")
                print("- Signal processing is consistent")
                print(
                    "\nAll concurrency calculation fixes are working correctly together.",
                )
            else:
                print("\n✗ Some validation checks failed")
                print("Please review the issues above.")

            return validation_results["valid"]

        except Exception as e:
            print(f"\n✗ Error during validation: {e}")
            import traceback

            traceback.print_exc()
            return False


def main():
    """Run Phase 5 integration validation."""
    validator = IntegrationValidator()

    # Test with default portfolio
    success = validator.run_full_validation()

    if success:
        print("\n" + "=" * 60)
        print("PHASE 5 VALIDATION COMPLETE")
        print("All fixes are integrated and working correctly!")
        print("=" * 60)

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
