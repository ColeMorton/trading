import pandas as pd
import yfinance as yf
import riskfolio as rp
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# def download_data(ticker, start_date, end_date):
#     data = yf.download(ticker, start=start_date, end=end_date)
#     return data['Adj Close']

def download_data(ticker: str) -> pd.DataFrame:
    """Download historical data from Yahoo Finance."""
    interval = '1h'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)

    try:
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        return data['Adj Close']
    except Exception as e:
        raise

try:
    # Download data
    start_date = '2020-01-01'
    end_date = '2024-10-25'
    virtual_data = download_data('VIRTUAL-USD')
    fet_data = download_data('FET-USD')
    sol_data = download_data('SOL-USD')
    rune_data = download_data('RUNE-USD')
    stx_data = download_data('STX4847-USD')
    apt_data = download_data('APT21794-USD')
    sui_data = download_data('SUI20947-USD')
    aave_data = download_data('AAVE-USD')

    # Combine data
    data = pd.concat([virtual_data, fet_data, sol_data, rune_data, stx_data, apt_data, sui_data, aave_data], axis=1)
    data.columns = ['VIRTUAL-USD', 'FET-USD', 'SOL-USD', 'RUNE-USD', 'STX4847-USD', 'APT21794-USD', 'SUI20947-USD', 'AAVE-USD']

    # Calculate returns
    returns = data.pct_change(fill_method=None).dropna()

    # Create portfolio object
    port = rp.Portfolio(returns)

    # Set up portfolio parameters
    method_mu = 'hist'  # Method to estimate expected returns
    method_cov = 'hist'  # Method to estimate covariance matrix

    # Estimate inputs
    port.assets_stats(method_mu=method_mu, method_cov=method_cov)

    # Set up optimization parameters
    model = 'Classic'  # Could be Classic (Markowitz), BL (Black Litterman) or FM (Factor Model)
    rm = 'MV'  # Risk measure: 'MV' (Variance), 'MAD' (Mean Absolute Deviation), 'MSV' (Semi Variance), etc.
    obj = 'Utility'  # Objective function: 'MinRisk', 'MaxRet', 'Utility', 'Sharpe' (Maximize Sharpe ratio)
    hist = True  # Use historical scenarios for risk measures that depend on scenarios
    rf = 0  # Risk-free rate
    l = 3  # Risk aversion factor, only useful when obj is 'Utility'

    # Sortino Ratio
    # rm = 'MSV'  # Risk measure: 'MV' (Variance), 'MAD' (Mean Absolute Deviation), 'MSV' (Semi Variance), etc.
    # obj = 'MaxRet'  # Objective function: 'MinRisk', 'MaxRet', 'Utility', 'Sharpe' (Maximize Sharpe ratio)

    rm = 'CVaR'  # Risk measure: 'MV' (Variance), 'MAD' (Mean Absolute Deviation), 'MSV' (Semi Variance), etc.

    # Optimize portfolio
    w = port.optimization(model=model, rm=rm, obj=obj, rf=rf, l=l, hist=hist)

    print("Optimal portfolio weights:")
    print(w.T)

    # Calculate portfolio performance
    portfolio_returns = (returns * w.T.values).sum(axis=1)

    print("\nPortfolio Metrics:")
    annualized_return = portfolio_returns.mean() * 252
    annualized_volatility = portfolio_returns.std() * np.sqrt(252)
    sharpe_ratio = annualized_return / annualized_volatility if annualized_volatility != 0 else 0

    print(f"Annualized Return: {annualized_return:.2%}")
    print(f"Annualized Volatility: {annualized_volatility:.2%}")
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")

    # Calculate individual asset performance
    for asset in returns.columns:
        asset_return = returns[asset]
        asset_weight = w.T[asset].values[0]
        asset_annualized_return = asset_return.mean() * 252
        asset_annualized_volatility = asset_return.std() * np.sqrt(252)
        asset_sharpe_ratio = asset_annualized_return / asset_annualized_volatility if asset_annualized_volatility != 0 else 0
        
        print(f"\n{asset} Metrics:")
        print(f"Weight: {asset_weight:.2%}")
        print(f"Annualized Return: {asset_annualized_return:.2%}")
        print(f"Annualized Volatility: {asset_annualized_volatility:.2%}")
        print(f"Sharpe Ratio: {asset_sharpe_ratio:.2f}")

    ax = rp.plot_pie(w=w, title='Sharpe Mean Variance', others=0.05, nrow=25, cmap = "tab20", height=6, width=10, ax=None)
    plt.show()
    
except Exception as e:
    print(f"An error occurred: {str(e)}")
    import sys
    print("Python version:", sys.version)
    print("Riskfolio-Lib version:", rp.__version__)
    print("Pandas version:", pd.__version__)
    print("Numpy version:", np.__version__)
