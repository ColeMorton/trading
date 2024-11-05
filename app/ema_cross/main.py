import argparse
from app.tools.get_data import download_data
from config import CONFIG
from app.tools.get_data import use_synthetic
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_rsi import calculate_rsi
import importlib

def main():
    parser = argparse.ArgumentParser(description="EMA Cross Strategy Analysis")
    parser.add_argument("analysis", choices=["parameter_sensitivity", "rsi", "stop_loss", "protective_stop_loss", "review"],
                        help="Type of analysis to run")
    args = parser.parse_args()

    # Prepare data
    if CONFIG['USE_SYNTHETIC']:
        data, synthetic_ticker = use_synthetic(CONFIG['TICKER_1'], CONFIG['TICKER_2'], CONFIG['USE_HOURLY_DATA'])
    else:
        data = download_data(CONFIG['TICKER_1'], CONFIG['YEARS'], CONFIG['USE_HOURLY_DATA'])
        synthetic_ticker = CONFIG['TICKER_1']

    data = calculate_mas(data, CONFIG['EMA_FAST'], CONFIG['EMA_SLOW'], CONFIG['USE_SMA'])
    
    if CONFIG['USE_RSI']:
        data = calculate_rsi(data, CONFIG['RSI_PERIOD'])

    # Run the selected analysis
    module = importlib.import_module(f"{args.analysis}")
    module.run_analysis(data, synthetic_ticker, CONFIG)

if __name__ == "__main__":
    main()
