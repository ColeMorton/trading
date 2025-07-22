#!/usr/bin/env python3
"""
Test Script for Raw Data Export Functionality

This script tests the raw data export system to ensure it works correctly
with the existing portfolio review infrastructure.
"""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

try:
    from contexts.portfolio.services.portfolio_data_export_service import (
        DataType,
        ExportConfig,
        ExportFormat,
        ExportResults,
        PortfolioDataExportService,
    )

    print("✓ Successfully imported PortfolioDataExportService")
except ImportError as e:
    print(f"✗ Failed to import PortfolioDataExportService: {e}")
    sys.exit(1)

try:
    import vectorbt as vbt

    print("✓ VectorBT is available")
except ImportError:
    print("✗ VectorBT not available - installing with: pip install vectorbt")
    sys.exit(1)


def create_mock_portfolio():
    """Create a simple mock VectorBT portfolio for testing."""
    print("Creating mock portfolio for testing...")

    # Create simple price data
    dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")
    np.random.seed(42)  # For reproducible results
    prices = 100 * np.cumprod(1 + np.random.normal(0.001, 0.02, len(dates)))

    price_data = pd.Series(prices, index=dates, name="Close")

    # Create simple signals (buy when price crosses above 20-day MA, sell when below)
    ma_20 = price_data.rolling(20).mean()
    entries = (price_data > ma_20) & (price_data.shift(1) <= ma_20.shift(1))
    exits = (price_data < ma_20) & (price_data.shift(1) >= ma_20.shift(1))

    # Create portfolio
    portfolio = vbt.Portfolio.from_signals(
        close=price_data, entries=entries, exits=exits, init_cash=10000, fees=0.001
    )

    print(f"✓ Created mock portfolio with {len(price_data)} data points")
    return portfolio


def test_export_service():
    """Test the export service functionality."""
    print("\n" + "=" * 50)
    print("TESTING RAW DATA EXPORT SERVICE")
    print("=" * 50)

    # Create mock portfolio
    portfolio = create_mock_portfolio()

    # Create temporary directory for exports
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")

        # Test 1: Basic export with all data types
        print("\n--- Test 1: Basic Export (All Data Types) ---")
        config = ExportConfig(
            output_dir=temp_dir,
            export_formats=[ExportFormat.CSV, ExportFormat.JSON],
            data_types=[DataType.ALL],
            include_vectorbt_object=True,
        )

        service = PortfolioDataExportService(config)
        results = service.export_portfolio_data(portfolio, "test_portfolio")

        if results.success:
            print(f"✓ Basic export successful: {results.total_files} files exported")
            for data_type, files in results.exported_files.items():
                print(f"  - {data_type}: {len(files)} files")
        else:
            print(f"✗ Basic export failed: {results.error_message}")
            return False

        # Test 2: Selective export
        print("\n--- Test 2: Selective Export ---")
        config2 = ExportConfig(
            output_dir=temp_dir,
            export_formats=[ExportFormat.CSV],
            data_types=[DataType.PORTFOLIO_VALUE, DataType.RETURNS, DataType.TRADES],
            include_vectorbt_object=False,
            filename_prefix="selective_test",
        )

        service2 = PortfolioDataExportService(config2)
        results2 = service2.export_portfolio_data(portfolio, "test_portfolio_selective")

        if results2.success:
            print(
                f"✓ Selective export successful: {results2.total_files} files exported"
            )
        else:
            print(f"✗ Selective export failed: {results2.error_message}")
            return False

        # Test 3: Verify file contents
        print("\n--- Test 3: File Content Verification ---")

        # Check portfolio value file
        portfolio_value_files = [
            f
            for f in results.exported_files.get("portfolio_value", [])
            if f.endswith(".csv")
        ]
        if portfolio_value_files:
            pv_file = portfolio_value_files[0]
            try:
                df = pd.read_csv(pv_file)
                required_columns = ["Date", "Portfolio_Value", "Normalized_Value"]
                if all(col in df.columns for col in required_columns):
                    print(f"✓ Portfolio value file structure correct: {len(df)} rows")
                else:
                    print(
                        f"✗ Portfolio value file missing columns: {df.columns.tolist()}"
                    )
                    return False
            except Exception as e:
                print(f"✗ Error reading portfolio value file: {e}")
                return False

        # Check statistics file
        stats_files = [
            f
            for f in results.exported_files.get("statistics", [])
            if f.endswith(".csv")
        ]
        if stats_files:
            stats_file = stats_files[0]
            try:
                df = pd.read_csv(stats_file)
                if "Metric" in df.columns and "Value" in df.columns and len(df) > 0:
                    print(f"✓ Statistics file structure correct: {len(df)} metrics")
                else:
                    print(
                        f"✗ Statistics file structure incorrect: {df.columns.tolist()}"
                    )
                    return False
            except Exception as e:
                print(f"✗ Error reading statistics file: {e}")
                return False

        # Test 4: VectorBT object loading
        print("\n--- Test 4: VectorBT Object Loading ---")
        vectorbt_files = [
            f
            for f in results.exported_files.get("vectorbt_object", [])
            if f.endswith(".pickle")
        ]
        if vectorbt_files:
            try:
                loaded_portfolio = service.load_vectorbt_portfolio(vectorbt_files[0])
                if hasattr(loaded_portfolio, "value") and hasattr(
                    loaded_portfolio, "stats"
                ):
                    print("✓ VectorBT object loaded successfully")

                    # Compare some basic stats
                    original_stats = portfolio.stats()
                    loaded_stats = loaded_portfolio.stats()
                    if (
                        abs(
                            original_stats["Total Return [%]"]
                            - loaded_stats["Total Return [%]"]
                        )
                        < 0.01
                    ):
                        print("✓ Loaded portfolio matches original")
                    else:
                        print("✗ Loaded portfolio differs from original")
                        return False
                else:
                    print("✗ Loaded object is not a valid VectorBT portfolio")
                    return False
            except Exception as e:
                print(f"✗ Error loading VectorBT object: {e}")
                return False

        print(f"\n✓ All tests passed! Export service is working correctly.")
        return True


def test_cli_integration():
    """Test CLI integration by checking imports and configuration models."""
    print("\n" + "=" * 50)
    print("TESTING CLI INTEGRATION")
    print("=" * 50)

    try:
        from cli.models.portfolio import (
            RawDataExportConfig,
            RawDataExportFormat,
            RawDataType,
        )

        print("✓ CLI models imported successfully")

        # Test creating a CLI config
        cli_config = RawDataExportConfig(
            enable=True,
            export_formats=[RawDataExportFormat.CSV, RawDataExportFormat.JSON],
            data_types=[RawDataType.ALL],
            include_vectorbt_object=True,
        )
        print("✓ CLI configuration created successfully")
        return True

    except ImportError as e:
        print(f"✗ CLI integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Raw Data Export System Test Suite")
    print("=================================")

    test_results = []

    # Test export service
    test_results.append(test_export_service())

    # Test CLI integration
    test_results.append(test_cli_integration())

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    passed_tests = sum(test_results)
    total_tests = len(test_results)

    if passed_tests == total_tests:
        print(f"✓ All {total_tests} tests passed!")
        print("\nThe raw data export system is ready for use.")
        print("\nTo use the system:")
        print("1. Run: trading-cli portfolio review --ticker SYMBOL --export-raw-data")
        print("2. Check data/outputs/portfolio_review/raw_data/ for exported files")
        print("3. Use the example_custom_charts.py script to generate custom charts")
        return True
    else:
        print(f"✗ {total_tests - passed_tests} of {total_tests} tests failed!")
        print("\nPlease check the error messages above and fix any issues.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
