"""Tests for DualPortfolioManager."""

import tempfile
from datetime import datetime

import pytest

from app.tools.accounts import (
    DualPortfolioManager,
    PortfolioHolding,
    PortfolioSummary,
    PortfolioType,
)


class TestDualPortfolioManager:
    """Test cases for DualPortfolioManager."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DualPortfolioManager(self.temp_dir)

    def test_initialization(self):
        """Test manager initialization."""
        assert self.manager.base_dir.name == self.temp_dir.split("/")[-1]
        assert self.manager.data_dir.exists()
        assert self.manager.holdings_file.name == "dual_portfolio_holdings.json"

    def test_add_portfolio_holding(self):
        """Test adding a portfolio holding."""
        holding = self.manager.add_portfolio_holding(
            symbol="AAPL",
            portfolio_type=PortfolioType.RISK_ON,
            position_value=5000.0,
            allocation_percentage=10.0,
            risk_amount=250.0,
            stop_loss_distance=0.05,
        )

        assert holding.symbol == "AAPL"
        assert holding.portfolio_type == PortfolioType.RISK_ON
        assert holding.position_value == 5000.0
        assert holding.allocation_percentage == 10.0
        assert holding.risk_amount == 250.0
        assert holding.stop_loss_distance == 0.05
        assert isinstance(holding.entry_date, datetime)

    def test_add_portfolio_holding_validation(self):
        """Test portfolio holding validation."""
        # Test empty symbol
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            self.manager.add_portfolio_holding("", PortfolioType.RISK_ON, 1000, 10)

        # Test invalid portfolio type
        with pytest.raises(ValueError, match="Invalid portfolio type"):
            self.manager.add_portfolio_holding("AAPL", "INVALID", 1000, 10)

        # Test negative position value
        with pytest.raises(ValueError, match="Position value must be positive"):
            self.manager.add_portfolio_holding("AAPL", PortfolioType.RISK_ON, -1000, 10)

        # Test invalid allocation percentage
        with pytest.raises(
            ValueError, match="Allocation percentage must be between 0 and 100"
        ):
            self.manager.add_portfolio_holding("AAPL", PortfolioType.RISK_ON, 1000, 150)

    def test_add_holding_with_string_portfolio_type(self):
        """Test adding holding with string portfolio type."""
        holding = self.manager.add_portfolio_holding(
            symbol="BTC-USD",
            portfolio_type="Investment",
            position_value=10000.0,
            allocation_percentage=25.0,
        )

        assert holding.portfolio_type == PortfolioType.INVESTMENT

    def test_get_portfolio_holding(self):
        """Test getting a portfolio holding."""
        # Add holding first
        self.manager.add_portfolio_holding(
            symbol="TSLA",
            portfolio_type=PortfolioType.RISK_ON,
            position_value=7500.0,
            allocation_percentage=15.0,
        )

        # Retrieve holding
        holding = self.manager.get_portfolio_holding("TSLA")
        assert holding is not None
        assert holding.symbol == "TSLA"
        assert holding.position_value == 7500.0

        # Test non-existent holding
        holding = self.manager.get_portfolio_holding("NONEXISTENT")
        assert holding is None

    def test_update_portfolio_holding(self):
        """Test updating a portfolio holding."""
        # Add initial holding
        self.manager.add_portfolio_holding(
            symbol="NVDA",
            portfolio_type=PortfolioType.RISK_ON,
            position_value=3000.0,
            allocation_percentage=8.0,
        )

        # Update holding
        updated_holding = self.manager.update_portfolio_holding(
            symbol="NVDA",
            position_value=4000.0,
            allocation_percentage=12.0,
            risk_amount=200.0,
        )

        assert updated_holding is not None
        assert updated_holding.position_value == 4000.0
        assert updated_holding.allocation_percentage == 12.0
        assert updated_holding.risk_amount == 200.0

    def test_get_holdings_by_portfolio_type(self):
        """Test getting holdings by portfolio type."""
        # Add holdings for both types
        self.manager.add_portfolio_holding("AAPL", PortfolioType.RISK_ON, 5000, 10)
        self.manager.add_portfolio_holding("TSLA", PortfolioType.RISK_ON, 7500, 15)
        self.manager.add_portfolio_holding("SPY", PortfolioType.INVESTMENT, 15000, 50)
        self.manager.add_portfolio_holding("QQQ", PortfolioType.INVESTMENT, 10000, 33)

        # Test Risk On holdings
        risk_on_holdings = self.manager.get_holdings_by_portfolio_type(
            PortfolioType.RISK_ON
        )
        assert len(risk_on_holdings) == 2
        symbols = [h.symbol for h in risk_on_holdings]
        assert "AAPL" in symbols
        assert "TSLA" in symbols

        # Test Investment holdings
        investment_holdings = self.manager.get_holdings_by_portfolio_type(
            PortfolioType.INVESTMENT
        )
        assert len(investment_holdings) == 2
        symbols = [h.symbol for h in investment_holdings]
        assert "SPY" in symbols
        assert "QQQ" in symbols

    def test_get_holdings_by_string_portfolio_type(self):
        """Test getting holdings by string portfolio type."""
        self.manager.add_portfolio_holding("BTC-USD", "Risk_On", 8000, 20)

        holdings = self.manager.get_holdings_by_portfolio_type("Risk_On")
        assert len(holdings) == 1
        assert holdings[0].symbol == "BTC-USD"

    def test_calculate_portfolio_summary(self):
        """Test portfolio summary calculation."""
        # Add holdings
        self.manager.add_portfolio_holding(
            "AAPL", PortfolioType.RISK_ON, 5000, 10, risk_amount=250
        )
        self.manager.add_portfolio_holding(
            "TSLA", PortfolioType.RISK_ON, 7500, 15, risk_amount=375
        )
        self.manager.add_portfolio_holding("SPY", PortfolioType.INVESTMENT, 15000, 50)
        self.manager.add_portfolio_holding("QQQ", PortfolioType.INVESTMENT, 10000, 33)

        summary = self.manager.calculate_portfolio_summary()

        assert summary.risk_on_total == 12500.0  # 5000 + 7500
        assert summary.investment_total == 25000.0  # 15000 + 10000
        assert summary.combined_total == 37500.0  # 12500 + 25000
        assert summary.risk_on_count == 2
        assert summary.investment_count == 2
        assert summary.total_risk_amount == 625.0  # 250 + 375

        # Check allocations (percentages)
        assert abs(summary.risk_on_allocation - 33.33) < 0.1  # 12500/37500 * 100
        assert abs(summary.investment_allocation - 66.67) < 0.1  # 25000/37500 * 100

        # Check portfolio risk percentage
        assert abs(summary.portfolio_risk_percentage - 1.67) < 0.1  # 625/37500 * 100

    def test_remove_portfolio_holding(self):
        """Test removing a portfolio holding."""
        # Add holding
        self.manager.add_portfolio_holding("AMZN", PortfolioType.RISK_ON, 6000, 12)

        # Verify it exists
        holding = self.manager.get_portfolio_holding("AMZN")
        assert holding is not None

        # Remove it
        removed = self.manager.remove_portfolio_holding("AMZN")
        assert removed is True

        # Verify it's gone
        holding = self.manager.get_portfolio_holding("AMZN")
        assert holding is None

        # Test removing non-existent holding
        removed = self.manager.remove_portfolio_holding("NONEXISTENT")
        assert removed is False

    def test_import_portfolio_from_dict(self):
        """Test importing portfolio from dictionary."""
        portfolio_dict = {
            "Risk_On": {
                "BTC-USD": {
                    "position_value": 10000,
                    "allocation": 25,
                    "risk_amount": 800,
                },
                "AAPL": {"position_value": 5000, "allocation": 12.5, "stop_loss": 0.05},
            },
            "Investment": {
                "SPY": {"position_value": 15000, "allocation": 50},
                "QQQ": {"position_value": 10000, "allocation": 33.3},
            },
        }

        self.manager.import_portfolio_from_dict(portfolio_dict)

        # Verify holdings were imported
        btc_holding = self.manager.get_portfolio_holding("BTC-USD")
        assert btc_holding is not None
        assert btc_holding.portfolio_type == PortfolioType.RISK_ON
        assert btc_holding.position_value == 10000
        assert btc_holding.risk_amount == 800

        spy_holding = self.manager.get_portfolio_holding("SPY")
        assert spy_holding is not None
        assert spy_holding.portfolio_type == PortfolioType.INVESTMENT
        assert spy_holding.position_value == 15000

    def test_get_excel_compatible_summary(self):
        """Test Excel-compatible summary generation."""
        from unittest.mock import Mock, patch

        # Add some holdings
        self.manager.add_portfolio_holding(
            "AAPL", PortfolioType.RISK_ON, 5000, 10, risk_amount=250
        )
        self.manager.add_portfolio_holding("SPY", PortfolioType.INVESTMENT, 15000, 50)

        # Mock the external services to avoid file dependencies
        with patch.object(
            self.manager.strategies_integration,
            "get_strategies_count_data",
            return_value=Mock(
                total_strategies_analyzed=17,
                stable_strategies_count=12,
                avg_concurrent_strategies=9.5,
                max_concurrent_strategies=17,
            ),
        ):
            summary = self.manager.get_excel_compatible_summary()

        assert "Risk_On_Total" in summary
        assert "Investment_Total" in summary
        assert "Combined_Total" in summary
        assert "Portfolio_Risk_Percentage" in summary
        assert "Last_Updated" in summary

        assert summary["Risk_On_Total"] == 5000.0
        assert summary["Investment_Total"] == 15000.0
        assert summary["Combined_Total"] == 20000.0

    def test_empty_portfolio_summary(self):
        """Test portfolio summary with no holdings."""
        summary = self.manager.calculate_portfolio_summary()

        assert summary.risk_on_total == 0.0
        assert summary.investment_total == 0.0
        assert summary.combined_total == 0.0
        assert summary.risk_on_count == 0
        assert summary.investment_count == 0
        assert summary.total_risk_amount == 0.0
        assert summary.portfolio_risk_percentage == 0.0
        assert summary.risk_on_allocation == 0.0
        assert summary.investment_allocation == 0.0

    def test_file_persistence(self):
        """Test that holdings persist across manager instances."""
        # Add holding with first manager instance
        self.manager.add_portfolio_holding("MSFT", PortfolioType.INVESTMENT, 8000, 20)

        # Create new manager instance with same directory
        new_manager = DualPortfolioManager(self.temp_dir)

        # Verify holding persists
        holding = new_manager.get_portfolio_holding("MSFT")
        assert holding is not None
        assert holding.position_value == 8000.0
