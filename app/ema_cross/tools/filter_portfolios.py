import polars as pl
from app.utils import get_path, get_filename

# Function to get row for metric extremes
def get_metric_rows(df, column):
    # Convert string numbers to numeric if needed
    if df[column].dtype == pl.Utf8:
        try:
            df = df.with_columns(pl.col(column).cast(pl.Float64).alias(column))
        except:
            pass  # Keep as string if conversion fails
    
    # Get the row index for max value
    max_idx = df[column].arg_max()
    max_row = df.row(max_idx)
    
    # Get the row index for min value
    min_idx = df[column].arg_min()
    min_row = df.row(min_idx)
    
    # For numeric columns, also get mean and median
    if df[column].dtype in [pl.Float64, pl.Int64] or (
        df[column].dtype == pl.Utf8 and all(str(x).replace('-', '').replace('.', '').isdigit() for x in df[column] if x is not None)
    ):
        mean_val = df[column].mean()
        # Find row closest to mean
        mean_idx = (df[column] - mean_val).abs().arg_min()
        mean_row = df.row(mean_idx)
        
        median_val = df[column].median()
        # Find row closest to median
        median_idx = (df[column] - median_val).abs().arg_min()
        median_row = df.row(median_idx)
        
        return [max_row, min_row, mean_row, median_row]
    else:
        # For non-numeric columns, only return max and min
        return [max_row, min_row]

# List of numeric metrics
numeric_metrics = [
    'Total Return [%]',
    'Total Fees Paid',
    'Max Drawdown [%]',
    'Total Trades',
    'Win Rate [%]',
    'Best Trade [%]',
    'Worst Trade [%]',
    'Avg Winning Trade [%]',
    'Avg Losing Trade [%]',
    'Profit Factor',
    'Expectancy',
    'Sharpe Ratio',
    'Calmar Ratio',
    'Omega Ratio',
    'Sortino Ratio'
]

# List of duration metrics
duration_metrics = [
    'Max Drawdown Duration',
    'Avg Winning Trade Duration',
    'Avg Losing Trade Duration'
]

def filter_portfolios(df, config):
    # Check if DataFrame is empty
    if len(df) == 0:
        print("No portfolios to filter - returning empty DataFrame")
        return df  # Return the empty DataFrame as is
        
    # Initialize result array
    result_rows = []

    # Process numeric metrics
    for metric in numeric_metrics:
        if metric in df.columns:  # Only process if metric exists in DataFrame
            rows = get_metric_rows(df, metric)
            if len(rows) == 4:  # If we got all four rows (numeric metric)
                result_rows.extend([
                    {**{'Metric Type': f'Most {metric}'}, **{col: val for col, val in zip(df.columns, rows[0])}},
                    {**{'Metric Type': f'Least {metric}'}, **{col: val for col, val in zip(df.columns, rows[1])}},
                    {**{'Metric Type': f'Mean {metric}'}, **{col: val for col, val in zip(df.columns, rows[2])}},
                    {**{'Metric Type': f'Median {metric}'}, **{col: val for col, val in zip(df.columns, rows[3])}}
                ])
            else:  # If we only got max/min rows (non-numeric metric)
                result_rows.extend([
                    {**{'Metric Type': f'Most {metric}'}, **{col: val for col, val in zip(df.columns, rows[0])}},
                    {**{'Metric Type': f'Least {metric}'}, **{col: val for col, val in zip(df.columns, rows[1])}}
                ])

    # Process duration metrics
    for metric in duration_metrics:
        if metric in df.columns:  # Only process if metric exists in DataFrame
            rows = get_metric_rows(df, metric)
            result_rows.extend([
                {**{'Metric Type': f'Most {metric}'}, **{col: val for col, val in zip(df.columns, rows[0])}},
                {**{'Metric Type': f'Least {metric}'}, **{col: val for col, val in zip(df.columns, rows[1])}}
            ])

    # If no results were generated, return empty DataFrame
    if not result_rows:
        print("No results generated - returning empty DataFrame")
        return pl.DataFrame()

    # Convert results to DataFrame
    result_df = pl.DataFrame(result_rows)

    # Sort portfolios by Total Return [%] in descending order
    if 'Total Return [%]' in result_df.columns:
        result_df = result_df.sort("Total Return [%]", descending=True)

    # Reorder columns to put Metric Type first
    cols = ['Metric Type'] + [col for col in result_df.columns if col != 'Metric Type']
    result_df = result_df.select(cols)

    # Export to CSV
    csv_path = get_path("csv", "ma_cross", config, 'portfolios_filtered')
    csv_filename = get_filename("csv", config)
    result_df.write_csv(csv_path + "/" + csv_filename)

    print(f"Analysis complete. Results written to {csv_path}")
    print(f"Total rows in output: {len(result_rows)}")

    return result_df
