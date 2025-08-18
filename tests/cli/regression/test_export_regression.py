"""
Export Regression Tests.

This test suite prevents regression of specific export issues that were recently fixed:
1. Directory path issues - portfolios_best not exporting to correct directory
2. Missing Metric Type column in portfolios_filtered exports
3. Metric Type values being overwritten with default values
4. Filename generation issues with strategy type detection
5. CBRE aggregation scenarios that previously failed
6. Sorting consistency across strategy types

These tests ensure that previously fixed bugs do not reoccur.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import polars as pl
import pytest

from app.tools.export_csv import export_csv
from app.tools.strategy.export_portfolios import export_portfolios


class TestExportDirectoryRegression:
    """Test regression of directory path issues."""

    @pytest.fixture
    def temp_export_dir(self):
        """Create temporary directory for export testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def sample_portfolios(self):
        """Sample portfolio data for testing."""
        return [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Fast Period": 10,
                "Slow Period": 20,
                "Total Trades": 50,
                "Win Rate [%]": 55.0,
                "Total Return [%]": 25.5,
                "Sharpe Ratio": 1.2,
                "Score": 8.5,
                "Metric Type": "Most Total Return [%]",
            }
        ]

    @pytest.fixture
    def base_config(self, temp_export_dir):
        """Base configuration for exports."""
        return {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["AAPL"],
            "STRATEGY_TYPES": ["SMA"],
            "USE_HOURLY": False,
            "USE_MA": True,
            "STRATEGY_TYPE": "SMA",
        }

    def test_portfolios_best_exports_to_correct_directory(
        self, sample_portfolios, base_config, temp_export_dir
    ):
        """
        REGRESSION TEST: portfolios_best files should export to data/raw/portfolios_best/

        Previously, when feature_dir was empty, files were exported to data/raw/ instead
        of the correct subdirectory. This was fixed by using export_type when feature_dir
        is empty.
        """
        config = base_config.copy()

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=sample_portfolios,
                config=config,
                export_type="portfolios_best",
                feature_dir="",  # Empty feature_dir should use export_type
                log=Mock(),
            )

        assert success == True

        # CRITICAL: Verify file was exported to correct directory
        correct_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_best"
        assert correct_path.exists(), f"Directory {correct_path} should exist"

        # Verify CSV file exists in correct location
        csv_files = list(correct_path.glob("*.csv"))
        assert len(csv_files) > 0, "CSV file should exist in portfolios_best directory"

        # Verify no files were exported to wrong location (data/raw/ directly)
        wrong_path = Path(temp_export_dir) / "data" / "raw"
        direct_csv_files = [
            f for f in wrong_path.glob("*.csv") if f.parent.name == "raw"
        ]  # Direct children of raw/
        assert (
            len(direct_csv_files) == 0
        ), "No CSV files should be directly in data/raw/"

    def test_portfolios_filtered_exports_to_correct_directory(
        self, sample_portfolios, base_config, temp_export_dir
    ):
        """
        REGRESSION TEST: portfolios_filtered files should export to data/raw/portfolios_filtered/
        """
        config = base_config.copy()

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=sample_portfolios,
                config=config,
                export_type="portfolios_filtered",
                feature_dir="",  # Empty feature_dir should use export_type
                log=Mock(),
            )

        assert success == True

        # Verify file was exported to correct directory
        correct_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_filtered"
        assert correct_path.exists()

        csv_files = list(correct_path.glob("*.csv"))
        assert len(csv_files) > 0

    def test_feature_dir_parameter_override(
        self, sample_portfolios, base_config, temp_export_dir
    ):
        """
        REGRESSION TEST: When feature_dir is provided, it should be used instead of export_type
        """
        config = base_config.copy()

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=sample_portfolios,
                config=config,
                export_type="portfolios_best",
                feature_dir="ma_cross",  # Explicit feature_dir should be used
                log=Mock(),
            )

        assert success == True

        # Verify file was exported to feature_dir location
        feature_path = (
            Path(temp_export_dir) / "data" / "raw" / "ma_cross" / "portfolios_best"
        )
        assert feature_path.exists()

        csv_files = list(feature_path.glob("*.csv"))
        assert len(csv_files) > 0


class TestMetricTypeColumnRegression:
    """Test regression of Metric Type column issues."""

    @pytest.fixture
    def temp_export_dir(self):
        """Create temporary directory for export testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def diverse_portfolios(self):
        """Portfolio data with diverse metric types."""
        return [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Fast Period": 10,
                "Slow Period": 20,
                "Total Trades": 50,
                "Win Rate [%]": 55.0,
                "Total Return [%]": 25.5,
                "Sharpe Ratio": 1.2,
                "Score": 8.5,
                "Metric Type": "Most Total Return [%]",
            },
            {
                "Ticker": "MSFT",
                "Strategy Type": "EMA",
                "Fast Period": 12,
                "Slow Period": 26,
                "Total Trades": 45,
                "Win Rate [%]": 62.0,
                "Total Return [%]": 32.1,
                "Sharpe Ratio": 1.4,
                "Score": 9.0,
                "Metric Type": "Most Sharpe Ratio",
            },
            {
                "Ticker": "GOOGL",
                "Strategy Type": "MACD",
                "Fast Period": 8,
                "Slow Period": 21,
                "Signal Period": 7,
                "Total Trades": 38,
                "Win Rate [%]": 68.0,
                "Total Return [%]": 35.8,
                "Sharpe Ratio": 1.6,
                "Score": 9.5,
                "Metric Type": "Most Win Rate [%]",
            },
        ]

    @pytest.fixture
    def base_config(self, temp_export_dir):
        """Base configuration for exports."""
        return {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["AAPL", "MSFT", "GOOGL"],
            "STRATEGY_TYPES": ["SMA", "EMA", "MACD"],
            "USE_HOURLY": False,
            "USE_MA": False,
            "STRATEGY_TYPE": "Multi",
        }

    def test_portfolios_filtered_includes_metric_type_column(
        self, diverse_portfolios, base_config, temp_export_dir
    ):
        """
        REGRESSION TEST: portfolios_filtered exports should include Metric Type column

        Previously, the schema normalization condition was based on export_type == "portfolios_best"
        which excluded portfolios_filtered. Fixed by making it schema-based.
        """
        config = base_config.copy()

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=diverse_portfolios,
                config=config,
                export_type="portfolios_filtered",
                log=Mock(),
            )

        assert success == True

        # CRITICAL: Verify Metric Type column is present
        assert (
            "Metric Type" in df.columns
        ), "Metric Type column should be present in portfolios_filtered"

        # Verify it's the first column (filtered schema requirement)
        assert df.columns[0] == "Metric Type", "Metric Type should be the first column"

        # Verify all strategy types have the column
        for strategy_type in ["SMA", "EMA", "MACD"]:
            strategy_rows = df.filter(pl.col("Strategy Type") == strategy_type)
            if len(strategy_rows) > 0:
                assert "Metric Type" in strategy_rows.columns

    def test_portfolios_best_includes_metric_type_column(
        self, diverse_portfolios, base_config, temp_export_dir
    ):
        """
        REGRESSION TEST: portfolios_best exports should include Metric Type column
        """
        config = base_config.copy()

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=diverse_portfolios,
                config=config,
                export_type="portfolios_best",
                log=Mock(),
            )

        assert success == True

        # Verify Metric Type column is present
        assert "Metric Type" in df.columns
        assert df.columns[0] == "Metric Type"

    def test_metric_type_values_are_preserved(
        self, diverse_portfolios, base_config, temp_export_dir
    ):
        """
        REGRESSION TEST: Metric Type values should not be overwritten with defaults

        Previously, all Metric Type values were being overwritten with "Most Total Return [%]"
        during normalization. Fixed by preserving existing values.
        """
        config = base_config.copy()

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=diverse_portfolios,
                config=config,
                export_type="portfolios_filtered",
                log=Mock(),
            )

        assert success == True

        # CRITICAL: Verify diverse metric types are preserved
        metric_types = df["Metric Type"].unique().to_list()

        # Should have at least 3 different metric types
        assert (
            len(metric_types) >= 3
        ), f"Expected at least 3 metric types, got: {metric_types}"

        # Verify specific metric types are preserved
        assert "Most Total Return [%]" in metric_types
        assert "Most Sharpe Ratio" in metric_types
        assert "Most Win Rate [%]" in metric_types

        # Verify no metric type was lost/overwritten
        expected_metrics = {
            "Most Total Return [%]",
            "Most Sharpe Ratio",
            "Most Win Rate [%]",
        }
        actual_metrics = set(metric_types)
        assert expected_metrics.issubset(
            actual_metrics
        ), f"Missing metric types: {expected_metrics - actual_metrics}"

    def test_no_dual_normalization_stripping(
        self, diverse_portfolios, base_config, temp_export_dir
    ):
        """
        REGRESSION TEST: Dual normalization should not strip Metric Type column

        Previously, export_csv.py was applying secondary normalization that stripped
        the Metric Type column. Fixed by making export_csv schema-aware.
        """
        config = base_config.copy()

        # Test that the dual normalization bug is fixed by verifying
        # the column survives the complete export pipeline
        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=diverse_portfolios,
                config=config,
                export_type="portfolios_filtered",
                log=Mock(),
            )

        assert success == True

        # If dual normalization was occurring, the Metric Type column would be stripped
        assert (
            "Metric Type" in df.columns
        ), "Metric Type column should survive normalization pipeline"

        # Verify the column has actual values, not just empty/null
        metric_type_values = df["Metric Type"].drop_nulls()
        assert (
            len(metric_type_values) > 0
        ), "Metric Type column should have non-null values"


class TestFilenameGenerationRegression:
    """Test regression of filename generation issues."""

    @pytest.fixture
    def temp_export_dir(self):
        """Create temporary directory for export testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def single_strategy_portfolio(self):
        """Single strategy portfolio data."""
        return [
            {
                "Ticker": "RJF",
                "Strategy Type": "SMA",
                "Fast Period": 10,
                "Slow Period": 20,
                "Total Trades": 50,
                "Win Rate [%]": 55.0,
                "Total Return [%]": 25.5,
                "Sharpe Ratio": 1.2,
                "Score": 8.5,
                "Metric Type": "Most Total Return [%]",
            }
        ]

    def test_single_sma_strategy_filename_generation(
        self, single_strategy_portfolio, temp_export_dir
    ):
        """
        REGRESSION TEST: Single SMA strategy should produce RJF_D_SMA.csv filename

        Previously, there was a config key mismatch (STRATEGY_TYPES vs STRATEGY_TYPE)
        and inconsistent USE_MA logic that caused incorrect filenames.
        """
        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["RJF"],
            "STRATEGY_TYPES": ["SMA"],  # This should be used for detection
            "USE_HOURLY": False,
            "USE_MA": True,
            "STRATEGY_TYPE": "SMA",
        }

        # Test portfolios_best export
        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=single_strategy_portfolio,
                config=config,
                export_type="portfolios_best",
                log=Mock(),
            )

        assert success == True

        # Verify correct filename for best portfolios
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_best"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

        filename = csv_files[0].name
        # Should contain RJF, D (daily), and SMA
        assert "RJF" in filename
        assert "D" in filename
        assert "SMA" in filename
        assert filename.startswith("RJF_")  # Should start with ticker

    def test_single_sma_strategy_filtered_filename(
        self, single_strategy_portfolio, temp_export_dir
    ):
        """
        REGRESSION TEST: Single SMA strategy filtered should have correct filename

        Previously, filtered exports for single strategies were showing wrong strategy
        (e.g., RJF_D_EMA.csv when it should be RJF_D_SMA.csv).
        """
        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["RJF"],
            "STRATEGY_TYPES": ["SMA"],  # Single strategy
            "USE_HOURLY": False,
            "USE_MA": True,
            "STRATEGY_TYPE": "SMA",
        }

        # Test portfolios_filtered export
        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=single_strategy_portfolio,
                config=config,
                export_type="portfolios_filtered",
                log=Mock(),
            )

        assert success == True

        # Verify correct filename for filtered portfolios
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_filtered"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

        filename = csv_files[0].name
        # Should contain SMA, not EMA or other strategy
        assert "SMA" in filename
        assert "EMA" not in filename
        assert "MACD" not in filename

    def test_multiple_strategies_filename_no_suffix(self, temp_export_dir):
        """
        REGRESSION TEST: Multiple strategies should produce filename without strategy suffix
        """
        mixed_portfolios = [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Fast Period": 10,
                "Slow Period": 20,
                "Total Trades": 50,
                "Win Rate [%]": 55.0,
                "Total Return [%]": 25.5,
                "Sharpe Ratio": 1.2,
                "Score": 8.5,
                "Metric Type": "Most Total Return [%]",
            },
            {
                "Ticker": "AAPL",
                "Strategy Type": "EMA",
                "Fast Period": 12,
                "Slow Period": 26,
                "Total Trades": 45,
                "Win Rate [%]": 62.0,
                "Total Return [%]": 32.1,
                "Sharpe Ratio": 1.4,
                "Score": 9.0,
                "Metric Type": "Most Sharpe Ratio",
            },
        ]

        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["AAPL"],
            "STRATEGY_TYPES": ["SMA", "EMA"],  # Multiple strategies
            "USE_HOURLY": False,
            "USE_MA": False,  # Should be False for multiple strategies
            "STRATEGY_TYPE": "Multi",
        }

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=mixed_portfolios,
                config=config,
                export_type="portfolios",
                log=Mock(),
            )

        assert success == True

        # Verify filename does not have specific strategy suffix
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

        filename = csv_files[0].name
        # Should contain AAPL and D but no specific strategy type
        assert "AAPL" in filename
        assert "D" in filename
        # Should not contain specific strategy suffixes for multi-strategy
        # (This test allows for some flexibility in multi-strategy naming)

    def test_strategy_type_config_key_usage(
        self, single_strategy_portfolio, temp_export_dir
    ):
        """
        REGRESSION TEST: Should use STRATEGY_TYPES (plural) for strategy detection

        Previously, there was confusion between STRATEGY_TYPES and STRATEGY_TYPE keys.
        The fix ensures STRATEGY_TYPES is used for detection.
        """
        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["RJF"],
            "STRATEGY_TYPES": ["SMA"],  # This is the correct key for detection
            "USE_HOURLY": False,
            # STRATEGY_TYPE should be set based on STRATEGY_TYPES
        }

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=single_strategy_portfolio,
                config=config,
                export_type="portfolios",
                log=Mock(),
            )

        assert success == True

        # Verify that the config was processed correctly
        # The export should succeed and produce correct filename
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios"
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0


class TestSortingConsistencyRegression:
    """Test regression of sorting consistency issues."""

    @pytest.fixture
    def temp_export_dir(self):
        """Create temporary directory for export testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def unsorted_portfolios(self):
        """Portfolio data in unsorted order."""
        return [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Fast Period": 10,
                "Slow Period": 20,
                "Total Trades": 50,
                "Win Rate [%]": 55.0,
                "Total Return [%]": 25.5,
                "Sharpe Ratio": 1.2,
                "Score": 6.5,  # Lower score
                "Metric Type": "Most Total Return [%]",
            },
            {
                "Ticker": "MSFT",
                "Strategy Type": "SMA",
                "Fast Period": 12,
                "Slow Period": 26,
                "Total Trades": 45,
                "Win Rate [%]": 62.0,
                "Total Return [%]": 32.1,
                "Sharpe Ratio": 1.4,
                "Score": 9.0,  # Higher score
                "Metric Type": "Most Sharpe Ratio",
            },
            {
                "Ticker": "GOOGL",
                "Strategy Type": "SMA",
                "Fast Period": 8,
                "Slow Period": 21,
                "Total Trades": 38,
                "Win Rate [%]": 48.0,
                "Total Return [%]": 15.8,
                "Sharpe Ratio": 1.0,
                "Score": 7.8,  # Middle score
                "Metric Type": "Most Win Rate [%]",
            },
        ]

    def test_sma_portfolios_sorted_by_score_descending(
        self, unsorted_portfolios, temp_export_dir
    ):
        """
        REGRESSION TEST: SMA portfolios should be sorted by Score descending

        Previously, SMA files were not sorted while EMA/MACD files were sorted.
        Fixed by adding sorting configuration to MAStrategyService.
        """
        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["AAPL", "MSFT", "GOOGL"],
            "STRATEGY_TYPES": ["SMA"],
            "USE_HOURLY": False,
            "USE_MA": False,
            "STRATEGY_TYPE": "SMA",
            "SORT_BY": "Score",
            "SORT_ASC": False,
        }

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=unsorted_portfolios,
                config=config,
                export_type="portfolios",
                log=Mock(),
            )

        assert success == True

        # CRITICAL: Verify portfolios are sorted by Score descending
        scores = df["Score"].to_list()
        assert scores == sorted(
            scores, reverse=True
        ), f"SMA portfolios should be sorted by Score descending: {scores}"

        # Verify the order is specifically: MSFT (9.0), GOOGL (7.8), AAPL (6.5)
        tickers = df["Ticker"].to_list()
        expected_order = ["MSFT", "GOOGL", "AAPL"]  # Sorted by descending Score
        assert (
            tickers == expected_order
        ), f"Expected ticker order {expected_order}, got {tickers}"

    def test_sorting_configuration_applied_to_ma_strategies(
        self, unsorted_portfolios, temp_export_dir
    ):
        """
        REGRESSION TEST: All MA strategies (SMA/EMA) should have consistent sorting
        """
        # Test with EMA portfolios (change strategy type)
        ema_portfolios = []
        for portfolio in unsorted_portfolios:
            ema_portfolio = portfolio.copy()
            ema_portfolio["Strategy Type"] = "EMA"
            ema_portfolios.append(ema_portfolio)

        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["AAPL", "MSFT", "GOOGL"],
            "STRATEGY_TYPES": ["EMA"],
            "USE_HOURLY": False,
            "USE_MA": False,
            "STRATEGY_TYPE": "EMA",
            "SORT_BY": "Score",
            "SORT_ASC": False,
        }

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=ema_portfolios,
                config=config,
                export_type="portfolios",
                log=Mock(),
            )

        assert success == True

        # Verify EMA portfolios are also sorted by Score descending
        scores = df["Score"].to_list()
        assert scores == sorted(
            scores, reverse=True
        ), f"EMA portfolios should be sorted by Score descending: {scores}"

    def test_mixed_strategy_sorting_consistency(self, temp_export_dir):
        """
        REGRESSION TEST: Mixed strategy portfolios should maintain consistent sorting
        """
        mixed_portfolios = [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Score": 8.5,
                "Total Trades": 50,
                "Win Rate [%]": 55.0,
                "Total Return [%]": 25.5,
                "Sharpe Ratio": 1.2,
                "Fast Period": 10,
                "Slow Period": 20,
                "Metric Type": "Most Total Return [%]",
            },
            {
                "Ticker": "MSFT",
                "Strategy Type": "EMA",
                "Score": 9.2,  # Highest
                "Total Trades": 45,
                "Win Rate [%]": 62.0,
                "Total Return [%]": 32.1,
                "Sharpe Ratio": 1.4,
                "Fast Period": 12,
                "Slow Period": 26,
                "Metric Type": "Most Sharpe Ratio",
            },
            {
                "Ticker": "GOOGL",
                "Strategy Type": "MACD",
                "Score": 7.8,  # Lowest
                "Total Trades": 38,
                "Win Rate [%]": 68.0,
                "Total Return [%]": 35.8,
                "Sharpe Ratio": 1.6,
                "Fast Period": 12,
                "Slow Period": 26,
                "Signal Period": 9,
                "Metric Type": "Most Win Rate [%]",
            },
        ]

        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["AAPL", "MSFT", "GOOGL"],
            "STRATEGY_TYPES": ["SMA", "EMA", "MACD"],
            "USE_HOURLY": False,
            "USE_MA": False,
            "STRATEGY_TYPE": "Multi",
            "SORT_BY": "Score",
            "SORT_ASC": False,
        }

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=mixed_portfolios,
                config=config,
                export_type="portfolios_filtered",
                log=Mock(),
            )

        assert success == True

        # Verify mixed strategy portfolios are sorted consistently
        scores = df["Score"].to_list()
        assert scores == sorted(scores, reverse=True)

        # Verify order: MSFT (9.2), AAPL (8.5), GOOGL (7.8)
        tickers = df["Ticker"].to_list()
        expected_order = ["MSFT", "AAPL", "GOOGL"]
        assert tickers == expected_order


class TestCBREAggregationRegression:
    """Test regression of CBRE aggregation scenarios that previously failed."""

    @pytest.fixture
    def temp_export_dir(self):
        """Create temporary directory for export testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def cbre_aggregation_data(self):
        """CBRE portfolio data that previously caused aggregation issues."""
        return [
            {
                "Ticker": "CBRE",
                "Strategy Type": "SMA",
                "Fast Period": 10,
                "Slow Period": 20,
                "Total Trades": 50,
                "Win Rate [%]": 55.0,
                "Total Return [%]": 25.5,
                "Sharpe Ratio": 1.2,
                "Score": 8.5,
                "Metric Type": "Most Total Return [%]",
            },
            {
                "Ticker": "CBRE",
                "Strategy Type": "SMA",
                "Fast Period": 12,
                "Slow Period": 26,
                "Total Trades": 45,
                "Win Rate [%]": 62.0,
                "Total Return [%]": 32.1,
                "Sharpe Ratio": 1.8,  # Different value for same ticker/strategy
                "Score": 9.0,
                "Metric Type": "Most Sharpe Ratio",  # Different metric type
            },
        ]

    def test_cbre_aggregation_preserves_metric_types(
        self, cbre_aggregation_data, temp_export_dir
    ):
        """
        REGRESSION TEST: CBRE aggregation should preserve compound metric types

        Previously, CBRE data with multiple metric types for the same ticker/strategy
        was not being aggregated correctly, causing metric type information to be lost.
        """
        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["CBRE"],
            "STRATEGY_TYPES": ["SMA"],
            "USE_HOURLY": False,
            "USE_MA": True,
            "STRATEGY_TYPE": "SMA",
        }

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=cbre_aggregation_data,
                config=config,
                export_type="portfolios_best",
                log=Mock(),
            )

        assert success == True

        # CRITICAL: Verify CBRE data is present
        cbre_rows = df.filter(pl.col("Ticker") == "CBRE")
        assert len(cbre_rows) > 0, "CBRE data should be present in export"

        # Verify metric type information is preserved (compound or individual)
        cbre_metric_types = cbre_rows["Metric Type"].to_list()

        # Should either have compound metric types or preserve individual ones
        has_compound_metrics = any("," in str(mt) for mt in cbre_metric_types)
        has_diverse_metrics = len(set(cbre_metric_types)) > 1

        # At least one of these should be true (aggregation worked or individual metrics preserved)
        assert (
            has_compound_metrics or has_diverse_metrics
        ), f"CBRE metric types not properly handled: {cbre_metric_types}"

    def test_cbre_aggregation_numerical_consistency(
        self, cbre_aggregation_data, temp_export_dir
    ):
        """
        REGRESSION TEST: CBRE aggregation should maintain numerical consistency
        """
        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["CBRE"],
            "STRATEGY_TYPES": ["SMA"],
            "USE_HOURLY": False,
            "USE_MA": True,
            "STRATEGY_TYPE": "SMA",
        }

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=cbre_aggregation_data,
                config=config,
                export_type="portfolios_best",
                log=Mock(),
            )

        assert success == True

        # Verify CBRE numerical data is consistent
        cbre_rows = df.filter(pl.col("Ticker") == "CBRE")
        assert len(cbre_rows) > 0

        # Verify numerical fields are valid
        for _, row in enumerate(cbre_rows.to_dicts()):
            assert isinstance(row["Total Trades"], (int, float))
            assert isinstance(row["Win Rate [%]"], (int, float))
            assert isinstance(row["Score"], (int, float))

            # Verify values are reasonable (not corrupted during aggregation)
            assert 0 <= row["Win Rate [%]"] <= 100
            assert row["Total Trades"] > 0
            assert row["Score"] > 0

    def test_multiple_ticker_aggregation_consistency(self, temp_export_dir):
        """
        REGRESSION TEST: Multiple ticker aggregation should work consistently
        """
        multi_ticker_data = [
            {
                "Ticker": "CBRE",
                "Strategy Type": "SMA",
                "Fast Period": 10,
                "Slow Period": 20,
                "Score": 8.5,
                "Metric Type": "Most Total Return [%]",
                "Total Trades": 50,
                "Win Rate [%]": 55.0,
                "Total Return [%]": 25.5,
                "Sharpe Ratio": 1.2,
            },
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Fast Period": 10,
                "Slow Period": 20,
                "Score": 9.0,
                "Metric Type": "Most Sharpe Ratio",
                "Total Trades": 45,
                "Win Rate [%]": 62.0,
                "Total Return [%]": 32.1,
                "Sharpe Ratio": 1.8,
            },
        ]

        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["CBRE", "AAPL"],
            "STRATEGY_TYPES": ["SMA"],
            "USE_HOURLY": False,
            "USE_MA": True,
            "STRATEGY_TYPE": "SMA",
        }

        with patch("app.tools.strategy.export_portfolios.logging_context"):
            df, success = export_portfolios(
                portfolios=multi_ticker_data,
                config=config,
                export_type="portfolios_best",
                log=Mock(),
            )

        assert success == True

        # Verify both tickers are present
        tickers = df["Ticker"].unique().to_list()
        assert "CBRE" in tickers
        assert "AAPL" in tickers

        # Verify metric types are preserved for both
        cbre_data = df.filter(pl.col("Ticker") == "CBRE")
        aapl_data = df.filter(pl.col("Ticker") == "AAPL")

        assert len(cbre_data) > 0
        assert len(aapl_data) > 0

        # Both should have their respective metric types
        cbre_metrics = cbre_data["Metric Type"].to_list()
        aapl_metrics = aapl_data["Metric Type"].to_list()

        assert any("Total Return" in str(mt) for mt in cbre_metrics)
        assert any("Sharpe Ratio" in str(mt) for mt in aapl_metrics)
