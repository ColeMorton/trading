import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates

# Constants
TICKER = 'WST'
USE_PORTFOLIO = False
PORTFOLIO = {'BTC-USD': 0.56, 'SPY': 0.44}

def download_stock_data(ticker, period="1y"):
    if isinstance(ticker, dict):
        data = None
        for symbol, weight in ticker.items():
            ticker_data = yf.download(symbol, period=period)['Adj Close']
            weighted_data = ticker_data * weight
            if data is None:
                data = weighted_data
            else:
                data += weighted_data
        data = data.to_frame(name='Adj Close')
    else:
        data = yf.download(ticker, period=period)

    data['Daily Return'] = data['Adj Close'].pct_change()
    return data

def filter_data_by_days(data, days):
    return data.tail(days)

def calculate_score(returns, mean, std_dev):
    score = pd.Series(index=returns.index, dtype=int)
    score[returns >= mean] = 0
    score[(returns < mean) & (returns > 0)] = 1
    score[(returns <= 0) & (returns > mean - std_dev)] = 2
    score[returns <= mean - std_dev] = 3
    return score

def plot_score(data_dict, ticker):
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.suptitle(f'{ticker}')

    # Calculate scores for each period
    scores = {}
    for period, data in data_dict.items():
        returns = data['Daily Return'].dropna() * 100
        mean = returns.mean()
        std_dev = returns.std()
        scores[period] = calculate_score(returns, mean, std_dev)

    # Find the minimum score for each date across all periods
    all_scores = pd.DataFrame(scores)
    min_scores = all_scores.min(axis=1)

    # Get the last 60 days of data
    last_60_days = data_dict[60].index
    last_60_days_scores = min_scores.loc[last_60_days]

    ax.plot(last_60_days_scores.index, last_60_days_scores, label='Score', color='purple')
    ax.set_title('Score Across All Periods (Last 60 Days)')
    ax.set_xlabel('Date')
    ax.set_ylabel('Score')
    ax.set_ylim(0, 5)
    ax.set_xlim(last_60_days[0], last_60_days[-1])
    ax.legend()

    # Add light-grey vertical lines for every date
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.grid(axis='x', color='grey', linestyle='-', linewidth=0.5, alpha=1)

    # Format x-axis labels
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    plt.tight_layout()
    plt.show()

def main():
    ticker = PORTFOLIO if USE_PORTFOLIO else TICKER
    periods = [60, 30, 15]

    data = download_stock_data(ticker)
    data_dict = {days: filter_data_by_days(data, days) for days in periods}

    plot_score(data_dict, ticker if isinstance(ticker, str) else "Portfolio")

if __name__ == "__main__":
    main()