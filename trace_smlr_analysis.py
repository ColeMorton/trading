#!/usr/bin/env python3
"""
Trace SMLR analysis to understand why only one strategy is displayed.
"""

import asyncio
import json
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.api.services.strategy_analysis_service import StrategyAnalysisService
from app.api.models.strategy_analysis import MACrossRequest
from app.api.dependencies import get_strategy_analysis_service


async def trace_smlr_analysis():
    """Trace SMLR analysis through the pipeline."""
    print("=== Tracing SMLR Analysis ===\n")
    
    # Create a request for SMLR analysis
    request = MACrossRequest(
        ticker=["SMLR", "AMZN"],
        windows=8,
        strategy_types=["SMA", "EMA"],
        use_current=True,
        minimums={
            "trades": 10,
            "win_rate": 0.40,
            "profit_factor": 1.0
        }
    )
    
    print(f"Request configuration:")
    print(json.dumps(request.dict(), indent=2))
    print("\n")
    
    # Get the service
    service = get_strategy_analysis_service()
    
    # Execute the analysis
    print("Executing analysis...")
    response = await service.analyze_portfolio(request)
    
    print(f"\nAnalysis Results:")
    print(f"Status: {response.status}")
    print(f"Total portfolios analyzed: {response.total_portfolios_analyzed}")
    print(f"Total portfolios filtered: {response.total_portfolios_filtered}")
    print(f"Number of portfolios in response: {len(response.portfolios)}")
    
    # Group portfolios by ticker
    portfolios_by_ticker = {}
    for portfolio in response.portfolios:
        ticker = portfolio.ticker
        if ticker not in portfolios_by_ticker:
            portfolios_by_ticker[ticker] = []
        portfolios_by_ticker[ticker].append(portfolio)
    
    print(f"\nPortfolios by ticker:")
    for ticker, portfolios in portfolios_by_ticker.items():
        print(f"\n{ticker}: {len(portfolios)} portfolios")
        
        # Group by strategy type
        by_strategy = {}
        for p in portfolios:
            strategy = p.strategy_type
            if strategy not in by_strategy:
                by_strategy[strategy] = []
            by_strategy[strategy].append(p)
        
        for strategy, strat_portfolios in by_strategy.items():
            print(f"  {strategy}: {len(strat_portfolios)} portfolios")
            
            # Show first few
            for i, p in enumerate(strat_portfolios[:3]):
                print(f"    {i+1}. Windows: {p.short_window}/{p.long_window}, Score: {p.score:.4f}, Metric Type: '{p.metric_type}'")
            
            if len(strat_portfolios) > 3:
                print(f"    ... and {len(strat_portfolios) - 3} more")
    
    # Check the exported files
    print("\n\nChecking exported files...")
    if response.portfolio_exports:
        for export_type, files in response.portfolio_exports.items():
            print(f"\n{export_type}:")
            for file in files:
                if "SMLR" in file:
                    print(f"  - {file}")
                    
                    # Read and check the file
                    file_path = Path(project_root) / file
                    if file_path.exists():
                        with open(file_path, 'r') as f:
                            lines = f.readlines()
                            print(f"    Lines in file: {len(lines)}")
                            if len(lines) > 1:
                                # Check for metric types
                                header = lines[0].strip()
                                if "Metric Type" in header:
                                    print("    Has Metric Type column")
                                    # Count unique ticker/strategy combinations
                                    unique_combos = set()
                                    for line in lines[1:]:
                                        parts = line.split(',')
                                        if len(parts) > 2:
                                            ticker = parts[1]  # Assuming Ticker is second column
                                            strategy = parts[2]  # Assuming Strategy Type is third column
                                            unique_combos.add(f"{ticker}-{strategy}")
                                    print(f"    Unique ticker-strategy combinations: {len(unique_combos)}")
                                    for combo in sorted(unique_combos):
                                        print(f"      - {combo}")


if __name__ == "__main__":
    asyncio.run(trace_smlr_analysis())