import socket
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/ticker-history", methods=["POST"])
def get_ticker_history():
    try:
        data = request.get_json()
        ticker_symbol = data.get("ticker", "BTC-USD")

        print(f"\nFetching data for {ticker_symbol}...")

        # Use download function which seems more reliable
        try:
            # Download with a specific date range
            end = datetime.now()
            start = end - timedelta(days=365 * 10)  # 10 years of data

            df = yf.download(
                ticker_symbol,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                progress=False,
            )

            if df.empty:
                # Try without date range
                df = yf.download(ticker_symbol, period="max", progress=False)

        except Exception as e:
            print(f"Download error: {e}")
            df = pd.DataFrame()

        # If download failed, try Ticker object
        if df.empty:
            try:
                ticker = yf.Ticker(ticker_symbol)
                df = ticker.history(period="max")
            except Exception as e:
                print(f"Ticker error: {e}")
                df = pd.DataFrame()

        if df.empty:
            raise ValueError(f"No data found for ticker {ticker_symbol}")

        print(f"Successfully fetched {len(df)} records")

        # Convert to JSON-friendly format
        history_data = []
        for date, row in df.iterrows():
            if pd.isna(row["Close"]):
                continue

            # Convert date to string
            date_str = (
                date.strftime("%Y-%m-%d")
                if hasattr(date, "strftime")
                else str(date).split()[0]
            )

            history_data.append(
                {
                    "date": date_str,
                    "open": float(row["Open"])
                    if pd.notna(row["Open"])
                    else float(row["Close"]),
                    "high": float(row["High"])
                    if pd.notna(row["High"])
                    else float(row["Close"]),
                    "low": float(row["Low"])
                    if pd.notna(row["Low"])
                    else float(row["Close"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]) if pd.notna(row["Volume"]) else 0,
                }
            )

        # Sort by date
        history_data.sort(key=lambda x: x["date"])

        return jsonify(
            {
                "success": True,
                "data": history_data,
                "ticker": ticker_symbol,
                "count": len(history_data),
            }
        )

    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        return jsonify({"success": False, "error": error_msg}), 400


def find_available_port(start_port=5000, max_attempts=100):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    raise RuntimeError(
        f"Could not find available port in range {start_port}-{start_port + max_attempts}"
    )


if __name__ == "__main__":
    port = find_available_port()
    print(f"Starting server on port {port}")
    print("NOTE: Running without debug mode to avoid yfinance issues")
    app.run(debug=False, port=port, use_reloader=False)
