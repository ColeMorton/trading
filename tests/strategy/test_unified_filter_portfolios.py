"""
Test Suite for Unified Portfolio Filtering System

This module tests the consolidated portfolio filtering functionality to ensure
it properly handles all strategy types while eliminating code duplication.
"""

from unittest.mock import Mock, patch

import polars as pl
import pytest

from app.tools.strategy.filter_portfolios import (
    PortfolioFilterConfig,
    _prepare_result_df,
    _process_metrics,
    create_metric_result,
    create_metric_result_from_rows,
    create_metric_summary,
    filter_and_export_portfolios,
    filter_portfolios,
    get_extreme_values,
    get_metric_rows,
)


class TestPortfolioFilterConfig:
    """Test cases for PortfolioFilterConfig."""

    def test_sma_configuration(self):
        """Test SMA strategy configuration."""
        config = PortfolioFilterConfig("SMA")

        assert config.strategy_type == "SMA"
        assert config.get_window_parameters() == ["Fast Period", "Slow Period"]

        display_prefs = config.get_display_preferences()
        assert display_prefs["sort_by"] == "Total Return [%]"
        assert display_prefs["sort_asc"] is False

    def test_macd_configuration(self):
        """Test MACD strategy configuration."""
        config = PortfolioFilterConfig("MACD")

        assert config.strategy_type == "MACD"
        assert config.get_window_parameters() == [
            "Fast Period",
            "Slow Period",
            "Signal Period",
        ]

    def test_mean_reversion_configuration(self):
        """Test Mean Reversion strategy configuration."""
        config = PortfolioFilterConfig("MEAN_REVERSION")

        assert config.strategy_type == "MEAN_REVERSION"
        assert config.get_window_parameters() == ["Change PCT"]

    def test_case_insensitive_strategy_type(self):
        """Test that strategy type is case insensitive."""
        config = PortfolioFilterConfig("sma")
        assert config.strategy_type == "SMA"

        config = PortfolioFilterConfig("Macd")
        assert config.strategy_type == "MACD"

    def test_unknown_strategy_fallback(self):
        """Test fallback behavior for unknown strategy types."""
        config = PortfolioFilterConfig("UNKNOWN")

        # Should fallback to default window parameters
        assert config.get_window_parameters() == ["Fast Period", "Slow Period"]


class TestCreateMetricResult:
    """Test cases for create_metric_result function."""

    def test_create_metric_result_sma(self):
        """Test creating metric result for SMA strategy."""
        df = pl.DataFrame(
            {
                "Fast Period": [10, 20],
                "Slow Period": [50, 100],
                "Total Return [%]": [5.0, 8.0],
                "Win Rate [%]": [60.0, 70.0],
            },
        )

        result = create_metric_result(
            metric="Total Return [%]",
            row_idx=1,
            df=df,
            label="Most",
            window_params=["Fast Period", "Slow Period"],
        )

        assert result["Metric Type"] == "Most Total Return [%]"
        assert result["Fast Period"] == 20
        assert result["Slow Period"] == 100
        assert result["Total Return [%]"] == 8.0
        assert result["Win Rate [%]"] == 70.0

    def test_create_metric_result_macd(self):
        """Test creating metric result for MACD strategy."""
        df = pl.DataFrame(
            {
                "Fast Period": [12, 15],
                "Slow Period": [26, 30],
                "Signal Period": [9, 12],
                "Total Return [%]": [6.0, 9.0],
            },
        )

        result = create_metric_result(
            metric="Total Return [%]",
            row_idx=0,
            df=df,
            label="Least",
            window_params=["Fast Period", "Slow Period", "Signal Period"],
        )

        assert result["Metric Type"] == "Least Total Return [%]"
        assert result["Fast Period"] == 12
        assert result["Slow Period"] == 26
        assert result["Signal Period"] == 9
        assert result["Total Return [%]"] == 6.0

    def test_create_metric_result_missing_params(self):
        """Test creating metric result with missing parameters."""
        df = pl.DataFrame({"Fast Period": [10], "Total Return [%]": [5.0]})

        result = create_metric_result(
            metric="Total Return [%]",
            row_idx=0,
            df=df,
            label="Mean",
            window_params=["Fast Period", "Slow Period", "Signal Period"],
        )

        assert result["Fast Period"] == 10
        assert result["Slow Period"] == 0  # Default value
        assert result["Signal Period"] == 0  # Default value


class TestGetMetricRows:
    """Test cases for get_metric_rows function."""

    def test_get_metric_rows_valid_metric(self):
        """Test getting metric rows for valid metric."""
        df = pl.DataFrame({"Total Return [%]": [5.0, 10.0, 3.0, 8.0, 7.0]})

        rows = get_metric_rows(df, "Total Return [%]")

        assert rows["most"] == 1  # Index of max value (10.0)
        assert rows["least"] == 2  # Index of min value (3.0)
        assert "mean" in rows
        assert "median" in rows

    def test_get_metric_rows_invalid_metric(self):
        """Test getting metric rows for invalid metric."""
        df = pl.DataFrame({"Total Return [%]": [5.0, 10.0, 3.0]})

        rows = get_metric_rows(df, "Invalid Metric")

        assert rows == {}

    def test_get_metric_rows_with_nulls(self):
        """Test getting metric rows with null values."""
        df = pl.DataFrame({"Total Return [%]": [5.0, None, 10.0, None, 3.0]})

        rows = get_metric_rows(df, "Total Return [%]")

        # Should handle nulls properly
        assert "most" in rows
        assert "least" in rows
        assert rows["most"] == 2  # Index of 10.0
        assert rows["least"] == 4  # Index of 3.0

    def test_get_metric_rows_empty_valid_series(self):
        """Test getting metric rows when all values are null."""
        df = pl.DataFrame({"Total Return [%]": [None, None, None]})

        rows = get_metric_rows(df, "Total Return [%]")

        assert rows == {}


class TestCreateMetricResultFromRows:
    """Test cases for create_metric_result_from_rows function."""

    def test_create_metric_result_from_rows(self):
        """Test creating metric results from row indices."""
        df = pl.DataFrame(
            {
                "Fast Period": [10, 20, 15],
                "Slow Period": [50, 100, 75],
                "Total Return [%]": [5.0, 10.0, 7.5],
            },
        )

        rows = {"most": 1, "least": 0, "mean": 2}

        results = create_metric_result_from_rows(
            metric="Total Return [%]",
            rows=rows,
            df=df,
            window_params=["Fast Period", "Slow Period"],
        )

        assert len(results) == 3

        # Check most result
        most_result = next(
            r for r in results if r["Metric Type"] == "Most Total Return [%]"
        )
        assert most_result["Fast Period"] == 20
        assert most_result["Total Return [%]"] == 10.0

        # Check least result
        least_result = next(
            r for r in results if r["Metric Type"] == "Least Total Return [%]"
        )
        assert least_result["Fast Period"] == 10
        assert least_result["Total Return [%]"] == 5.0

    def test_create_metric_result_from_rows_none_values(self):
        """Test creating results with None values in rows dict."""
        df = pl.DataFrame({"Total Return [%]": [5.0, 10.0]})

        rows = {"most": 1, "least": None, "mean": 0}

        results = create_metric_result_from_rows(
            metric="Total Return [%]",
            rows=rows,
            df=df,
        )

        assert len(results) == 2  # Should skip None values
        assert any(r["Metric Type"] == "Most Total Return [%]" for r in results)
        assert any(r["Metric Type"] == "Mean Total Return [%]" for r in results)
        assert not any(r["Metric Type"] == "Least Total Return [%]" for r in results)


class TestProcessMetrics:
    """Test cases for _process_metrics function."""

    def test_process_metrics_multiple_metrics(self):
        """Test processing multiple metrics."""
        df = pl.DataFrame(
            {
                "Fast Period": [10, 20, 15],
                "Slow Period": [50, 100, 75],
                "Total Return [%]": [5.0, 10.0, 7.5],
                "Win Rate [%]": [60.0, 80.0, 70.0],
            },
        )

        metrics = ["Total Return [%]", "Win Rate [%]"]
        window_params = ["Fast Period", "Slow Period"]

        results = _process_metrics(df, metrics, window_params)

        # Should have 4 results per metric (most, least, mean, median) × 2 metrics = 8 results
        assert len(results) == 8

        # Check that we have results for both metrics
        return_results = [r for r in results if "Total Return" in r["Metric Type"]]
        win_rate_results = [r for r in results if "Win Rate" in r["Metric Type"]]

        assert len(return_results) == 4
        assert len(win_rate_results) == 4

    def test_process_metrics_missing_metrics(self):
        """Test processing metrics that don't exist in DataFrame."""
        df = pl.DataFrame(
            {
                "Total Return [%]": [5.0, 10.0],
            },
        )

        metrics = ["Total Return [%]", "Missing Metric", "Another Missing"]

        results = _process_metrics(df, metrics)

        # Should only process the existing metric
        assert len(results) == 4  # 4 statistics for 1 metric
        assert all("Total Return" in r["Metric Type"] for r in results)

    def test_process_metrics_empty_metrics_list(self):
        """Test processing with empty metrics list."""
        df = pl.DataFrame(
            {
                "Total Return [%]": [5.0, 10.0],
            },
        )

        results = _process_metrics(df, [])

        assert results == []


class TestFilterPortfolios:
    """Test cases for filter_portfolios function."""

    def test_filter_portfolios_sma_strategy(self):
        """Test filtering portfolios for SMA strategy."""
        df = pl.DataFrame(
            {
                "Fast Period": [10, 20, 15],
                "Slow Period": [50, 100, 75],
                "Total Return [%]": [5.0, 10.0, 7.5],
                "Win Rate [%]": [60.0, 80.0, 70.0],
                "Profit Factor": [1.2, 1.5, 1.3],
            },
        )

        config = {
            "STRATEGY_TYPE": "SMA",
            "SORT_BY": "Total Return [%]",
            "SORT_ASC": False,
        }
        mock_log = Mock()

        result = filter_portfolios(df, config, mock_log, "SMA")

        assert not result.is_empty()
        assert len(result) > 0

        # Verify logging
        mock_log.assert_any_call("Filtering 3 portfolios for SMA strategy")

    def test_filter_portfolios_empty_dataframe(self):
        """Test filtering with empty DataFrame."""
        df = pl.DataFrame()
        config = {"STRATEGY_TYPE": "SMA"}
        mock_log = Mock()

        result = filter_portfolios(df, config, mock_log)

        assert result.is_empty()
        mock_log.assert_called_with("No portfolios to filter", "warning")

    def test_filter_portfolios_auto_detect_strategy(self):
        """Test filtering with auto-detected strategy type."""
        df = pl.DataFrame(
            {
                "Fast Period": [12, 15],
                "Slow Period": [26, 30],
                "Signal Period": [9, 12],
                "Total Return [%]": [6.0, 9.0],
            },
        )

        config = {"STRATEGY_TYPE": "MACD"}

        result = filter_portfolios(df, config)

        assert not result.is_empty()

    def test_filter_portfolios_no_strategy_type(self):
        """Test filtering with no strategy type (should default to SMA)."""
        df = pl.DataFrame(
            {
                "Fast Period": [10, 20],
                "Slow Period": [50, 100],
                "Total Return [%]": [5.0, 10.0],
            },
        )

        config = {}

        result = filter_portfolios(df, config)

        assert not result.is_empty()


class TestFilterAndExportPortfolios:
    """Test cases for filter_and_export_portfolios function."""

    @patch("app.tools.strategy.export_portfolios.export_portfolios")
    def test_filter_and_export_success(self, mock_export):
        """Test successful filtering and export."""
        df = pl.DataFrame(
            {
                "Fast Period": [10, 20],
                "Slow Period": [50, 100],
                "Total Return [%]": [5.0, 10.0],
            },
        )

        config = {"STRATEGY_TYPE": "SMA"}
        mock_log = Mock()

        # Mock successful export
        mock_export.return_value = (pl.DataFrame(), True)

        result = filter_and_export_portfolios(df, config, mock_log)

        assert result is True
        mock_export.assert_called_once()

        # Verify export was called with correct parameters
        call_args = mock_export.call_args
        assert call_args[1]["export_type"] == "portfolios_filtered"
        assert call_args[1]["feature_dir"] == ""

    @patch("app.tools.strategy.export_portfolios.export_portfolios")
    def test_filter_and_export_empty_filtered_results(self, mock_export):
        """Test filtering and export with no filtered results."""
        df = pl.DataFrame()  # Empty DataFrame

        config = {"STRATEGY_TYPE": "SMA"}
        mock_log = Mock()

        result = filter_and_export_portfolios(df, config, mock_log)

        assert result is False
        mock_export.assert_not_called()
        mock_log.assert_called_with("No filtered portfolios to export", "warning")

    @patch("app.tools.strategy.export_portfolios.export_portfolios")
    def test_filter_and_export_export_failure(self, mock_export):
        """Test filtering and export with export failure."""
        df = pl.DataFrame({"Total Return [%]": [5.0, 10.0]})

        config = {"STRATEGY_TYPE": "SMA"}
        mock_log = Mock()

        # Mock export failure
        mock_export.return_value = (pl.DataFrame(), False)

        result = filter_and_export_portfolios(df, config, mock_log)

        assert result is False


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    def test_create_metric_summary(self):
        """Test create_metric_summary convenience function."""
        df = pl.DataFrame(
            {
                "Fast Period": [10, 20, 15],
                "Slow Period": [50, 100, 75],
                "Total Return [%]": [5.0, 10.0, 7.5],
            },
        )

        summary = create_metric_summary(df, "Total Return [%]", "SMA")

        assert len(summary) == 4  # most, least, mean, median
        assert all("Total Return" in s["Metric Type"] for s in summary)
        assert all("Fast Period" in s for s in summary)
        assert all("Slow Period" in s for s in summary)

    def test_get_extreme_values_default_metrics(self):
        """Test get_extreme_values with default metrics."""
        df = pl.DataFrame(
            {
                "Fast Period": [10, 20],
                "Slow Period": [50, 100],
                "Total Return [%]": [5.0, 10.0],
                "Win Rate [%]": [60.0, 80.0],
            },
        )

        result = get_extreme_values(df, strategy_type="SMA")

        assert not result.is_empty()
        assert len(result) > 0

    def test_get_extreme_values_specific_metrics(self):
        """Test get_extreme_values with specific metrics."""
        df = pl.DataFrame(
            {
                "Fast Period": [10, 20],
                "Slow Period": [50, 100],
                "Total Return [%]": [5.0, 10.0],
                "Win Rate [%]": [60.0, 80.0],
            },
        )

        result = get_extreme_values(
            df,
            metrics=["Total Return [%]"],
            strategy_type="SMA",
        )

        assert not result.is_empty()
        # Should only have results for Total Return metric
        assert all("Total Return" in row["Metric Type"] for row in result.to_dicts())


class TestPrepareResultDf:
    """Test cases for _prepare_result_df function."""

    def test_prepare_result_df_sorting(self):
        """Test preparing result DataFrame with sorting."""
        result_rows = [
            {
                "Metric Type": "Most Total Return [%]",
                "Total Return [%]": 10.0,
                "Fast Period": 20,
            },
            {
                "Metric Type": "Least Total Return [%]",
                "Total Return [%]": 5.0,
                "Fast Period": 10,
            },
        ]

        config = {"SORT_BY": "Total Return [%]", "SORT_ASC": False}
        filter_config = PortfolioFilterConfig("SMA")

        result_df = _prepare_result_df(result_rows, config, filter_config)

        assert not result_df.is_empty()
        assert len(result_df) == 2

        # Should be sorted by Total Return descending
        returns = result_df["Total Return [%]"].to_list()
        assert returns == [10.0, 5.0]

    def test_prepare_result_df_empty_results(self):
        """Test preparing result DataFrame with empty results."""
        result_rows = []
        config = {}
        filter_config = PortfolioFilterConfig("SMA")

        result_df = _prepare_result_df(result_rows, config, filter_config)

        assert result_df.is_empty()


if __name__ == "__main__":
    pytest.main([__file__])
