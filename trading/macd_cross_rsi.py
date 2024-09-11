import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# Constants
END_DATE = '2024-09-11'
ASSET = 'BTC-USD'
STOP_LOSS = 4.5
USE_LOG_Y = True
SHORT_PERIOD = 20
LONG_PERIOD = 34
SIGNAL_PERIOD = 13
RSI_PERIOD = 14
USE_HOURLY_DATA = True  # Set to False for daily data
LOSERS_ONLY = True  # Set to True to analyze only losing trades
WINNERS_ONLY = False  # Set to True to analyze only winning trades

class MACDCrossStrategy:
    """
    A class to implement and analyze the MACD Crossover trading strategy.
    """

    def __init__(self, asset: str, end_date: str, 
                 short_period: int, long_period: int, signal_period: int, stop_loss: float, rsi_period: int,
                 use_hourly_data: bool, losers_only: bool, winners_only: bool):
        """
        Initialize the MACDCrossStrategy with given parameters.

        :param asset: The asset symbol
        :param end_date: End date for data analysis
        :param short_period: Short period for MACD
        :param long_period: Long period for MACD
        :param signal_period: Signal period for MACD
        :param stop_loss: Stop loss percentage
        :param rsi_period: Period for RSI calculation
        :param use_hourly_data: Whether to use hourly data (True) or daily data (False)
        :param losers_only: Whether to analyze only losing trades
        :param winners_only: Whether to analyze only winning trades
        """
        self.asset = asset
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.short_period = short_period
        self.long_period = long_period
        self.signal_period = signal_period
        self.stop_loss = stop_loss
        self.rsi_period = rsi_period
        self.use_hourly_data = use_hourly_data
        self.losers_only = losers_only
        self.winners_only = winners_only
        self.data = None
        self.set_start_date()

    def set_start_date(self):
        """Set the start date based on whether hourly or daily data is used."""
        if self.use_hourly_data:
            self.start_date = self.end_date - timedelta(days=365)
        else:
            self.start_date = self.end_date - timedelta(days=365 * 10)  # 10 years for daily data

    def fetch_data(self) -> None:
        """Fetch asset price data from Yahoo Finance."""
        interval = '1h' if self.use_hourly_data else '1d'
        self.data = yf.download(self.asset, start=self.start_date, end=self.end_date, interval=interval)
        if self.data.empty:
            raise ValueError("No data fetched for the given asset and date range.")
        
        # For hourly data, we need to handle potential missing hours
        if self.use_hourly_data:
            self.data = self.data.resample('h').ffill()  # Forward fill missing hourly data

    def calculate_indicators(self) -> None:
        """Calculate MACD and RSI."""
        # Calculate MACD
        exp1 = self.data['Adj Close'].ewm(span=self.short_period, adjust=False).mean()
        exp2 = self.data['Adj Close'].ewm(span=self.long_period, adjust=False).mean()
        self.data['MACD'] = exp1 - exp2
        self.data['Signal_Line'] = self.data['MACD'].ewm(span=self.signal_period, adjust=False).mean()
        
        # Calculate RSI
        delta = self.data['Adj Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        self.data['RSI'] = 100 - (100 / (1 + rs))

    def generate_signals(self) -> None:
        """Generate trading signals based on MACD crossover and stop loss."""
        self.data['Signal'] = np.where(self.data['MACD'] > self.data['Signal_Line'], 1, 0)
        self.data['Stop_Loss'] = self.data['Adj Close'] * (1 - self.stop_loss)
        self.data['Stop_Loss'] = self.data['Stop_Loss'].where(self.data['Signal'] == 1).ffill()
        
        self.data['Position'] = 0
        mask = (self.data['Signal'] == 1) & (self.data['Adj Close'] > self.data['Stop_Loss'].shift(1))
        self.data.loc[mask, 'Position'] = 1

    def calculate_returns(self) -> None:
        """Calculate strategy returns."""
        self.data['Strategy_Return'] = self.data['Adj Close'].pct_change() * self.data['Position'].shift(1)
        self.data['Trade_Return'] = self.data['Strategy_Return']
        self.data['RSI_Open'] = self.data['RSI'].where(self.data['Position'].shift(1) == 1)

    def filter_trades(self) -> None:
        """Filter trades based on user preferences."""
        if self.losers_only:
            self.data = self.data[self.data['Trade_Return'] < 0].copy()
        elif self.winners_only:
            self.data = self.data[self.data['Trade_Return'] > 0].copy()
        self.data = self.data.dropna(subset=['RSI_Open'])

    def run_strategy(self) -> pd.DataFrame:
        """Execute the complete strategy and return the resulting DataFrame."""
        self.fetch_data()
        self.calculate_indicators()
        self.generate_signals()
        self.calculate_returns()
        self.filter_trades()
        return self.data

    @staticmethod
    def plot_rsi_distribution(data: pd.DataFrame, asset: str, short: int, long: int, signal: int, use_log_y: bool, use_hourly_data: bool, losers_only: bool, winners_only: bool) -> None:
        """
        Plot the distribution of RSI values at the time of open/long signals.

        :param data: DataFrame containing the strategy data
        :param asset: Asset symbol
        :param short: Short period for MACD
        :param long: Long period for MACD
        :param signal: Signal period for MACD
        :param use_log_y: Whether to use logarithmic scale for Y-axis
        :param use_hourly_data: Whether hourly data was used
        :param losers_only: Whether only losing trades are analyzed
        :param winners_only: Whether only winning trades are analyzed
        """
        plt.figure(figsize=(12, 8))
        sns.histplot(data['RSI_Open'], kde=True, bins=100, stat='density')
        interval = "Hourly (365 days)" if use_hourly_data else "Daily (10 years)"
        trade_type = "Losing Trades" if losers_only else "Winning Trades" if winners_only else "All Trades"
        plt.title(f'{asset} MACD ({short},{long},{signal}) Crossover Strategy RSI Distribution\n{interval}, {trade_type}', fontsize=16)
        plt.xlabel('RSI Value', fontsize=12)
        plt.ylabel('Density', fontsize=12)
        plt.grid(True, alpha=0.3)

        stats = {
            'Mean': data['RSI_Open'].mean(),
            'Median': data['RSI_Open'].median(),
            '75th Percentile': data['RSI_Open'].quantile(0.75),
            '25th Percentile': data['RSI_Open'].quantile(0.25)
        }

        colors = ['r', 'g', 'purple', 'orange']
        for (label, value), color in zip(stats.items(), colors):
            plt.axvline(value, color=color, linestyle='--', label=f'{label}: {value:.2f}')

        plt.axvline(50, color='k', linestyle='-', label='Neutral (50)')

        if use_log_y:
            plt.yscale('log')

        plt.legend(fontsize=10, loc='upper left')
        plt.tight_layout()
        plt.show()

def main():
    strategy = MACDCrossStrategy(ASSET, END_DATE, SHORT_PERIOD, LONG_PERIOD, SIGNAL_PERIOD, STOP_LOSS, RSI_PERIOD, USE_HOURLY_DATA, LOSERS_ONLY, WINNERS_ONLY)
    strategy_data = strategy.run_strategy()
    MACDCrossStrategy.plot_rsi_distribution(strategy_data, ASSET, SHORT_PERIOD, LONG_PERIOD, SIGNAL_PERIOD, USE_LOG_Y, USE_HOURLY_DATA, LOSERS_ONLY, WINNERS_ONLY)

if __name__ == "__main__":
    main()
