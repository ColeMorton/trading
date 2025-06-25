"""
Kelly-Optimized Position Sizing Algorithm
=========================================

Advanced position sizing system that intelligently incorporates Kelly Criterion
with CVaR risk management and custom stop-loss levels. Removes hybrid approach
for pure Kelly-based optimization with risk constraints.

Key Features:
- Strategy-specific Kelly calculations using win rate and profit factor
- Stop-loss adjusted Kelly for actual risk per trade
- CVaR portfolio-level risk management
- Position correlation and diversification effects
"""

import json
import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

try:
    from scipy.optimize import minimize

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

import yfinance as yf


@dataclass
class StrategyMetrics:
    """Enhanced strategy metrics including stop-loss data"""

    ticker: str
    strategy_type: str
    short_window: int
    long_window: int
    total_return: float
    win_rate: float
    profit_factor: float
    sortino_ratio: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    expectancy: float
    calmar_ratio: float
    avg_winning_trade: float
    avg_losing_trade: float
    stop_loss: float  # Custom stop-loss percentage


@dataclass
class KellyOptimizedResult:
    """Kelly-optimized position sizing results"""

    ticker: str
    theoretical_kelly: float
    risk_adjusted_kelly: float
    stop_loss_adjusted_kelly: float
    final_allocation: float
    dollar_amount: float
    position_shares: int
    max_risk_per_trade: float
    expected_return: float
    risk_contribution: float


class KellyOptimizedSizer:
    """
    Kelly Criterion-based position sizing with intelligent risk management

    Core Philosophy:
    1. Use true Kelly Criterion calculations based on strategy win rates and payoffs
    2. Adjust Kelly for actual stop-loss risk (not theoretical max drawdown)
    3. Apply portfolio-level CVaR constraints
    4. Optimize for diversification benefits
    """

    def __init__(
        self,
        kelly_params_path: str = "data/kelly/kelly_parameters.json",
        accounts_path: str = "data/accounts/manual_balances.json",
        cvar_target: float = 0.118,
        max_position_risk: float = 0.15,
        correlation_adjustment: float = 0.8,
    ):
        """
        Initialize Kelly-optimized position sizer

        Args:
            kelly_params_path: Path to Kelly parameters JSON file
            accounts_path: Path to account balances JSON file
            cvar_target: Portfolio CVaR target (11.8%)
            max_position_risk: Maximum risk per position (15%)
            correlation_adjustment: Adjustment for position correlation (0.8 = 20% correlation discount)
        """
        # Load Kelly parameters from JSON
        self.global_kelly_base = self.load_kelly_parameters(kelly_params_path)

        # Load and calculate total capital from account balances
        self.total_capital = self.load_total_capital(accounts_path)

        self.cvar_target = cvar_target
        self.max_position_risk = max_position_risk
        self.correlation_adjustment = correlation_adjustment

    def load_kelly_parameters(self, kelly_params_path: str) -> float:
        """Load Kelly criterion from JSON file"""
        try:
            with open(kelly_params_path, "r") as f:
                kelly_data = json.load(f)
            return kelly_data["kelly_criterion"]
        except Exception as e:
            print(
                f"Warning: Could not load Kelly parameters from {kelly_params_path}: {e}"
            )
            return 0.0448  # Fallback to 4.48%

    def load_total_capital(self, accounts_path: str) -> float:
        """Load and sum account balances from JSON file"""
        try:
            with open(accounts_path, "r") as f:
                accounts_data = json.load(f)

            total_capital = sum(
                account["balance"] for account in accounts_data["balances"]
            )
            return total_capital
        except Exception as e:
            print(f"Warning: Could not load account balances from {accounts_path}: {e}")
            return 14194.36  # Fallback amount

    def load_strategy_data_enhanced(
        self, incoming_csv: str, current_csv: str
    ) -> Tuple[List[StrategyMetrics], List[StrategyMetrics]]:
        """Load strategy metrics with stop-loss data"""

        # Load incoming strategies with stop-loss data
        incoming_df = pd.read_csv(incoming_csv)
        incoming_strategies = []

        for _, row in incoming_df.iterrows():
            strategy = StrategyMetrics(
                ticker=row["Ticker"],
                strategy_type=row["Strategy Type"],
                short_window=row["Short Window"],
                long_window=row["Long Window"],
                total_return=row["Total Return [%]"] / 100,
                win_rate=row["Win Rate [%]"] / 100,
                profit_factor=row["Profit Factor"],
                sortino_ratio=row["Sortino Ratio"],
                sharpe_ratio=row["Sharpe Ratio"],
                max_drawdown=row["Max Drawdown [%]"] / 100,
                volatility=row["Annualized Volatility"],
                expectancy=row["Expectancy per Trade"],
                calmar_ratio=row["Calmar Ratio"],
                avg_winning_trade=row["Avg Winning Trade [%]"] / 100,
                avg_losing_trade=abs(row["Avg Losing Trade [%]"])
                / 100,  # Convert to positive
                stop_loss=row["Stop Loss [%]"],  # Already as decimal (0.12, 0.105)
            )
            incoming_strategies.append(strategy)

        # Load current strategies (without stop-loss data for now)
        current_df = pd.read_csv(current_csv)
        current_strategies = []

        for _, row in current_df.iterrows():
            strategy = StrategyMetrics(
                ticker=row["Ticker"],
                strategy_type=row["Strategy Type"],
                short_window=row["Short Window"],
                long_window=row["Long Window"],
                total_return=row["Total Return [%]"] / 100,
                win_rate=row["Win Rate [%]"] / 100,
                profit_factor=row["Profit Factor"],
                sortino_ratio=row["Sortino Ratio"],
                sharpe_ratio=row["Sharpe Ratio"],
                max_drawdown=row["Max Drawdown [%]"] / 100,
                volatility=row["Annualized Volatility"],
                expectancy=row["Expectancy"],
                calmar_ratio=row["Calmar Ratio"],
                avg_winning_trade=0.15,  # Estimated 15% average win
                avg_losing_trade=0.08,  # Estimated 8% average loss
                stop_loss=0.10,  # Estimated 10% stop-loss
            )
            current_strategies.append(strategy)

        return incoming_strategies, current_strategies

    def calculate_theoretical_kelly(self, strategy: StrategyMetrics) -> float:
        """
        Calculate theoretical Kelly Criterion: K = (bp - q) / b

        Where:
        - b = average win / average loss (payoff ratio)
        - p = win probability
        - q = loss probability (1-p)
        """

        # Calculate payoff ratio (b)
        if strategy.avg_losing_trade > 0:
            payoff_ratio = strategy.avg_winning_trade / strategy.avg_losing_trade
        else:
            # Fallback to profit factor approximation
            payoff_ratio = (
                strategy.profit_factor * strategy.win_rate / (1 - strategy.win_rate)
            )

        # Kelly formula
        win_prob = strategy.win_rate
        loss_prob = 1 - win_prob

        theoretical_kelly = (payoff_ratio * win_prob - loss_prob) / payoff_ratio

        # Ensure positive Kelly (negative Kelly means don't trade)
        return max(theoretical_kelly, 0.0)

    def calculate_risk_adjusted_kelly(
        self, strategy: StrategyMetrics, theoretical_kelly: float
    ) -> float:
        """
        Adjust Kelly for strategy quality and risk characteristics
        """

        # Quality adjustments
        sortino_factor = min(
            strategy.sortino_ratio / 1.2, 2.0
        )  # Normalize around 1.2 Sortino
        calmar_factor = min(
            strategy.calmar_ratio / 0.5, 2.0
        )  # Normalize around 0.5 Calmar

        # Risk adjustments
        drawdown_penalty = 1 / (
            1 + strategy.max_drawdown * 2
        )  # Penalty for high drawdown
        volatility_penalty = 1 / (
            1 + strategy.volatility
        )  # Penalty for high volatility

        # Combined adjustment factor
        quality_factor = np.sqrt(sortino_factor * calmar_factor)
        risk_factor = np.sqrt(drawdown_penalty * volatility_penalty)

        adjustment_factor = quality_factor * risk_factor

        # Apply global Kelly base as a scaling factor
        risk_adjusted_kelly = (
            theoretical_kelly * adjustment_factor * (self.global_kelly_base / 0.045)
        )

        return min(risk_adjusted_kelly, self.max_position_risk)

    def calculate_stop_loss_adjusted_kelly(
        self, strategy: StrategyMetrics, risk_adjusted_kelly: float
    ) -> float:
        """
        Adjust Kelly for actual stop-loss risk rather than theoretical max drawdown

        This is crucial: Kelly should reflect the actual risk per trade (stop-loss)
        not the historical maximum drawdown.
        """

        # The stop-loss represents our actual risk per trade
        actual_risk_per_trade = strategy.stop_loss

        # If theoretical Kelly assumes different risk levels, we need to scale
        # Standard Kelly assumes you can lose 100% of position
        # But with stop-loss, you only risk the stop-loss percentage

        # Calculate effective Kelly for stop-loss risk
        # If stop-loss is 10%, we can afford larger position than theoretical Kelly suggests
        stop_loss_multiplier = 0.10 / actual_risk_per_trade  # 10% baseline stop-loss

        # Apply multiplier but cap at reasonable levels
        stop_loss_adjusted = risk_adjusted_kelly * min(stop_loss_multiplier, 2.0)

        # Ensure we don't exceed maximum position risk
        return min(stop_loss_adjusted, self.max_position_risk)

    def apply_portfolio_constraints(
        self, allocations: Dict[str, float], strategies: List[StrategyMetrics]
    ) -> Dict[str, float]:
        """
        Apply portfolio-level constraints including CVaR targeting
        """

        # Calculate total portfolio risk
        total_risk = 0
        for strategy in strategies:
            alloc = allocations.get(strategy.ticker, 0.0)
            # Risk contribution = allocation * volatility * stop_loss
            risk_contrib = alloc * strategy.volatility * strategy.stop_loss
            total_risk += risk_contrib

        # Apply correlation adjustment (positions aren't perfectly uncorrelated)
        adjusted_risk = total_risk * self.correlation_adjustment

        # If risk exceeds CVaR target, scale down all allocations proportionally
        if adjusted_risk > self.cvar_target:
            scale_factor = self.cvar_target / adjusted_risk
            allocations = {
                ticker: alloc * scale_factor for ticker, alloc in allocations.items()
            }

        return allocations

    def optimize_kelly_allocations(
        self, strategies: List[StrategyMetrics]
    ) -> Dict[str, float]:
        """
        Optimize Kelly allocations with portfolio constraints
        """

        allocations = {}

        for strategy in strategies:
            # Step 1: Calculate theoretical Kelly
            theoretical_kelly = self.calculate_theoretical_kelly(strategy)

            # Step 2: Apply risk adjustments
            risk_adjusted_kelly = self.calculate_risk_adjusted_kelly(
                strategy, theoretical_kelly
            )

            # Step 3: Adjust for stop-loss reality
            stop_loss_adjusted_kelly = self.calculate_stop_loss_adjusted_kelly(
                strategy, risk_adjusted_kelly
            )

            allocations[strategy.ticker] = stop_loss_adjusted_kelly

        # Step 4: Apply portfolio-level constraints
        constrained_allocations = self.apply_portfolio_constraints(
            allocations, strategies
        )

        return constrained_allocations

    def get_current_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Get current market prices for position calculation"""

        prices = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")
                if not hist.empty:
                    prices[ticker] = hist["Close"].iloc[-1]
                else:
                    prices[ticker] = 100.0  # Fallback price
            except:
                prices[ticker] = 100.0  # Fallback price

        return prices

    def calculate_kelly_optimized_positions(
        self,
        incoming_strategies: List[StrategyMetrics],
        current_strategies: List[StrategyMetrics],
    ) -> List[KellyOptimizedResult]:
        """
        Calculate Kelly-optimized position sizes
        """

        # Get optimal allocations
        all_strategies = incoming_strategies + current_strategies
        optimal_allocations = self.optimize_kelly_allocations(all_strategies)

        # Get current prices
        tickers = [s.ticker for s in incoming_strategies]
        current_prices = self.get_current_prices(tickers)

        # Calculate position sizing results for incoming strategies only
        results = []

        for strategy in incoming_strategies:
            ticker = strategy.ticker

            # Calculate all Kelly variants for transparency
            theoretical_kelly = self.calculate_theoretical_kelly(strategy)
            risk_adjusted_kelly = self.calculate_risk_adjusted_kelly(
                strategy, theoretical_kelly
            )
            stop_loss_adjusted_kelly = self.calculate_stop_loss_adjusted_kelly(
                strategy, risk_adjusted_kelly
            )
            final_allocation = optimal_allocations.get(ticker, 0.0)

            # Calculate dollar amounts and shares
            dollar_amount = final_allocation * self.total_capital
            current_price = current_prices.get(ticker, 100.0)
            position_shares = int(dollar_amount / current_price)
            actual_dollar_amount = position_shares * current_price

            # Calculate risk metrics
            max_risk_per_trade = actual_dollar_amount * strategy.stop_loss
            expected_return = final_allocation * strategy.total_return
            risk_contribution = (
                final_allocation * strategy.volatility * strategy.stop_loss
            )

            result = KellyOptimizedResult(
                ticker=ticker,
                theoretical_kelly=theoretical_kelly,
                risk_adjusted_kelly=risk_adjusted_kelly,
                stop_loss_adjusted_kelly=stop_loss_adjusted_kelly,
                final_allocation=final_allocation,
                dollar_amount=actual_dollar_amount,
                position_shares=position_shares,
                max_risk_per_trade=max_risk_per_trade,
                expected_return=expected_return,
                risk_contribution=risk_contribution,
            )

            results.append(result)

        return results

    def generate_kelly_report(self, results: List[KellyOptimizedResult]) -> str:
        """Generate comprehensive Kelly-optimized position sizing report"""

        report = []
        report.append("=" * 80)
        report.append("KELLY-OPTIMIZED POSITION SIZING REPORT")
        report.append("=" * 80)
        report.append(f"Total Capital: ${self.total_capital:,.2f}")
        report.append(f"Global Kelly Base: {self.global_kelly_base:.1%}")
        report.append(f"CVaR Target: {self.cvar_target:.1%}")
        report.append(f"Max Position Risk: {self.max_position_risk:.1%}")
        report.append(f"Correlation Adjustment: {self.correlation_adjustment:.1%}")
        report.append("")

        # Kelly calculation breakdown
        report.append("KELLY CRITERION ANALYSIS")
        report.append("-" * 50)
        report.append(
            f"{'Ticker':<8} {'Theor%':<8} {'Risk%':<8} {'Stop%':<8} {'Final%':<8} {'Shares':<8} {'Amount':<12}"
        )
        report.append("-" * 50)

        total_allocation = 0
        total_amount = 0
        total_risk = 0

        for result in results:
            report.append(
                f"{result.ticker:<8} "
                f"{result.theoretical_kelly:<8.1%} "
                f"{result.risk_adjusted_kelly:<8.1%} "
                f"{result.stop_loss_adjusted_kelly:<8.1%} "
                f"{result.final_allocation:<8.1%} "
                f"{result.position_shares:<8} "
                f"${result.dollar_amount:<11,.0f}"
            )
            total_allocation += result.final_allocation
            total_amount += result.dollar_amount
            total_risk += result.risk_contribution

        report.append("-" * 50)
        report.append(
            f"{'TOTAL':<40} {total_allocation:<8.1%} {'':<8} ${total_amount:<11,.0f}"
        )
        report.append("")

        # Risk analysis
        report.append("KELLY RISK ANALYSIS")
        report.append("-" * 30)
        report.append(f"Total Portfolio Risk: {total_risk:.1%}")
        report.append(f"CVaR Target Utilization: {total_risk/self.cvar_target:.1%}")
        report.append(
            f"Average Kelly per Position: {total_allocation/len(results):.1%}"
        )

        # Individual position analysis
        report.append("\nINDIVIDUAL KELLY BREAKDOWN")
        report.append("-" * 40)

        for result in results:
            report.append(f"\n{result.ticker}:")
            report.append(f"  Theoretical Kelly: {result.theoretical_kelly:.1%}")
            report.append(f"  Risk-Adjusted Kelly: {result.risk_adjusted_kelly:.1%}")
            report.append(
                f"  Stop-Loss Adjusted: {result.stop_loss_adjusted_kelly:.1%}"
            )
            report.append(f"  Final Allocation: {result.final_allocation:.1%}")
            report.append(f"  Position Shares: {result.position_shares:,}")
            report.append(f"  Dollar Amount: ${result.dollar_amount:,.0f}")
            report.append(f"  Max Risk per Trade: ${result.max_risk_per_trade:,.0f}")
            report.append(f"  Expected Return: {result.expected_return:.1%}")

        return "\n".join(report)

    def export_to_json(
        self,
        results: List[KellyOptimizedResult],
        output_path: str = "data/positions/incoming.json",
    ) -> bool:
        """Export position sizing results to JSON file"""

        try:
            # Prepare JSON structure
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "total_capital": self.total_capital,
                "kelly_criterion": self.global_kelly_base,
                "cvar_target": self.cvar_target,
                "cvar_utilization": sum(r.risk_contribution for r in results),
                "positions": [],
                "portfolio_summary": {
                    "total_allocation": sum(r.final_allocation for r in results),
                    "total_amount": sum(r.dollar_amount for r in results),
                    "total_risk": sum(r.risk_contribution for r in results),
                    "remaining_capacity": self.cvar_target
                    - sum(r.risk_contribution for r in results),
                    "average_kelly": sum(r.final_allocation for r in results)
                    / len(results)
                    if results
                    else 0,
                },
            }

            # Sort results by allocation size for priority ordering
            sorted_results = sorted(
                results, key=lambda x: x.final_allocation, reverse=True
            )

            # Add position data
            for i, result in enumerate(sorted_results, 1):
                position_data = {
                    "ticker": result.ticker,
                    "strategy_type": "SMA",  # Default, should be extracted from strategy data
                    "theoretical_kelly": round(result.theoretical_kelly, 3),
                    "risk_adjusted_kelly": round(result.risk_adjusted_kelly, 3),
                    "stop_loss_adjusted_kelly": round(
                        result.stop_loss_adjusted_kelly, 3
                    ),
                    "final_allocation": round(result.final_allocation, 3),
                    "position_shares": result.position_shares,
                    "dollar_amount": round(result.dollar_amount, 2),
                    "stop_loss_percentage": None,  # Will be populated from strategy data
                    "max_risk_per_trade": round(result.max_risk_per_trade, 2),
                    "expected_return": round(result.expected_return, 3),
                    "risk_contribution": round(result.risk_contribution, 3),
                    "priority": i,
                }
                export_data["positions"].append(position_data)

            # Ensure directory exists
            import os

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Write JSON file
            with open(output_path, "w") as f:
                json.dump(export_data, f, indent=2)

            print(f"✅ Position sizing results exported to: {output_path}")
            return True

        except Exception as e:
            print(f"❌ Error exporting to JSON: {e}")
            return False


def main():
    """Example usage of the Kelly-optimized position sizer"""

    # Initialize Kelly-optimized sizer with data file paths
    sizer = KellyOptimizedSizer(
        kelly_params_path="data/kelly/kelly_parameters.json",
        accounts_path="data/accounts/manual_balances.json",
        cvar_target=0.118,
        max_position_risk=0.15,
        correlation_adjustment=0.8,
    )

    # Display loaded parameters
    print(f"Loaded Kelly Criterion: {sizer.global_kelly_base:.1%}")
    print(f"Loaded Total Capital: ${sizer.total_capital:,.2f}")
    print()

    # Load strategy data
    incoming_strategies, current_strategies = sizer.load_strategy_data_enhanced(
        incoming_csv="../../csv/strategies/incoming.csv",
        current_csv="../../csv/strategies/risk_on.csv",
    )

    # Calculate Kelly-optimized positions
    results = sizer.calculate_kelly_optimized_positions(
        incoming_strategies, current_strategies
    )

    # Generate and print report
    report = sizer.generate_kelly_report(results)
    print(report)

    # Export results to JSON
    sizer.export_to_json(results, "data/positions/incoming.json")


if __name__ == "__main__":
    main()
