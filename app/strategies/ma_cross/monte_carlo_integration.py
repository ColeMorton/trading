"""
Monte Carlo Integration for MA Cross Strategy Pipeline

This module integrates Monte Carlo parameter robustness testing with the existing
MA Cross strategy analysis pipeline. It provides enhanced parameter validation
and strategy selection based on stability analysis.
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import polars as pl

from app.strategies.ma_cross.config.parameter_testing import ParameterTestingConfig
from app.strategies.ma_cross.tools.parameter_sensitivity import (
    analyze_parameter_sensitivity,
)
from app.strategies.monte_carlo.parameter_robustness import (
    MonteCarloConfig,
    run_parameter_robustness_analysis,
)
from app.tools.setup_logging import setup_logging


class MonteCarloEnhancedAnalyzer:
    """
    Enhanced MA Cross analyzer with Monte Carlo parameter robustness testing.

    This class extends the existing parameter sensitivity analysis with Monte Carlo
    methods to identify robust parameter combinations that perform consistently
    across different market conditions.
    """

    def __init__(
        self,
        parameter_config: ParameterTestingConfig,
        mc_config: Optional[MonteCarloConfig] = None,
        robustness_threshold: float = 0.7,
    ):
        """
        Initialize the Monte Carlo enhanced analyzer.

        Args:
            parameter_config: Standard parameter testing configuration
            mc_config: Monte Carlo configuration (uses defaults if None)
            robustness_threshold: Minimum stability score for parameter acceptance
        """
        self.parameter_config = parameter_config
        self.mc_config = mc_config or MonteCarloConfig()
        self.robustness_threshold = robustness_threshold
        self.log = None

    def run_enhanced_analysis(self) -> Dict[str, Any]:
        """
        Run enhanced parameter analysis with Monte Carlo robustness testing.

        Returns:
            Dictionary containing both standard and robustness analysis results
        """
        # Setup logging
        self.log, log_close, _, _ = setup_logging(
            module_name="ma_cross_monte_carlo", log_file="enhanced_analysis.log"
        )

        try:
            self.log("Starting Monte Carlo enhanced parameter analysis")

            # Step 1: Run standard parameter sensitivity analysis
            self.log("Phase 1: Standard parameter sensitivity analysis")
            standard_results = self._run_standard_analysis()

            if not standard_results:
                self.log("No results from standard analysis", "error")
                return {
                    "standard_results": [],
                    "robust_parameters": [],
                    "recommendations": [],
                }

            # Step 2: Filter promising parameter combinations
            self.log("Phase 2: Filtering promising parameter combinations")
            promising_params = self._filter_promising_parameters(standard_results)

            if not promising_params:
                self.log("No promising parameters found", "warning")
                return {
                    "standard_results": standard_results,
                    "robust_parameters": [],
                    "recommendations": [],
                }

            # Step 3: Run Monte Carlo robustness analysis on filtered parameters
            self.log("Phase 3: Monte Carlo robustness analysis")
            robustness_results = self._run_robustness_analysis(promising_params)

            # Step 4: Generate recommendations
            self.log("Phase 4: Generating parameter recommendations")
            recommendations = self._generate_recommendations(
                standard_results, robustness_results
            )

            # Step 5: Export comprehensive results
            self.log("Phase 5: Exporting results")
            self._export_enhanced_results(
                standard_results, robustness_results, recommendations
            )

            return {
                "standard_results": standard_results,
                "robust_parameters": robustness_results,
                "recommendations": recommendations,
                "summary": self._create_analysis_summary(
                    standard_results, robustness_results
                ),
            }

        finally:
            if log_close:
                log_close()

    def _run_standard_analysis(self) -> List[Dict[str, Any]]:
        """Run standard parameter sensitivity analysis."""
        config_dict = self.parameter_config.to_dict()

        all_results = []
        for ticker in self.parameter_config.tickers:
            self.log(f"Running standard analysis for {ticker}")

            # Update config for current ticker
            current_config = config_dict.copy()
            current_config["TICKER"] = ticker

            try:
                # Download data and run analysis (simplified version of existing pipeline)
                from app.tools.get_data import download_data

                data = download_data(ticker, current_config, self.log)
                if data is None:
                    self.log(f"No data available for {ticker}", "warning")
                    continue

                # Generate parameter combinations
                short_windows = list(range(5, self.parameter_config.windows))
                long_windows = list(
                    range(
                        self.parameter_config.windows, self.parameter_config.windows * 3
                    )
                )

                # Run parameter sensitivity analysis
                results_df = analyze_parameter_sensitivity(
                    data, short_windows, long_windows, current_config, self.log
                )

                if results_df is not None:
                    ticker_results = results_df.to_dicts()
                    all_results.extend(ticker_results)

            except Exception as e:
                self.log(f"Standard analysis failed for {ticker}: {str(e)}", "error")
                continue

        return all_results

    def _filter_promising_parameters(
        self, standard_results: List[Dict[str, Any]], top_percentage: float = 0.3
    ) -> List[Tuple[str, int, int]]:
        """
        Filter promising parameter combinations for robustness testing.

        Args:
            standard_results: Results from standard parameter analysis
            top_percentage: Percentage of top-performing combinations to test

        Returns:
            List of (ticker, short_window, long_window) tuples
        """
        if not standard_results:
            return []

        # Sort by a composite score (e.g., Sharpe ratio, return, etc.)
        def calculate_composite_score(result: Dict[str, Any]) -> float:
            sharpe = result.get("Sharpe Ratio", 0)
            total_return = result.get("Total Return [%]", 0)
            win_rate = result.get("Win Rate [%]", 0)
            max_dd = abs(result.get("Max Drawdown [%]", 100))  # Lower is better

            # Composite score with weights
            score = (
                0.4 * sharpe
                + 0.3 * (total_return / 100)
                + 0.2 * (win_rate / 100)
                - 0.1 * (max_dd / 100)
            )
            return score

        # Calculate scores and sort
        scored_results = [
            (calculate_composite_score(result), result)
            for result in standard_results
            if result.get("Ticker")
            and result.get("Short Window")
            and result.get("Long Window")
        ]

        scored_results.sort(key=lambda x: x[0], reverse=True)

        # Select top percentage
        n_select = max(1, int(len(scored_results) * top_percentage))
        selected_results = scored_results[:n_select]

        # Extract parameter combinations
        promising_params = [
            (result["Ticker"], int(result["Short Window"]), int(result["Long Window"]))
            for score, result in selected_results
        ]

        self.log(
            f"Selected {len(promising_params)} promising parameter combinations from {len(standard_results)} total"
        )

        return promising_params

    def _run_robustness_analysis(
        self, promising_params: List[Tuple[str, int, int]]
    ) -> Dict[str, List]:
        """
        Run Monte Carlo robustness analysis on promising parameters.

        Args:
            promising_params: List of (ticker, short_window, long_window) tuples

        Returns:
            Dictionary with robustness analysis results
        """
        if not promising_params:
            return {}

        # Group parameters by ticker
        ticker_params = {}
        for ticker, short, long in promising_params:
            if ticker not in ticker_params:
                ticker_params[ticker] = {"short_windows": set(), "long_windows": set()}
            ticker_params[ticker]["short_windows"].add(short)
            ticker_params[ticker]["long_windows"].add(long)

        # Convert sets to sorted lists
        for ticker in ticker_params:
            ticker_params[ticker]["short_windows"] = sorted(
                ticker_params[ticker]["short_windows"]
            )
            ticker_params[ticker]["long_windows"] = sorted(
                ticker_params[ticker]["long_windows"]
            )

        # Run robustness analysis for each ticker
        all_robustness_results = {}

        for ticker, param_ranges in ticker_params.items():
            self.log(f"Running robustness analysis for {ticker}")

            strategy_config = {
                "DIRECTION": self.parameter_config.direction,
                "USE_HOURLY": self.parameter_config.use_hourly,
                "USE_YEARS": self.parameter_config.use_years,
                "YEARS": self.parameter_config.years,
                "STRATEGY_TYPE": self.parameter_config.strategy_types[0]
                if self.parameter_config.strategy_types
                else "SMA",
            }

            try:
                ticker_results = run_parameter_robustness_analysis(
                    tickers=[ticker],
                    parameter_ranges=param_ranges,
                    strategy_config=strategy_config,
                    mc_config=self.mc_config,
                )

                all_robustness_results.update(ticker_results)

            except Exception as e:
                self.log(f"Robustness analysis failed for {ticker}: {str(e)}", "error")
                continue

        return all_robustness_results

    def _generate_recommendations(
        self,
        standard_results: List[Dict[str, Any]],
        robustness_results: Dict[str, List],
    ) -> List[Dict[str, Any]]:
        """
        Generate parameter recommendations based on both analyses.

        Args:
            standard_results: Standard parameter analysis results
            robustness_results: Monte Carlo robustness analysis results

        Returns:
            List of parameter recommendations
        """
        recommendations = []

        # Create lookup for standard results
        standard_lookup = {}
        for result in standard_results:
            key = (
                result.get("Ticker"),
                result.get("Short Window"),
                result.get("Long Window"),
            )
            standard_lookup[key] = result

        # Analyze robustness results
        for ticker, ticker_robustness in robustness_results.items():
            for robustness_result in ticker_robustness:
                short, long = robustness_result.parameter_combination

                # Find corresponding standard result
                standard_key = (ticker, short, long)
                standard_result = standard_lookup.get(standard_key, {})

                # Create recommendation
                recommendation = {
                    "Ticker": ticker,
                    "Short_Window": short,
                    "Long_Window": long,
                    # Standard metrics
                    "Standard_Sharpe": standard_result.get("Sharpe Ratio", 0),
                    "Standard_Return": standard_result.get("Total Return [%]", 0),
                    "Standard_Max_DD": standard_result.get("Max Drawdown [%]", 0),
                    # Robustness metrics
                    "Stability_Score": robustness_result.stability_score,
                    "Parameter_Robustness": robustness_result.parameter_robustness,
                    "Regime_Consistency": robustness_result.regime_consistency,
                    "Is_Stable": robustness_result.is_stable,
                    # Monte Carlo statistics
                    "MC_Mean_Sharpe": robustness_result.performance_mean.get(
                        "Sharpe Ratio", 0
                    ),
                    "MC_Sharpe_CI_Lower": robustness_result.confidence_intervals.get(
                        "Sharpe Ratio", (0, 0)
                    )[0],
                    "MC_Sharpe_CI_Upper": robustness_result.confidence_intervals.get(
                        "Sharpe Ratio", (0, 0)
                    )[1],
                    # Recommendation score (composite of performance and stability)
                    "Recommendation_Score": self._calculate_recommendation_score(
                        standard_result, robustness_result
                    ),
                    "Recommendation_Rank": "TBD",  # Will be filled after sorting
                }

                recommendations.append(recommendation)

        # Sort by recommendation score and assign ranks
        recommendations.sort(key=lambda x: x["Recommendation_Score"], reverse=True)

        for i, rec in enumerate(recommendations):
            rec["Recommendation_Rank"] = i + 1

            # Add qualitative assessment (updated for new scoring scale)
            # Note: Recommendation scores can now range up to 3.0 due to robustness enhancement
            if rec["Recommendation_Score"] > 1.5:
                rec["Assessment"] = "Highly Recommended"
            elif rec["Recommendation_Score"] > 1.0:
                rec["Assessment"] = "Recommended"
            elif rec["Recommendation_Score"] > 0.5:
                rec["Assessment"] = "Conditional"
            else:
                rec["Assessment"] = "Not Recommended"

        return recommendations

    def _calculate_recommendation_score(
        self, standard_result: Dict[str, Any], robustness_result
    ) -> float:
        """
        Calculate composite recommendation score consistent with existing strategy scoring.

        Uses the same normalization functions and weighting philosophy as the main
        strategy scoring system in stats_converter.py, with additional robustness factors.
        """
        # Import normalization functions from stats_converter
        from app.tools.stats_converter import (
            calculate_beats_bnh_normalized,
            calculate_expectancy_per_trade_normalized,
            calculate_profit_factor_normalized,
            calculate_sortino_normalized,
            calculate_total_trades_normalized,
            calculate_win_rate_normalized,
        )

        # Use the same metrics and normalization as the main strategy score
        win_rate_normalized = calculate_win_rate_normalized(
            standard_result.get("Win Rate [%]", 0),
            total_trades=standard_result.get("Total Trades", 0),
        )
        total_trades_normalized = calculate_total_trades_normalized(
            standard_result.get("Total Trades", 0)
        )
        sortino_normalized = calculate_sortino_normalized(
            standard_result.get("Sortino Ratio", 0)
        )
        profit_factor_normalized = calculate_profit_factor_normalized(
            standard_result.get("Profit Factor", 0)
        )
        expectancy_per_trade_normalized = calculate_expectancy_per_trade_normalized(
            standard_result.get("Expectancy per Trade", 0)
        )
        beats_bnh_normalized = calculate_beats_bnh_normalized(
            standard_result.get("Beats BNH [%]", 0)
        )

        # Calculate base strategy score using same formula as stats_converter.py
        base_strategy_score = (
            win_rate_normalized * 2.5  # 31.25% weight (includes confidence)
            + total_trades_normalized * 1.5  # 18.75% weight (execution feasibility)
            + sortino_normalized * 1.2  # 15.0% weight (risk-adjusted return)
            + profit_factor_normalized * 1.2  # 15.0% weight (profit sustainability)
            + expectancy_per_trade_normalized
            * 1.0  # 12.5% weight (per-trade expectation)
            + beats_bnh_normalized * 0.6  # 7.5% weight (market outperformance)
        ) / 8.0  # Same normalization as original

        # Apply confidence multiplier using same logic as stats_converter.py
        total_trades_count = standard_result.get("Total Trades", 0)
        if total_trades_count < 20:
            confidence_multiplier = 0.1 + 0.4 * (total_trades_count / 20) ** 3
        elif total_trades_count < 40:
            confidence_multiplier = 0.5 + 0.3 * ((total_trades_count - 20) / 20) ** 2
        elif total_trades_count < 50:
            confidence_multiplier = 0.8 + 0.2 * ((total_trades_count - 40) / 10)
        else:
            confidence_multiplier = 1.0

        strategy_score = base_strategy_score * confidence_multiplier

        # Add Monte Carlo robustness enhancement factor
        # This enhances the base strategy score based on parameter stability
        robustness_enhancement = (
            0.6 * robustness_result.stability_score
            + 0.3 * robustness_result.parameter_robustness  # Parameter stability weight
            + 0.1  # Robustness across conditions
            * robustness_result.regime_consistency  # Regime consistency
        )

        # Apply robustness enhancement as a multiplier (1.0 to 1.5 range)
        # This means stable parameters get up to 50% score boost
        robustness_multiplier = 1.0 + (0.5 * robustness_enhancement)

        # Final recommendation score
        final_score = strategy_score * robustness_multiplier

        # Cap at reasonable maximum (slightly higher than strategy score cap due to robustness bonus)
        return min(3.0, final_score)

    def _create_analysis_summary(
        self,
        standard_results: List[Dict[str, Any]],
        robustness_results: Dict[str, List],
    ) -> Dict[str, Any]:
        """Create summary of the analysis."""
        total_combinations = len(standard_results)
        tested_combinations = sum(
            len(results) for results in robustness_results.values()
        )
        stable_combinations = sum(
            1
            for results in robustness_results.values()
            for result in results
            if result.is_stable
        )

        return {
            "total_parameter_combinations": total_combinations,
            "tested_combinations": tested_combinations,
            "stable_combinations": stable_combinations,
            "stability_rate": stable_combinations / tested_combinations
            if tested_combinations > 0
            else 0,
            "tickers_analyzed": len(self.parameter_config.tickers),
            "monte_carlo_simulations": self.mc_config.num_simulations,
            "confidence_level": self.mc_config.confidence_level,
        }

    def _export_enhanced_results(
        self,
        standard_results: List[Dict[str, Any]],
        robustness_results: Dict[str, List],
        recommendations: List[Dict[str, Any]],
    ) -> None:
        """Export comprehensive analysis results."""
        output_dir = "csv/ma_cross/monte_carlo_enhanced"
        os.makedirs(output_dir, exist_ok=True)

        # Export recommendations
        if recommendations:
            rec_df = pl.DataFrame(recommendations)
            rec_df.write_csv(os.path.join(output_dir, "parameter_recommendations.csv"))

        # Export standard results with robustness flags
        enhanced_standard = []
        robustness_lookup = {}

        # Create robustness lookup
        for ticker, results in robustness_results.items():
            for result in results:
                short, long = result.parameter_combination
                robustness_lookup[(ticker, short, long)] = result

        # Enhance standard results
        for result in standard_results:
            enhanced_result = result.copy()
            key = (
                result.get("Ticker"),
                result.get("Short Window"),
                result.get("Long Window"),
            )

            if key in robustness_lookup:
                robustness_data = robustness_lookup[key]
                enhanced_result.update(
                    {
                        "Stability_Score": robustness_data.stability_score,
                        "Parameter_Robustness": robustness_data.parameter_robustness,
                        "Is_Stable": robustness_data.is_stable,
                        "Tested_with_MC": True,
                    }
                )
            else:
                enhanced_result.update(
                    {
                        "Stability_Score": None,
                        "Parameter_Robustness": None,
                        "Is_Stable": None,
                        "Tested_with_MC": False,
                    }
                )

            enhanced_standard.append(enhanced_result)

        if enhanced_standard:
            enhanced_df = pl.DataFrame(enhanced_standard)
            enhanced_df.write_csv(
                os.path.join(output_dir, "enhanced_parameter_analysis.csv")
            )

        self.log(f"Enhanced analysis results exported to {output_dir}")


def run_monte_carlo_enhanced_ma_cross(
    tickers: List[str],
    windows: int = 50,
    strategy_types: List[str] = ["SMA", "EMA"],
    mc_simulations: int = 1000,
    direction: str = "Long",
) -> Dict[str, Any]:
    """
    Convenience function to run Monte Carlo enhanced MA Cross analysis.

    Args:
        tickers: List of ticker symbols
        windows: Maximum window size for parameter testing
        strategy_types: List of strategy types to test
        mc_simulations: Number of Monte Carlo simulations
        direction: Trading direction ("Long" or "Short")

    Returns:
        Complete analysis results
    """
    # Create configurations
    param_config = ParameterTestingConfig(
        tickers=tickers,
        windows=windows,
        strategy_types=strategy_types,
        direction=direction,
        use_hourly=False,
        use_years=True,
        years=3,
    )

    mc_config = MonteCarloConfig(
        num_simulations=mc_simulations,
        confidence_level=0.95,
        enable_regime_analysis=True,
    )

    # Run enhanced analysis
    analyzer = MonteCarloEnhancedAnalyzer(param_config, mc_config)
    results = analyzer.run_enhanced_analysis()

    return results


if __name__ == "__main__":
    # Example usage
    results = run_monte_carlo_enhanced_ma_cross(
        tickers=["BTC-USD", "SPY"],
        windows=89,
        strategy_types=["EMA"],
        mc_simulations=1000,  # Reduced for testing
        direction="Long",
    )

    print("Monte Carlo Enhanced MA Cross Analysis Complete!")
    print(f"Analysis Summary: {results.get('summary', {})}")
