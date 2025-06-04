import os
import signal
import socket
import sys
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
        ticker = data.get("ticker", "BTC-USD")

        # Import shared module to clear errors
        from yfinance import shared

        shared._ERRORS = {}

        # Create a fresh ticker object
        ticker_obj = yf.Ticker(ticker)

        # Reset any cached data (only if attributes exist)
        if hasattr(ticker_obj, "_history"):
            ticker_obj._history = None
        if hasattr(ticker_obj, "_history_metadata"):
            ticker_obj._history_metadata = None

        # Use the method that worked in debug: ticker.history()
        history = None
        error_messages = []

        try:
            # This is the method that worked in our debug test
            history = ticker_obj.history(period="1mo")
            if not history.empty:
                print(
                    f"Successfully fetched {ticker} data with period=1mo, {len(history)} records"
                )
            else:
                error_messages.append("No data returned for 1mo period")
        except Exception as e:
            error_messages.append(f"1mo period failed: {e}")

        # Fallback to different periods
        if history is None or history.empty:
            for period in ["3mo", "6mo", "1y"]:
                try:
                    history = ticker_obj.history(period=period)
                    if not history.empty:
                        print(
                            f"Successfully fetched {ticker} data with period={period}, {len(history)} records"
                        )
                        break
                    else:
                        error_messages.append(f"No data for period {period}")
                except Exception as e:
                    error_messages.append(f"Period {period} failed: {e}")

        # Last resort - try download function with auto_adjust=False to avoid format issues
        if history is None or history.empty:
            try:
                history = yf.download(
                    ticker, period="1mo", progress=False, auto_adjust=False
                )
                if not history.empty:
                    print(
                        f"Successfully fetched {ticker} using download(), {len(history)} records"
                    )
                else:
                    error_messages.append("Download returned no data")
            except Exception as e:
                error_messages.append(f"Download failed: {e}")

        if history is None or history.empty:
            # Compile all error messages for debugging
            all_errors = "; ".join(error_messages)

            # Check if there were any errors recorded in shared
            if hasattr(shared, "_ERRORS") and ticker in shared._ERRORS:
                shared_error = str(shared._ERRORS[ticker])
                raise ValueError(f"Yahoo Finance error for {ticker}: {shared_error}")
            else:
                raise ValueError(
                    f"No data found for ticker {ticker}. Errors: {all_errors}"
                )

        # Convert to JSON-friendly format
        history_data = []
        for date, row in history.iterrows():
            # Skip rows with NaN close prices
            if pd.isna(row["Close"]):
                continue

            # Handle timezone-aware datetime objects
            if hasattr(date, "tz_localize"):
                date_str = date.strftime("%Y-%m-%d")
            else:
                date_str = str(date).split()[0]  # Get just the date part

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

        # Sort by date to ensure chronological order
        history_data.sort(key=lambda x: x["date"])

        return jsonify(
            {
                "success": True,
                "data": history_data,
                "ticker": ticker,
                "count": len(history_data),
            }
        )

    except Exception as e:
        print(f"Error fetching {ticker}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400


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


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    print(f"\nReceived signal {sig}. Shutting down gracefully...")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    port = find_available_port()
    print(f"Starting server on port {port}")
    print("Press Ctrl+C to stop the server")

    try:
        app.run(debug=True, port=port, use_reloader=False)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        print("Server stopped.")
