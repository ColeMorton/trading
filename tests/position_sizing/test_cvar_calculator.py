"""
Unit tests for CVaR Calculator

Tests Excel B12/E11 formula accuracy against known values.
"""

from unittest.mock import mock_open, patch

import pytest

from app.tools.risk.cvar_calculator import CVaRCalculator


class TestCVaRCalculator:
    """Test CVaR calculator functionality and Excel formula accuracy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = CVaRCalculator()

        # Mock data matching actual concurrency files
        self.mock_trades_data = {
            "portfolio_metrics": {
                "risk": {
                    "combined_risk": {
                        "cvar_95": {"value": -0.10658084758791905},
                        "var_95": {"value": -0.050966740390329085},
                        "cvar_99": {"value": -0.23884351702880238},
                        "var_99": {"value": -0.12526210517785705},
                    }
                }
            }
        }

        self.mock_portfolio_data = {
            "portfolio_metrics": {
                "risk": {
                    "combined_risk": {
                        "cvar_95": {"value": -0.0721535590852867},
                        "var_95": {"value": -0.04062868394886115},
                        "cvar_99": {"value": -0.12570809534840688},
                        "var_99": {"value": -0.08846974801496799},
                    }
                }
            }
        }

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    @patch("pathlib.Path.exists")
    def test_calculate_trading_cvar(self, mock_exists, mock_json_load, mock_file):
        """Test trading CVaR calculation from trades.json."""
        mock_exists.return_value = True
        mock_json_load.return_value = self.mock_trades_data

        result = self.calculator.calculate_trading_cvar()

        assert result == -0.10658084758791905
        mock_file.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    @patch("pathlib.Path.exists")
    def test_calculate_investment_cvar(self, mock_exists, mock_json_load, mock_file):
        """Test investment CVaR calculation from portfolio.json."""
        mock_exists.return_value = True
        mock_json_load.return_value = self.mock_portfolio_data

        result = self.calculator.calculate_investment_cvar()

        assert result == -0.0721535590852867
        mock_file.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    @patch("pathlib.Path.exists")
    def test_excel_b12_equivalent(self, mock_exists, mock_json_load, mock_file):
        """Test Excel B12 formula: Trading CVaR * Net Worth."""
        mock_exists.return_value = True
        mock_json_load.return_value = self.mock_trades_data

        net_worth = 100000.0  # $100,000 portfolio
        expected = abs(-0.10658084758791905 * 100000.0)  # Should be positive

        result = self.calculator.calculate_excel_b12_equivalent(net_worth)

        assert result == expected
        assert result > 0  # Risk amount should be positive

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    @patch("pathlib.Path.exists")
    def test_excel_e11_equivalent(self, mock_exists, mock_json_load, mock_file):
        """Test Excel E11 formula: Investment CVaR."""
        mock_exists.return_value = True
        mock_json_load.return_value = self.mock_portfolio_data

        net_worth = 100000.0
        expected = -0.0721535590852867  # Should remain negative

        result = self.calculator.calculate_excel_e11_equivalent(net_worth)

        assert result == expected
        assert result < 0  # CVaR should be negative

    def test_get_portfolio_risk_metrics(self):
        """Test comprehensive risk metrics calculation."""

        # Mock the _load_json_file method to return different data based on file path
        def mock_load_json(file_path):
            if "trades.json" in str(file_path):
                return self.mock_trades_data
            return self.mock_portfolio_data

        with patch.object(
            self.calculator, "_load_json_file", side_effect=mock_load_json
        ):
            result = self.calculator.get_portfolio_risk_metrics()

            assert "trading_cvar_95" in result
            assert "investment_cvar_95" in result
            assert result["trading_cvar_95"] == -0.10658084758791905
            assert result["investment_cvar_95"] == -0.0721535590852867

    @patch("pathlib.Path.exists")
    def test_file_not_found_error(self, mock_exists):
        """Test handling of missing files."""
        mock_exists.return_value = False
        with pytest.raises(FileNotFoundError):
            self.calculator.calculate_trading_cvar()

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    @patch("pathlib.Path.exists")
    def test_missing_key_error(self, mock_exists, mock_json_load, mock_file):
        """Test handling of malformed JSON structure."""
        mock_exists.return_value = True
        mock_json_load.return_value = {"incomplete": "data"}

        with pytest.raises(KeyError):
            self.calculator.calculate_trading_cvar()

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    @patch("pathlib.Path.exists")
    def test_validate_cvar_calculations(self, mock_exists, mock_json_load, mock_file):
        """Test CVaR validation against backtest data."""
        mock_exists.return_value = True

        def side_effect(*args, **kwargs):
            if "trades.json" in str(args[0]):
                return self.mock_trades_data
            return self.mock_portfolio_data

        mock_json_load.side_effect = side_effect

        is_valid, results = self.calculator.validate_cvar_calculations()

        assert isinstance(is_valid, bool)
        assert isinstance(results, dict)
        assert "trading_cvar_match" in results
        assert "investment_cvar_match" in results

    def test_excel_formula_precision(self):
        """Test that calculations maintain Excel-level precision."""
        # Use known values that would be in Excel
        test_cases = [
            {
                "net_worth": 100000.0,
                "trading_cvar": -0.10658084758791905,
                "expected_b12": 10658.084758791905,
            },
            {
                "net_worth": 250000.0,
                "trading_cvar": -0.10658084758791905,
                "expected_b12": 26645.211896979762,
            },
        ]

        for case in test_cases:
            # Mock the CVaR value
            with patch.object(
                self.calculator,
                "calculate_trading_cvar",
                return_value=case["trading_cvar"],
            ):
                result = self.calculator.calculate_excel_b12_equivalent(
                    case["net_worth"]
                )
                assert (
                    abs(result - case["expected_b12"]) < 1e-10
                )  # High precision match
