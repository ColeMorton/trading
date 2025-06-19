"""
Test Position Sizing API Endpoints

This module contains comprehensive tests for the position sizing API endpoints,
covering all functionality including dashboard data, position calculations,
account management, and Excel validation.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.services.position_sizing_orchestrator import (
    DashboardData,
    PositionSizingResponse,
)
from app.tools.accounts import (
    AccountBalance,
    DrawdownEntry,
    NetWorthCalculation,
    PortfolioType,
    PositionEntry,
)


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_service_coordinator():
    """Create mock enhanced service coordinator."""
    mock_coordinator = MagicMock()

    # Mock dashboard data
    mock_dashboard = DashboardData(
        net_worth=100000.0,
        account_balances={"IBKR": 60000.0, "Bybit": 30000.0, "Cash": 10000.0},
        portfolio_risk_metrics={
            "trading_cvar": 0.15,
            "investment_cvar": 0.12,
            "risk_amount": 11800.0,
            "kelly_criterion": 0.25,
            "num_primary": 15,
            "num_outliers": 3,
            "total_strategies": 17,
        },
        active_positions=[
            {
                "symbol": "AAPL",
                "position_value": 5000.0,
                "risk_amount": 250.0,
                "account_type": "IBKR",
            }
        ],
        incoming_signals=[],
        strategic_holdings=[],
        risk_allocation_buckets=[
            {"risk_level": 0.118, "allocation_amount": 11800.0, "percentage": 11.8}
        ],
        total_strategies_count=17,
        last_updated=datetime.now(),
    )

    # Mock position sizing response
    mock_ps_response = PositionSizingResponse(
        symbol="AAPL",
        recommended_position_size=33.33,
        position_value=5000.0,
        risk_amount=250.0,
        kelly_percentage=0.25,
        allocation_percentage=0.05,
        stop_loss_price=142.5,
        confidence_metrics={"confidence_score": 0.85},
        risk_bucket_allocation=11800.0,
        account_allocation={"IBKR": 3000.0, "Bybit": 1500.0, "Cash": 500.0},
        calculation_timestamp=datetime.now(),
    )

    # Configure mock methods
    mock_coordinator.get_position_sizing_dashboard = AsyncMock(
        return_value=mock_dashboard.__dict__
    )
    mock_coordinator.calculate_position_size_for_signal = AsyncMock(
        return_value=mock_ps_response
    )
    mock_coordinator.get_position_analysis = AsyncMock(
        return_value={
            "symbol": "AAPL",
            "position_tracking": {"position_value": 5000.0},
            "risk_metrics": {"max_risk_amount": 250.0},
        }
    )
    mock_coordinator.process_new_position = AsyncMock(
        return_value={
            "position_entry": PositionEntry(
                symbol="AAPL", position_value=5000.0, account_type="IBKR"
            )
        }
    )
    mock_coordinator.update_position_metrics = AsyncMock(return_value={"success": True})
    mock_coordinator.get_risk_allocation_summary = AsyncMock(
        return_value={"net_worth": 100000.0, "risk_utilization_percentage": 25.0}
    )

    # Mock position sizing orchestrator
    mock_coordinator.position_sizing = MagicMock()
    mock_coordinator.position_sizing.account_service = MagicMock()
    mock_coordinator.position_sizing.account_service.update_account_balance = MagicMock(
        return_value=AccountBalance(
            account_type="IBKR", balance=60000.0, updated_at=datetime.now()
        )
    )
    mock_coordinator.position_sizing.account_service.calculate_net_worth = MagicMock(
        return_value=NetWorthCalculation(
            total_net_worth=100000.0,
            ibkr_balance=60000.0,
            bybit_balance=30000.0,
            cash_balance=10000.0,
            last_updated=datetime.now(),
            account_breakdown={"IBKR": 60000.0, "Bybit": 30000.0, "Cash": 10000.0},
        )
    )
    mock_coordinator.position_sizing.kelly_sizer = MagicMock()
    mock_coordinator.position_sizing.kelly_sizer.update_parameters = MagicMock()
    mock_coordinator.position_sizing.kelly_sizer.get_current_parameters = MagicMock(
        return_value={"num_primary": 15, "num_outliers": 3, "kelly_criterion": 0.25}
    )

    mock_coordinator.validate_excel_compatibility = AsyncMock(
        return_value={
            "validated": True,
            "discrepancies": [],
            "validations": [
                {"field": "net_worth", "status": "passed", "value": 100000.0}
            ],
        }
    )
    mock_coordinator.export_position_sizing_data = AsyncMock(
        return_value="/tmp/position_sizing_export_20231201_120000.json"
    )
    mock_coordinator.sync_with_strategy_results = AsyncMock(
        return_value={"synced_positions": [], "new_signals": []}
    )

    return mock_coordinator


class TestPositionSizingDashboard:
    """Test position sizing dashboard endpoints."""

    @patch("app.api.dependencies.get_service_coordinator")
    def test_get_dashboard_success(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test successful dashboard data retrieval."""
        mock_get_coordinator.return_value = mock_service_coordinator

        response = client.get("/api/position-sizing/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "net_worth" in data["data"]
        assert data["data"]["net_worth"] == 100000.0

    @patch("app.api.dependencies.get_service_coordinator")
    def test_get_dashboard_error(self, mock_get_coordinator, client):
        """Test dashboard error handling."""
        mock_coordinator = MagicMock()
        mock_coordinator.get_position_sizing_dashboard = AsyncMock(
            side_effect=Exception("Dashboard error")
        )
        mock_get_coordinator.return_value = mock_coordinator

        response = client.get("/api/position-sizing/dashboard")

        assert response.status_code == 500
        assert "Failed to retrieve dashboard" in response.json()["detail"]


class TestPositionSizeCalculation:
    """Test position size calculation endpoints."""

    @patch("app.api.dependencies.get_service_coordinator")
    def test_calculate_position_size_success(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test successful position size calculation."""
        mock_get_coordinator.return_value = mock_service_coordinator

        request_data = {
            "symbol": "AAPL",
            "signal_type": "entry",
            "entry_price": 150.0,
            "stop_loss_distance": 0.05,
        }

        response = client.post("/api/position-sizing/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["symbol"] == "AAPL"
        assert "recommended_position_size" in data["data"]

    @patch("app.api.dependencies.get_service_coordinator")
    def test_calculate_position_size_validation_error(
        self, mock_get_coordinator, client
    ):
        """Test position size calculation with invalid data."""
        mock_get_coordinator.return_value = MagicMock()

        request_data = {
            "symbol": "",  # Invalid empty symbol
            "signal_type": "entry",
            "entry_price": -150.0,  # Invalid negative price
        }

        response = client.post("/api/position-sizing/calculate", json=request_data)

        assert response.status_code == 422  # Validation error


class TestPositionManagement:
    """Test position management endpoints."""

    @patch("app.api.dependencies.get_service_coordinator")
    def test_get_active_positions(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test retrieving active positions."""
        mock_get_coordinator.return_value = mock_service_coordinator

        response = client.get("/api/position-sizing/positions")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "positions" in data["data"]

    @patch("app.api.dependencies.get_service_coordinator")
    def test_get_position_analysis(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test getting position analysis for a specific symbol."""
        mock_get_coordinator.return_value = mock_service_coordinator

        response = client.get("/api/position-sizing/positions/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["symbol"] == "AAPL"

    @patch("app.api.dependencies.get_service_coordinator")
    def test_add_position_entry(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test adding a new position entry."""
        mock_get_coordinator.return_value = mock_service_coordinator

        request_data = {
            "symbol": "AAPL",
            "position_value": 5000.0,
            "stop_loss_distance": 0.05,
            "entry_price": 150.0,
        }

        response = client.post("/api/position-sizing/positions", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Position entry added" in data["message"]

    @patch("app.api.dependencies.get_service_coordinator")
    def test_update_position_metrics(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test updating position metrics."""
        mock_get_coordinator.return_value = mock_service_coordinator

        request_data = {"position_value": 5500.0, "stop_loss_distance": 0.04}

        response = client.put("/api/position-sizing/positions/AAPL", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestAccountManagement:
    """Test account management endpoints."""

    @patch("app.api.dependencies.get_service_coordinator")
    def test_update_account_balance(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test updating account balance."""
        mock_get_coordinator.return_value = mock_service_coordinator

        request_data = {"account_type": "IBKR", "balance": 65000.0}

        response = client.post(
            "/api/position-sizing/accounts/balance", json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["account_type"] == "IBKR"

    @patch("app.api.dependencies.get_service_coordinator")
    def test_update_account_balance_invalid(self, mock_get_coordinator, client):
        """Test updating account balance with invalid data."""
        mock_coordinator = MagicMock()
        mock_coordinator.position_sizing.account_service.update_account_balance.side_effect = ValueError(
            "Invalid account type"
        )
        mock_get_coordinator.return_value = mock_coordinator

        request_data = {"account_type": "INVALID", "balance": 65000.0}

        response = client.post(
            "/api/position-sizing/accounts/balance", json=request_data
        )

        assert response.status_code == 400

    @patch("app.api.dependencies.get_service_coordinator")
    def test_get_account_balances(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test retrieving all account balances."""
        mock_get_coordinator.return_value = mock_service_coordinator

        response = client.get("/api/position-sizing/accounts/balances")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "net_worth" in data["data"]


class TestKellyParameters:
    """Test Kelly criterion parameter management."""

    @patch("app.api.dependencies.get_service_coordinator")
    def test_update_kelly_parameters(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test updating Kelly criterion parameters."""
        mock_get_coordinator.return_value = mock_service_coordinator

        request_data = {"num_primary": 20, "num_outliers": 5, "kelly_criterion": 0.3}

        response = client.post(
            "/api/position-sizing/kelly/parameters", json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestRiskAllocation:
    """Test risk allocation endpoints."""

    @patch("app.api.dependencies.get_service_coordinator")
    def test_get_risk_allocation_summary(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test getting risk allocation summary."""
        mock_get_coordinator.return_value = mock_service_coordinator

        response = client.get("/api/position-sizing/risk/allocation")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "net_worth" in data["data"]


class TestExcelValidation:
    """Test Excel validation functionality."""

    @patch("app.api.dependencies.get_service_coordinator")
    def test_validate_excel_compatibility(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test Excel validation."""
        mock_get_coordinator.return_value = mock_service_coordinator

        request_data = {
            "net_worth": 100000.0,
            "trading_cvar": 0.15,
            "risk_amount": 11800.0,
        }

        response = client.post("/api/position-sizing/validate/excel", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["validated"] is True

    @patch("app.api.dependencies.get_service_coordinator")
    def test_validate_excel_compatibility_with_discrepancies(
        self, mock_get_coordinator, client
    ):
        """Test Excel validation with discrepancies."""
        mock_coordinator = MagicMock()
        mock_coordinator.validate_excel_compatibility = AsyncMock(
            return_value={
                "validated": False,
                "discrepancies": [
                    {
                        "field": "net_worth",
                        "expected": 100000.0,
                        "actual": 95000.0,
                        "difference": 5000.0,
                    }
                ],
                "validations": [],
            }
        )
        mock_get_coordinator.return_value = mock_coordinator

        request_data = {"net_worth": 100000.0}

        response = client.post("/api/position-sizing/validate/excel", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "warning"
        assert data["data"]["validated"] is False
        assert len(data["data"]["discrepancies"]) > 0


class TestDataExport:
    """Test data export functionality."""

    @patch("app.api.dependencies.get_service_coordinator")
    def test_export_position_sizing_data(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test exporting position sizing data."""
        mock_get_coordinator.return_value = mock_service_coordinator

        response = client.post("/api/position-sizing/export")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "export_path" in data["data"]


class TestStrategyResultsSync:
    """Test strategy results synchronization."""

    @patch("app.api.dependencies.get_service_coordinator")
    def test_sync_with_strategy_results(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test synchronizing with strategy results."""
        mock_get_coordinator.return_value = mock_service_coordinator

        strategy_results = {
            "deduplicated_portfolios": [
                {"ticker": "AAPL", "signals": [{"position": 1, "price": 150.0}]}
            ]
        }

        response = client.post(
            "/api/position-sizing/sync/strategy-results", json=strategy_results
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestHealthCheck:
    """Test health check endpoint."""

    @patch("app.api.dependencies.get_service_coordinator")
    def test_health_check_healthy(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test health check when service is healthy."""
        mock_get_coordinator.return_value = mock_service_coordinator

        response = client.get("/api/position-sizing/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @patch("app.api.dependencies.get_service_coordinator")
    def test_health_check_unhealthy(self, mock_get_coordinator, client):
        """Test health check when service is unhealthy."""
        mock_coordinator = MagicMock()
        mock_coordinator.position_sizing.account_service.calculate_net_worth.side_effect = Exception(
            "Service error"
        )
        mock_get_coordinator.return_value = mock_coordinator

        response = client.get("/api/position-sizing/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"


class TestValidationErrors:
    """Test request validation and error handling."""

    def test_position_entry_negative_value(self, client):
        """Test position entry with negative value."""
        request_data = {
            "symbol": "AAPL",
            "position_value": -5000.0,  # Invalid negative value
        }

        response = client.post("/api/position-sizing/positions", json=request_data)

        assert response.status_code == 422

    def test_account_balance_negative(self, client):
        """Test account balance update with negative value."""
        request_data = {
            "account_type": "IBKR",
            "balance": -1000.0,  # Invalid negative balance
        }

        response = client.post(
            "/api/position-sizing/accounts/balance", json=request_data
        )

        assert response.status_code == 422

    def test_stop_loss_distance_out_of_range(self, client):
        """Test stop loss distance outside valid range."""
        request_data = {
            "symbol": "AAPL",
            "signal_type": "entry",
            "stop_loss_distance": 1.5,  # Invalid > 1.0
        }

        response = client.post("/api/position-sizing/calculate", json=request_data)

        assert response.status_code == 422

    def test_kelly_parameters_invalid(self, client):
        """Test Kelly parameters with invalid values."""
        request_data = {
            "num_primary": -5,  # Invalid negative
            "num_outliers": 3,
            "kelly_criterion": 1.5,  # Invalid > 1.0
        }

        response = client.post(
            "/api/position-sizing/kelly/parameters", json=request_data
        )

        assert response.status_code == 422


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple endpoints."""

    @patch("app.api.dependencies.get_service_coordinator")
    def test_complete_position_workflow(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test complete workflow: update balance -> calculate size -> add position."""
        mock_get_coordinator.return_value = mock_service_coordinator

        # 1. Update account balance
        balance_response = client.post(
            "/api/position-sizing/accounts/balance",
            json={"account_type": "IBKR", "balance": 60000.0},
        )
        assert balance_response.status_code == 200

        # 2. Calculate position size
        calc_response = client.post(
            "/api/position-sizing/calculate",
            json={
                "symbol": "AAPL",
                "signal_type": "entry",
                "entry_price": 150.0,
                "stop_loss_distance": 0.05,
            },
        )
        assert calc_response.status_code == 200

        # 3. Add position entry
        position_response = client.post(
            "/api/position-sizing/positions",
            json={
                "symbol": "AAPL",
                "position_value": 5000.0,
                "stop_loss_distance": 0.05,
                "entry_price": 150.0,
            },
        )
        assert position_response.status_code == 200

        # 4. Get updated dashboard
        dashboard_response = client.get("/api/position-sizing/dashboard")
        assert dashboard_response.status_code == 200

    @patch("app.api.dependencies.get_service_coordinator")
    def test_risk_management_workflow(
        self, mock_get_coordinator, client, mock_service_coordinator
    ):
        """Test risk management workflow."""
        mock_get_coordinator.return_value = mock_service_coordinator

        # 1. Get risk allocation summary
        risk_response = client.get("/api/position-sizing/risk/allocation")
        assert risk_response.status_code == 200

        # 2. Update Kelly parameters
        kelly_response = client.post(
            "/api/position-sizing/kelly/parameters",
            json={"num_primary": 20, "num_outliers": 5, "kelly_criterion": 0.3},
        )
        assert kelly_response.status_code == 200

        # 3. Validate Excel compatibility
        validation_response = client.post(
            "/api/position-sizing/validate/excel",
            json={"net_worth": 100000.0, "risk_amount": 11800.0},
        )
        assert validation_response.status_code == 200


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
