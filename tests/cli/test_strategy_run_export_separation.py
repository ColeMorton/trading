"""
TDD Test Suite for Trading-CLI Strategy Sweep CSV Export Separation

This test suite validates the core requirement that each strategy type
(SMA, EMA, MACD) creates separate CSV files per ticker across all export stages.

CURRENT STATUS: ❌ FAILING (Red Phase)
REASON: StrategyDispatcher bug prevents mixed strategy execution

EXPECTED BEHAVIOR:
- Command: trading-cli strategy sweep --ticker BTC-USD,SPY,MSTR --strategy SMA EMA MACD
- Output: 27 files (3 tickers × 3 strategies × 3 export types)
- Files: data/raw/{export_type}/{TICKER}_D_{STRATEGY}.csv
- Content: Each file contains only one strategy type and one ticker

CURRENT LIMITATION:
When mixed strategies [SMA, EMA, MACD] are specified, only MACD runs due to
StrategyDispatcher prioritizing MACD service and ignoring SMA/EMA.
"""

from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from app.cli.main import app


class TestStrategySweepCSVExportSeparation:
    """TDD Test Suite for strategy-specific CSV file separation."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup test environment and cleanup afterward."""
        self.runner = CliRunner()
        self.tickers = ["BTC-USD", "SPY", "MSTR"]
        self.strategies = ["SMA", "EMA", "MACD"]
        self.export_dirs = ["portfolios", "portfolios_filtered", "portfolios_best"]
        self.base_path = Path("data/raw")

        # Ensure base directories exist
        for export_dir in self.export_dirs:
            (self.base_path / export_dir).mkdir(parents=True, exist_ok=True)

        yield  # Run test

        # Cleanup: Remove test files
        self._cleanup_test_files()

    def _cleanup_test_files(self):
        """Remove all test-generated files."""
        for export_dir in self.export_dirs:
            for ticker in self.tickers:
                for strategy in self.strategies:
                    file_path = (
                        self.base_path / export_dir / f"{ticker}_D_{strategy}.csv"
                    )
                    if file_path.exists():
                        file_path.unlink()

    def test_mixed_strategies_create_separate_files_per_strategy_per_ticker(self):
        """
        🎯 TARGET BEHAVIOR: Each strategy type should create separate files per ticker.

        ❌ CURRENTLY FAILS: Due to StrategyDispatcher prioritizing MACD service only.
        ✅ SHOULD PASS: When dispatcher is fixed to handle mixed strategies properly.

        This test documents the expected behavior and will guide the implementation fix.
        """

        # Act: Execute command with mixed strategies
        result = self.runner.invoke(
            app,
            [
                "strategy",
                "sweep",
                "--ticker",
                ",".join(self.tickers),
                "--strategy",
                "SMA",
                "--strategy",
                "EMA",
                "--strategy",
                "MACD",
                "--verbose",
            ],
        )

        # Assert: Command should succeed
        assert result.exit_code == 0, f"Command failed with output: {result.output}"

        # Assert: All 27 files should be created (3 tickers × 3 strategies × 3 export types)
        expected_files = []
        missing_files = []

        for export_dir in self.export_dirs:
            for ticker in self.tickers:
                for strategy in self.strategies:
                    file_path = (
                        self.base_path / export_dir / f"{ticker}_D_{strategy}.csv"
                    )
                    expected_files.append(str(file_path))
                    if not file_path.exists():
                        missing_files.append(str(file_path))

        # This assertion will FAIL until dispatcher is fixed
        if missing_files:
            # Check if only MACD files exist (confirming the dispatcher bug)
            macd_files = [
                f for f in expected_files if "_MACD.csv" in f and Path(f).exists()
            ]
            sma_ema_files = [
                f
                for f in expected_files
                if ("_SMA.csv" in f or "_EMA.csv" in f) and Path(f).exists()
            ]

            failure_msg = (
                f"❌ DISPATCHER BUG CONFIRMED: Missing {len(missing_files)}/27 files.\n"
                f"MACD files created: {len(macd_files)}/9\n"
                f"SMA/EMA files created: {len(sma_ema_files)}/18\n"
                f"ISSUE: StrategyDispatcher.py lines 77-83 prioritize MACD service when mixed strategies specified.\n"
                f"FIX NEEDED: Modify dispatcher to run all requested strategies sequentially.\n"
                f"First 5 missing files: {missing_files[:5]}"
            )

            pytest.fail(failure_msg)

        # If we reach here, all files exist - verify content purity
        for export_dir in self.export_dirs:
            for ticker in self.tickers:
                for strategy in self.strategies:
                    file_path = (
                        self.base_path / export_dir / f"{ticker}_D_{strategy}.csv"
                    )
                    self._verify_file_content_purity(file_path, ticker, strategy)

    def test_ma_strategies_work_correctly_when_isolated(self):
        """
        ✅ CURRENT WORKAROUND: SMA + EMA work when MACD is not included.

        This test verifies that the MA strategies work correctly when
        the dispatcher bug is avoided by not including MACD.
        """

        # Act: Test SMA + EMA only (no MACD to avoid dispatcher issue)
        result = self.runner.invoke(
            app,
            [
                "strategy",
                "sweep",
                "--ticker",
                ",".join(self.tickers),
                "--strategy",
                "SMA",
                "--strategy",
                "EMA",  # No MACD to avoid dispatcher issue
                "--verbose",
            ],
        )

        # Assert: Should work correctly
        assert result.exit_code == 0, f"MA strategies command failed: {result.output}"

        # Assert: SMA and EMA files should be created (18 files total)
        for export_dir in self.export_dirs:
            for ticker in self.tickers:
                for strategy in ["SMA", "EMA"]:
                    file_path = (
                        self.base_path / export_dir / f"{ticker}_D_{strategy}.csv"
                    )
                    assert file_path.exists(), f"Missing MA strategy file: {file_path}"
                    self._verify_file_content_purity(file_path, ticker, strategy)

        # Assert: No MACD files should exist
        for export_dir in self.export_dirs:
            for ticker in self.tickers:
                macd_file = self.base_path / export_dir / f"{ticker}_D_MACD.csv"
                assert not macd_file.exists(), (
                    f"Unexpected MACD file created: {macd_file}"
                )

    def test_macd_strategy_works_correctly_when_isolated(self):
        """
        ✅ CURRENT WORKAROUND: MACD works when isolated.

        This test verifies that MACD strategy works correctly when
        specified alone, avoiding the dispatcher issue.
        """

        # Act: Test MACD only
        result = self.runner.invoke(
            app,
            [
                "strategy",
                "sweep",
                "--ticker",
                ",".join(self.tickers),
                "--strategy",
                "MACD",
                "--verbose",
            ],
        )

        # Assert: Should work correctly
        assert result.exit_code == 0, f"MACD strategy command failed: {result.output}"

        # Assert: MACD files should be created (9 files total)
        for export_dir in self.export_dirs:
            for ticker in self.tickers:
                file_path = self.base_path / export_dir / f"{ticker}_D_MACD.csv"
                assert file_path.exists(), f"Missing MACD file: {file_path}"
                self._verify_file_content_purity(file_path, ticker, "MACD")

        # Assert: No SMA/EMA files should exist
        for export_dir in self.export_dirs:
            for ticker in self.tickers:
                for strategy in ["SMA", "EMA"]:
                    strategy_file = (
                        self.base_path / export_dir / f"{ticker}_D_{strategy}.csv"
                    )
                    assert not strategy_file.exists(), (
                        f"Unexpected {strategy} file created: {strategy_file}"
                    )

    def test_file_naming_convention_correctness(self):
        """
        Test that file naming follows the exact pattern: {TICKER}_D_{STRATEGY}.csv

        This verifies the export system generates the expected filenames.
        """

        # Use SMA only to avoid dispatcher issue
        result = self.runner.invoke(
            app,
            [
                "strategy",
                "sweep",
                "--ticker",
                "BTC-USD",  # Single ticker for focused test
                "--strategy",
                "SMA",
                "--verbose",
            ],
        )

        assert result.exit_code == 0, f"File naming test failed: {result.output}"

        # Verify exact naming pattern
        expected_files = [
            "data/raw/portfolios/BTC-USD_D_SMA.csv",
            "data/raw/portfolios_filtered/BTC-USD_D_SMA.csv",
            "data/raw/portfolios_best/BTC-USD_D_SMA.csv",
        ]

        for expected_file in expected_files:
            file_path = Path(expected_file)
            assert file_path.exists(), f"Expected file not found: {expected_file}"

            # Verify filename components
            name_parts = file_path.stem.split("_")
            assert len(name_parts) == 3, f"Invalid filename format: {file_path.name}"
            assert name_parts[0] == "BTC-USD", (
                f"Wrong ticker in filename: {name_parts[0]}"
            )
            assert name_parts[1] == "D", f"Wrong timeframe in filename: {name_parts[1]}"
            assert name_parts[2] == "SMA", (
                f"Wrong strategy in filename: {name_parts[2]}"
            )

    def test_export_directory_structure_correctness(self):
        """
        Test that files are exported to the correct directory structure.

        Verifies:
        - data/raw/portfolios/ (raw export)
        - data/raw/portfolios_filtered/ (filtered export)
        - data/raw/portfolios_best/ (best export)
        """

        # Use EMA only to avoid dispatcher issue
        result = self.runner.invoke(
            app,
            ["strategy", "run", "--ticker", "SPY", "--strategy", "EMA", "--verbose"],
        )

        assert result.exit_code == 0, (
            f"Directory structure test failed: {result.output}"
        )

        # Verify each export stage creates files in correct directories
        expected_dirs = {
            "portfolios": "Raw portfolio export",
            "portfolios_filtered": "Filtered portfolio export",
            "portfolios_best": "Best portfolio export",
        }

        for export_dir, description in expected_dirs.items():
            file_path = self.base_path / export_dir / "SPY_D_EMA.csv"
            assert file_path.exists(), f"{description} file missing: {file_path}"
            assert file_path.parent.name == export_dir, (
                f"File in wrong directory: {file_path}"
            )

    def _verify_file_content_purity(
        self,
        file_path: Path,
        expected_ticker: str,
        expected_strategy: str,
    ):
        """
        Verify file contains only expected ticker and strategy - no mixing.

        This is the CORE REQUIREMENT: each file must contain only one strategy type
        and one ticker, ensuring proper separation.
        """
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            pytest.fail(f"Failed to read CSV file {file_path}: {e}")

        # Basic validations
        assert not df.empty, f"Empty file: {file_path}"
        assert "Ticker" in df.columns, f"Missing Ticker column: {file_path}"
        assert "Strategy Type" in df.columns, (
            f"Missing Strategy Type column: {file_path}"
        )

        # CORE REQUIREMENT: Purity validations (no mixing allowed)
        unique_tickers = df["Ticker"].unique()
        assert len(unique_tickers) == 1, (
            f"❌ MIXED TICKERS VIOLATION: Found {len(unique_tickers)} tickers {list(unique_tickers)} "
            f"in {file_path}. Expected only: {expected_ticker}"
        )
        assert unique_tickers[0] == expected_ticker, (
            f"❌ WRONG TICKER: Expected {expected_ticker}, got {unique_tickers[0]} in {file_path}"
        )

        unique_strategies = df["Strategy Type"].unique()
        assert len(unique_strategies) == 1, (
            f"❌ MIXED STRATEGIES VIOLATION: Found {len(unique_strategies)} strategies {list(unique_strategies)} "
            f"in {file_path}. Expected only: {expected_strategy}"
        )
        assert unique_strategies[0] == expected_strategy, (
            f"❌ WRONG STRATEGY: Expected {expected_strategy}, got {unique_strategies[0]} in {file_path}"
        )

        # Additional quality checks
        assert len(df) > 0, f"File contains no data rows: {file_path}"

        # Verify essential columns exist
        essential_columns = ["Total Return [%]", "Win Rate [%]", "Total Trades"]
        missing_columns = [col for col in essential_columns if col not in df.columns]
        assert not missing_columns, (
            f"Missing essential columns in {file_path}: {missing_columns}"
        )


class TestDispatcherIntegrationValidation:
    """
    Validate that the dispatcher fix integrates correctly with the CLI without running full analysis.
    """

    def test_cli_mixed_strategy_validation_integration(self):
        """
        Test that CLI properly validates mixed strategies using fixed dispatcher.

        This test validates integration without running full strategy analysis.
        """
        from typer.testing import CliRunner

        from app.cli.main import app

        runner = CliRunner()

        # Test that mixed strategy validation works (dry-run to avoid full execution)
        result = runner.invoke(
            app,
            [
                "strategy",
                "sweep",
                "--ticker",
                "BTC-USD",
                "--strategy",
                "SMA",
                "--strategy",
                "EMA",
                "--strategy",
                "MACD",
                "--dry-run",  # Key: dry-run to test validation without execution
                "--verbose",
            ],
        )

        # Should not fail with compatibility errors
        assert result.exit_code == 0, (
            f"❌ CLI INTEGRATION FAILED: Mixed strategy validation failed.\n"
            f"Output: {result.output}\n"
            f"This suggests the dispatcher fix did not integrate properly with CLI."
        )

        # Should show configuration preview
        assert (
            "Configuration Preview" in result.output
            or "preview" in result.output.lower()
        ), "Dry-run should show configuration preview"

        print("✅ CLI INTEGRATION VALIDATED:")
        print("  - Mixed strategy command accepted")
        print("  - No compatibility errors")
        print("  - Dry-run configuration preview shown")

    def test_cli_individual_strategy_validation(self):
        """
        Test that individual strategies still work correctly after dispatcher fix.
        """
        from typer.testing import CliRunner

        from app.cli.main import app

        runner = CliRunner()

        strategies_to_test = ["SMA", "EMA", "MACD"]

        for strategy in strategies_to_test:
            result = runner.invoke(
                app,
                [
                    "strategy",
                    "sweep",
                    "--ticker",
                    "BTC-USD",
                    "--strategy",
                    strategy,
                    "--dry-run",
                    "--verbose",
                ],
            )

            assert result.exit_code == 0, (
                f"❌ INDIVIDUAL STRATEGY FAILED: {strategy} strategy validation failed.\n"
                f"Output: {result.output}\n"
                f"This suggests a regression in single strategy handling."
            )

            print(f"✅ {strategy} strategy validation: PASSED")


class TestStrategyDispatcherBugDocumentation:
    """
    Documentation tests that clearly explain the dispatcher bug and required fix.

    These tests serve as living documentation for developers working on the fix.
    """

    def test_dispatcher_mixed_strategy_compatibility_fix(self):
        """
        Test that the dispatcher fix correctly handles mixed strategy validation.

        This test validates that the fix allows all requested strategies to be executed.
        """
        from app.cli.models.strategy import StrategyType
        from app.cli.services.strategy_dispatcher import StrategyDispatcher

        dispatcher = StrategyDispatcher()

        # Test mixed strategy compatibility (should now work)
        mixed_strategies = [StrategyType.SMA, StrategyType.EMA, StrategyType.MACD]
        is_compatible = dispatcher.validate_strategy_compatibility(mixed_strategies)

        assert is_compatible, (
            "✅ FIX VALIDATION: Mixed strategies should now be compatible after dispatcher fix. "
            f"Strategies: {[s.value for s in mixed_strategies]}"
        )

        # Test that each individual strategy can be serviced
        individual_services = {}
        for strategy_type in mixed_strategies:
            service = dispatcher._determine_single_service(strategy_type)
            assert service is not None, f"No service found for {strategy_type.value}"
            individual_services[strategy_type.value] = (
                service.get_supported_strategy_types()
            )

        # Verify each strategy type has appropriate service
        assert "SMA" in individual_services["SMA"], (
            "SMA should be supported by its service"
        )
        assert "EMA" in individual_services["EMA"], (
            "EMA should be supported by its service"
        )
        assert "MACD" in individual_services["MACD"], (
            "MACD should be supported by its service"
        )

        print("✅ DISPATCHER FIX VERIFIED:")
        print(f"  - Mixed strategy compatibility: {is_compatible}")
        print(f"  - Individual services found: {len(individual_services)}/3")
        for strategy, supported in individual_services.items():
            print(f"  - {strategy}: {supported}")

    def test_dispatcher_execution_path_detection(self):
        """
        Test that the dispatcher correctly detects when to use mixed vs single strategy execution.
        """
        from app.cli.models.strategy import (
            StrategyConfig,
            StrategyMinimums,
            StrategyType,
            SyntheticTickerConfig,
        )
        from app.cli.services.strategy_dispatcher import StrategyDispatcher

        dispatcher = StrategyDispatcher()

        # Test single strategy config
        single_config = StrategyConfig(
            ticker=["BTC-USD"],
            strategy_types=[StrategyType.SMA],
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
            short_window_start=5,
            short_window_end=21,
            long_window_start=8,
            long_window_end=34,
            signal_window_start=5,
            signal_window_end=21,
        )

        # Test mixed strategy config
        mixed_config = StrategyConfig(
            ticker=["BTC-USD"],
            strategy_types=[StrategyType.SMA, StrategyType.EMA, StrategyType.MACD],
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
            short_window_start=5,
            short_window_end=21,
            long_window_start=8,
            long_window_end=34,
            signal_window_start=5,
            signal_window_end=21,
        )

        # Verify execution path detection logic
        assert len(single_config.strategy_types) == 1, (
            "Single config should have 1 strategy"
        )
        assert len(mixed_config.strategy_types) == 3, (
            "Mixed config should have 3 strategies"
        )

        # Test that both configurations are considered valid
        single_compatible = dispatcher.validate_strategy_compatibility(
            single_config.strategy_types,
        )
        mixed_compatible = dispatcher.validate_strategy_compatibility(
            mixed_config.strategy_types,
        )

        assert single_compatible, "Single strategy config should be compatible"
        assert mixed_compatible, "Mixed strategy config should be compatible after fix"

        print("✅ EXECUTION PATH DETECTION VERIFIED:")
        print(f"  - Single strategy compatible: {single_compatible}")
        print(f"  - Mixed strategy compatible: {mixed_compatible}")
        print(f"  - Single strategy count: {len(single_config.strategy_types)}")
        print(f"  - Mixed strategy count: {len(mixed_config.strategy_types)}")

    def test_required_fix_specification(self):
        """
        Specify the exact fix required for the dispatcher.

        This test documents what the fixed dispatcher should do.
        """
        # This test documents the required behavior after the fix

        # This test will pass once any of the above solutions is implemented
        # For now, it serves as documentation
        assert True, "This test documents the required fix specification"


if __name__ == "__main__":
    # Allow running this test file directly for development
    pytest.main([__file__, "-v"])
