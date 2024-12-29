import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
from skfolio import PerfMeasure, RiskMeasure
from skfolio.optimization import MeanRisk
from skfolio.preprocessing import prices_to_returns as sk_prices_to_returns

def download_data(ticker: str) -> pd.DataFrame:
    """Download historical data from Yahoo Finance."""
    interval = '1d'

    try:
        data = yf.download(ticker, period="max", interval=interval)
        return data['Adj Close']
    except Exception as e:
        raise

try:
    # Download data
    start_date = '2020-01-01'
    end_date = '2024-10-25'

    # Combine data
    data = pd.concat([
        download_data('NVDA'),
        download_data('NFLX'),
        download_data('AMD'),
        download_data('AMAT'),
        download_data('AMZN'),
        download_data('MU'),
        download_data('AAPL')
    ], axis=1)
    data.columns = [
        'NVDA',
        'NFLX',
        'AMD',
        'AMAT',
        'AMZN',
        'MU',
        'AAPL'
    ]

    # Calculate returns using skfolio's preprocessing
    returns = sk_prices_to_returns(data)

    # Create and configure the optimization model
    model = MeanRisk(
        risk_measure=RiskMeasure.SEMI_VARIANCE,  # Using semi-variance for Sortino ratio
        min_weights=0.09438,  # Minimum 8% allocation
        max_weights=0.19019,   # Maximum 100% allocation
        portfolio_params=dict(
            name="Optimized Portfolio",
            performance_measure=PerfMeasure.MEAN,  # Use mean return with semi-variance risk
            risk_free_rate=0.0
        )
    )

    # Fit model and get optimal weights
    model.fit(returns)
    w = model.weights_

    # Convert weights to DataFrame for consistency with previous format
    weights_df = pd.DataFrame(w, index=data.columns, columns=['weight'])

    print("Optimal portfolio weights:")
    print(weights_df.T)

    # Calculate portfolio performance
    portfolio_returns = (returns * w).sum(axis=1)

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
        asset_weight = weights_df.loc[asset, 'weight']
        asset_annualized_return = asset_return.mean() * 252
        asset_annualized_volatility = asset_return.std() * np.sqrt(252)
        asset_sharpe_ratio = asset_annualized_return / asset_annualized_volatility if asset_annualized_volatility != 0 else 0
        
        print(f"\n{asset} Metrics:")
        print(f"Weight: {asset_weight:.2%}")
        print(f"Annualized Return: {asset_annualized_return:.2%}")
        print(f"Annualized Volatility: {asset_annualized_volatility:.2%}")
        print(f"Sharpe Ratio: {asset_sharpe_ratio:.2f}")

    # Create portfolio object for visualization
    portfolio = model.predict(returns)
    
    # Plot portfolio composition
    fig = portfolio.plot_composition()
    plt.show()

except Exception as e:
    print(f"An error occurred: {str(e)}")
    import sys
    print("Python version:", sys.version)
    print("Pandas version:", pd.__version__)
    print("Numpy version:", np.__version__)
