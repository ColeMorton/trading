"""
==================
Efficient Frontier
==================

This tutorial uses the :class:`~skfolio.optimization.MeanRisk` optimization to find an
ensemble of portfolios belonging to the Mean-Variance efficient frontier (pareto font).
"""

from plotly.io import show
from skfolio import PerfMeasure, RatioMeasure, RiskMeasure
from skfolio.datasets import load_sp500_dataset
from skfolio.optimization import MeanRisk
from skfolio.preprocessing import prices_to_returns
from sklearn.model_selection import train_test_split

from app.tools.setup_logging import setup_logging


def create_efficient_frontier() -> tuple[bool, str]:
    """
    Create and analyze the efficient frontier using Mean-Risk optimization.

    Returns:
        Tuple[bool, str]: Success status and message

    Raises:
        Exception: If optimization or analysis fails
    """
    log, log_close, _, _ = setup_logging("efficient_frontier", "efficient_frontier.log")

    try:
        # Load and prepare data
        log("Loading S&P 500 dataset...", "info")
        prices = load_sp500_dataset()
        X = prices_to_returns(prices)
        X_train, X_test = train_test_split(X, test_size=0.33, shuffle=False)

        # Create Mean-Variance model
        log("Creating Mean-Variance model...", "info")
        model = MeanRisk(
            risk_measure=RiskMeasure.VARIANCE,
            efficient_frontier_size=30,  # Using 30 portfolios as specified
            portfolio_params={"name": "Variance"},
        )

        # Fit model and predict
        log("Fitting model on training data...", "info")
        model.fit(X_train)
        print("\nModel Weights Shape:")
        print(model.weights_.shape)

        population_train = model.predict(X_train)
        population_test = model.predict(X_test)

        # Analysis
        log("Analyzing results...", "info")
        population_train.set_portfolio_params(tag="Train")
        population_test.set_portfolio_params(tag="Test")

        population = population_train + population_test

        # Plot efficient frontier
        fig = population.plot_measures(
            x=RiskMeasure.ANNUALIZED_STANDARD_DEVIATION,
            y=PerfMeasure.ANNUALIZED_MEAN,
            color_scale=RatioMeasure.ANNUALIZED_SHARPE_RATIO,
            hover_measures=[
                RiskMeasure.MAX_DRAWDOWN,
                RatioMeasure.ANNUALIZED_SORTINO_RATIO,
            ],
        )
        show(fig)

        # Plot portfolio compositions and explicitly show it
        composition_fig = population_train.plot_composition()
        show(composition_fig)

        # Calculate and display performance metrics
        print("\nSharpe Ratios (Test Set):")
        print(population_test.measures(measure=RatioMeasure.ANNUALIZED_SHARPE_RATIO))

        print("\nFull Portfolio Summary:")
        print(population.summary())

        log("Successfully completed efficient frontier analysis", "info")
        log_close()
        return True, "Efficient frontier analysis completed successfully"

    except Exception as e:
        error_msg = f"Error in efficient frontier analysis: {e!s}"
        log(error_msg, "error")
        log_close()
        raise Exception(error_msg)


if __name__ == "__main__":
    success, message = create_efficient_frontier()
