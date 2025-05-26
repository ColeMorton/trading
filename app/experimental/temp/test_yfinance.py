import yfinance as yf
import sys

print(f"yfinance version: {yf.__version__}")

tickers = ["AAPL", "MSFT", "GOOGL", "BTC-USD"]

for ticker_symbol in tickers:
    print(f"\nTesting {ticker_symbol}:")
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Try to get info
        try:
            info = ticker.info
            print(f"  ✓ Info available: {info.get('shortName', 'N/A')}")
        except:
            print("  ✗ Info not available")
        
        # Try to get history
        try:
            hist = ticker.history(period="1mo")
            if not hist.empty:
                print(f"  ✓ History available: {len(hist)} days")
                print(f"    Latest close: ${hist['Close'][-1]:.2f}")
            else:
                print("  ✗ History empty")
        except Exception as e:
            print(f"  ✗ History error: {e}")
            
        # Try download
        try:
            data = yf.download(ticker_symbol, period="1mo", progress=False)
            if not data.empty:
                print(f"  ✓ Download successful: {len(data)} days")
            else:
                print("  ✗ Download returned empty data")
        except Exception as e:
            print(f"  ✗ Download error: {e}")
            
    except Exception as e:
        print(f"  ✗ General error: {e}")