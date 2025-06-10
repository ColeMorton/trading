#!/usr/bin/env python3
"""
Trace SMLR in CSV files to understand the data flow.
"""

import csv
from pathlib import Path

import pandas as pd


def trace_smlr_in_csv():
    """Trace SMLR entries in various CSV files."""
    base_path = Path("/Users/colemorton/Projects/trading")

    print("=== Tracing SMLR in CSV Files ===\n")

    # 1. Check DAILY.csv for raw input
    daily_csv = base_path / "csv/strategies/DAILY.csv"
    print(f"1. Checking {daily_csv.name}:")

    if daily_csv.exists():
        df = pd.read_csv(daily_csv)
        smlr_rows = df[df["Ticker"] == "SMLR"]
        amzn_rows = df[df["Ticker"] == "AMZN"]

        print(f"   Total rows: {len(df)}")
        print(f"   SMLR rows: {len(smlr_rows)}")
        print(f"   AMZN rows: {len(amzn_rows)}")

        # Group by strategy type
        if len(smlr_rows) > 0:
            smlr_by_strategy = smlr_rows.groupby("Strategy Type").size()
            print(f"\n   SMLR by strategy type:")
            for strategy, count in smlr_by_strategy.items():
                print(f"     {strategy}: {count}")

        if len(amzn_rows) > 0:
            amzn_by_strategy = amzn_rows.groupby("Strategy Type").size()
            print(f"\n   AMZN by strategy type:")
            for strategy, count in amzn_by_strategy.items():
                print(f"     {strategy}: {count}")

    # 2. Check portfolios_filtered for SMLR
    print("\n\n2. Checking portfolios_filtered directory:")
    filtered_dir = base_path / "csv/portfolios_filtered"

    # Look for recent date directories
    date_dirs = sorted(
        [d for d in filtered_dir.iterdir() if d.is_dir() and d.name.startswith("2025")]
    )

    if date_dirs:
        latest_date_dir = date_dirs[-1]
        print(f"   Latest date directory: {latest_date_dir.name}")

        # Find SMLR files
        smlr_files = list(latest_date_dir.glob("SMLR*.csv"))
        print(f"   SMLR files found: {len(smlr_files)}")

        for file in smlr_files:
            print(f"\n   File: {file.name}")
            df = pd.read_csv(file)
            print(f"     Rows: {len(df)}")

            if "Metric Type" in df.columns:
                print("     Has Metric Type column")
                # Show unique metric types
                metric_types = df["Metric Type"].unique()
                print(f"     Unique metric types: {len(metric_types)}")
                for mt in metric_types[:5]:  # Show first 5
                    print(f"       - {mt}")
                if len(metric_types) > 5:
                    print(f"       ... and {len(metric_types) - 5} more")

            # Check strategy types
            if "Strategy Type" in df.columns:
                strategies = df["Strategy Type"].unique()
                print(f"     Strategy types: {list(strategies)}")

    # 3. Check portfolios_best for aggregated data
    print("\n\n3. Checking portfolios_best directory:")
    best_dir = base_path / "csv/portfolios_best"

    # Look for recent date directories
    date_dirs = sorted(
        [d for d in best_dir.iterdir() if d.is_dir() and d.name.startswith("2025")]
    )

    if date_dirs:
        latest_date_dir = date_dirs[-1]
        print(f"   Latest date directory: {latest_date_dir.name}")

        # Find files containing data
        csv_files = list(latest_date_dir.glob("*.csv"))
        print(f"   CSV files found: {len(csv_files)}")

        for file in csv_files[:3]:  # Check first 3 files
            print(f"\n   File: {file.name}")
            df = pd.read_csv(file)

            # Look for SMLR and AMZN
            if "Ticker" in df.columns:
                smlr_rows = df[df["Ticker"] == "SMLR"]
                amzn_rows = df[df["Ticker"] == "AMZN"]

                print(f"     SMLR rows: {len(smlr_rows)}")
                print(f"     AMZN rows: {len(amzn_rows)}")

                if len(smlr_rows) > 0 and "Strategy Type" in df.columns:
                    smlr_strategies = smlr_rows["Strategy Type"].unique()
                    print(f"     SMLR strategies: {list(smlr_strategies)}")

                    # Show metric types if available
                    if "Metric Type" in df.columns:
                        for idx, row in smlr_rows.iterrows():
                            strategy = row["Strategy Type"]
                            metric_type = row["Metric Type"]
                            print(f"       {strategy}: {metric_type}")

                if len(amzn_rows) > 0 and "Strategy Type" in df.columns:
                    amzn_strategies = amzn_rows["Strategy Type"].unique()
                    print(f"     AMZN strategies: {list(amzn_strategies)}")


if __name__ == "__main__":
    trace_smlr_in_csv()
