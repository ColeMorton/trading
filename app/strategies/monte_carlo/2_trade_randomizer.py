import json
import logging
import os
from typing import List

import matplotlib.pyplot as plt
import polars as pl

TICKER = "BTC-USD"
NUM_PERMUTATIONS = 1000

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def load_trade_data(file_path: str) -> pl.DataFrame:
    """
    Load trade data from a CSV file into a polars DataFrame.
    """
    try:
        logging.info(f"Loading trade data from {file_path}")
        return pl.read_csv(file_path)
    except Exception as e:
        logging.error(f"Error loading trade data: {str(e)}")
        raise


def shuffle_trades(trades: pl.DataFrame) -> pl.DataFrame:
    """
    Shuffle the trades randomly.
    """
    return trades.sample(fraction=1, shuffle=True)


def get_random_permutations(
    trades: pl.DataFrame, num_permutations: int
) -> List[pl.DataFrame]:
    """
    Generate a list of randomly shuffled trade permutations.
    """
    logging.info(f"Generating {num_permutations} random permutations")
    return [shuffle_trades(trades) for _ in range(num_permutations)]


def calculate_cumulative_returns(trades: pl.DataFrame) -> List[float]:
    """
    Calculate cumulative returns for a series of trades.
    """
    returns = trades["Return (%)"].to_list()
    cumulative_returns = [1]
    for r in returns:
        cumulative_returns.append(cumulative_returns[-1] * (1 + r / 100))
    return cumulative_returns


def plot_permutations(permutations: List[pl.DataFrame], original_trades: pl.DataFrame):
    """
    Plot the cumulative returns of all permutations and the original trade sequence.
    """
    plt.figure(figsize=(12, 6))

    # Plot permutations
    for perm in permutations[:1000]:  # Limit to 1000 permutations for clarity
        cumulative_returns = calculate_cumulative_returns(perm)
        plt.plot(cumulative_returns, color="gray", alpha=0.1)

    # Plot original trade sequence
    original_cumulative_returns = calculate_cumulative_returns(original_trades)
    plt.plot(
        original_cumulative_returns,
        color="blue",
        linewidth=2,
        label="Original Sequence",
    )

    plt.title(f"{TICKER} Trade Permutations")
    plt.xlabel("Trade Number")
    plt.ylabel("Cumulative Return")
    plt.legend()

    # Save the plot
    plot_filename = (
        f"png/monte_carlo/permutations/{TICKER}_monte_carlo_permutations.png"
    )
    plt.savefig(plot_filename)
    logging.info(f"Plot saved as {plot_filename}")


def main():
    try:
        # Load the trade data
        data = pl.read_csv(f"csv/monte_carlo/{TICKER}_trade_data_ema_cross.csv")

        # Generate random permutations
        permutations = get_random_permutations(data, NUM_PERMUTATIONS)

        # Create the JSON structure
        json_data = {
            "ticker": TICKER,
            "num_permutations": NUM_PERMUTATIONS,
            "permutations": [],
        }

        # Convert permutations to JSON-compatible format
        for perm in permutations:
            json_data["permutations"].append(perm.to_dict(as_series=False))

        # Create 'json/' directory if it doesn't exist
        json_dir = "json/"
        os.makedirs(json_dir, exist_ok=True)

        # Export the data to a JSON file in the 'json/' directory
        json_filename = os.path.join(
            json_dir, f"monte_carlo/{TICKER}_ema_cross_permutations.json"
        )
        with open(json_filename, "w") as json_file:
            json.dump(json_data, json_file)

        print(f"Exported trade data to {json_filename}")

        # Plot the permutations
        plot_permutations(permutations, data)

        logging.info("Trade randomization and plotting completed successfully")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
