import polars as pl
import logging
from app.utils import get_path, get_filename

def parameter_sensitivity_export(portfolios: pl.DataFrame, config: dict) -> None:
    logging.info("Starting parameter sensitivity export")

    try:
        # Create DataFrame with explicit schema for numeric columns
        df = pl.DataFrame(portfolios)
        
        # Sort portfolios by Total Return [%] in descending order
        df = df.sort("Total Return [%]", descending=True)

        # Export to CSV
        csv_path = get_path("csv", "ma_cross", config, 'portfolios')
        csv_filename = get_filename("csv", config)
        df.write_csv(csv_path + "/" + csv_filename)

        print(f"Export complete. Portfolios written to {csv_path}")
        print(f"Total rows in output: {len(df)}")

        return df
        
    except Exception as e:
        logging.error(f"Failed to create DataFrame: {e}")