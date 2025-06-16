import os

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from scipy import stats

TICKER = "BTC-USD"
BASE_DIR = "/Users/colemorton/Projects/trading"


def visualize_performance(csv_file):
    # Load the performance data
    df = pl.read_csv(csv_file)

    # Print basic statistics of the final portfolio value
    final_portfolio_values = df["final_portfolio_value"].to_numpy()
    print("Final Portfolio Value Statistics:")
    print(f"Mean: {np.mean(final_portfolio_values)}")
    print(f"Median: {np.median(final_portfolio_values)}")
    print(f"Min: {np.min(final_portfolio_values)}")
    print(f"Max: {np.max(final_portfolio_values)}")
    print(f"Standard Deviation: {np.std(final_portfolio_values)}")

    # Visualize the distribution of maximum drawdowns
    plt.figure(figsize=(10, 6))
    plt.hist(df["max_drawdown"].to_numpy(), bins=50, edgecolor="black")
    plt.title("Distribution of Maximum Drawdowns")
    plt.xlabel("Maximum Drawdown")
    plt.ylabel("Frequency")
    plt.savefig(
        os.path.join(
            BASE_DIR, f"png/monte_carlo/max_drawdown_distribution/{TICKER}.png"
        )
    )
    plt.close()

    # Visualize the cumulative distribution of returns
    plt.figure(figsize=(10, 6))
    returns = df["cumulative_return"].sort()
    cumulative = np.arange(1, len(returns) + 1) / len(returns)
    plt.plot(returns, cumulative)
    plt.title("Cumulative Distribution of Returns")
    plt.xlabel("Cumulative Return")
    plt.ylabel("Cumulative Probability")
    plt.savefig(
        os.path.join(
            BASE_DIR, f"png/monte_carlo/returns_cumulative_distribution/{TICKER}.png"
        )
    )
    plt.close()

    # Visualize the distribution of Sharpe ratios
    plt.figure(figsize=(10, 6))
    plt.hist(df["sharpe_ratio"].to_numpy(), bins=50, edgecolor="black")
    plt.title("Distribution of Sharpe Ratios")
    plt.xlabel("Sharpe Ratio")
    plt.ylabel("Frequency")
    plt.savefig(
        os.path.join(
            BASE_DIR, f"png/monte_carlo/sharpe_ratio_distribution/{TICKER}.png"
        )
    )
    plt.close()

    # Visualize the distribution of final portfolio values
    plt.figure(figsize=(12, 6))

    # Calculate the kernel density estimation
    kde = stats.gaussian_kde(final_portfolio_values)
    x_range = np.linspace(
        min(final_portfolio_values), max(final_portfolio_values), 1000
    )
    kde_values = kde(x_range)

    # Plot histogram
    plt.hist(
        final_portfolio_values, bins=50, edgecolor="black", density=True, alpha=0.7
    )

    # Plot KDE
    plt.plot(x_range, kde_values, "r-", linewidth=2, label="KDE")

    plt.title("Distribution of Final Portfolio Values")
    plt.xlabel("Final Portfolio Value")
    plt.ylabel("Density")
    plt.yscale("log")  # Use log scale for y-axis

    # Format x-axis labels
    plt.gca().xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, p: format(int(x), ","))
    )

    plt.axvline(
        x=df["var_5_percent"][0],
        color="g",
        linestyle="dashed",
        linewidth=2,
        label="5% VaR",
    )
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        os.path.join(
            BASE_DIR, f"png/monte_carlo/final_portfolio_value_distribution/{TICKER}.png"
        )
    )
    plt.close()


if __name__ == "__main__":
    visualize_performance(
        os.path.join(BASE_DIR, f"csv/monte_carlo/{TICKER}_performance.csv")
    )
    print("Visualization complete. Check the output directory for the generated plots.")
