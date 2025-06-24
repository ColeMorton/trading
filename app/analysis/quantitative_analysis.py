"""
Comprehensive Quantitative Analysis for Trading Strategies

This module performs advanced quantitative analysis on trading strategy data,
providing professional-grade insights and recommendations for portfolio optimization.

Key Features:
- Strategy performance analysis with risk-adjusted metrics
- Portfolio optimization and correlation analysis
- Monte Carlo simulation support
- Value at Risk (VaR) calculations
- Professional report generation with actionable recommendations
"""

import json
import logging
import warnings
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Scientific computing imports
from scipy import stats

try:
    from scipy.optimize import minimize

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# Optional plotting imports
try:
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.style.use("seaborn-v0_8")
    sns.set_palette("husl")
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

# Project imports
from app.tools.logging_context import logging_context
from app.tools.project_utils import get_project_root


@dataclass
class StrategyMetrics:
    """Data class for comprehensive strategy metrics"""

    ticker: str
    strategy_type: str
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    var_95: float
    var_99: float
    skewness: float
    kurtosis: float
    beta: Optional[float] = None
    alpha: Optional[float] = None
    correlation_to_market: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class PortfolioAnalysis:
    """Data class for portfolio-level analysis results"""

    total_strategies: int
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    var_95: float
    var_99: float
    diversification_ratio: float
    correlation_matrix: Dict
    top_performers: List[str]
    risk_contributors: List[str]
    recommendations: List[str]


class QuantitativeAnalyzer:
    """
    Advanced quantitative analysis engine for trading strategies.

    Provides comprehensive statistical analysis, risk assessment, and
    portfolio optimization recommendations based on strategy performance data.
    """

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize the quantitative analyzer"""
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(get_project_root())

        self.strategies_dir = self.base_dir / "csv" / "strategies"
        self.json_dir = self.base_dir / "json"
        self.trade_history_dir = self.json_dir / "trade_history"
        self.output_dir = self.base_dir / "reports"
        self.output_dir.mkdir(exist_ok=True)

        # Initialize data containers
        self.trades_data: Optional[pd.DataFrame] = None
        self.incoming_data: Optional[pd.DataFrame] = None
        self.json_data: Optional[Dict] = None
        self.strategy_metrics: List[StrategyMetrics] = []

        # Market benchmark data (if available)
        self.benchmark_return = 0.10  # Default 10% annual return

    def load_data(self) -> bool:
        """Load all required data files"""
        try:
            # Load trades.csv (existing portfolio)
            trades_path = self.strategies_dir / "trades.csv"
            if trades_path.exists():
                self.trades_data = pd.read_csv(trades_path)
                print(
                    f"Loaded {len(self.trades_data)} existing strategies from trades.csv"
                )
            else:
                print("Warning: trades.csv not found")
                return False

            # Load incoming.csv (potential new positions)
            incoming_path = self.strategies_dir / "incoming.csv"
            if incoming_path.exists():
                self.incoming_data = pd.read_csv(incoming_path)
                print(
                    f"Loaded {len(self.incoming_data)} incoming strategies from incoming.csv"
                )
            else:
                print("Warning: incoming.csv not found")

            # Load JSON enhancement data if available
            json_files = list(self.trade_history_dir.glob("*.json"))
            if json_files:
                print(f"Found {len(json_files)} JSON trade history files")
                # Load first available JSON file as example
                with open(json_files[0], "r") as f:
                    self.json_data = json.load(f)
                    print(f"Loaded JSON data from {json_files[0].name}")

            return True

        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return False

    def calculate_strategy_metrics(self, data: pd.DataFrame) -> List[StrategyMetrics]:
        """Calculate comprehensive metrics for each strategy"""
        metrics = []

        for _, row in data.iterrows():
            try:
                # Core metrics
                ticker = row.get("Ticker", "Unknown")
                strategy_type = row.get("Strategy Type", "Unknown")
                total_return = row.get("Total Return [%]", 0) / 100
                annualized_return = row.get("Annualized Return", 0)
                annualized_volatility = row.get("Annualized Volatility", 0)

                # Risk metrics
                sharpe_ratio = row.get("Sharpe Ratio", 0)
                sortino_ratio = row.get("Sortino Ratio", 0)
                calmar_ratio = row.get("Calmar Ratio", 0)
                max_drawdown = row.get("Max Drawdown [%]", 0)

                # Performance metrics
                win_rate = row.get("Win Rate [%]", 0)
                profit_factor = row.get("Profit Factor", 0)

                # Statistical metrics
                skewness = row.get("Skew", 0)
                kurtosis = row.get("Kurtosis", 0)
                beta = row.get("Beta", None)
                alpha = row.get("Alpha", None)

                # Calculate VaR (approximate from available data)
                var_95 = self._calculate_var(
                    annualized_return, annualized_volatility, 0.95
                )
                var_99 = self._calculate_var(
                    annualized_return, annualized_volatility, 0.99
                )

                metric = StrategyMetrics(
                    ticker=ticker,
                    strategy_type=strategy_type,
                    total_return=total_return,
                    annualized_return=annualized_return,
                    annualized_volatility=annualized_volatility,
                    sharpe_ratio=sharpe_ratio,
                    sortino_ratio=sortino_ratio,
                    calmar_ratio=calmar_ratio,
                    max_drawdown=max_drawdown,
                    win_rate=win_rate,
                    profit_factor=profit_factor,
                    var_95=var_95,
                    var_99=var_99,
                    skewness=skewness,
                    kurtosis=kurtosis,
                    beta=beta,
                    alpha=alpha,
                )

                metrics.append(metric)

            except Exception as e:
                print(f"Error calculating metrics for {ticker}: {str(e)}")
                continue

        return metrics

    def _calculate_var(
        self, return_rate: float, volatility: float, confidence: float
    ) -> float:
        """Calculate Value at Risk using parametric method"""
        try:
            z_score = stats.norm.ppf(1 - confidence)
            var = return_rate + z_score * volatility
            return var
        except:
            return 0.0

    def analyze_portfolio_correlation(self, data: pd.DataFrame) -> pd.DataFrame:
        """Analyze correlation between strategies"""
        try:
            # Create correlation matrix based on available metrics
            correlation_columns = [
                "Total Return [%]",
                "Sharpe Ratio",
                "Max Drawdown [%]",
                "Win Rate [%]",
                "Profit Factor",
                "Annualized Volatility",
            ]

            # Filter available columns
            available_columns = [
                col for col in correlation_columns if col in data.columns
            ]

            if len(available_columns) >= 2:
                correlation_matrix = data[available_columns].corr()
                return correlation_matrix
            else:
                print("Insufficient data for correlation analysis")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error in correlation analysis: {str(e)}")
            return pd.DataFrame()

    def calculate_portfolio_metrics(
        self, strategies: List[StrategyMetrics]
    ) -> PortfolioAnalysis:
        """Calculate portfolio-level metrics and analysis"""
        if not strategies:
            return None

        try:
            # Aggregate metrics
            total_strategies = len(strategies)
            avg_return = np.mean([s.total_return for s in strategies])
            avg_annualized_return = np.mean([s.annualized_return for s in strategies])
            avg_volatility = np.mean([s.annualized_volatility for s in strategies])
            avg_sharpe = np.mean([s.sharpe_ratio for s in strategies])
            max_drawdown = np.max([s.max_drawdown for s in strategies])

            # Portfolio VaR (simplified)
            portfolio_var_95 = np.mean([s.var_95 for s in strategies])
            portfolio_var_99 = np.mean([s.var_99 for s in strategies])

            # Diversification ratio (simplified)
            strategy_volatilities = [s.annualized_volatility for s in strategies]
            diversification_ratio = np.mean(strategy_volatilities) / np.sqrt(
                np.mean(np.square(strategy_volatilities))
            )

            # Top performers
            sorted_strategies = sorted(
                strategies, key=lambda x: x.sharpe_ratio, reverse=True
            )
            top_performers = [s.ticker for s in sorted_strategies[:5]]

            # Risk contributors (highest drawdown)
            risk_sorted = sorted(strategies, key=lambda x: x.max_drawdown, reverse=True)
            risk_contributors = [s.ticker for s in risk_sorted[:3]]

            # Generate recommendations
            recommendations = self._generate_recommendations(strategies)

            return PortfolioAnalysis(
                total_strategies=total_strategies,
                total_return=avg_return,
                annualized_return=avg_annualized_return,
                annualized_volatility=avg_volatility,
                sharpe_ratio=avg_sharpe,
                max_drawdown=max_drawdown,
                var_95=portfolio_var_95,
                var_99=portfolio_var_99,
                diversification_ratio=diversification_ratio,
                correlation_matrix={},  # Will be populated separately
                top_performers=top_performers,
                risk_contributors=risk_contributors,
                recommendations=recommendations,
            )

        except Exception as e:
            print(f"Error calculating portfolio metrics: {str(e)}")
            return None

    def _generate_recommendations(self, strategies: List[StrategyMetrics]) -> List[str]:
        """Generate actionable trading recommendations based on analysis"""
        recommendations = []

        try:
            # Performance recommendations
            high_sharpe_strategies = [s for s in strategies if s.sharpe_ratio > 1.0]
            if high_sharpe_strategies:
                recommendations.append(
                    f"Consider increasing allocation to high Sharpe ratio strategies: "
                    f"{', '.join([s.ticker for s in high_sharpe_strategies[:3]])}"
                )

            # Risk management recommendations
            high_drawdown_strategies = [s for s in strategies if s.max_drawdown > 50]
            if high_drawdown_strategies:
                recommendations.append(
                    f"Review risk management for high drawdown strategies: "
                    f"{', '.join([s.ticker for s in high_drawdown_strategies[:3]])}"
                )

            # Diversification recommendations
            strategy_types = {}
            for s in strategies:
                strategy_types[s.strategy_type] = (
                    strategy_types.get(s.strategy_type, 0) + 1
                )

            dominant_strategy = max(strategy_types, key=strategy_types.get)
            if strategy_types[dominant_strategy] / len(strategies) > 0.7:
                recommendations.append(
                    f"Portfolio is concentrated in {dominant_strategy} strategies. "
                    f"Consider diversifying with other strategy types."
                )

            # Win rate recommendations
            low_win_rate_strategies = [s for s in strategies if s.win_rate < 40]
            if low_win_rate_strategies:
                recommendations.append(
                    f"Monitor low win rate strategies for potential optimization: "
                    f"{', '.join([s.ticker for s in low_win_rate_strategies[:3]])}"
                )

            # Volatility recommendations
            avg_volatility = np.mean([s.annualized_volatility for s in strategies])
            high_vol_strategies = [
                s for s in strategies if s.annualized_volatility > avg_volatility * 1.5
            ]
            if high_vol_strategies:
                recommendations.append(
                    f"Consider position sizing adjustments for high volatility strategies: "
                    f"{', '.join([s.ticker for s in high_vol_strategies[:3]])}"
                )

        except Exception as e:
            print(f"Error generating recommendations: {str(e)}")
            recommendations.append(
                "Unable to generate specific recommendations due to data limitations."
            )

        return recommendations

    def compare_portfolios(self) -> Dict:
        """Compare existing trades vs incoming strategies"""
        comparison = {}

        try:
            if self.trades_data is not None:
                existing_metrics = self.calculate_strategy_metrics(self.trades_data)
                existing_analysis = self.calculate_portfolio_metrics(existing_metrics)
                comparison["existing"] = existing_analysis

            if self.incoming_data is not None:
                incoming_metrics = self.calculate_strategy_metrics(self.incoming_data)
                incoming_analysis = self.calculate_portfolio_metrics(incoming_metrics)
                comparison["incoming"] = incoming_analysis

            # Combined analysis
            if self.trades_data is not None and self.incoming_data is not None:
                combined_data = pd.concat(
                    [self.trades_data, self.incoming_data], ignore_index=True
                )
                combined_metrics = self.calculate_strategy_metrics(combined_data)
                combined_analysis = self.calculate_portfolio_metrics(combined_metrics)
                comparison["combined"] = combined_analysis

                # Enhancement analysis
                if existing_analysis and combined_analysis:
                    enhancement_impact = {
                        "return_improvement": combined_analysis.annualized_return
                        - existing_analysis.annualized_return,
                        "sharpe_improvement": combined_analysis.sharpe_ratio
                        - existing_analysis.sharpe_ratio,
                        "risk_change": combined_analysis.max_drawdown
                        - existing_analysis.max_drawdown,
                        "diversification_change": combined_analysis.diversification_ratio
                        - existing_analysis.diversification_ratio,
                    }
                    comparison["enhancement_impact"] = enhancement_impact

        except Exception as e:
            print(f"Error in portfolio comparison: {str(e)}")

        return comparison

    def run_monte_carlo_analysis(
        self,
        strategies: List[StrategyMetrics],
        num_simulations: int = 10000,
        time_horizon: int = 252,
    ) -> Dict:
        """Run Monte Carlo simulation for portfolio projections"""
        try:
            if not strategies:
                return {}

            # Portfolio statistics
            portfolio_return = np.mean([s.annualized_return for s in strategies])
            portfolio_volatility = np.mean(
                [s.annualized_volatility for s in strategies]
            )

            # Run simulations
            simulations = []
            for _ in range(num_simulations):
                daily_returns = np.random.normal(
                    portfolio_return / 252,
                    portfolio_volatility / np.sqrt(252),
                    time_horizon,
                )
                final_value = np.prod(1 + daily_returns)
                simulations.append(final_value)

            simulations = np.array(simulations)

            # Calculate statistics
            monte_carlo_results = {
                "mean_final_value": np.mean(simulations),
                "median_final_value": np.median(simulations),
                "std_final_value": np.std(simulations),
                "var_95": np.percentile(simulations, 5),
                "var_99": np.percentile(simulations, 1),
                "probability_of_loss": np.sum(simulations < 1.0) / num_simulations,
                "probability_of_doubling": np.sum(simulations > 2.0) / num_simulations,
            }

            return monte_carlo_results

        except Exception as e:
            print(f"Error in Monte Carlo analysis: {str(e)}")
            return {}

    def generate_comprehensive_report(self) -> str:
        """Generate a comprehensive quantitative analysis report"""

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("COMPREHENSIVE QUANTITATIVE ANALYSIS REPORT")
        report_lines.append("=" * 80)
        report_lines.append(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report_lines.append("")

        try:
            # Portfolio comparison
            comparison = self.compare_portfolios()

            # Executive Summary
            report_lines.append("EXECUTIVE SUMMARY")
            report_lines.append("-" * 40)

            if "existing" in comparison and comparison["existing"]:
                existing = comparison["existing"]
                report_lines.append(
                    f"• Existing Portfolio: {existing.total_strategies} strategies"
                )
                report_lines.append(
                    f"• Portfolio Sharpe Ratio: {existing.sharpe_ratio:.3f}"
                )
                report_lines.append(
                    f"• Annualized Return: {existing.annualized_return*100:.2f}%"
                )
                report_lines.append(f"• Maximum Drawdown: {existing.max_drawdown:.2f}%")

            if "incoming" in comparison and comparison["incoming"]:
                incoming = comparison["incoming"]
                report_lines.append(
                    f"• Incoming Strategies: {incoming.total_strategies} strategies"
                )
                report_lines.append(
                    f"• Incoming Sharpe Ratio: {incoming.sharpe_ratio:.3f}"
                )
                report_lines.append(
                    f"• Incoming Annualized Return: {incoming.annualized_return*100:.2f}%"
                )

            if "enhancement_impact" in comparison:
                impact = comparison["enhancement_impact"]
                report_lines.append(
                    f"• Expected Return Enhancement: {impact['return_improvement']*100:.2f}%"
                )
                report_lines.append(
                    f"• Expected Sharpe Improvement: {impact['sharpe_improvement']:.3f}"
                )

            report_lines.append("")

            # Detailed Analysis for Existing Portfolio
            if "existing" in comparison and comparison["existing"]:
                existing = comparison["existing"]
                report_lines.append("EXISTING PORTFOLIO ANALYSIS")
                report_lines.append("-" * 40)
                report_lines.append(f"Total Strategies: {existing.total_strategies}")
                report_lines.append(
                    f"Annualized Return: {existing.annualized_return*100:.2f}%"
                )
                report_lines.append(
                    f"Annualized Volatility: {existing.annualized_volatility*100:.2f}%"
                )
                report_lines.append(f"Sharpe Ratio: {existing.sharpe_ratio:.3f}")
                report_lines.append(f"Maximum Drawdown: {existing.max_drawdown:.2f}%")
                report_lines.append(f"95% VaR: {existing.var_95*100:.2f}%")
                report_lines.append(f"99% VaR: {existing.var_99*100:.2f}%")
                report_lines.append(
                    f"Diversification Ratio: {existing.diversification_ratio:.3f}"
                )
                report_lines.append("")

                if existing.top_performers:
                    report_lines.append("Top Performing Strategies:")
                    for i, ticker in enumerate(existing.top_performers, 1):
                        report_lines.append(f"  {i}. {ticker}")
                    report_lines.append("")

                if existing.risk_contributors:
                    report_lines.append("Highest Risk Contributors:")
                    for i, ticker in enumerate(existing.risk_contributors, 1):
                        report_lines.append(f"  {i}. {ticker}")
                    report_lines.append("")

            # Incoming Portfolio Analysis
            if "incoming" in comparison and comparison["incoming"]:
                incoming = comparison["incoming"]
                report_lines.append("INCOMING STRATEGIES ANALYSIS")
                report_lines.append("-" * 40)
                report_lines.append(f"Total Strategies: {incoming.total_strategies}")
                report_lines.append(
                    f"Annualized Return: {incoming.annualized_return*100:.2f}%"
                )
                report_lines.append(
                    f"Annualized Volatility: {incoming.annualized_volatility*100:.2f}%"
                )
                report_lines.append(f"Sharpe Ratio: {incoming.sharpe_ratio:.3f}")
                report_lines.append(f"Maximum Drawdown: {incoming.max_drawdown:.2f}%")
                report_lines.append("")

                if incoming.top_performers:
                    report_lines.append("Top Incoming Strategies:")
                    for i, ticker in enumerate(incoming.top_performers, 1):
                        report_lines.append(f"  {i}. {ticker}")
                    report_lines.append("")

            # Portfolio Enhancement Analysis
            if "enhancement_impact" in comparison:
                impact = comparison["enhancement_impact"]
                report_lines.append("PORTFOLIO ENHANCEMENT ANALYSIS")
                report_lines.append("-" * 40)
                report_lines.append(
                    f"Expected Return Enhancement: {impact['return_improvement']*100:.2f}%"
                )
                report_lines.append(
                    f"Expected Sharpe Improvement: {impact['sharpe_improvement']:.3f}"
                )
                report_lines.append(
                    f"Risk Change (Max Drawdown): {impact['risk_change']:.2f}%"
                )
                report_lines.append(
                    f"Diversification Change: {impact['diversification_change']:.3f}"
                )
                report_lines.append("")

                # Enhancement recommendations
                if impact["return_improvement"] > 0:
                    report_lines.append(
                        "✓ Adding incoming strategies is expected to improve returns"
                    )
                else:
                    report_lines.append(
                        "⚠ Adding incoming strategies may reduce overall returns"
                    )

                if impact["sharpe_improvement"] > 0:
                    report_lines.append(
                        "✓ Adding incoming strategies should improve risk-adjusted returns"
                    )
                else:
                    report_lines.append(
                        "⚠ Adding incoming strategies may worsen risk-adjusted returns"
                    )

                report_lines.append("")

            # Monte Carlo Analysis
            if "existing" in comparison and comparison["existing"]:
                existing_metrics = self.calculate_strategy_metrics(self.trades_data)
                mc_results = self.run_monte_carlo_analysis(existing_metrics)

                if mc_results:
                    report_lines.append("MONTE CARLO SIMULATION (1 Year Projection)")
                    report_lines.append("-" * 40)
                    report_lines.append(
                        f"Expected Portfolio Value: {mc_results['mean_final_value']:.3f}"
                    )
                    report_lines.append(
                        f"Median Portfolio Value: {mc_results['median_final_value']:.3f}"
                    )
                    report_lines.append(
                        f"95% Confidence Interval: {mc_results['var_95']:.3f}"
                    )
                    report_lines.append(
                        f"99% Confidence Interval: {mc_results['var_99']:.3f}"
                    )
                    report_lines.append(
                        f"Probability of Loss: {mc_results['probability_of_loss']*100:.1f}%"
                    )
                    report_lines.append(
                        f"Probability of Doubling: {mc_results['probability_of_doubling']*100:.1f}%"
                    )
                    report_lines.append("")

            # Recommendations
            report_lines.append("ACTIONABLE RECOMMENDATIONS")
            report_lines.append("-" * 40)

            # Gather all recommendations
            all_recommendations = []

            if "existing" in comparison and comparison["existing"]:
                all_recommendations.extend(comparison["existing"].recommendations)

            if "incoming" in comparison and comparison["incoming"]:
                all_recommendations.extend(comparison["incoming"].recommendations)

            # Add portfolio enhancement recommendations
            if "enhancement_impact" in comparison:
                impact = comparison["enhancement_impact"]
                if impact["return_improvement"] > 0.05:  # 5% improvement
                    all_recommendations.append(
                        "STRONG RECOMMENDATION: Add incoming strategies to portfolio - "
                        "significant return enhancement expected"
                    )
                elif impact["sharpe_improvement"] > 0.2:
                    all_recommendations.append(
                        "RECOMMENDATION: Add incoming strategies - "
                        "meaningful risk-adjusted return improvement expected"
                    )

                if impact["risk_change"] > 10:  # 10% increase in max drawdown
                    all_recommendations.append(
                        "CAUTION: Adding incoming strategies may increase portfolio risk. "
                        "Consider position sizing adjustments."
                    )

            # Display recommendations
            if all_recommendations:
                for i, rec in enumerate(all_recommendations, 1):
                    report_lines.append(f"{i}. {rec}")
            else:
                report_lines.append(
                    "No specific recommendations available based on current data."
                )

            report_lines.append("")
            report_lines.append("=" * 80)
            report_lines.append("END OF REPORT")
            report_lines.append("=" * 80)

        except Exception as e:
            report_lines.append(f"Error generating report: {str(e)}")

        return "\n".join(report_lines)

    def save_report(self, report_content: str, filename: Optional[str] = None) -> str:
        """Save the analysis report to file"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"quantitative_analysis_report_{timestamp}.txt"

            report_path = self.output_dir / filename

            with open(report_path, "w") as f:
                f.write(report_content)

            print(f"Report saved to: {report_path}")
            return str(report_path)

        except Exception as e:
            print(f"Error saving report: {str(e)}")
            return ""

    def export_metrics_to_json(self, filename: Optional[str] = None) -> str:
        """Export detailed metrics to JSON for further analysis"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"strategy_metrics_{timestamp}.json"

            export_path = self.output_dir / filename

            # Prepare export data
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "existing_strategies": [],
                "incoming_strategies": [],
                "portfolio_comparison": {},
            }

            # Add existing strategies
            if self.trades_data is not None:
                existing_metrics = self.calculate_strategy_metrics(self.trades_data)
                export_data["existing_strategies"] = [
                    m.to_dict() for m in existing_metrics
                ]

            # Add incoming strategies
            if self.incoming_data is not None:
                incoming_metrics = self.calculate_strategy_metrics(self.incoming_data)
                export_data["incoming_strategies"] = [
                    m.to_dict() for m in incoming_metrics
                ]

            # Add comparison data
            comparison = self.compare_portfolios()
            if comparison:
                export_data["portfolio_comparison"] = comparison

            with open(export_path, "w") as f:
                json.dump(export_data, f, indent=2, default=str)

            print(f"Metrics exported to: {export_path}")
            return str(export_path)

        except Exception as e:
            print(f"Error exporting metrics: {str(e)}")
            return ""


def main():
    """Main execution function for comprehensive quantitative analysis"""
    print("Starting Comprehensive Quantitative Analysis...")
    print("=" * 60)

    # Initialize analyzer
    analyzer = QuantitativeAnalyzer()

    # Load data
    if not analyzer.load_data():
        print("Failed to load required data files. Exiting.")
        return False

    print("\nGenerating comprehensive analysis report...")

    # Generate comprehensive report
    report = analyzer.generate_comprehensive_report()

    # Display report
    print("\n" + report)

    # Save report to file
    report_path = analyzer.save_report(report)

    # Export detailed metrics
    metrics_path = analyzer.export_metrics_to_json()

    print(f"\nAnalysis complete!")
    print(f"Report saved: {report_path}")
    print(f"Metrics exported: {metrics_path}")

    return True


if __name__ == "__main__":
    main()
