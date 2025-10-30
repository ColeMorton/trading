"""
Integration tests for Position Sizing Phase 1 Components

Tests integration between CVaR calculator, Kelly criterion, allocation optimizer,
and risk allocation systems with realistic data.
"""

from unittest.mock import patch

from app.tools.allocation.efficient_frontier_integration import AllocationOptimizer
from app.tools.position_sizing.kelly_criterion import KellyCriterionSizer
from app.tools.position_sizing.risk_allocation import RiskAllocationCalculator
from app.tools.risk.cvar_calculator import CVaRCalculator


class TestPositionSizingIntegration:
    """Integration tests for Phase 1 position sizing components."""

    def setup_method(self):
        """Set up test fixtures with realistic portfolio data."""
        self.cvar_calculator = CVaRCalculator()
        self.kelly_sizer = KellyCriterionSizer()
        self.risk_allocator = RiskAllocationCalculator()
        self.allocation_optimizer = AllocationOptimizer()

        # Realistic portfolio parameters
        self.net_worth = 250000.0  # $250k portfolio
        self.num_primary = 85  # 85 primary trades
        self.num_outliers = 15  # 15 outlier trades
        self.kelly_criterion = 0.25  # 25% Kelly optimal

    @patch("app.tools.risk.cvar_calculator.CVaRCalculator.calculate_trading_cvar")
    @patch("app.tools.risk.cvar_calculator.CVaRCalculator.calculate_investment_cvar")
    def test_complete_excel_formula_chain(
        self,
        mock_investment_cvar,
        mock_trading_cvar,
    ):
        """Test complete Excel formula chain B2→B5→B12/E11→B17-B21."""
        # Mock CVaR values from actual concurrency data
        mock_trading_cvar.return_value = -0.10658084758791905
        mock_investment_cvar.return_value = -0.0721535590852867

        # Excel B2: Net Worth
        net_worth = self.net_worth  # $250,000

        # Excel B5: Risk allocation (=$B$2*0.118)
        risk_allocation = self.risk_allocator.calculate_excel_b5_equivalent(net_worth)
        expected_b5 = 250000.0 * 0.118  # $29,500
        assert risk_allocation == expected_b5

        # Excel B12: Trading risk amount (=E11*$B$2)
        trading_risk = self.cvar_calculator.calculate_excel_b12_equivalent(net_worth)
        expected_b12 = abs(-0.10658084758791905 * 250000.0)  # $26,645.21
        assert abs(trading_risk - expected_b12) < 0.01

        # Excel E11: Investment CVaR
        investment_cvar = self.cvar_calculator.calculate_excel_e11_equivalent(net_worth)
        expected_e11 = -0.0721535590852867
        assert investment_cvar == expected_e11

        # Excel B17-B21: Kelly analysis
        b20_confidence = self.kelly_sizer.calculate_excel_b20_equivalent(
            self.num_primary,
            self.num_outliers,
        )
        expected_b20 = 85 / (85 + 15)  # 0.85
        assert b20_confidence == expected_b20

        b21_adjusted_kelly = self.kelly_sizer.calculate_excel_b21_equivalent(
            self.num_primary,
            self.num_outliers,
            self.kelly_criterion,
        )
        expected_b21 = 0.25 * 0.85  # 0.2125
        assert b21_adjusted_kelly == expected_b21

    def test_position_sizing_workflow(self):
        """Test realistic position sizing workflow."""
        # Step 1: Calculate risk allocation (11.8% of portfolio)
        risk_allocation = self.risk_allocator.calculate_risk_allocation(self.net_worth)
        assert risk_allocation.risk_amount == 29500.0  # $29.5k available for risk

        # Step 2: Apply Kelly criterion adjustment
        kelly_analysis = self.kelly_sizer.get_complete_kelly_analysis(
            self.num_primary,
            self.num_outliers,
            self.kelly_criterion,
            self.net_worth,
        )

        # Kelly-adjusted position size should be smaller than max risk
        assert kelly_analysis.recommended_position_size < risk_allocation.risk_amount
        assert kelly_analysis.recommended_position_size == 6268.75  # 29500 * 0.2125

        # Step 3: Position risk per individual position
        single_position_risk = self.risk_allocator.calculate_position_risk_limit(
            self.net_worth,
            1,
        )
        assert single_position_risk == 29500.0  # Full allocation for 1 position

        # Multiple positions
        five_position_risk = self.risk_allocator.calculate_position_risk_limit(
            self.net_worth,
            5,
        )
        assert five_position_risk == 5900.0  # $29.5k / 5 positions

    @patch(
        "app.tools.allocation.efficient_frontier_integration.AllocationOptimizer.get_price_data",
    )
    def test_portfolio_allocation_integration(self, mock_price_data):
        """Test integration with portfolio allocation optimization."""
        # Mock price data
        mock_price_data.side_effect = lambda symbol: {
            "AAPL": 150.0,
            "MSFT": 250.0,
            "GOOGL": 2500.0,
        }.get(symbol, 100.0)

        # Get current prices for portfolio
        symbols = ["AAPL", "MSFT", "GOOGL"]
        prices = self.allocation_optimizer.get_multiple_prices(symbols)

        assert prices["AAPL"] == 150.0
        assert prices["MSFT"] == 250.0
        assert prices["GOOGL"] == 2500.0

        # Calculate position values with risk allocation
        total_risk_budget = self.risk_allocator.calculate_excel_b5_equivalent(
            self.net_worth,
        )

        # Example allocation percentages (would come from efficient frontier)
        allocations = {"AAPL": 40.0, "MSFT": 35.0, "GOOGL": 25.0}

        position_values = self.allocation_optimizer.calculate_position_values(
            allocations,
            total_risk_budget,
        )

        assert position_values["AAPL"] == 11800.0  # 40% of $29.5k
        assert position_values["MSFT"] == 10325.0  # 35% of $29.5k
        assert position_values["GOOGL"] == 7375.0  # 25% of $29.5k

    def test_risk_utilization_monitoring(self):
        """Test risk utilization monitoring across multiple positions."""
        # Simulate current portfolio positions
        current_positions = {
            "AAPL": 8000.0,  # $8k risk exposure
            "MSFT": 6000.0,  # $6k risk exposure
            "BTC-USD": 4000.0,  # $4k risk exposure
        }

        total_current_exposure = sum(current_positions.values())  # $18k

        utilization = self.risk_allocator.calculate_risk_utilization(
            self.net_worth,
            total_current_exposure,
        )

        assert utilization["allocated_risk"] == 29500.0  # Total allocation
        assert utilization["current_exposure"] == 18000.0  # Current usage
        assert abs(utilization["utilization_percentage"] - 61.02) < 0.01  # 18k/29.5k
        assert utilization["remaining_capacity"] == 11500.0  # Available capacity
        assert not utilization["is_over_allocated"]  # Within limits

    def test_multi_account_coordination(self):
        """Test coordination across multiple trading accounts."""
        account_balances = {
            "IBKR": 150000.0,  # $150k in Interactive Brokers
            "Bybit": 75000.0,  # $75k in Bybit
            "Cash": 25000.0,  # $25k in cash
        }

        # Calculate risk allocation per account
        account_allocations = self.risk_allocator.calculate_multiple_account_allocation(
            account_balances,
        )

        # Verify account-specific allocations
        assert account_allocations["IBKR"].risk_amount == 17700.0  # 150k * 11.8%
        assert account_allocations["Bybit"].risk_amount == 8850.0  # 75k * 11.8%
        assert account_allocations["Cash"].risk_amount == 2950.0  # 25k * 11.8%

        # Total should match single calculation
        total_risk = sum(alloc.risk_amount for alloc in account_allocations.values())
        single_calc = self.risk_allocator.calculate_excel_b5_equivalent(self.net_worth)
        assert total_risk == single_calc

    @patch("app.tools.risk.cvar_calculator.CVaRCalculator.get_portfolio_risk_metrics")
    def test_comprehensive_risk_metrics(self, mock_risk_metrics):
        """Test comprehensive risk metrics calculation."""
        # Mock realistic risk metrics
        mock_risk_metrics.return_value = {
            "trading_cvar_95": -0.10658084758791905,
            "investment_cvar_95": -0.0721535590852867,
            "trading_var_95": -0.050966740390329085,
            "investment_var_95": -0.04062868394886115,
        }

        risk_metrics = self.cvar_calculator.get_portfolio_risk_metrics()

        # Calculate dollar risk amounts
        trading_risk_amount = abs(risk_metrics["trading_cvar_95"] * self.net_worth)
        investment_risk_amount = abs(
            risk_metrics["investment_cvar_95"] * self.net_worth,
        )

        assert abs(trading_risk_amount - 26645.21) < 0.01
        assert abs(investment_risk_amount - 18038.39) < 0.01

        # Compare with risk allocation limit
        risk_limit = self.risk_allocator.calculate_excel_b5_equivalent(self.net_worth)

        # Trading risk should be within our 11.8% allocation
        assert trading_risk_amount < risk_limit  # CVaR risk < allocation limit

    def test_validation_and_error_handling(self):
        """Test validation and error handling across components."""
        # Test Kelly validation
        kelly_valid, _kelly_msg = self.kelly_sizer.validate_kelly_inputs(
            self.num_primary,
            self.num_outliers,
            self.kelly_criterion,
        )
        assert kelly_valid

        # Test risk percentage validation
        risk_valid, _risk_msg = self.risk_allocator.validate_risk_percentage(0.118)
        assert risk_valid

        # Test allocation constraint validation
        allocations = {"AAPL": 45.0, "MSFT": 35.0, "GOOGL": 20.0}
        (
            alloc_valid,
            _alloc_msg,
        ) = self.allocation_optimizer.validate_allocation_constraints(allocations)
        assert alloc_valid

    def test_excel_formula_consistency(self):
        """Test that all Excel formulas produce consistent results."""
        # This test ensures our implementation matches Excel calculations exactly

        # Known Excel values for validation
        excel_test_data = {
            "B2_net_worth": 250000.0,
            "B5_risk_allocation": 29500.0,  # =B2*0.118
            "B17_primary": 85,
            "B18_outliers": 15,
            "B19_kelly": 0.25,
            "B20_confidence": 0.85,  # =B17/(B17+B18)
            "B21_adjusted_kelly": 0.2125,  # =B19*B20
        }

        # Test each formula
        b5_result = self.risk_allocator.calculate_excel_b5_equivalent(
            excel_test_data["B2_net_worth"],
        )
        assert b5_result == excel_test_data["B5_risk_allocation"]

        b20_result = self.kelly_sizer.calculate_excel_b20_equivalent(
            excel_test_data["B17_primary"],
            excel_test_data["B18_outliers"],
        )
        assert b20_result == excel_test_data["B20_confidence"]

        b21_result = self.kelly_sizer.calculate_excel_b21_equivalent(
            excel_test_data["B17_primary"],
            excel_test_data["B18_outliers"],
            excel_test_data["B19_kelly"],
        )
        assert b21_result == excel_test_data["B21_adjusted_kelly"]
