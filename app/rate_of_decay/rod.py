import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def calculate_equity_curve(initial_equity, risk_percentage, num_losses):
    """
    Calculate the equity curve after a series of consecutive losses.

    :param initial_equity: Initial equity
    :param risk_percentage: Fixed risk percentage per trade
    :param num_losses: Number of consecutive losses
    :return: Array of equity values
    """
    risk = risk_percentage / 100
    equity = np.zeros(num_losses + 1)
    equity[0] = initial_equity

    for i in range(1, num_losses + 1):
        equity[i] = equity[i - 1] * (1 - risk)

    return equity


def calculate_rate_of_decay(risk_percentage):
    """
    Calculate the rate of decay based on the risk percentage.

    :param risk_percentage: Fixed risk percentage per trade
    :return: Rate of decay
    """
    risk = risk_percentage / 100
    return np.log(1 - risk)


def model_loss_streaks(
    initial_equity,
    risk_percentage,
    max_streak_length,
    loss_probability,
):
    """
    Model loss streaks based on the given parameters.

    :param initial_equity: Initial equity
    :param risk_percentage: Fixed risk percentage per trade
    :param max_streak_length: Maximum streak length to model
    :param loss_probability: Probability of a loss on each trade
    :return: DataFrame with streak lengths and their probabilities
    """
    streak_lengths = np.arange(1, max_streak_length + 1)
    streak_probabilities = loss_probability**streak_lengths * (1 - loss_probability)
    equity_values = calculate_equity_curve(
        initial_equity,
        risk_percentage,
        max_streak_length,
    )

    return pd.DataFrame(
        {
            "Streak Length": streak_lengths,
            "Probability": streak_probabilities,
            "Equity": equity_values[1:],
        },
    )


def plot_rod_model(streak_data, rate_of_decay, output_path):
    """
    Plot the Rate of Decay model results and save to a file.

    :param streak_data: DataFrame with streak data
    :param rate_of_decay: Calculated rate of decay
    :param output_path: Path to save the plot
    """
    _fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

    ax1.plot(streak_data["Streak Length"], streak_data["Equity"])
    ax1.set_title("Equity Curve During Loss Streak")
    ax1.set_xlabel("Consecutive Losses")
    ax1.set_ylabel("Equity")

    ax2.bar(streak_data["Streak Length"], streak_data["Probability"])
    ax2.set_title("Probability of Loss Streaks")
    ax2.set_xlabel("Streak Length")
    ax2.set_ylabel("Probability")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    print(f"Rate of Decay: {rate_of_decay:.4f}")
    print(f"Plot saved to: {output_path}")


def main():
    # Load trade data
    trade_data = pd.read_csv("data/raw/monte_carlo/BTC-USD_trade_data_ema_cross.csv")

    # Calculate win rate and average risk per trade
    win_rate = (trade_data["Return (%)"] > 0).mean()
    avg_risk = abs(trade_data["Return (%)"][trade_data["Return (%)"] < 0].mean())

    # Model parameters
    initial_equity = 10000
    risk_percentage = avg_risk * 100  # Convert to percentage
    max_streak_length = 20
    loss_probability = 1 - win_rate

    # Calculate rate of decay
    rate_of_decay = calculate_rate_of_decay(risk_percentage)

    # Model loss streaks
    streak_data = model_loss_streaks(
        initial_equity,
        risk_percentage,
        max_streak_length,
        loss_probability,
    )

    # Create output directory if it doesn't exist
    output_dir = "images/rate_of_decay"
    os.makedirs(output_dir, exist_ok=True)

    # Plot results and save to file
    output_path = os.path.join(output_dir, "rod_model_plot.png")
    plot_rod_model(streak_data, rate_of_decay, output_path)


if __name__ == "__main__":
    main()
