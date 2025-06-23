"""
Position Sizing API Router

This module provides RESTful API endpoints for position sizing operations,
integrating with the enhanced service coordinator to provide real-time
position sizing calculations and dashboard data.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.dependencies import get_service_coordinator
from app.api.models.common import ErrorResponse
from app.tools.accounts import PortfolioType
from app.tools.services.enhanced_service_coordinator import EnhancedServiceCoordinator

router = APIRouter(prefix="/position-sizing", tags=["Position Sizing"])


# Request/Response Models
class AccountBalanceUpdate(BaseModel):
    """Request model for updating account balances."""

    account_type: str = Field(..., description="Account type: IBKR, Bybit, or Cash")
    balance: float = Field(
        ..., ge=0, description="Account balance (must be non-negative)"
    )


class PositionEntryRequest(BaseModel):
    """Request model for new position entry."""

    symbol: str = Field(..., description="Ticker symbol")
    position_value: float = Field(
        ..., gt=0, description="Position value from trade fill"
    )
    stop_loss_distance: Optional[float] = Field(
        None, ge=0, le=1, description="Stop loss distance (0-1)"
    )
    entry_price: Optional[float] = Field(None, gt=0, description="Entry price")
    portfolio_type: str = Field(
        "Risk_On", description="Portfolio type: Risk_On or Investment"
    )


class PositionUpdateRequest(BaseModel):
    """Request model for updating position metrics."""

    position_value: Optional[float] = Field(
        None, ge=0, description="New position value"
    )
    stop_loss_distance: Optional[float] = Field(
        None, ge=0, le=1, description="New stop loss distance"
    )
    current_position: Optional[float] = Field(
        None, description="Current position from broker"
    )
    entry_price: Optional[float] = Field(None, gt=0, description="New entry price")
    shares: Optional[float] = Field(None, ge=0, description="Number of shares")
    current_value: Optional[float] = Field(
        None, ge=0, description="Current market value"
    )


class PositionSizingCalculationRequest(BaseModel):
    """Request model for position sizing calculation."""

    symbol: str = Field(..., description="Ticker symbol")
    signal_type: str = Field(..., description="Signal type: entry or exit")
    portfolio_type: str = Field(
        "Risk_On", description="Portfolio type: Risk_On or Investment"
    )
    entry_price: Optional[float] = Field(None, gt=0, description="Entry price")
    stop_loss_distance: Optional[float] = Field(
        0.05, ge=0, le=1, description="Stop loss distance"
    )
    confidence_level: Optional[str] = Field(
        "primary", description="Confidence level: primary or outlier"
    )


class KellyParametersUpdate(BaseModel):
    """Request model for updating Kelly criterion parameters."""

    num_primary: int = Field(..., ge=0, description="Number of primary trades")
    num_outliers: int = Field(..., ge=0, description="Number of outlier trades")
    kelly_criterion: float = Field(
        ..., ge=0, le=1, description="Kelly criterion value (0-1)"
    )


class ExcelValidationRequest(BaseModel):
    """Request model for Excel validation."""

    net_worth: Optional[float] = Field(
        None, description="Expected net worth from Excel"
    )
    trading_cvar: Optional[float] = Field(
        None, description="Expected trading CVaR from Excel"
    )
    investment_cvar: Optional[float] = Field(
        None, description="Expected investment CVaR from Excel"
    )
    risk_amount: Optional[float] = Field(
        None, description="Expected risk amount from Excel"
    )
    total_strategies: Optional[int] = Field(
        None, description="Expected total strategies count"
    )


# API Endpoints
@router.get("/dashboard", summary="Get position sizing dashboard data")
async def get_position_sizing_dashboard(
    service: EnhancedServiceCoordinator = Depends(get_service_coordinator),
) -> Dict[str, Any]:
    """
    Get complete position sizing dashboard data.

    Returns comprehensive dashboard data including:
    - Net worth and account balances
    - Portfolio risk metrics (CVaR, Kelly criterion)
    - Active positions with risk amounts
    - Incoming signals for position sizing
    - Strategic holdings (Investment portfolio)
    - Risk allocation buckets
    """
    try:
        dashboard_data = await service.get_position_sizing_dashboard()
        return {
            "status": "success",
            "data": dashboard_data,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve dashboard: {str(e)}"
        )


@router.post("/calculate", summary="Calculate optimal position size")
async def calculate_position_size(
    request: PositionSizingCalculationRequest,
    service: EnhancedServiceCoordinator = Depends(get_service_coordinator),
) -> Dict[str, Any]:
    """
    Calculate optimal position size for a new signal.

    Uses Kelly criterion, risk allocation, and maximum allocation
    constraints to determine the optimal position size.
    """
    try:
        # Convert portfolio type string to enum
        portfolio_type = (
            PortfolioType.RISK_ON
            if request.portfolio_type == "Risk_On"
            else PortfolioType.INVESTMENT
        )

        # Calculate position size
        response = await service.calculate_position_size_for_signal(
            symbol=request.symbol,
            signal_data={
                "position": 1 if request.signal_type == "entry" else -1,
                "price": request.entry_price,
                "stop_loss_distance": request.stop_loss_distance,
                "confidence_level": request.confidence_level,
            },
            portfolio_type=portfolio_type,
        )

        return {
            "status": "success",
            "data": {
                "symbol": response.symbol,
                "recommended_position_size": response.recommended_position_size,
                "position_value": response.position_value,
                "risk_amount": response.risk_amount,
                "kelly_percentage": response.kelly_percentage,
                "allocation_percentage": response.allocation_percentage,
                "stop_loss_price": response.stop_loss_price,
                "confidence_metrics": response.confidence_metrics,
                "risk_bucket_allocation": response.risk_bucket_allocation,
                "account_allocation": response.account_allocation,
                "calculation_timestamp": response.calculation_timestamp.isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Position sizing calculation failed: {str(e)}"
        )


@router.get("/positions", summary="Get all active positions")
async def get_active_positions(
    portfolio_type: Optional[str] = Query(None, description="Filter by portfolio type"),
    service: EnhancedServiceCoordinator = Depends(get_service_coordinator),
) -> Dict[str, Any]:
    """
    Get all active positions with their current metrics.

    Optionally filter by portfolio type (Risk_On or Investment).
    """
    try:
        dashboard = await service.get_position_sizing_dashboard()
        positions = dashboard["active_positions"]

        # Filter by portfolio type if specified
        if portfolio_type:
            positions = [
                p for p in positions if p.get("portfolio_type") == portfolio_type
            ]

        return {
            "status": "success",
            "data": {
                "positions": positions,
                "total_count": len(positions),
                "total_value": sum(p.get("position_value", 0) for p in positions),
                "total_risk": sum(p.get("risk_amount", 0) for p in positions),
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve positions: {str(e)}"
        )


@router.get("/positions/{symbol}", summary="Get position analysis for a symbol")
async def get_position_analysis(
    symbol: str, service: EnhancedServiceCoordinator = Depends(get_service_coordinator)
) -> Dict[str, Any]:
    """
    Get comprehensive position analysis for a specific symbol.

    Returns detailed position tracking, risk metrics, and portfolio allocation.
    """
    try:
        analysis = await service.get_position_analysis(symbol.upper())
        return {
            "status": "success",
            "data": analysis,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Position analysis failed: {str(e)}"
        )


@router.post("/positions", summary="Add new position entry")
async def add_position_entry(
    request: PositionEntryRequest,
    service: EnhancedServiceCoordinator = Depends(get_service_coordinator),
) -> Dict[str, Any]:
    """
    Add a new position entry from manual trade fill.

    Creates entries in position tracker, drawdown calculator,
    and portfolio manager.
    """
    try:
        result = await service.process_new_position(
            symbol=request.symbol,
            position_value=request.position_value,
            stop_loss_distance=request.stop_loss_distance,
            entry_price=request.entry_price,
            portfolio_type=request.portfolio_type,
        )

        return {
            "status": "success",
            "data": result,
            "message": f"Position entry added for {request.symbol}",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add position: {str(e)}")


@router.put("/positions/{symbol}", summary="Update position metrics")
async def update_position_metrics(
    symbol: str,
    request: PositionUpdateRequest,
    service: EnhancedServiceCoordinator = Depends(get_service_coordinator),
) -> Dict[str, Any]:
    """
    Update position metrics for an existing position.

    Updates can include position value, stop loss, current position, etc.
    """
    try:
        # Convert request to updates dictionary
        updates = request.dict(exclude_unset=True)

        result = await service.update_position_metrics(symbol.upper(), updates)

        if result["success"]:
            return {
                "status": "success",
                "data": result,
                "message": f"Position metrics updated for {symbol}",
                "timestamp": datetime.now().isoformat(),
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to update position metrics for {symbol}",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.post("/accounts/balance", summary="Update account balance")
async def update_account_balance(
    request: AccountBalanceUpdate,
    service: EnhancedServiceCoordinator = Depends(get_service_coordinator),
) -> Dict[str, Any]:
    """
    Update manual account balance entry.

    Accepts balance updates for IBKR, Bybit, or Cash accounts.
    """
    try:
        # Update balance through position sizing orchestrator
        balance = service.position_sizing.account_service.update_account_balance(
            request.account_type, request.balance
        )

        # Get updated net worth
        net_worth = service.position_sizing.account_service.calculate_net_worth()

        return {
            "status": "success",
            "data": {
                "account_type": balance.account_type,
                "balance": balance.balance,
                "updated_at": balance.updated_at.isoformat(),
                "net_worth": net_worth.total_net_worth,
                "all_balances": net_worth.account_breakdown,
            },
            "timestamp": datetime.now().isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update balance: {str(e)}"
        )


@router.get("/accounts/balances", summary="Get all account balances")
async def get_account_balances(
    service: EnhancedServiceCoordinator = Depends(get_service_coordinator),
) -> Dict[str, Any]:
    """
    Get all account balances and net worth calculation.
    """
    try:
        net_worth = service.position_sizing.account_service.calculate_net_worth()

        return {
            "status": "success",
            "data": {
                "net_worth": net_worth.total_net_worth,
                "ibkr_balance": net_worth.ibkr_balance,
                "bybit_balance": net_worth.bybit_balance,
                "cash_balance": net_worth.cash_balance,
                "account_breakdown": net_worth.account_breakdown,
                "last_updated": net_worth.last_updated.isoformat(),
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve balances: {str(e)}"
        )


@router.get("/kelly", summary="Get Kelly criterion parameters")
async def get_kelly_parameters(
    service: EnhancedServiceCoordinator = Depends(get_service_coordinator),
) -> Dict[str, Any]:
    """
    Get current Kelly criterion parameters.
    """
    try:
        params = service.position_sizing.kelly_sizer.get_current_parameters()
        
        return {
            "status": "success",
            "data": {
                "kellyCriterion": params.get("kelly_criterion", 0.0448),
                "numPrimary": params.get("num_primary", 214),
                "numOutliers": params.get("num_outliers", 25),
                "lastUpdated": datetime.now().isoformat(),
                "source": "Trading Journal",
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get Kelly parameters: {str(e)}"
        )


@router.post("/kelly", summary="Update Kelly criterion parameters")
async def update_kelly_parameters(
    request: KellyParametersUpdate,
    service: EnhancedServiceCoordinator = Depends(get_service_coordinator),
) -> Dict[str, Any]:
    """
    Update Kelly criterion parameters from manual trading journal.
    """
    try:
        # Update parameters through Kelly sizer
        service.position_sizing.kelly_sizer.update_parameters(
            num_primary=request.num_primary,
            num_outliers=request.num_outliers,
            kelly_criterion=request.kelly_criterion,
        )

        # Get updated parameters
        params = service.position_sizing.kelly_sizer.get_current_parameters()

        return {
            "status": "success",
            "data": {
                "kellyCriterion": params.get("kelly_criterion", request.kelly_criterion),
                "numPrimary": params.get("num_primary", request.num_primary),
                "numOutliers": params.get("num_outliers", request.num_outliers),
                "lastUpdated": datetime.now().isoformat(),
                "source": "Trading Journal",
            },
            "message": "Kelly parameters updated successfully",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update Kelly parameters: {str(e)}"
        )


@router.get("/risk/allocation", summary="Get risk allocation summary")
async def get_risk_allocation_summary(
    service: EnhancedServiceCoordinator = Depends(get_service_coordinator),
) -> Dict[str, Any]:
    """
    Get summary of risk allocation across all portfolios.

    Shows current risk utilization, available capacity, and bucket allocations.
    """
    try:
        summary = await service.get_risk_allocation_summary()
        return {
            "status": "success",
            "data": summary,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get risk allocation: {str(e)}"
        )


@router.post("/validate/excel", summary="Validate against Excel calculations")
async def validate_excel_compatibility(
    request: ExcelValidationRequest,
    service: EnhancedServiceCoordinator = Depends(get_service_coordinator),
) -> Dict[str, Any]:
    """
    Validate position sizing calculations against Excel formulas.

    Compares system calculations with expected Excel values.
    """
    try:
        # Convert request to validation dictionary
        excel_data = request.dict(exclude_unset=True)

        validation_results = await service.validate_excel_compatibility(excel_data)

        return {
            "status": "success" if validation_results["validated"] else "warning",
            "data": validation_results,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post("/export", summary="Export position sizing data")
async def export_position_sizing_data(
    service: EnhancedServiceCoordinator = Depends(get_service_coordinator),
) -> Dict[str, Any]:
    """
    Export current position sizing system state for Excel migration.

    Creates a JSON export file with all position sizing data.
    """
    try:
        export_path = await service.export_position_sizing_data()

        return {
            "status": "success",
            "data": {
                "export_path": export_path,
                "export_timestamp": datetime.now().isoformat(),
            },
            "message": "Position sizing data exported successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/sync/strategy-results", summary="Sync with strategy analysis results")
async def sync_with_strategy_results(
    strategy_results: Dict[str, Any],
    service: EnhancedServiceCoordinator = Depends(get_service_coordinator),
) -> Dict[str, Any]:
    """
    Synchronize position sizing with latest strategy analysis results.

    Processes new signals and updates position metrics based on strategy output.
    """
    try:
        sync_results = await service.sync_with_strategy_results(strategy_results)

        return {
            "status": "success",
            "data": sync_results,
            "message": "Successfully synchronized with strategy results",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# Health check endpoint
@router.get("/health", summary="Check position sizing service health")
async def health_check(
    service: EnhancedServiceCoordinator = Depends(get_service_coordinator),
) -> Dict[str, Any]:
    """
    Check health status of position sizing service.
    """
    try:
        # Verify service components are accessible
        net_worth = service.position_sizing.account_service.calculate_net_worth()
        strategies_count = (
            service.position_sizing.strategies_integration.get_total_strategies_count()
        )

        return {
            "status": "healthy",
            "data": {
                "service": "position_sizing",
                "components": {
                    "account_service": "operational",
                    "position_tracker": "operational",
                    "strategies_integration": "operational",
                    "orchestrator": "operational",
                },
                "metrics": {
                    "net_worth": net_worth.total_net_worth,
                    "total_strategies": strategies_count,
                },
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
