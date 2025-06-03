import matplotlib.pyplot as plt
import polars as pl

from app.tools.get_config import get_config
from app.utils import get_filename, get_path

# Default Configuration
CONFIG = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": "max",
    "USE_HOURLY": False,
    "TICKER": "SOL-USD",
    "USE_SYNTHETIC": True,
    "TICKER_1": "BTC-USD",
    "TICKER_2": "SPY",
    "SHORT_WINDOW": 11,
    "LONG_WINDOW": 17,
    "SHORT": False,
    "USE_GBM": True,
    "USE_SMA": False,
    "BASE_DIR": ".",
    "WINDOWS": 55,
}

config = get_config(CONFIG)


def get_median(config: dict) -> pl.DataFrame:
    filename = get_filename("csv", config)
    path = get_path("csv", "geometric_brownian_motion", config, "filtered_simulations")
    fullpath = f"{path}/{filename}"

    print(f"Imported {fullpath}")

    # Read the CSV file
    df = pl.read_csv(fullpath)

    # Select and rename columns, using Date column directly
    df = df.select(
        [
            pl.col("Date").str.to_datetime().alias("Date"),
            pl.col("median").alias("Close"),
        ]
    )

    return df


if __name__ == "__main__":
    df = get_median(config)
    print(df)

    # Create the plot
    plt.figure(figsize=(12, 6))
    plt.plot(df["Date"].to_numpy(), df["Close"].to_numpy(), linewidth=2)
    plt.title(f'Median Price Path - {config["TICKER_1"]} vs {config["TICKER_2"]}')
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Display the plot
    plt.show()
