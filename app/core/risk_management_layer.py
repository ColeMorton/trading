"""
Risk Management Layer

This module provides a centralized risk management system that consolidates risk calculation
and management logic from across the trading platform. It standardizes risk metrics,
position sizing, and risk controls across all strategy execution patterns.

Key Features:
- Unified risk metrics calculation (VaR, CVaR, Sharpe, Sortino, etc.)
- Portfolio-level risk assessment and correlation analysis
- Dynamic position sizing based on risk parameters
- Stop-loss and take-profit management
- Risk budget allocation and monitoring
- Scenario analysis and stress testing
"""

import numpy as np
import pandas as pd
import polars as pl
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class RiskMeasure(Enum):
    """Standard risk measures."""
    VAR_95 = "var_95"  # 95% Value at Risk
    VAR_99 = "var_99"  # 99% Value at Risk
    CVAR_95 = "cvar_95"  # 95% Conditional Value at Risk
    CVAR_99 = "cvar_99"  # 99% Conditional Value at Risk
    MAX_DRAWDOWN = "max_drawdown"
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    CALMAR_RATIO = "calmar_ratio"
    VOLATILITY = "volatility"
    SKEWNESS = "skewness"
    KURTOSIS = "kurtosis"


class PositionSizingMethod(Enum):
    """Position sizing methods."""
    FIXED_PERCENTAGE = "fixed_percentage"
    KELLY_CRITERION = "kelly_criterion"
    VOLATILITY_TARGET = "volatility_target"
    RISK_PARITY = "risk_parity"
    MAX_DRAWDOWN_TARGET = "max_drawdown_target"


@dataclass
class RiskParameters:
    """Risk management parameters."""
    
    # Position Sizing
    max_position_size: float = 0.10  # Maximum 10% per position
    portfolio_heat: float = 0.02  # Maximum 2% portfolio risk per trade
    volatility_target: float = 0.15  # Target 15% annualized volatility
    
    # Stop Loss / Take Profit
    max_stop_loss: float = 0.05  # Maximum 5% stop loss
    profit_target_ratio: float = 2.0  # 2:1 reward-to-risk ratio
    trailing_stop_activation: float = 0.02  # Activate trailing stop at 2% profit
    
    # Portfolio Risk Limits
    max_portfolio_drawdown: float = 0.15  # Maximum 15% portfolio drawdown
    max_correlation: float = 0.70  # Maximum correlation between positions
    max_sector_concentration: float = 0.30  # Maximum 30% in any sector
    
    # Risk Metrics Thresholds
    min_sharpe_ratio: float = 0.50  # Minimum acceptable Sharpe ratio
    max_var_95: float = 0.05  # Maximum 5% daily VaR
    min_win_rate: float = 0.40  # Minimum 40% win rate
    
    # Rebalancing
    rebalance_frequency: str = "monthly"  # monthly, weekly, daily
    drift_threshold: float = 0.05  # 5% drift before rebalancing


class RiskMetrics(BaseModel):
    """Container for calculated risk metrics."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Basic Statistics
    total_return: float = Field(..., description="Total return percentage")
    annualized_return: float = Field(..., description="Annualized return percentage")
    volatility: float = Field(..., description="Annualized volatility")
    
    # Risk-Adjusted Returns
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    calmar_ratio: float = Field(..., description="Calmar ratio")
    
    # Drawdown Metrics
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    max_drawdown_duration: int = Field(..., description="Maximum drawdown duration in periods")
    current_drawdown: float = Field(..., description="Current drawdown percentage")
    
    # Value at Risk
    var_95: float = Field(..., description="95% Value at Risk")
    var_99: float = Field(..., description="99% Value at Risk")
    cvar_95: float = Field(..., description="95% Conditional Value at Risk")
    cvar_99: float = Field(..., description="99% Conditional Value at Risk")
    
    # Distribution Metrics
    skewness: float = Field(..., description="Return skewness")
    kurtosis: float = Field(..., description="Return kurtosis")
    
    # Trade-Based Metrics
    win_rate: float = Field(..., description="Win rate percentage")
    profit_factor: float = Field(..., description="Profit factor")
    avg_win: float = Field(..., description="Average winning trade")
    avg_loss: float = Field(..., description="Average losing trade")
    largest_win: float = Field(..., description="Largest winning trade")
    largest_loss: float = Field(..., description="Largest losing trade")
    
    # Frequency Metrics
    trade_frequency: float = Field(..., description="Trades per year")
    hold_time_avg: float = Field(..., description="Average holding time in days")
    
    # Additional Context
    calculation_date: datetime = Field(default_factory=datetime.now)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    total_trades: int = 0


class PositionSizer:
    """Position sizing calculator using various methods."""
    
    def __init__(self, risk_params: RiskParameters):
        """Initialize with risk parameters."""
        self.risk_params = risk_params
    
    def calculate_position_size(
        self,
        method: PositionSizingMethod,
        portfolio_value: float,
        entry_price: float,
        stop_loss: float,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None,
        volatility: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate position size using specified method.
        
        Returns:
            Dictionary with position size info including shares, dollar amount, and risk metrics
        """
        if method == PositionSizingMethod.FIXED_PERCENTAGE:
            return self._fixed_percentage_sizing(portfolio_value, entry_price)
        
        elif method == PositionSizingMethod.KELLY_CRITERION:
            if not all([win_rate, avg_win, avg_loss]):
                raise ValueError("Kelly criterion requires win_rate, avg_win, and avg_loss")
            return self._kelly_criterion_sizing(
                portfolio_value, entry_price, stop_loss, win_rate, avg_win, avg_loss
            )
        
        elif method == PositionSizingMethod.VOLATILITY_TARGET:
            if volatility is None:
                raise ValueError("Volatility target sizing requires volatility parameter")
            return self._volatility_target_sizing(
                portfolio_value, entry_price, volatility
            )
        
        elif method == PositionSizingMethod.MAX_DRAWDOWN_TARGET:
            return self._max_drawdown_sizing(
                portfolio_value, entry_price, stop_loss
            )
        
        else:
            raise ValueError(f"Unsupported position sizing method: {method}")
    
    def _fixed_percentage_sizing(
        self, 
        portfolio_value: float, 
        entry_price: float
    ) -> Dict[str, Any]:
        """Fixed percentage position sizing."""
        dollar_amount = portfolio_value * self.risk_params.max_position_size
        shares = int(dollar_amount / entry_price)
        actual_dollar_amount = shares * entry_price
        actual_percentage = actual_dollar_amount / portfolio_value
        
        return {
            "method": "fixed_percentage",
            "shares": shares,
            "dollar_amount": actual_dollar_amount,
            "percentage": actual_percentage,
            "target_percentage": self.risk_params.max_position_size,
            "risk_per_share": 0.0  # No specific risk calculation for fixed percentage
        }
    
    def _kelly_criterion_sizing(
        self,
        portfolio_value: float,
        entry_price: float,
        stop_loss: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> Dict[str, Any]:
        """Kelly criterion position sizing."""
        # Calculate Kelly fraction: f = (bp - q) / b
        # where b = avg_win/avg_loss, p = win_rate, q = 1 - win_rate
        
        if avg_loss == 0:
            raise ValueError("Average loss cannot be zero for Kelly criterion")
        
        b = avg_win / abs(avg_loss)  # Payoff ratio
        p = win_rate  # Win probability
        q = 1 - win_rate  # Loss probability
        
        kelly_fraction = (b * p - q) / b
        
        # Apply safety factor and limits
        safety_factor = 0.25  # Use 25% of Kelly for safety
        kelly_fraction = max(0, min(kelly_fraction * safety_factor, self.risk_params.max_position_size))
        
        dollar_amount = portfolio_value * kelly_fraction
        shares = int(dollar_amount / entry_price)
        actual_dollar_amount = shares * entry_price
        
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss)
        total_risk = shares * risk_per_share
        portfolio_risk = total_risk / portfolio_value
        
        return {
            "method": "kelly_criterion",
            "shares": shares,
            "dollar_amount": actual_dollar_amount,
            "percentage": actual_dollar_amount / portfolio_value,
            "kelly_fraction": kelly_fraction,
            "risk_per_share": risk_per_share,
            "total_risk": total_risk,
            "portfolio_risk": portfolio_risk,
            "payoff_ratio": b,
            "win_rate": p
        }
    
    def _volatility_target_sizing(
        self,
        portfolio_value: float,
        entry_price: float,
        volatility: float
    ) -> Dict[str, Any]:
        """Volatility target position sizing."""
        # Size position to achieve target portfolio volatility
        target_vol = self.risk_params.volatility_target
        position_vol_contribution = min(target_vol / volatility, self.risk_params.max_position_size)
        
        dollar_amount = portfolio_value * position_vol_contribution
        shares = int(dollar_amount / entry_price)
        actual_dollar_amount = shares * entry_price
        
        return {
            "method": "volatility_target",
            "shares": shares,
            "dollar_amount": actual_dollar_amount,
            "percentage": actual_dollar_amount / portfolio_value,
            "target_volatility": target_vol,
            "asset_volatility": volatility,
            "vol_contribution": position_vol_contribution
        }
    
    def _max_drawdown_sizing(
        self,
        portfolio_value: float,
        entry_price: float,
        stop_loss: float
    ) -> Dict[str, Any]:
        """Position sizing based on maximum drawdown target."""
        # Size position so that stop loss hit equals portfolio heat
        risk_per_share = abs(entry_price - stop_loss)
        max_risk = portfolio_value * self.risk_params.portfolio_heat
        shares = int(max_risk / risk_per_share)
        
        actual_dollar_amount = shares * entry_price
        total_risk = shares * risk_per_share
        
        return {
            "method": "max_drawdown_target",
            "shares": shares,
            "dollar_amount": actual_dollar_amount,
            "percentage": actual_dollar_amount / portfolio_value,
            "risk_per_share": risk_per_share,
            "total_risk": total_risk,
            "portfolio_risk": total_risk / portfolio_value,
            "target_portfolio_heat": self.risk_params.portfolio_heat
        }


class RiskCalculator:
    """Centralized risk metrics calculator."""
    
    @staticmethod
    def calculate_comprehensive_metrics(
        returns: Union[pd.Series, np.ndarray, List[float]],
        trades: Optional[pd.DataFrame] = None,
        benchmark_returns: Optional[Union[pd.Series, np.ndarray]] = None,
        risk_free_rate: float = 0.02
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics from returns series.
        
        Args:
            returns: Return series (can be daily, weekly, etc.)
            trades: Optional trades DataFrame with trade-level details
            benchmark_returns: Optional benchmark returns for relative metrics
            risk_free_rate: Risk-free rate for Sharpe ratio calculation
            
        Returns:
            RiskMetrics object with calculated metrics
        """
        if isinstance(returns, list):
            returns = np.array(returns)
        if isinstance(returns, np.ndarray):
            returns = pd.Series(returns)
        
        # Remove any NaN values
        returns = returns.dropna()
        
        if len(returns) == 0:
            raise ValueError("Empty returns series provided")
        
        # Basic return statistics
        total_return = (1 + returns).prod() - 1
        periods_per_year = RiskCalculator._infer_frequency(returns)
        annualized_return = (1 + total_return) ** (periods_per_year / len(returns)) - 1
        volatility = returns.std() * np.sqrt(periods_per_year)
        
        # Risk-adjusted returns
        excess_returns = returns - risk_free_rate / periods_per_year
        sharpe_ratio = excess_returns.mean() / returns.std() * np.sqrt(periods_per_year) if returns.std() > 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino_ratio = excess_returns.mean() / downside_std * np.sqrt(periods_per_year) if downside_std > 0 else 0
        
        # Drawdown calculations
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Find max drawdown duration
        drawdown_duration = RiskCalculator._calculate_drawdown_duration(drawdown)
        current_drawdown = drawdown.iloc[-1] if len(drawdown) > 0 else 0
        
        # Calmar ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Value at Risk calculations
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        # Conditional Value at Risk (Expected Shortfall)
        cvar_95 = returns[returns <= var_95].mean() if any(returns <= var_95) else var_95
        cvar_99 = returns[returns <= var_99].mean() if any(returns <= var_99) else var_99
        
        # Distribution metrics
        skewness = returns.skew()
        kurtosis = returns.kurtosis()
        
        # Trade-based metrics (if trades provided)
        trade_metrics = RiskCalculator._calculate_trade_metrics(trades) if trades is not None else {}
        
        return RiskMetrics(
            total_return=total_return * 100,
            annualized_return=annualized_return * 100,
            volatility=volatility * 100,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_drawdown * 100,
            max_drawdown_duration=drawdown_duration,
            current_drawdown=current_drawdown * 100,
            var_95=var_95 * 100,
            var_99=var_99 * 100,
            cvar_95=cvar_95 * 100,
            cvar_99=cvar_99 * 100,
            skewness=skewness,
            kurtosis=kurtosis,
            **trade_metrics
        )
    
    @staticmethod
    def _infer_frequency(returns: pd.Series) -> int:
        """Infer the frequency of returns series (periods per year)."""
        if hasattr(returns, 'index') and hasattr(returns.index, 'freq'):
            # Try to get frequency from index
            freq = returns.index.freq
            if freq is not None:
                freq_str = str(freq)
                if 'D' in freq_str:
                    return 252  # Daily
                elif 'W' in freq_str:
                    return 52   # Weekly
                elif 'M' in freq_str:
                    return 12   # Monthly
        
        # Fallback: assume daily if more than 100 observations, otherwise monthly
        return 252 if len(returns) > 100 else 12
    
    @staticmethod
    def _calculate_drawdown_duration(drawdown: pd.Series) -> int:
        """Calculate maximum drawdown duration."""
        max_duration = 0
        current_duration = 0
        
        for dd in drawdown:
            if dd < 0:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0
        
        return max_duration
    
    @staticmethod
    def _calculate_trade_metrics(trades: pd.DataFrame) -> Dict[str, float]:
        """Calculate trade-based risk metrics."""
        if trades is None or len(trades) == 0:
            return {
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
                "trade_frequency": 0.0,
                "hold_time_avg": 0.0,
                "total_trades": 0
            }
        
        # Assume trades DataFrame has 'pnl' or 'return' column
        pnl_col = 'pnl' if 'pnl' in trades.columns else 'return'
        if pnl_col not in trades.columns:
            return {"win_rate": 0.0, "profit_factor": 0.0, "total_trades": len(trades)}
        
        pnl = trades[pnl_col]
        wins = pnl[pnl > 0]
        losses = pnl[pnl < 0]
        
        win_rate = len(wins) / len(pnl) * 100 if len(pnl) > 0 else 0
        profit_factor = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else 0
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = losses.mean() if len(losses) > 0 else 0
        largest_win = wins.max() if len(wins) > 0 else 0
        largest_loss = losses.min() if len(losses) > 0 else 0
        
        # Calculate holding time if date columns exist
        hold_time_avg = 0.0
        if 'entry_date' in trades.columns and 'exit_date' in trades.columns:
            hold_times = pd.to_datetime(trades['exit_date']) - pd.to_datetime(trades['entry_date'])
            hold_time_avg = hold_times.dt.days.mean()
        
        # Estimate trade frequency (trades per year)
        trade_frequency = 0.0
        if 'entry_date' in trades.columns and len(trades) > 1:
            date_range = pd.to_datetime(trades['entry_date'].max()) - pd.to_datetime(trades['entry_date'].min())
            years = date_range.days / 365.25
            trade_frequency = len(trades) / years if years > 0 else 0
        
        return {
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "largest_win": largest_win,
            "largest_loss": largest_loss,
            "trade_frequency": trade_frequency,
            "hold_time_avg": hold_time_avg,
            "total_trades": len(trades)
        }


class RiskManagementLayer:
    """
    Unified risk management layer providing centralized risk assessment and controls.
    
    This layer consolidates risk management functionality from across the trading platform,
    providing consistent risk calculations, position sizing, and risk monitoring.
    """
    
    def __init__(self, risk_params: RiskParameters = None):
        """Initialize risk management layer."""
        self.risk_params = risk_params or RiskParameters()
        self.position_sizer = PositionSizer(self.risk_params)
        self.calculator = RiskCalculator()
    
    def assess_strategy_risk(
        self,
        returns: Union[pd.Series, np.ndarray, List[float]],
        trades: Optional[pd.DataFrame] = None,
        benchmark_returns: Optional[Union[pd.Series, np.ndarray]] = None
    ) -> RiskMetrics:
        """Assess comprehensive risk metrics for a strategy."""
        return self.calculator.calculate_comprehensive_metrics(
            returns, trades, benchmark_returns
        )
    
    def calculate_position_size(
        self,
        method: PositionSizingMethod,
        portfolio_value: float,
        entry_price: float,
        stop_loss: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Calculate optimal position size using specified method."""
        return self.position_sizer.calculate_position_size(
            method, portfolio_value, entry_price, stop_loss, **kwargs
        )
    
    def validate_trade(
        self,
        portfolio_value: float,
        position_size: float,
        entry_price: float,
        stop_loss: float,
        current_positions: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Validate a proposed trade against risk parameters.
        
        Returns:
            Dictionary with validation results and recommended adjustments
        """
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "recommended_size": position_size,
            "risk_metrics": {}
        }
        
        # Check position size limits
        position_value = position_size * entry_price
        position_percentage = position_value / portfolio_value
        
        if position_percentage > self.risk_params.max_position_size:
            validation_result["errors"].append(
                f"Position size ({position_percentage:.2%}) exceeds maximum allowed "
                f"({self.risk_params.max_position_size:.2%})"
            )
            validation_result["is_valid"] = False
            validation_result["recommended_size"] = int(
                (portfolio_value * self.risk_params.max_position_size) / entry_price
            )
        
        # Check risk per trade
        risk_per_share = abs(entry_price - stop_loss)
        total_risk = position_size * risk_per_share
        portfolio_risk = total_risk / portfolio_value
        
        if portfolio_risk > self.risk_params.portfolio_heat:
            validation_result["warnings"].append(
                f"Trade risk ({portfolio_risk:.2%}) exceeds recommended portfolio heat "
                f"({self.risk_params.portfolio_heat:.2%})"
            )
        
        # Check stop loss size
        stop_loss_percentage = abs(entry_price - stop_loss) / entry_price
        if stop_loss_percentage > self.risk_params.max_stop_loss:
            validation_result["errors"].append(
                f"Stop loss ({stop_loss_percentage:.2%}) exceeds maximum allowed "
                f"({self.risk_params.max_stop_loss:.2%})"
            )
            validation_result["is_valid"] = False
        
        validation_result["risk_metrics"] = {
            "position_percentage": position_percentage,
            "portfolio_risk": portfolio_risk,
            "stop_loss_percentage": stop_loss_percentage,
            "risk_per_share": risk_per_share,
            "total_risk": total_risk
        }
        
        return validation_result
    
    def get_portfolio_risk_summary(
        self, 
        positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate portfolio-level risk summary.
        
        Args:
            positions: List of position dictionaries with at least:
                      {'ticker': str, 'value': float, 'volatility': float}
        
        Returns:
            Portfolio risk summary
        """
        if not positions:
            return {"total_value": 0, "portfolio_volatility": 0, "concentration_risk": 0}
        
        total_value = sum(pos["value"] for pos in positions)
        
        # Calculate portfolio volatility (simplified - assumes no correlation)
        portfolio_var = sum(
            (pos["value"] / total_value) ** 2 * pos.get("volatility", 0.15) ** 2
            for pos in positions
        )
        portfolio_volatility = np.sqrt(portfolio_var)
        
        # Calculate concentration risk (Herfindahl index)
        weights = [pos["value"] / total_value for pos in positions]
        concentration_risk = sum(w ** 2 for w in weights)
        
        # Identify largest positions
        sorted_positions = sorted(positions, key=lambda x: x["value"], reverse=True)
        top_3_concentration = sum(pos["value"] for pos in sorted_positions[:3]) / total_value
        
        return {
            "total_value": total_value,
            "portfolio_volatility": portfolio_volatility,
            "concentration_risk": concentration_risk,
            "top_3_concentration": top_3_concentration,
            "number_of_positions": len(positions),
            "avg_position_size": total_value / len(positions),
            "largest_position": sorted_positions[0] if sorted_positions else None
        }