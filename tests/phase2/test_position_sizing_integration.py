"""Tests for PositionSizingPortfolioIntegration."""

import tempfile
from unittest.mock import Mock, patch

from app.tools.portfolio import PositionSizingPortfolioIntegration


class TestPositionSizingPortfolioIntegration:
    """Test cases for PositionSizingPortfolioIntegration."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.integration = PositionSizingPortfolioIntegration(self.temp_dir)

    def test_initialization(self):
        """Test integration initialization."""
        assert self.integration.base_dir.name == self.temp_dir.split("/")[-1]
        assert self.integration.balance_service is not None
        assert self.integration.position_tracker is not None
        assert self.integration.drawdown_calculator is not None
        assert self.integration.strategies_integration is not None
        assert self.integration.dual_portfolio is not None
        assert self.integration.cvar_calculator is not None
        assert self.integration.kelly_sizer is not None
        assert self.integration.risk_allocator is not None
        assert self.integration.allocation_optimizer is not None
        assert self.integration.price_integration is not None

    @patch("app.tools.position_sizing.PriceDataIntegration.get_current_price")
    @patch("app.tools.risk.CVaRCalculator.calculate_trading_cvar")
    @patch("app.tools.risk.CVaRCalculator.calculate_investment_cvar")
    def test_create_position_sizing_row(
        self, mock_investment_cvar, mock_trading_cvar, mock_price
    ):
        """Test creating a position sizing row."""
        # Setup mocks
        mock_trading_cvar.return_value = -0.0234
        mock_investment_cvar.return_value = -0.0156
        mock_price.return_value = 150.0

        # Setup manual data
        manual_data = {
            "num_primary_trades": 12,
            "num_outlier_trades": 3,
            "kelly_criterion_value": 0.20,
            "position_value": 5000.0,
            "stop_loss_distance": 0.05,
            "allocation_percentage": 10.0,
            "portfolio_type": "Risk_On",
            "current_price": 150.0,
            "entry_price": 148.0,
        }

        # Setup account balances
        self.integration.balance_service.update_multiple_balances(
            {"IBKR": 50000.0, "Bybit": 25000.0, "Cash": 10000.0}
        )

        row = self.integration.create_position_sizing_row(
            ticker="AAPL",
            strategy_type="SMA",
            fast_period=20,
            slow_period=50,
            manual_data=manual_data,
        )

        # Verify basic fields
        assert row["ticker"] == "AAPL"
        assert row["strategy_type"] == "SMA"
        assert row["fast_period"] == 20
        assert row["slow_period"] == 50

        # Verify account balances
        assert row["IBKR_Balance"] == 50000.0
        assert row["Bybit_Balance"] == 25000.0
        assert row["Cash_Balance"] == 10000.0
        assert row["Net_Worth"] == 85000.0

        # Verify position data
        assert row["Position_Value"] == 5000.0
        assert row["Stop_Loss_Distance"] == 0.05
        assert row["Max_Risk_Amount"] == 250.0  # 5000 * 0.05

        # Verify CVaR data
        assert row["CVaR_Trading"] == -0.0234
        assert row["CVaR_Investment"] == -0.0156

        # Verify Kelly data
        assert row["Num_Primary_Trades"] == 12
        assert row["Num_Outlier_Trades"] == 3
        assert row["Kelly_Criterion_Value"] == 0.20

        # Verify price data
        assert row["Current_Price"] == 150.0
        assert row["Entry_Price"] == 148.0

    def test_create_position_sizing_portfolio(self):
        """Test creating a position sizing portfolio DataFrame."""
        # Setup account balances
        self.integration.balance_service.update_multiple_balances(
            {"IBKR": 60000.0, "Bybit": 30000.0, "Cash": 15000.0}
        )

        tickers = ["AAPL", "TSLA", "BTC-USD"]
        manual_data_by_ticker = {
            "AAPL": {"position_value": 5000.0, "stop_loss_distance": 0.05},
            "TSLA": {"position_value": 7500.0, "stop_loss_distance": 0.08},
            "BTC-USD": {"position_value": 10000.0, "stop_loss_distance": 0.10},
        }

        # Mock external dependencies
        with (
            patch.multiple(
                self.integration.cvar_calculator,
                calculate_trading_cvar=Mock(return_value=-0.025),
                calculate_investment_cvar=Mock(return_value=-0.018),
            ),
            patch.object(
                self.integration.price_integration,
                "get_current_price",
                side_effect=[150.0, 800.0, 45000.0],  # Prices for AAPL, TSLA, BTC-USD
            ),
        ):
            df = self.integration.create_position_sizing_portfolio(
                tickers, manual_data_by_ticker
            )

        # Verify DataFrame structure
        assert len(df) == 3
        assert "ticker" in df.columns
        assert "Net_Worth" in df.columns
        assert "Position_Value" in df.columns
        assert "CVaR_Trading" in df.columns

        # Verify ticker data
        tickers_in_df = df.select("ticker").to_series().to_list()
        assert "AAPL" in tickers_in_df
        assert "TSLA" in tickers_in_df
        assert "BTC-USD" in tickers_in_df

    def test_validate_position_sizing_data(self):
        """Test position sizing data validation."""
        # Valid data
        valid_data = {
            "IBKR_Balance": 50000.0,
            "Bybit_Balance": 25000.0,
            "Cash_Balance": 10000.0,
            "Net_Worth": 85000.0,
            "Position_Value": 5000.0,
            "Stop_Loss_Distance": 0.05,
            "Max_Risk_Amount": 250.0,
            "Risk_Allocation_Amount": 10030.0,  # 85000 * 0.118
        }

        is_valid, results = self.integration.validate_position_sizing_data(valid_data)

        assert is_valid
        assert results["is_valid"]
        assert len(results["validation_errors"]) == 0
        assert results["excel_formula_matches"]["Net_Worth"]
        assert results["excel_formula_matches"]["Max_Risk_Amount"]
        assert results["excel_formula_matches"]["Risk_Allocation_Amount"]

    def test_validate_position_sizing_data_invalid(self):
        """Test position sizing data validation with invalid data."""
        # Invalid data - missing required fields and calculation errors
        invalid_data = {
            "IBKR_Balance": 50000.0,
            "Bybit_Balance": 25000.0,
            "Cash_Balance": 10000.0,
            "Net_Worth": 90000.0,  # Should be 85000
            "Position_Value": -5000.0,  # Negative value - invalid
            "Stop_Loss_Distance": 1.5,  # > 1.0 - invalid
            "Max_Risk_Amount": 300.0,  # Should be 250.0 if calculated correctly
        }

        is_valid, results = self.integration.validate_position_sizing_data(invalid_data)

        assert not is_valid
        assert not results["is_valid"]
        assert len(results["validation_errors"]) > 0
        assert "currency value cannot be negative" in str(results["validation_errors"])
        assert "percentage must be between 0 and 1" in str(results["validation_errors"])

    def test_import_manual_data_from_excel(self):
        """Test importing manual data from Excel format."""
        excel_data = {
            "account_balances": {"IBKR": 50000, "Bybit": 25000, "Cash": 10000},
            "positions": {
                "AAPL": {"position_value": 5000, "stop_loss_distance": 0.05},
                "TSLA": {"position_value": 7500, "stop_loss_distance": 0.08},
            },
            "portfolio_holdings": {
                "Risk_On": {"AAPL": {"allocation": 15}, "TSLA": {"allocation": 20}},
                "Investment": {"SPY": {"allocation": 40}},
            },
        }

        self.integration.import_manual_data_from_excel(excel_data)

        # Verify account balances were imported
        net_worth = self.integration.balance_service.calculate_net_worth()
        assert net_worth.total_net_worth == 85000.0

        # Verify position data was imported
        aapl_position = self.integration.position_tracker.get_position_entry("AAPL")
        assert aapl_position is not None
        assert aapl_position.position_value == 5000.0

        aapl_drawdown = self.integration.drawdown_calculator.get_drawdown_entry("AAPL")
        assert aapl_drawdown is not None
        assert aapl_drawdown.stop_loss_distance == 0.05

    def test_get_comprehensive_portfolio_summary(self):
        """Test comprehensive portfolio summary generation."""
        # Setup some data
        self.integration.balance_service.update_multiple_balances(
            {"IBKR": 40000.0, "Bybit": 20000.0, "Cash": 5000.0}
        )

        self.integration.position_tracker.add_position_entry("AAPL", 3000.0, 0.04)
        self.integration.dual_portfolio.add_portfolio_holding(
            "AAPL", "Risk_On", 3000.0, 15.0, risk_amount=120.0
        )

        # Mock strategies integration to avoid file dependencies
        with patch.object(
            self.integration.strategies_integration,
            "get_comprehensive_summary",
            return_value={
                "strategies_count": {"total": 17, "stable": 12},
                "concurrency": {"average": 9.5, "maximum": 17},
                "data_quality": {"stability_score": 0.526, "file_freshness": True},
            },
        ):
            summary = self.integration.get_comprehensive_portfolio_summary()

        # Verify summary structure
        assert "timestamp" in summary
        assert "account_balances" in summary
        assert "positions" in summary
        assert "risk_management" in summary
        assert "strategies" in summary
        assert "portfolio_coordination" in summary
        assert "schema_info" in summary
        assert "data_integrity" in summary

        # Verify specific values
        assert summary["account_balances"]["net_worth"]["total"] == 65000.0
        assert summary["positions"]["total_value"] == 3000.0
        assert summary["positions"]["count"] == 1

    def test_generate_excel_compatible_export(self):
        """Test Excel-compatible export generation."""
        # Setup minimal data
        self.integration.balance_service.update_account_balance("IBKR", 30000.0)

        tickers = ["AAPL"]

        # Mock dependencies to avoid external calls
        with (
            patch.multiple(
                self.integration.cvar_calculator,
                calculate_trading_cvar=Mock(return_value=-0.02),
                calculate_investment_cvar=Mock(return_value=-0.015),
            ),
            patch.object(
                self.integration.price_integration,
                "get_current_price",
                return_value=150.0,
            ),
            patch.object(
                self.integration.strategies_integration,
                "get_strategies_count_data",
                return_value=Mock(
                    total_strategies_analyzed=17,
                    stable_strategies_count=12,
                    avg_concurrent_strategies=9.5,
                    max_concurrent_strategies=17,
                ),
            ),
        ):
            export_data = self.integration.generate_excel_compatible_export(tickers)

        # Verify export structure
        assert "portfolio_data" in export_data
        assert "summary" in export_data
        assert "manual_entry_template" in export_data
        assert "formula_references" in export_data
        assert "export_metadata" in export_data

        # Verify portfolio data
        assert len(export_data["portfolio_data"]) == 1
        assert export_data["portfolio_data"][0]["ticker"] == "AAPL"

        # Verify metadata
        metadata = export_data["export_metadata"]
        assert metadata["schema_version"] == "position_sizing_v1.0"
        assert "export_timestamp" in metadata
        assert "total_columns" in metadata

    def test_schema_integration(self):
        """Test schema integration and validation."""
        # Verify schema components are accessible
        assert self.integration.schema is not None
        assert self.integration.validator is not None

        # Test schema summary
        schema_summary = self.integration.schema.get_schema_summary()
        assert "total_columns" in schema_summary
        assert "manual_entry_columns" in schema_summary
        assert "auto_calculated_columns" in schema_summary
        assert "column_groups" in schema_summary

        # Verify reasonable column counts
        assert schema_summary["total_columns"] > 20  # Should have many columns
        assert schema_summary["manual_entry_columns"] > 5  # Several manual entry fields
        assert (
            schema_summary["auto_calculated_columns"] > 5
        )  # Several calculated fields
