from flask import Flask, render_template, jsonify, request
import yfinance as yf
import pandas as pd
import socket
from datetime import datetime, timedelta
import subprocess
import json
import sys

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ticker-history', methods=['POST'])
def get_ticker_history():
    try:
        data = request.get_json()
        ticker = data.get('ticker', 'BTC-USD')
        
        # Use subprocess to bypass any caching issues
        fetch_script = f"""
import yfinance as yf
import json
import sys

ticker = yf.Ticker("{ticker}")
history = ticker.history(period="max")

if history.empty:
    # Try shorter periods
    for period in ["10y", "5y", "2y", "1y", "6mo", "3mo", "1mo"]:
        history = ticker.history(period=period)
        if not history.empty:
            break

if not history.empty:
    data = []
    for date, row in history.iterrows():
        data.append({{
            'date': str(date).split()[0],
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Close']),
            'volume': int(row['Volume'])
        }})
    print(json.dumps({{'success': True, 'data': data}}))
else:
    print(json.dumps({{'success': False, 'error': 'No data found'}}))
"""
        
        # Run the script in a subprocess
        result = subprocess.run(
            [sys.executable, '-c', fetch_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                if output['success']:
                    return jsonify({
                        'success': True,
                        'data': output['data'],
                        'ticker': ticker,
                        'count': len(output['data'])
                    })
                else:
                    raise ValueError("No data returned from yfinance")
            except json.JSONDecodeError:
                print(f"Invalid JSON output: {result.stdout}")
                raise ValueError("Failed to parse data")
        else:
            print(f"Subprocess error: {result.stderr}")
            raise ValueError(f"Failed to fetch data: {result.stderr}")
            
    except Exception as e:
        print(f"Error fetching {ticker}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

def find_available_port(start_port=5000, max_attempts=100):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"Could not find available port in range {start_port}-{start_port + max_attempts}")

if __name__ == '__main__':
    port = find_available_port()
    print(f"Starting server on port {port}")
    app.run(debug=True, port=port)