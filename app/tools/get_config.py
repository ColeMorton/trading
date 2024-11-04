def get_config(config: dict) -> dict:
    if config.get('USE_SYNTHETIC', False) == True:
        config["TICKER"] = f"{config['TICKER_1']}{config['TICKER_2']}"

    if not config.get('BASE_DIR'):
        config["BASE_DIR"] = 'C:/Projects/trading'

    if not config.get('PERIOD') and config.get('USE_YEARS', False) == False:
        config["PERIOD"] = 'max'

    return config
