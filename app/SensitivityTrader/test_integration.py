#!/usr/bin/env python3
"""
Test script to verify SensitivityTrader MA Cross API integration
"""

import requests
import json
import time

# API endpoints
API_BASE_URL = "http://127.0.0.1:8000"
MA_CROSS_ENDPOINT = f"{API_BASE_URL}/api/ma-cross/analyze"

def test_ma_cross_integration():
    """Test the MA Cross API integration with SensitivityTrader parameters"""
    
    # Sample request matching SensitivityTrader form data
    request_data = {
        "TICKER": ["BTC-USD", "ETH-USD"],
        "WINDOWS": 89,
        "DIRECTION": "Long",
        "STRATEGY_TYPES": ["SMA", "EMA"],
        "USE_HOURLY": False,
        "USE_YEARS": False,
        "YEARS": 15,
        "USE_SYNTHETIC": False,
        "REFRESH": True,
        "MINIMUMS": {
            "WIN_RATE": 0.44,
            "TRADES": 54,
            "EXPECTANCY_PER_TRADE": 1,
            "PROFIT_FACTOR": 1,
            "SORTINO_RATIO": 0.4
        },
        "SORT_BY": "Score",
        "SORT_ASC": False,
        "USE_GBM": False,
        "async_execution": False
    }
    
    print("Testing MA Cross API Integration...")
    print(f"Request: {json.dumps(request_data, indent=2)}")
    
    try:
        # Send request
        response = requests.post(MA_CROSS_ENDPOINT, json=request_data)
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            # Synchronous execution
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"Total Portfolios Analyzed: {data.get('total_portfolios_analyzed')}")
            print(f"Total Portfolios Filtered: {data.get('total_portfolios_filtered')}")
            print(f"Execution Time: {data.get('execution_time')} seconds")
            
            # Check for portfolio exports
            if 'portfolio_exports' in data:
                exports = data['portfolio_exports']
                print("\nPortfolio Exports:")
                for export_type, paths in exports.items():
                    print(f"  {export_type}: {len(paths)} files")
                    if export_type == 'portfolios_best' and paths:
                        print(f"    Best portfolios: {paths}")
            
            # Display some results
            if 'portfolios' in data and data['portfolios']:
                print(f"\nSample Results (first 3):")
                for i, portfolio in enumerate(data['portfolios'][:3]):
                    print(f"  {i+1}. {portfolio['ticker']} - {portfolio['strategy_type']} "
                          f"({portfolio['short_window']}/{portfolio['long_window']}) "
                          f"Score: {portfolio['score']:.2f}")
                          
        elif response.status_code == 202:
            # Asynchronous execution
            data = response.json()
            execution_id = data.get('execution_id')
            print(f"Async execution started: {execution_id}")
            
            # Poll for results
            print("Polling for results...")
            max_attempts = 30
            for i in range(max_attempts):
                time.sleep(2)
                status_response = requests.get(f"{API_BASE_URL}/api/ma-cross/status/{execution_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"  Status: {status_data.get('status')} - {status_data.get('progress')}")
                    
                    if status_data.get('status') == 'completed':
                        print("Analysis completed!")
                        if 'results' in status_data:
                            print(f"  Found {len(status_data['results'])} results")
                        break
                    elif status_data.get('status') == 'failed':
                        print(f"Analysis failed: {status_data.get('error')}")
                        break
                        
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Make sure the API server is running on port 8000")
    except Exception as e:
        print(f"Error: {e}")

def test_csv_retrieval():
    """Test retrieving CSV files from the data endpoint"""
    print("\n\nTesting CSV Retrieval...")
    
    # Test path - this would come from portfolio_exports in real usage
    test_path = "csv/portfolios_best/BTC-USD_20250527_1326_D.csv"
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/data/{test_path}")
        if response.status_code == 200:
            data = response.json()
            print(f"Successfully retrieved CSV data")
            print(f"Format: {data.get('format')}")
            if 'data' in data and data['data']:
                print(f"Rows: {len(data['data'])}")
                print(f"Sample row: {data['data'][0] if data['data'] else 'No data'}")
        else:
            print(f"Could not retrieve CSV: {response.status_code}")
            
    except Exception as e:
        print(f"Error retrieving CSV: {e}")

if __name__ == "__main__":
    # Test MA Cross integration
    test_ma_cross_integration()
    
    # Test CSV retrieval
    test_csv_retrieval()
    
    print("\n\nIntegration test complete!")
    print("\nTo fully test the UI integration:")
    print("1. Start the API server: python -m app.api.run")
    print("2. Start SensitivityTrader: python app/SensitivityTrader/main.py")
    print("3. Open http://localhost:5000 in your browser")
    print("4. Enter tickers (e.g., BTC-USD, ETH-USD) and click 'Run Analysis'")
    print("5. Check for results in the table and 'Export Best' button")