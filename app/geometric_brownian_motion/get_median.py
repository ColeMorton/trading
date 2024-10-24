import polars as pl

def get_median(config: dict) -> pl.DataFrame:
    # Read the CSV file
    df = pl.read_csv(f"csv/geometric_brownian_motion/{config['TICKER_1']}_gbm_extracted_simulations.csv")
    
    # Select and rename columns
    df = df.select([
        pl.col("timestamp").alias("Date"),
        pl.col("median").alias("Close")
    ])
    
    return df

if __name__ == "__main__":
    df = get_median()
    print(df)
