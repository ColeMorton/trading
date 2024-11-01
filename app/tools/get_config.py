def get_config(config: dict) -> dict:
    if config.get('USE_SYNTHETIC', False) == True:
        config["TICKER"] = f"{config['TICKER_1']}{config['TICKER_2']}"

    return config

