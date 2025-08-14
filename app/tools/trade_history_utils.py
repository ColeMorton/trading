"""
Trade History Utilities

Utility functions for working with trade history data across different formats and sources.
Provides standardized interfaces for common trade history operations.

Features:
- Position data validation and normalization
- Trade quality assessment algorithms
- Portfolio management utilities
- Data format conversion helpers
- Batch processing functions
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

# Add the parent directory to the Python path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import backward compatibility wrapper
from app.tools.position_service_wrapper import (
    TradingSystemConfig,
    add_position_to_portfolio,
    assess_trade_quality,
    create_position_record,
    get_config,
    validate_strategy_type,
    validate_ticker,
)

logger = logging.getLogger(__name__)


def validate_position_data(position: Dict[str, Any]) -> List[str]:
    """Validate position data and return list of validation errors."""
    errors = []

    # Required fields
    required_fields = [
        "Position_UUID",
        "Ticker",
        "Strategy_Type",
        "Short_Window",
        "Long_Window",
        "Entry_Timestamp",
        "Avg_Entry_Price",
        "Direction",
    ]

    for field in required_fields:
        if field not in position or position[field] is None:
            errors.append(f"Missing required field: {field}")

    # Validate ticker
    if "Ticker" in position and not validate_ticker(position["Ticker"]):
        errors.append(f"Invalid ticker format: {position['Ticker']}")

    # Validate strategy type
    if "Strategy_Type" in position and not validate_strategy_type(
        position["Strategy_Type"]
    ):
        errors.append(f"Invalid strategy type: {position['Strategy_Type']}")

    # Validate numeric fields
    numeric_fields = ["Short_Window", "Long_Window", "Avg_Entry_Price", "Position_Size"]
    for field in numeric_fields:
        if field in position and position[field] is not None:
            try:
                float(position[field])
                if field in ["Short_Window", "Long_Window"] and position[field] <= 0:
                    errors.append(f"{field} must be positive")
                if field == "Avg_Entry_Price" and position[field] <= 0:
                    errors.append(f"{field} must be positive")
            except (ValueError, TypeError):
                errors.append(f"{field} must be numeric")

    # Validate direction
    if "Direction" in position:
        valid_directions = ["Long", "Short"]
        if position["Direction"] not in valid_directions:
            errors.append(f"Direction must be one of: {valid_directions}")

    return errors


def normalize_position_data(position: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize position data to standard format."""
    normalized = position.copy()

    # Normalize ticker to uppercase
    if "Ticker" in normalized and normalized["Ticker"]:
        normalized["Ticker"] = str(normalized["Ticker"]).upper()

    # Normalize strategy type to uppercase
    if "Strategy_Type" in normalized and normalized["Strategy_Type"]:
        normalized["Strategy_Type"] = str(normalized["Strategy_Type"]).upper()

    # Normalize direction to title case
    if "Direction" in normalized and normalized["Direction"]:
        normalized["Direction"] = str(normalized["Direction"]).title()

    # Convert numeric fields
    numeric_fields = [
        "Short_Window",
        "Long_Window",
        "Signal_Window",
        "Avg_Entry_Price",
        "Avg_Exit_Price",
        "Position_Size",
        "PnL",
        "Return",
        "Duration_Days",
        "Max_Favourable_Excursion",
        "Max_Adverse_Excursion",
        "MFE_MAE_Ratio",
        "Exit_Efficiency",
        "Days_Since_Entry",
        "Current_Unrealized_PnL",
    ]

    for field in numeric_fields:
        if field in normalized and normalized[field] is not None:
            try:
                normalized[field] = float(normalized[field])
            except (ValueError, TypeError):
                normalized[field] = None

    # Convert integer fields
    integer_fields = [
        "Short_Window",
        "Long_Window",
        "Signal_Window",
        "Days_Since_Entry",
    ]
    for field in integer_fields:
        if field in normalized and normalized[field] is not None:
            try:
                normalized[field] = int(float(normalized[field]))
            except (ValueError, TypeError):
                normalized[field] = None

    return normalized


def get_portfolio_summary(
    portfolio_name: str, config: TradingSystemConfig = None
) -> Dict[str, Any]:
    """Get summary statistics for a portfolio."""
    if config is None:
        config = get_config()

    portfolio_file = config.get_portfolio_file(portfolio_name)
    if not portfolio_file.exists():
        return {"error": f"Portfolio {portfolio_name} not found"}

    df = pd.read_csv(portfolio_file)

    if df.empty:
        return {"total_positions": 0}

    # Basic counts
    total_positions = len(df)
    open_positions = len(df[df["Status"] == "Open"])
    closed_positions = len(df[df["Status"] == "Closed"])

    # Strategy breakdown
    strategy_counts = df["Strategy_Type"].value_counts().to_dict()

    # Trade quality breakdown
    quality_counts = {}
    if "Trade_Quality" in df.columns:
        quality_counts = df["Trade_Quality"].value_counts().to_dict()

    # Risk metrics for closed positions
    closed_df = df[df["Status"] == "Closed"].copy()
    risk_metrics = {}

    if not closed_df.empty and "Max_Favourable_Excursion" in closed_df.columns:
        mfe_col = closed_df["Max_Favourable_Excursion"].dropna()
        mae_col = closed_df["Max_Adverse_Excursion"].dropna()

        if not mfe_col.empty:
            risk_metrics = {
                "avg_mfe": float(mfe_col.mean()),
                "avg_mae": float(mae_col.mean()),
                "avg_mfe_mae_ratio": float((mfe_col / mae_col).mean())
                if not mae_col.empty
                else None,
            }

    # Performance metrics for closed positions
    performance_metrics = {}
    if not closed_df.empty and "Return" in closed_df.columns:
        returns = closed_df["Return"].dropna()
        if not returns.empty:
            performance_metrics = {
                "avg_return": float(returns.mean()),
                "win_rate": float((returns > 0).mean()),
                "total_return": float(returns.sum()),
            }

    summary = {
        "portfolio_name": portfolio_name,
        "total_positions": total_positions,
        "open_positions": open_positions,
        "closed_positions": closed_positions,
        "strategy_breakdown": strategy_counts,
        "trade_quality_breakdown": quality_counts,
        "risk_metrics": risk_metrics,
        "performance_metrics": performance_metrics,
        "last_updated": datetime.now().isoformat(),
    }

    return summary


def compare_portfolios(
    portfolio_names: List[str], config: TradingSystemConfig = None
) -> Dict[str, Any]:
    """Compare multiple portfolios and return comparative analysis."""
    if config is None:
        config = get_config()

    portfolios_data = {}

    for name in portfolio_names:
        summary = get_portfolio_summary(name, config)
        if "error" not in summary:
            portfolios_data[name] = summary

    if not portfolios_data:
        return {"error": "No valid portfolios found"}

    # Comparative metrics
    comparison = {
        "portfolios": portfolios_data,
        "comparison": {
            "total_positions": {
                name: data["total_positions"] for name, data in portfolios_data.items()
            },
            "win_rates": {},
            "avg_returns": {},
            "quality_distributions": {},
        },
    }

    # Extract win rates and returns
    for name, data in portfolios_data.items():
        perf = data.get("performance_metrics", {})
        comparison["comparison"]["win_rates"][name] = perf.get("win_rate")
        comparison["comparison"]["avg_returns"][name] = perf.get("avg_return")
        comparison["comparison"]["quality_distributions"][name] = data.get(
            "trade_quality_breakdown", {}
        )

    return comparison


def export_portfolio_summary(
    portfolio_name: str, output_file: str = None, config: TradingSystemConfig = None
):
    """Export portfolio summary to JSON file."""
    if config is None:
        config = get_config()

    summary = get_portfolio_summary(portfolio_name, config)

    if output_file is None:
        output_file = str(config.base_dir / f"{portfolio_name}_summary.json")

    import json

    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Portfolio summary exported to {output_file}")
    return output_file


def bulk_update_trade_quality(
    portfolio_name: str, config: TradingSystemConfig = None
) -> int:
    """Bulk update trade quality assessments for all positions in a portfolio."""
    if config is None:
        config = get_config()

    portfolio_file = config.get_portfolio_file(portfolio_name)
    if not portfolio_file.exists():
        logger.error(f"Portfolio {portfolio_name} not found")
        return 0

    df = pd.read_csv(portfolio_file)
    updated_count = 0

    for idx, row in df.iterrows():
        mfe = row.get("Max_Favourable_Excursion")
        mae = row.get("Max_Adverse_Excursion")
        exit_eff = row.get("Exit_Efficiency")
        return_pct = row.get("Return")

        if pd.notna(mfe) and pd.notna(mae):
            new_quality = assess_trade_quality(mfe, mae, exit_eff, return_pct)
            if new_quality != row.get("Trade_Quality", ""):
                df.at[idx, "Trade_Quality"] = new_quality
                updated_count += 1

    if updated_count > 0:
        df.to_csv(portfolio_file, index=False)
        logger.info(
            f"Updated trade quality for {updated_count} positions in {portfolio_name}"
        )

    return updated_count


def find_duplicate_positions(
    portfolio_name: str, config: TradingSystemConfig = None
) -> List[str]:
    """Find duplicate positions in a portfolio based on UUID."""
    if config is None:
        config = get_config()

    portfolio_file = config.get_portfolio_file(portfolio_name)
    if not portfolio_file.exists():
        logger.error(f"Portfolio {portfolio_name} not found")
        return []

    df = pd.read_csv(portfolio_file)

    # Find duplicate UUIDs
    duplicates = df[df.duplicated(subset=["Position_UUID"], keep=False)]

    if not duplicates.empty:
        duplicate_uuids = duplicates["Position_UUID"].unique().tolist()
        logger.warning(
            f"Found {len(duplicate_uuids)} duplicate position UUIDs in {portfolio_name}"
        )
        return duplicate_uuids

    return []


def remove_duplicate_positions(
    portfolio_name: str, config: TradingSystemConfig = None
) -> int:
    """Remove duplicate positions from a portfolio, keeping the first occurrence."""
    if config is None:
        config = get_config()

    portfolio_file = config.get_portfolio_file(portfolio_name)
    if not portfolio_file.exists():
        logger.error(f"Portfolio {portfolio_name} not found")
        return 0

    df = pd.read_csv(portfolio_file)
    original_count = len(df)

    # Remove duplicates based on Position_UUID, keeping first
    df_cleaned = df.drop_duplicates(subset=["Position_UUID"], keep="first")

    removed_count = original_count - len(df_cleaned)

    if removed_count > 0:
        df_cleaned.to_csv(portfolio_file, index=False)
        logger.info(
            f"Removed {removed_count} duplicate positions from {portfolio_name}"
        )

    return removed_count


def merge_portfolios(
    source_portfolios: List[str],
    target_portfolio: str,
    config: TradingSystemConfig = None,
) -> int:
    """Merge multiple portfolios into a target portfolio, handling duplicates."""
    if config is None:
        config = get_config()

    all_positions = []

    # Collect positions from all source portfolios
    for portfolio_name in source_portfolios:
        portfolio_file = config.get_portfolio_file(portfolio_name)
        if portfolio_file.exists():
            df = pd.read_csv(portfolio_file)
            all_positions.append(df)
            logger.info(f"Loaded {len(df)} positions from {portfolio_name}")

    if not all_positions:
        logger.warning("No valid source portfolios found")
        return 0

    # Combine all positions
    combined_df = pd.concat(all_positions, ignore_index=True)

    # Remove duplicates based on Position_UUID
    original_count = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=["Position_UUID"], keep="first")
    final_count = len(combined_df)

    # Save to target portfolio
    target_file = config.get_portfolio_file(target_portfolio)
    combined_df.to_csv(target_file, index=False)

    logger.info(f"Merged {original_count} positions into {target_portfolio}")
    logger.info(f"Removed {original_count - final_count} duplicates")
    logger.info(f"Final portfolio has {final_count} unique positions")

    return final_count


# Quick utility functions
def quick_add_position(
    ticker: str, strategy: str, short: int, long: int, portfolio: str = "live_signals"
) -> str:
    """Quick way to add a position with minimal parameters."""
    return add_position_to_portfolio(
        ticker=ticker,
        strategy_type=strategy,
        short_window=short,
        long_window=long,
        portfolio_name=portfolio,
    )


def list_portfolios(config: TradingSystemConfig = None) -> List[str]:
    """List all available portfolio files."""
    if config is None:
        config = get_config()

    positions_dir = config.positions_dir
    if not positions_dir.exists():
        return []

    csv_files = list(positions_dir.glob("*.csv"))
    portfolio_names = [f.stem for f in csv_files]

    return sorted(portfolio_names)


def get_position_by_uuid(
    uuid: str, portfolio_name: str = None, config: TradingSystemConfig = None
) -> Optional[Dict[str, Any]]:
    """Get a specific position by UUID from a portfolio or search all portfolios."""
    if config is None:
        config = get_config()

    portfolios_to_search = (
        [portfolio_name] if portfolio_name else list_portfolios(config)
    )

    for portfolio in portfolios_to_search:
        portfolio_file = config.get_portfolio_file(portfolio)
        if portfolio_file.exists():
            df = pd.read_csv(portfolio_file)
            matches = df[df["Position_UUID"] == uuid]
            if not matches.empty:
                position = matches.iloc[0].to_dict()
                position["_portfolio"] = portfolio
                return position

    return None


def main():
    """Main CLI entry point for trade history utilities."""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(
        description="Trade History Utilities - Portfolio management and analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get portfolio summary
  python %(prog)s --summary --portfolio live_signals

  # Compare portfolios
  python %(prog)s --compare --portfolios "live_signals,protected,risk_on"

  # Update trade quality
  python %(prog)s --update-quality --portfolio live_signals

  # Merge portfolios
  python %(prog)s --merge --source "portfolio1,portfolio2" --target "combined"

  # List all portfolios
  python %(prog)s --list-portfolios

  # Remove duplicates
  python %(prog)s --remove-duplicates --portfolio live_signals

  # Find position by UUID
  python %(prog)s --find-position --uuid "AAPL_SMA_20_50_20250101"
        """,
    )

    # Configuration options
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "--base-dir", type=str, help="Base directory for trading system"
    )
    config_group.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    config_group.add_argument("--debug", action="store_true", help="Debug mode")
    config_group.add_argument(
        "--health-check", action="store_true", help="Check system health"
    )

    # Main operations
    operations = parser.add_mutually_exclusive_group(required=True)
    operations.add_argument(
        "--summary", action="store_true", help="Get portfolio summary"
    )
    operations.add_argument(
        "--compare", action="store_true", help="Compare multiple portfolios"
    )
    operations.add_argument(
        "--update-quality", action="store_true", help="Update trade quality assessments"
    )
    operations.add_argument("--merge", action="store_true", help="Merge portfolios")
    operations.add_argument(
        "--list-portfolios", action="store_true", help="List all portfolios"
    )
    operations.add_argument(
        "--remove-duplicates", action="store_true", help="Remove duplicate positions"
    )
    operations.add_argument(
        "--find-duplicates", action="store_true", help="Find duplicate positions"
    )
    operations.add_argument(
        "--find-position", action="store_true", help="Find position by UUID"
    )
    operations.add_argument(
        "--export-summary", action="store_true", help="Export portfolio summary to JSON"
    )
    operations.add_argument(
        "--validate-portfolio", action="store_true", help="Validate portfolio data"
    )
    operations.add_argument(
        "--normalize-portfolio", action="store_true", help="Normalize portfolio data"
    )
    operations.add_argument(
        "--fix-quality", action="store_true", help="Fix data quality issues"
    )

    # Portfolio parameters
    portfolio_group = parser.add_argument_group("Portfolio Parameters")
    portfolio_group.add_argument("--portfolio", type=str, help="Portfolio name")
    portfolio_group.add_argument(
        "--portfolios", type=str, help="Comma-separated portfolio names"
    )
    portfolio_group.add_argument(
        "--source", type=str, help="Source portfolios for merge (comma-separated)"
    )
    portfolio_group.add_argument(
        "--target", type=str, help="Target portfolio for merge"
    )
    portfolio_group.add_argument("--uuid", type=str, help="Position UUID to find")
    portfolio_group.add_argument("--output", type=str, help="Output file path")

    args = parser.parse_args()

    # Configure logging
    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

    logger = logging.getLogger(__name__)

    try:
        # Set up configuration
        if args.base_dir:
            from app.tools.position_service_wrapper import TradingSystemConfig

            config = TradingSystemConfig(base_dir=args.base_dir)
            config.ensure_directories()
            logger.info(f"Using base directory: {config.base_dir}")

        # Health check
        if args.health_check:
            from app.tools.position_service_wrapper import get_config

            config = get_config()

            print("System Health Check:")
            print(f"✓ Base directory: {config.base_dir}")
            print(
                f"✓ Price data directory: {config.prices_dir} ({'exists' if config.prices_dir.exists() else 'missing'})"
            )
            print(
                f"✓ Positions directory: {config.positions_dir} ({'exists' if config.positions_dir.exists() else 'missing'})"
            )
            print(f"✓ Available portfolios: {len(list_portfolios())}")

            for portfolio in list_portfolios():
                summary = get_portfolio_summary(portfolio)
                print(f"  - {portfolio}: {summary.get('total_positions', 0)} positions")

            return 0

        # Handle operations
        if args.summary:
            if not args.portfolio:
                logger.error("Missing required argument: --portfolio")
                return 1

            summary = get_portfolio_summary(args.portfolio)

            if "error" in summary:
                print(f"Error: {summary['error']}")
                return 1

            print(f"\n{args.portfolio.upper()} PORTFOLIO SUMMARY")
            print("=" * (len(args.portfolio) + 18))
            print(f"Total positions: {summary.get('total_positions', 0)}")
            print(f"Open positions: {summary.get('open_positions', 0)}")
            print(f"Closed positions: {summary.get('closed_positions', 0)}")

            # Strategy breakdown
            strategies = summary.get("strategy_breakdown", {})
            if strategies:
                print(f"\nStrategy Breakdown:")
                for strategy, count in strategies.items():
                    print(f"  {strategy}: {count}")

            # Trade quality breakdown
            quality = summary.get("trade_quality_breakdown", {})
            if quality:
                print(f"\nTrade Quality:")
                for qual, count in quality.items():
                    print(f"  {qual}: {count}")

            # Performance metrics
            performance = summary.get("performance_metrics", {})
            if performance:
                print(f"\nPerformance Metrics:")
                if performance.get("win_rate") is not None:
                    print(f"  Win rate: {performance['win_rate']:.2%}")
                if performance.get("avg_return") is not None:
                    print(f"  Average return: {performance['avg_return']:.2%}")
                if performance.get("total_return") is not None:
                    print(f"  Total return: {performance['total_return']:.2%}")

            # Risk metrics
            risk = summary.get("risk_metrics", {})
            if risk:
                print(f"\nRisk Metrics:")
                if risk.get("avg_mfe") is not None:
                    print(f"  Average MFE: {risk['avg_mfe']:.2%}")
                if risk.get("avg_mae") is not None:
                    print(f"  Average MAE: {risk['avg_mae']:.2%}")
                if risk.get("avg_mfe_mae_ratio") is not None:
                    print(f"  Average MFE/MAE ratio: {risk['avg_mfe_mae_ratio']:.2f}")

        elif args.compare:
            if not args.portfolios:
                logger.error("Missing required argument: --portfolios")
                return 1

            portfolio_names = [name.strip() for name in args.portfolios.split(",")]
            comparison = compare_portfolios(portfolio_names)

            if "error" in comparison:
                print(f"Error: {comparison['error']}")
                return 1

            print("\nPORTFOLIO COMPARISON")
            print("=" * 20)

            # Total positions
            print("Total Positions:")
            for name, count in comparison["comparison"]["total_positions"].items():
                print(f"  {name}: {count}")

            # Win rates
            win_rates = comparison["comparison"]["win_rates"]
            if any(rate for rate in win_rates.values() if rate is not None):
                print("\nWin Rates:")
                for name, rate in win_rates.items():
                    if rate is not None:
                        print(f"  {name}: {rate:.2%}")

            # Average returns
            avg_returns = comparison["comparison"]["avg_returns"]
            if any(ret for ret in avg_returns.values() if ret is not None):
                print("\nAverage Returns:")
                for name, ret in avg_returns.items():
                    if ret is not None:
                        print(f"  {name}: {ret:.2%}")

        elif args.update_quality:
            if not args.portfolio:
                logger.error("Missing required argument: --portfolio")
                return 1

            updated = bulk_update_trade_quality(args.portfolio)
            print(f"Updated trade quality for {updated} positions in {args.portfolio}")

        elif args.merge:
            if not args.source or not args.target:
                logger.error("Missing required arguments: --source and --target")
                return 1

            source_portfolios = [name.strip() for name in args.source.split(",")]
            final_count = merge_portfolios(source_portfolios, args.target)
            print(f"Merged {len(source_portfolios)} portfolios into {args.target}")
            print(f"Final portfolio has {final_count} unique positions")

        elif args.list_portfolios:
            portfolios = list_portfolios()
            if portfolios:
                print("Available Portfolios:")
                for portfolio in portfolios:
                    summary = get_portfolio_summary(portfolio)
                    count = summary.get("total_positions", 0)
                    print(f"  {portfolio}: {count} positions")
            else:
                print("No portfolios found")

        elif args.remove_duplicates:
            if not args.portfolio:
                logger.error("Missing required argument: --portfolio")
                return 1

            removed = remove_duplicate_positions(args.portfolio)
            print(f"Removed {removed} duplicate positions from {args.portfolio}")

        elif args.find_duplicates:
            if not args.portfolio:
                logger.error("Missing required argument: --portfolio")
                return 1

            duplicates = find_duplicate_positions(args.portfolio)
            if duplicates:
                print(
                    f"Found {len(duplicates)} duplicate position UUIDs in {args.portfolio}:"
                )
                for uuid in duplicates:
                    print(f"  {uuid}")
            else:
                print(f"No duplicate positions found in {args.portfolio}")

        elif args.find_position:
            if not args.uuid:
                logger.error("Missing required argument: --uuid")
                return 1

            position = get_position_by_uuid(args.uuid, args.portfolio)
            if position:
                portfolio = position.pop("_portfolio")
                print(f"Found position {args.uuid} in portfolio: {portfolio}")
                print("Position details:")
                for key, value in position.items():
                    if value is not None and value != "":
                        print(f"  {key}: {value}")
            else:
                print(f"Position {args.uuid} not found")
                return 1

        elif args.export_summary:
            if not args.portfolio:
                logger.error("Missing required argument: --portfolio")
                return 1

            output_file = export_portfolio_summary(args.portfolio, args.output)
            print(f"Exported portfolio summary to: {output_file}")

        elif args.validate_portfolio:
            if not args.portfolio:
                logger.error("Missing required argument: --portfolio")
                return 1

            from app.tools.position_service_wrapper import get_config

            config = get_config()
            portfolio_file = config.get_portfolio_file(args.portfolio)

            if not portfolio_file.exists():
                print(f"Portfolio {args.portfolio} not found")
                return 1

            df = pd.read_csv(portfolio_file)
            total_errors = 0

            print(f"Validating {args.portfolio} portfolio ({len(df)} positions)...")

            for idx, row in df.iterrows():
                position = row.to_dict()
                errors = validate_position_data(position)
                if errors:
                    print(
                        f"Position {idx + 1} ({position.get('Position_UUID', 'No UUID')}):"
                    )
                    for error in errors:
                        print(f"  ✗ {error}")
                    total_errors += len(errors)

            if total_errors == 0:
                print(
                    f"✓ Portfolio {args.portfolio} validation passed - no errors found"
                )
            else:
                print(
                    f"✗ Portfolio {args.portfolio} validation failed - {total_errors} errors found"
                )
                return 1

        elif args.normalize_portfolio:
            if not args.portfolio:
                logger.error("Missing required argument: --portfolio")
                return 1

            from app.tools.position_service_wrapper import get_config

            config = get_config()
            portfolio_file = config.get_portfolio_file(args.portfolio)

            if not portfolio_file.exists():
                print(f"Portfolio {args.portfolio} not found")
                return 1

            df = pd.read_csv(portfolio_file)

            print(f"Normalizing {args.portfolio} portfolio ({len(df)} positions)...")

            normalized_positions = []
            for _, row in df.iterrows():
                position = row.to_dict()
                normalized = normalize_position_data(position)
                normalized_positions.append(normalized)

            # Save normalized data
            normalized_df = pd.DataFrame(normalized_positions)
            normalized_df.to_csv(portfolio_file, index=False)

            print(
                f"✓ Normalized {len(normalized_positions)} positions in {args.portfolio}"
            )

        elif args.fix_quality:
            if not args.portfolio:
                logger.error("Missing required argument: --portfolio")
                return 1

            # Run multiple quality fixes
            print(f"Fixing data quality issues in {args.portfolio}...")

            # Remove duplicates
            removed_dupes = remove_duplicate_positions(args.portfolio)
            if removed_dupes > 0:
                print(f"✓ Removed {removed_dupes} duplicate positions")

            # Update trade quality
            updated_quality = bulk_update_trade_quality(args.portfolio)
            if updated_quality > 0:
                print(f"✓ Updated trade quality for {updated_quality} positions")

            # Normalize data
            from app.tools.position_service_wrapper import get_config

            config = get_config()
            portfolio_file = config.get_portfolio_file(args.portfolio)

            if portfolio_file.exists():
                df = pd.read_csv(portfolio_file)
                normalized_positions = []
                for _, row in df.iterrows():
                    position = row.to_dict()
                    normalized = normalize_position_data(position)
                    normalized_positions.append(normalized)

                normalized_df = pd.DataFrame(normalized_positions)
                normalized_df.to_csv(portfolio_file, index=False)
                print(f"✓ Normalized {len(normalized_positions)} positions")

            print(f"✓ Quality fixes completed for {args.portfolio}")

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        if args.debug or args.verbose:
            logger.exception("Full error details:")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
