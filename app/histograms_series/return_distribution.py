import json
from typing import NotRequired, TypedDict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import norm, percentileofscore

from app.tools.download_data import download_data
from app.tools.setup_logging import setup_logging

TICKER = "PENDLE-USD"
INCLUDE_OPTION_STRATEGY = False

# 09-05-25 @ 100000 SOL-USD
# DELTA = 0.39
# DAYS_TO_EXPIRY = 9
# STRIKE_DISTANCE = 4.86 # Percentage
# Option Strategy Analysis:
# Strike Distance: +8.00%
# Days to Expiry: 16
# Historical Probability of Exceeding Strike: 31.30%
# Market-Implied Probability (Delta): 32.00%
# Difference: 0.70%

# 09-05-25 @ 100000 BTC-USD
DELTA = 0.26
DAYS_TO_EXPIRY = 16
STRIKE_DISTANCE = 7  # Percentage
# Option Strategy Analysis:
# Strike Distance: +8.00%
# Days to Expiry: 16
# Historical Probability of Exceeding Strike: 31.30%
# Market-Implied Probability (Delta): 32.00%
# Difference: 0.70%

# 30-05-25 @ 106000 BTC-USD
# DELTA = 0.14
# DAYS_TO_EXPIRY = 38
# STRIKE_DISTANCE = 21.11 # Percentage
# Option Strategy Analysis:
# Strike Distance: +21.11%
# Days to Expiry: 38
# Historical Probability of Exceeding Strike: 26.46%
# Market-Implied Probability (Delta): 14.00%
# Difference: -12.46%

log, log_close, _, _ = setup_logging(
    module_name="return_distribution", log_file="return_distribution.log"
)


class DataConfig(TypedDict):
    """Configuration type definition.

    Required Fields:
        PERIOD (str): Data period

    Optional Fields:
        USE_YEARS (NotRequired[bool]): Use years
        YEARS (NotRequired[int]): Number of years
        USE_CURRENT (NotRequired[bool]): Use current
    """

    PERIOD: str
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[int]
    USE_CURRENT: NotRequired[bool]


def load_config(file_path="config.json"):
    """Load configuration settings from a JSON file."""
    log(f"Loading configuration from file: {file_path}")
    with open(file_path, "r") as file:
        config = json.load(file)
    log("Configuration loaded successfully.")
    return config


def fetch_data(ticker: str) -> pd.DataFrame:
    """Fetch historical price data for a given ticker."""
    log(f"Fetching data for ticker: {ticker}")
    data_config: DataConfig = {
        "PERIOD": "max",
    }
    df = download_data(ticker, data_config, log)
    data = df.to_pandas()
    data.set_index("Date", inplace=True)
    if data.empty:
        log("No data fetched for the given asset and date range.", "error")
        raise ValueError("No data fetched for the given asset and date range.")
    log("Data fetched successfully.")
    return data


def calculate_returns(data, timeframe):
    """Calculate returns based on the specified timeframe."""
    log(f"Calculating returns for timeframe: {timeframe}")
    data.loc[:, "Return"] = data.Close.pct_change()
    if timeframe == "D":
        returns = data["Return"].dropna()
    elif timeframe == "3D":
        returns = data["Return"].resample("3D").sum().dropna()
    elif timeframe == "W":
        returns = data["Return"].resample("W-MON").sum().dropna()
    elif timeframe == "2W":
        returns = data["Return"].resample("2W-MON").sum().dropna()
    else:
        log(f"Invalid timeframe specified: {timeframe}", "error")
        raise ValueError("Invalid timeframe specified. Use 'D', '3D', 'W', or '2W'.")
    if returns.empty:
        log("No valid returns calculated. Try increasing the date range.", "error")
        raise ValueError("No valid returns calculated. Try increasing the date range.")
    log("Returns calculated successfully.")
    return returns


def calculate_custom_period_returns(data, days):
    """
    Calculate returns for a custom period of days.

    Args:
        data (pd.DataFrame): Price data with Close prices
        days (int): Number of days for the return calculation

    Returns:
        pd.Series: Series of returns for the specified period
    """
    log(f"Calculating returns for custom period: {days} days")
    data_copy = data.copy()
    data_copy.loc[:, "Return"] = data_copy.Close.pct_change()

    # For crypto which trades 7 days a week
    if "-USD" in TICKER:
        returns = data_copy["Return"].rolling(window=days).sum().dropna()
    # For stocks which trade 5 days a week
    else:
        # Approximate trading days
        trading_days = int(days * 5 / 7)
        returns = data_copy["Return"].rolling(window=trading_days).sum().dropna()

    if returns.empty:
        log("No valid returns calculated for custom period.", "error")
        raise ValueError(f"No valid returns calculated for {days}-day period.")

    log(f"Custom {days}-day returns calculated successfully.")
    return returns


def calculate_var(returns):
    """Calculate Value at Risk (VaR)"""
    log("Calculating VaR for returns.")
    var_95 = np.percentile(returns, 5)
    var_99 = np.percentile(returns, 1)
    log("VaR calculated successfully.")
    return var_95, var_99


def compare_probabilities(returns, strike_return, delta):
    """
    Compare historical probability with market-implied probability.

    Args:
        returns (pd.Series): Series of returns
        strike_return (float): Return percentage for the strike price
        delta (float): Option delta representing market-implied probability

    Returns:
        tuple: (historical_probability, market_implied_probability, difference)
    """
    log(f"Comparing probabilities for strike return: {strike_return:.2%}")

    # Calculate historical probability of exceeding the strike return
    historical_probability = 100 - percentileofscore(returns, strike_return)

    # Market-implied probability from delta
    market_implied_probability = delta * 100

    # Calculate difference
    difference = market_implied_probability - historical_probability

    log(
        f"Historical probability: {
    historical_probability:.2f}%, Market-implied: {
        market_implied_probability:.2f}%"
    )
    return historical_probability, market_implied_probability, difference


def plot_return_distribution(
    returns, var_95, var_99, ticker, timeframe, ax, current_return, strike_analysis=None
):
    """
    Plot the return distribution with VaR lines and additional statistics.

    Args:
        returns (pd.Series): Series of returns
        var_95 (float): 95% Value at Risk
        var_99 (float): 99% Value at Risk
        ticker (str): Ticker symbol
        timeframe (str): Timeframe of the returns
        ax (matplotlib.axes): Axes to plot on
        current_return (float): Current return
        strike_analysis (tuple, optional): Tuple containing (strike_return, historical_prob,
                                          market_prob, difference)
    """
    log(f"Plotting return distribution for ticker: {ticker}, timeframe: {timeframe}")
    # Calculate additional statistics
    mean = np.mean(returns)
    median = np.median(returns)
    std_dev = returns.std()
    std_pos = mean + std_dev / 2
    std_neg = mean - std_dev / 2
    skewness = returns.skew()
    kurtosis = returns.kurtosis()

    sns.histplot(returns, bins=50, kde=True, ax=ax, alpha=0.2)
    ax.axvline(
        x=std_pos,
        color="blue",
        linestyle=":",
        linewidth=2,
        label=f"+1 Std Dev = {std_pos:.2%}",
    )
    ax.axvline(
        x=std_neg,
        color="blue",
        linestyle=":",
        linewidth=2,
        label=f"-1 Std Dev = {std_neg:.2%}",
    )
    ax.axvline(
        x=var_95,
        color="red",
        linestyle="--",
        linewidth=1,
        label=f"95% VaR = {var_95:.2%}",
    )
    ax.axvline(
        x=var_99,
        color="red",
        linestyle="--",
        linewidth=1,
        label=f"99% VaR = {var_99:.2%}",
    )
    ax.axvline(
        x=mean, color="green", linestyle="-", linewidth=1, label=f"Mean = {mean:.2%}"
    )
    ax.axvline(
        x=median,
        color="orange",
        linestyle="-.",
        linewidth=1,
        label=f"Median = {median:.2%}",
    )
    ax.axvline(0, color="k", linestyle="-", linewidth=1, label="Zero")

    # Calculate Rarity based on the sign of the current return
    # current_return = returns.iloc[-1]  # Use .iloc[-1] instead of [-1]
    if current_return < 0:
        negative_returns = returns[returns < 0]
        rarity = norm.cdf(
            current_return,
            loc=np.mean(negative_returns),
            scale=np.std(negative_returns),
        )
    else:
        positive_returns = returns[returns > 0]
        rarity = norm.cdf(
            current_return,
            loc=np.mean(positive_returns),
            scale=np.std(positive_returns),
        )
    rarity_percentage = (1 - rarity) * 100  # Convert to percentage

    # Calculate Rarity based on the sign of the current return
    if current_return < 0:
        negative_returns = returns[returns < 0]
        percentile = percentileofscore(negative_returns, current_return, kind="rank")
    else:
        positive_returns = returns[returns > 0]
        percentile = percentileofscore(positive_returns, current_return, kind="rank")

    ax.axvline(
        x=current_return,
        color="purple",
        linestyle="--",
        linewidth=2,
        label=f"Current Return = {current_return:.2%}",
    )

    # Add strike analysis if provided
    if strike_analysis is not None:
        strike_return, historical_prob, market_prob, difference = strike_analysis

        # Add strike line
        ax.axvline(
            x=strike_return,
            color="magenta",
            linestyle="--",
            linewidth=2,
            label=f"Strike (+{
    strike_return*
    100:.2f}%): {
        historical_prob:.2f}% hist vs {
            market_prob:.2f}% implied",
        )

        # Add comparison text
        risk_assessment = (
            "Market overpricing risk" if difference > 0 else "Market underpricing risk"
        )

        # Calculate additional metrics
        expected_return = np.mean(returns)
        probability_above_zero = 100 - percentileofscore(returns, 0)
        max_profit_probability = 100 - historical_prob

        # Add text box with metrics
        ax.text(
            0.99,
            0.80,
            f"Market-Historical Diff: {difference:.2f}%\n"
            + f"{risk_assessment}\n"
            + f"Expected Return: {expected_return:.2%}\n"
            + f"Prob. of Positive Return: {probability_above_zero:.2f}%\n"
            + f"Prob. of Max Profit: {max_profit_probability:.2f}%",
            transform=ax.transAxes,
            verticalalignment="top",
            horizontalalignment="right",
            fontsize=8,
            bbox=dict(facecolor="white", alpha=0.7),
        )

    ax.text(
        0.99,
        0.99,
        f"Std Dev: {
    std_dev:.2%}\nSkewness: {
        skewness:.2f}\nKurtosis: {
            kurtosis:.2f}\nRarity: {
                rarity_percentage:.2f}\nPercentile: {
                    percentile:.2f}%",
        transform=ax.transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        fontsize=8,
    )

    ax.set_title(f"{timeframe} Return Distribution", fontsize=10)
    ax.set_xlabel(f"{timeframe} Return", fontsize=8)
    ax.set_ylabel("Frequency", fontsize=8)
    ax.legend(fontsize=6)
    ax.grid(True)
    log("Return distribution plotted successfully.")


def main():
    """Main function to execute the return distribution analysis."""
    log("Starting return distribution analysis.")

    # Fetch asset price data
    data = fetch_data(TICKER)

    # Determine plot layout based on whether option strategy is included
    if INCLUDE_OPTION_STRATEGY:
        log("Including option strategy analysis.")
        fig, axs = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(
            f"{TICKER} Return Distributions with Option Strategy Analysis", fontsize=16
        )
    else:
        fig, axs = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f"{TICKER} Return Distributions", fontsize=16)

    # Calculate returns and plot for each timeframe
    timeframes = ["2W", "W", "3D", "D"]
    for i, (timeframe, ax) in enumerate(zip(timeframes, axs.flatten())):
        # Get the last adjusted close price and the one before the resampled period
        current_close = data.Close.iloc[-1]

        # Standard trading days logic
        if timeframe == "3D":
            previous_close = data.Close.iloc[
                -4
            ]  # 3 days before (plus 1 to account for pct_change offset)

        # Check if the ticker contains "-USD"
        if "-USD" in TICKER:
            # Use 7 trading days for W and 14 trading days for 2W
            if timeframe == "W":
                previous_close = data.Close.iloc[-8]  # 7 trading days ago
            elif timeframe == "2W":
                previous_close = data.Close.iloc[-15]  # 14 trading days ago
        else:
            if timeframe == "W":
                previous_close = data.Close.iloc[-6]  # 5 trading days ago
            elif timeframe == "2W":
                previous_close = data.Close.iloc[-11]  # 10 trading days ago

        # Calculate the current return
        current_return = (current_close - previous_close) / previous_close

        returns = calculate_returns(data, timeframe)
        var_95, var_99 = calculate_var(returns)
        plot_return_distribution(
            returns, var_95, var_99, TICKER, timeframe, ax, current_return
        )

    # Add option strategy analysis if enabled
    if INCLUDE_OPTION_STRATEGY:
        # Calculate strike return
        strike_return = STRIKE_DISTANCE / 100

        # Add custom timeframe for days to expiry
        custom_ax = axs.flatten()[4]
        custom_timeframe = f"{DAYS_TO_EXPIRY}D"

        # Calculate custom period returns
        custom_returns = calculate_custom_period_returns(data, DAYS_TO_EXPIRY)

        # Calculate VaR for custom period
        custom_var_95, custom_var_99 = calculate_var(custom_returns)

        # Calculate current return for custom period
        if "-USD" in TICKER:
            previous_close = data.Close.iloc[-DAYS_TO_EXPIRY - 1]
        else:
            # Approximate trading days
            trading_days = int(DAYS_TO_EXPIRY * 5 / 7)
            previous_close = data.Close.iloc[-trading_days - 1]

        current_close = data.Close.iloc[-1]
        custom_current_return = (current_close - previous_close) / previous_close

        # Compare probabilities
        historical_prob, market_prob, difference = compare_probabilities(
            custom_returns, strike_return, DELTA
        )

        # Plot custom period with strike analysis
        plot_return_distribution(
            custom_returns,
            custom_var_95,
            custom_var_99,
            TICKER,
            custom_timeframe,
            custom_ax,
            custom_current_return,
            strike_analysis=(strike_return, historical_prob, market_prob, difference),
        )

        # Add summary in the last subplot
        summary_ax = axs.flatten()[5]
        summary_ax.axis("off")
        summary_ax.text(
            0.5,
            0.95,
            "Option Strategy Summary",
            ha="center",
            va="top",
            fontsize=14,
            fontweight="bold",
        )

        # Create a summary table
        table_data = [
            ["Parameter", "Value"],
            ["Ticker", TICKER],
            ["Days to Expiry", str(DAYS_TO_EXPIRY)],
            ["Strike Distance", f"+{STRIKE_DISTANCE:.2f}%"],
            ["Option Delta", str(DELTA)],
            ["Historical Probability", f"{historical_prob:.2f}%"],
            ["Market-Implied Probability", f"{market_prob:.2f}%"],
            ["Probability Difference", f"{difference:.2f}%"],
            [
                "Risk Assessment",
                (
                    "Market overpricing risk"
                    if difference > 0
                    else "Market underpricing risk"
                ),
            ],
            ["Expected Return", f"{np.mean(custom_returns):.2%}"],
            ["Max Profit Probability", f"{100-historical_prob:.2f}%"],
        ]

        table = summary_ax.table(cellText=table_data, loc="center", cellLoc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)

        # Print option strategy diagnostic information
        print("\nOption Strategy Analysis:")
        print(f"Strike Distance: +{STRIKE_DISTANCE:.2f}%")
        print(f"Days to Expiry: {DAYS_TO_EXPIRY}")
        print(f"Historical Probability of Exceeding Strike: {historical_prob:.2f}%")
        print(f"Market-Implied Probability (Delta): {market_prob:.2f}%")
        print(f"Difference: {difference:.2f}%")

    plt.tight_layout()
    plt.show()

    # Print some diagnostic information
    print(f"\nTotal days of data: {len(data)}")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")
    log("Return distribution analysis completed.")
    log_close()


if __name__ == "__main__":
    main()
