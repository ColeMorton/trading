from app.ema_cross.tools.parameter_sensitivity import analyze_parameter_sensitivity
from app.tools.get_data import get_data
from app.tools.setup_logging import setup_logging

if __name__ == "__main__":
    # Setup logging
    log_dir = "logs/macd"
    log, log_close, _, _ = setup_logging('macd', log_dir, 'macd_cross.log')

    try:
        config = {
            "USE_SMA": True,
            "TICKER": 'BTC-USD',
            "WINDOWS": 89
        }

        # Get data
        data = get_data(config["TICKER"], config)
        if data is None:
            log("Failed to get data", "error")
            log_close()
            exit(1)

        # Create window ranges
        short_windows = list(range(2, config["WINDOWS"]))
        long_windows = list(range(3, config["WINDOWS"]))

        # Run parameter sensitivity analysis
        portfolios_df = analyze_parameter_sensitivity(data, short_windows, long_windows, config)
        
        if portfolios_df is None:
            log("Parameter sensitivity analysis failed", "error")
        else:
            log("Analysis completed successfully")

        log_close()
        
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise
