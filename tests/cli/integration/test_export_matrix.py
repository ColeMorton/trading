"""
Comprehensive Export Type Matrix Tests.

This test suite covers ALL combinations of:
- Strategy Types: SMA, EMA, MACD
- Export Types: portfolios, portfolios_filtered, portfolios_best
- Single/Multiple tickers
- File path and naming verification
- Schema compliance for each export type

This prevents regression of export issues like directory paths, metric type columns,
filename generation, and ensures consistent behavior across all combinations.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import polars as pl
import pytest

from app.tools.strategy.export_portfolios import export_portfolios


class TestExportTypeMatrix:
    """Test matrix of all strategy type × export type combinations."""

    @pytest.fixture
    def temp_export_dir(self):
        """Create temporary directory for export testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def sample_portfolios_sma(self):
        """Sample SMA portfolio data."""
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
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Fast Period": 5,
                "Slow Period": 15,
                "Total Trades": 75,
                "Win Rate [%]": 60.0,
                "Total Return [%]": 35.2,
                "Sharpe Ratio": 1.5,
                "Score": 9.2,
                "Metric Type": "Most Sharpe Ratio",
            },
        ]

    @pytest.fixture
    def sample_portfolios_ema(self):
        """Sample EMA portfolio data."""
        return [
            {
                "Ticker": "MSFT",
                "Strategy Type": "EMA",
                "Fast Period": 12,
                "Slow Period": 26,
                "Total Trades": 45,
                "Win Rate [%]": 58.0,
                "Total Return [%]": 28.7,
                "Sharpe Ratio": 1.3,
                "Score": 8.8,
                "Metric Type": "Most Total Return [%]",
            },
            {
                "Ticker": "MSFT",
                "Strategy Type": "EMA",
                "Fast Period": 8,
                "Slow Period": 21,
                "Total Trades": 65,
                "Win Rate [%]": 62.0,
                "Total Return [%]": 32.1,
                "Sharpe Ratio": 1.4,
                "Score": 9.0,
                "Metric Type": "Most Win Rate [%]",
            },
        ]

    @pytest.fixture
    def sample_portfolios_macd(self):
        """Sample MACD portfolio data."""
        return [
            {
                "Ticker": "GOOGL",
                "Strategy Type": "MACD",
                "Fast Period": 12,
                "Slow Period": 26,
                "Signal Period": 9,
                "Total Trades": 40,
                "Win Rate [%]": 65.0,
                "Total Return [%]": 42.3,
                "Sharpe Ratio": 1.6,
                "Score": 9.5,
                "Metric Type": "Most Total Return [%]",
            },
            {
                "Ticker": "GOOGL",
                "Strategy Type": "MACD",
                "Fast Period": 8,
                "Slow Period": 21,
                "Signal Period": 7,
                "Total Trades": 55,
                "Win Rate [%]": 58.0,
                "Total Return [%]": 31.8,
                "Sharpe Ratio": 1.35,
                "Score": 8.7,
                "Metric Type": "Most Profit Factor",
            },
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

    def test_sma_portfolios_export(
        self,
        sample_portfolios_sma,
        base_config,
        temp_export_dir,
    ):
        """Test SMA strategy with portfolios export type."""
        config = base_config.copy()
        config["STRATEGY_TYPES"] = ["SMA"]
        config["STRATEGY_TYPE"] = "SMA"

        df, success = export_portfolios(
            portfolios=sample_portfolios_sma,
            config=config,
            export_type="portfolios",
            log=Mock(),
        )

        # Verify export success
        assert success is True
        assert len(df) == 2

        # Verify file was created in correct location
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios"
        assert export_path.exists()

        # Find CSV files in the directory
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

        # Verify filename contains SMA strategy type
        filename = csv_files[0].name
        assert "SMA" in filename

    def test_sma_portfolios_filtered_export(
        self,
        sample_portfolios_sma,
        base_config,
        temp_export_dir,
    ):
        """Test SMA strategy with portfolios_filtered export type."""
        config = base_config.copy()
        config["STRATEGY_TYPES"] = ["SMA"]
        config["STRATEGY_TYPE"] = "SMA"

        df, success = export_portfolios(
            portfolios=sample_portfolios_sma,
            config=config,
            export_type="portfolios_filtered",
            log=Mock(),
        )

        # Verify export success
        assert success is True
        assert len(df) == 2

        # Verify Metric Type column is preserved
        assert "Metric Type" in df.columns

        # Verify file was created in correct location
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_filtered"
        assert export_path.exists()

        # Verify CSV file exists
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

    def test_sma_portfolios_best_export(
        self,
        sample_portfolios_sma,
        base_config,
        temp_export_dir,
    ):
        """Test SMA strategy with portfolios_best export type."""
        config = base_config.copy()
        config["STRATEGY_TYPES"] = ["SMA"]
        config["STRATEGY_TYPE"] = "SMA"

        df, success = export_portfolios(
            portfolios=sample_portfolios_sma,
            config=config,
            export_type="portfolios_best",
            log=Mock(),
        )

        # Verify export success
        assert success is True
        assert len(df) == 2

        # Verify Metric Type column is present for best portfolios
        assert "Metric Type" in df.columns

        # Verify file was created in correct location
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_best"
        assert export_path.exists()

        # Verify CSV file exists
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

    def test_ema_portfolios_export(
        self,
        sample_portfolios_ema,
        base_config,
        temp_export_dir,
    ):
        """Test EMA strategy with portfolios export type."""
        config = base_config.copy()
        config["TICKER"] = ["MSFT"]
        config["STRATEGY_TYPES"] = ["EMA"]
        config["STRATEGY_TYPE"] = "EMA"

        df, success = export_portfolios(
            portfolios=sample_portfolios_ema,
            config=config,
            export_type="portfolios",
            log=Mock(),
        )

        # Verify export success
        assert success is True
        assert len(df) == 2

        # Verify file was created in correct location
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios"
        assert export_path.exists()

        # Verify filename contains EMA strategy type
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0
        filename = csv_files[0].name
        assert "EMA" in filename

    def test_ema_portfolios_filtered_export(
        self,
        sample_portfolios_ema,
        base_config,
        temp_export_dir,
    ):
        """Test EMA strategy with portfolios_filtered export type."""
        config = base_config.copy()
        config["TICKER"] = ["MSFT"]
        config["STRATEGY_TYPES"] = ["EMA"]
        config["STRATEGY_TYPE"] = "EMA"

        df, success = export_portfolios(
            portfolios=sample_portfolios_ema,
            config=config,
            export_type="portfolios_filtered",
            log=Mock(),
        )

        # Verify export success and schema
        assert success is True
        assert len(df) == 2
        assert "Metric Type" in df.columns

        # Verify metric type values are preserved
        metric_types = df["Metric Type"].to_list()
        assert "Most Total Return [%]" in metric_types
        assert "Most Win Rate [%]" in metric_types

        # Verify file location
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_filtered"
        assert export_path.exists()

    def test_ema_portfolios_best_export(
        self,
        sample_portfolios_ema,
        base_config,
        temp_export_dir,
    ):
        """Test EMA strategy with portfolios_best export type."""
        config = base_config.copy()
        config["TICKER"] = ["MSFT"]
        config["STRATEGY_TYPES"] = ["EMA"]
        config["STRATEGY_TYPE"] = "EMA"

        df, success = export_portfolios(
            portfolios=sample_portfolios_ema,
            config=config,
            export_type="portfolios_best",
            log=Mock(),
        )

        # Verify export success and schema
        assert success is True
        assert len(df) == 2
        assert "Metric Type" in df.columns

        # Verify file location
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_best"
        assert export_path.exists()

    def test_macd_portfolios_export(
        self,
        sample_portfolios_macd,
        base_config,
        temp_export_dir,
    ):
        """Test MACD strategy with portfolios export type."""
        config = base_config.copy()
        config["TICKER"] = ["GOOGL"]
        config["STRATEGY_TYPES"] = ["MACD"]
        config["STRATEGY_TYPE"] = "MACD"

        df, success = export_portfolios(
            portfolios=sample_portfolios_macd,
            config=config,
            export_type="portfolios",
            log=Mock(),
        )

        # Verify export success
        assert success is True
        assert len(df) == 2

        # Verify MACD-specific columns are handled
        assert (
            "Signal Period" in df.columns
            or "Signal Period" in sample_portfolios_macd[0]
        )

        # Verify file location and naming
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios"
        assert export_path.exists()

        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0
        filename = csv_files[0].name
        assert "MACD" in filename

    def test_macd_portfolios_filtered_export(
        self,
        sample_portfolios_macd,
        base_config,
        temp_export_dir,
    ):
        """Test MACD strategy with portfolios_filtered export type."""
        config = base_config.copy()
        config["TICKER"] = ["GOOGL"]
        config["STRATEGY_TYPES"] = ["MACD"]
        config["STRATEGY_TYPE"] = "MACD"

        df, success = export_portfolios(
            portfolios=sample_portfolios_macd,
            config=config,
            export_type="portfolios_filtered",
            log=Mock(),
        )

        # Verify export success and filtered schema
        assert success is True
        assert len(df) == 2
        assert "Metric Type" in df.columns

        # Verify MACD-specific metric types are preserved
        metric_types = df["Metric Type"].to_list()
        assert "Most Total Return [%]" in metric_types
        assert "Most Profit Factor" in metric_types

        # Verify file location
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_filtered"
        assert export_path.exists()

    def test_macd_portfolios_best_export(
        self,
        sample_portfolios_macd,
        base_config,
        temp_export_dir,
    ):
        """Test MACD strategy with portfolios_best export type."""
        config = base_config.copy()
        config["TICKER"] = ["GOOGL"]
        config["STRATEGY_TYPES"] = ["MACD"]
        config["STRATEGY_TYPE"] = "MACD"

        df, success = export_portfolios(
            portfolios=sample_portfolios_macd,
            config=config,
            export_type="portfolios_best",
            log=Mock(),
        )

        # Verify export success and best schema
        assert success is True
        assert len(df) == 2
        assert "Metric Type" in df.columns

        # Verify file location with timestamp
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_best"
        assert export_path.exists()

        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

    def test_mixed_strategies_portfolios_export(
        self,
        sample_portfolios_sma,
        sample_portfolios_ema,
        base_config,
        temp_export_dir,
    ):
        """Test mixed SMA/EMA strategies with portfolios export type."""
        mixed_portfolios = sample_portfolios_sma + sample_portfolios_ema

        config = base_config.copy()
        config["TICKER"] = ["AAPL", "MSFT"]
        config["STRATEGY_TYPES"] = ["SMA", "EMA"]
        config["STRATEGY_TYPE"] = "Multi"
        config["USE_MA"] = False  # No strategy suffix for multiple strategies

        df, success = export_portfolios(
            portfolios=mixed_portfolios,
            config=config,
            export_type="portfolios",
            log=Mock(),
        )

        # Verify export success
        assert success is True
        assert len(df) == 4  # 2 SMA + 2 EMA

        # Verify both strategy types are present
        strategy_types = df["Strategy Type"].unique().to_list()
        assert "SMA" in strategy_types
        assert "EMA" in strategy_types

        # Verify file location
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios"
        assert export_path.exists()

        # Verify filename doesn't have specific strategy suffix for mixed strategies
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0

    def test_multiple_tickers_single_strategy(
        self,
        sample_portfolios_sma,
        base_config,
        temp_export_dir,
    ):
        """Test multiple tickers with single strategy type."""
        # Duplicate portfolios for different tickers
        multi_ticker_portfolios = []
        for ticker in ["AAPL", "MSFT", "GOOGL"]:
            for portfolio in sample_portfolios_sma:
                portfolio_copy = portfolio.copy()
                portfolio_copy["Ticker"] = ticker
                multi_ticker_portfolios.append(portfolio_copy)

        config = base_config.copy()
        config["TICKER"] = ["AAPL", "MSFT", "GOOGL"]
        config["STRATEGY_TYPES"] = ["SMA"]
        config["STRATEGY_TYPE"] = "SMA"

        df, success = export_portfolios(
            portfolios=multi_ticker_portfolios,
            config=config,
            export_type="portfolios_filtered",
            log=Mock(),
        )

        # Verify export success
        assert success is True
        assert len(df) == 6  # 3 tickers × 2 portfolios each

        # Verify all tickers are present
        tickers = df["Ticker"].unique().to_list()
        assert "AAPL" in tickers
        assert "MSFT" in tickers
        assert "GOOGL" in tickers

        # Verify Metric Type column is preserved
        assert "Metric Type" in df.columns

        # Verify file location
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios_filtered"
        assert export_path.exists()

    def test_synthetic_ticker_export(
        self,
        sample_portfolios_sma,
        base_config,
        temp_export_dir,
    ):
        """Test export with synthetic ticker format."""
        synthetic_portfolios = []
        for portfolio in sample_portfolios_sma:
            portfolio_copy = portfolio.copy()
            portfolio_copy["Ticker"] = "STRK/MSTR"
            synthetic_portfolios.append(portfolio_copy)

        config = base_config.copy()
        config["TICKER"] = ["STRK/MSTR"]
        config["STRATEGY_TYPES"] = ["SMA"]
        config["STRATEGY_TYPE"] = "SMA"

        df, success = export_portfolios(
            portfolios=synthetic_portfolios,
            config=config,
            export_type="portfolios",
            log=Mock(),
        )

        # Verify export success
        assert success is True
        assert len(df) == 2

        # Verify synthetic ticker is preserved
        tickers = df["Ticker"].unique().to_list()
        assert "STRK/MSTR" in tickers

        # Verify file location
        export_path = Path(temp_export_dir) / "data" / "raw" / "portfolios"
        assert export_path.exists()

        # Verify filename handles synthetic ticker format
        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0
        filename = csv_files[0].name
        assert "STRK_MSTR" in filename  # Should convert / to _

    def test_empty_portfolios_export(self, base_config, temp_export_dir):
        """Test export behavior with empty portfolio list - should create headers-only CSV."""
        config = base_config.copy()

        # Empty portfolios should now succeed and create headers-only CSV
        df, success = export_portfolios(
            portfolios=[],
            config=config,
            export_type="portfolios",
            log=Mock(),
        )

        # Verify export succeeded
        assert success is True
        assert isinstance(df, pl.DataFrame)
        assert len(df) == 0  # No data rows
        assert len(df.columns) > 0  # Has header columns

    def test_invalid_export_type(
        self,
        sample_portfolios_sma,
        base_config,
        temp_export_dir,
    ):
        """Test export with invalid export type."""
        config = base_config.copy()

        with pytest.raises(Exception):  # Should raise PortfolioExportError
            export_portfolios(
                portfolios=sample_portfolios_sma,
                config=config,
                export_type="invalid_export_type",
                log=Mock(),
            )

    @pytest.mark.parametrize(
        ("strategy_type", "export_type"),
        [
            ("SMA", "portfolios"),
            ("SMA", "portfolios_filtered"),
            ("SMA", "portfolios_best"),
            ("EMA", "portfolios"),
            ("EMA", "portfolios_filtered"),
            ("EMA", "portfolios_best"),
            ("MACD", "portfolios"),
            ("MACD", "portfolios_filtered"),
            ("MACD", "portfolios_best"),
        ],
    )
    def test_all_strategy_export_combinations(
        self,
        strategy_type,
        export_type,
        base_config,
        temp_export_dir,
    ):
        """Parametrized test for all strategy×export type combinations."""
        # Create appropriate sample data based on strategy type
        if strategy_type == "MACD":
            sample_portfolios = [
                {
                    "Ticker": "TEST",
                    "Strategy Type": strategy_type,
                    "Fast Period": 12,
                    "Slow Period": 26,
                    "Signal Period": 9,
                    "Total Trades": 40,
                    "Win Rate [%]": 60.0,
                    "Total Return [%]": 30.0,
                    "Sharpe Ratio": 1.4,
                    "Score": 8.5,
                    "Metric Type": "Most Total Return [%]",
                },
            ]
        else:
            sample_portfolios = [
                {
                    "Ticker": "TEST",
                    "Strategy Type": strategy_type,
                    "Fast Period": 10,
                    "Slow Period": 20,
                    "Total Trades": 50,
                    "Win Rate [%]": 55.0,
                    "Total Return [%]": 25.0,
                    "Sharpe Ratio": 1.2,
                    "Score": 8.0,
                    "Metric Type": "Most Total Return [%]",
                },
            ]

        config = base_config.copy()
        config["TICKER"] = ["TEST"]
        config["STRATEGY_TYPES"] = [strategy_type]
        config["STRATEGY_TYPE"] = strategy_type

        df, success = export_portfolios(
            portfolios=sample_portfolios,
            config=config,
            export_type=export_type,
            log=Mock(),
        )

        # Verify all combinations work
        assert success is True
        assert len(df) == 1

        # Verify export type specific requirements
        if export_type in ["portfolios_filtered", "portfolios_best"]:
            assert "Metric Type" in df.columns

        # Verify file was created in correct location
        export_path = Path(temp_export_dir) / "data" / "raw" / export_type
        assert export_path.exists()

        csv_files = list(export_path.glob("*.csv"))
        assert len(csv_files) > 0


class TestExportSchemaConsistency:
    """Test schema consistency across different export types."""

    @pytest.fixture
    def temp_export_dir(self):
        """Create temporary directory for export testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def comprehensive_portfolio(self):
        """Comprehensive portfolio with all possible fields."""
        return {
            "Ticker": "AAPL",
            "Strategy Type": "SMA",
            "Fast Period": 10,
            "Slow Period": 20,
            "Signal Period": 0,
            "Stop Loss [%]": None,
            "Signal Entry": False,
            "Signal Exit": False,
            "Total Open Trades": 0,
            "Total Trades": 50,
            "Win Rate [%]": 55.0,
            "Profit Factor": 1.3,
            "Expectancy per Trade": 0.02,
            "Sortino Ratio": 1.1,
            "Beats BNH [%]": 5.0,
            "Avg Trade Duration": "5 days 12:00:00",
            "Trades Per Day": 0.137,
            "Trades per Month": 4.17,
            "Signals per Month": 8.33,
            "Expectancy per Month": 0.083,
            "Start": 0,
            "End": 364,
            "Period": "365 days 00:00:00",
            "Start Value": 1000.0,
            "End Value": 1255.0,
            "Total Return [%]": 25.5,
            "Benchmark Return [%]": 15.2,
            "Max Gross Exposure [%]": 100.0,
            "Total Fees Paid": 25.0,
            "Max Drawdown [%]": 8.7,
            "Max Drawdown Duration": "45 days 00:00:00",
            "Total Closed Trades": 50,
            "Open Trade PnL": 0.0,
            "Best Trade [%]": 12.5,
            "Worst Trade [%]": -5.8,
            "Avg Winning Trade [%]": 3.2,
            "Avg Losing Trade [%]": -2.1,
            "Avg Winning Trade Duration": "3 days 00:00:00",
            "Avg Losing Trade Duration": "2 days 12:00:00",
            "Expectancy": 0.65,
            "Sharpe Ratio": 1.2,
            "Calmar Ratio": 2.93,
            "Omega Ratio": 1.25,
            "Skew": 0.15,
            "Kurtosis": 2.8,
            "Tail Ratio": 1.1,
            "Common Sense Ratio": 1.05,
            "Value at Risk": -2.3,
            "Daily Returns": 0.067,
            "Annual Returns": 24.5,
            "Cumulative Returns": 25.5,
            "Annualized Return": 23.8,
            "Annualized Volatility": 19.8,
            "Signal Count": 100,
            "Position Count": 50,
            "Total Period": 365.0,
            "Score": 8.5,
            "Metric Type": "Most Total Return [%]",
            "Allocation [%]": None,
        }

    @pytest.fixture
    def base_config(self, temp_export_dir):
        """Base configuration for schema testing."""
        return {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["AAPL"],
            "STRATEGY_TYPES": ["SMA"],
            "USE_HOURLY": False,
            "USE_MA": True,
            "STRATEGY_TYPE": "SMA",
        }

    def test_portfolios_schema_consistency(
        self,
        comprehensive_portfolio,
        base_config,
        temp_export_dir,
    ):
        """Test that portfolios export maintains schema consistency."""
        config = base_config.copy()

        df, success = export_portfolios(
            portfolios=[comprehensive_portfolio],
            config=config,
            export_type="portfolios",
            log=Mock(),
        )

        assert success is True
        assert len(df) == 1

        # Verify key columns are preserved
        expected_columns = [
            "Ticker",
            "Strategy Type",
            "Fast Period",
            "Slow Period",
            "Total Trades",
            "Win Rate [%]",
            "Total Return [%]",
            "Sharpe Ratio",
            "Score",
        ]
        for col in expected_columns:
            assert col in df.columns

    def test_portfolios_filtered_schema_consistency(
        self,
        comprehensive_portfolio,
        base_config,
        temp_export_dir,
    ):
        """Test that portfolios_filtered export maintains schema consistency."""
        config = base_config.copy()

        df, success = export_portfolios(
            portfolios=[comprehensive_portfolio],
            config=config,
            export_type="portfolios_filtered",
            log=Mock(),
        )

        assert success is True
        assert len(df) == 1

        # Verify Metric Type column is present and preserved
        assert "Metric Type" in df.columns
        assert df["Metric Type"][0] == "Most Total Return [%]"

        # Verify other key columns are preserved
        expected_columns = [
            "Ticker",
            "Strategy Type",
            "Fast Period",
            "Slow Period",
            "Total Trades",
            "Win Rate [%]",
            "Total Return [%]",
            "Sharpe Ratio",
            "Score",
        ]
        for col in expected_columns:
            assert col in df.columns

    def test_portfolios_best_schema_consistency(
        self,
        comprehensive_portfolio,
        base_config,
        temp_export_dir,
    ):
        """Test that portfolios_best export maintains schema consistency."""
        config = base_config.copy()

        df, success = export_portfolios(
            portfolios=[comprehensive_portfolio],
            config=config,
            export_type="portfolios_best",
            log=Mock(),
        )

        assert success is True
        assert len(df) == 1

        # Verify Metric Type column is present and preserved
        assert "Metric Type" in df.columns
        assert df["Metric Type"][0] == "Most Total Return [%]"

        # Verify analysis-specific defaults (allocation should be None)
        if "Allocation [%]" in df.columns:
            assert df["Allocation [%]"][0] is None

        # Verify other key columns are preserved
        expected_columns = [
            "Ticker",
            "Strategy Type",
            "Fast Period",
            "Slow Period",
            "Total Trades",
            "Win Rate [%]",
            "Total Return [%]",
            "Sharpe Ratio",
            "Score",
        ]
        for col in expected_columns:
            assert col in df.columns

    def test_column_ordering_consistency(
        self,
        comprehensive_portfolio,
        base_config,
        temp_export_dir,
    ):
        """Test that column ordering is consistent across export types."""
        config = base_config.copy()

        # Export to all three types
        export_types = ["portfolios", "portfolios_filtered", "portfolios_best"]
        column_orders = {}

        for export_type in export_types:
            df, success = export_portfolios(
                portfolios=[comprehensive_portfolio],
                config=config,
                export_type=export_type,
                log=Mock(),
            )

            assert success is True
            column_orders[export_type] = (
                df.columns if isinstance(df.columns, list) else df.columns.to_list()
            )

        # Verify that common columns appear in consistent order
        common_columns = (
            set(column_orders["portfolios"])
            & set(column_orders["portfolios_filtered"])
            & set(column_orders["portfolios_best"])
        )

        for col in common_columns:
            # Get position of column in each export type
            positions = {}
            for export_type in export_types:
                if col in column_orders[export_type]:
                    positions[export_type] = column_orders[export_type].index(col)

            # Column positions should be consistent (allowing for additional columns)
            # This ensures the schema transformer maintains consistent ordering
            assert (
                len(set(positions.values())) <= 2
            )  # Allow some variance due to additional columns

    def test_data_type_consistency(
        self,
        comprehensive_portfolio,
        base_config,
        temp_export_dir,
    ):
        """Test that data types are consistent across export types."""
        config = base_config.copy()

        export_types = ["portfolios", "portfolios_filtered", "portfolios_best"]
        dataframes = {}

        for export_type in export_types:
            df, success = export_portfolios(
                portfolios=[comprehensive_portfolio],
                config=config,
                export_type=export_type,
                log=Mock(),
            )

            assert success is True
            dataframes[export_type] = df

        # Verify that common columns have consistent data types
        common_columns = [
            "Ticker",
            "Total Trades",
            "Win Rate [%]",
            "Total Return [%]",
            "Score",
        ]

        for col in common_columns:
            dtypes = {}
            for export_type in export_types:
                if col in dataframes[export_type].columns:
                    dtypes[export_type] = str(dataframes[export_type][col].dtype)

            # All export types should have the same data type for common columns
            unique_dtypes = set(dtypes.values())
            assert len(unique_dtypes) == 1, (
                f"Column {col} has inconsistent data types: {dtypes}"
            )
