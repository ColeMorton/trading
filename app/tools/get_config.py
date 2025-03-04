def get_config(config: dict) -> dict:
    if config.get('USE_SYNTHETIC', False) == True:
        config["TICKER"] = f"{config['TICKER_1']}_{config['TICKER_2']}"

    if not config.get('BASE_DIR'):
        config["BASE_DIR"] = '.'

    if not config.get('PERIOD') and config.get('USE_YEARS', False) == False:
        config["PERIOD"] = 'max'

    if not config.get('RSI_WINDOW'):
        config["RSI_WINDOW"] = 14

    if not config.get('SHORT'):
        config["SHORT"] = False

    return config
