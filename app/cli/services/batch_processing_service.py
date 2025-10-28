"""
Batch Processing Service

This module provides batch processing functionality for handling large ticker lists
with progress tracking and duplicate prevention.
"""

from collections.abc import Callable
import csv
from datetime import datetime
from pathlib import Path

import pandas as pd

from app.tools.console_logging import ConsoleLogger


class BatchProcessingService:
    """
    Service for managing batch processing of ticker lists with CSV tracking.

    Handles reading batch files, cleaning old entries, tracking processed tickers,
    and updating progress after successful ticker processing.
    """

    def __init__(
        self,
        batch_file_path: str = "data/raw/batch.csv",
        console: ConsoleLogger | None = None,
    ):
        """
        Initialize batch processing service.

        Args:
            batch_file_path: Path to the batch tracking CSV file
            console: Console logger for user-facing output
        """
        self.batch_file_path = Path(batch_file_path)
        self.console = console or ConsoleLogger()

        # Ensure the directory exists
        self.batch_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize file if it doesn't exist
        if not self.batch_file_path.exists():
            self._create_batch_file()

    def _create_batch_file(self) -> None:
        """Create a new batch file with proper headers."""
        with open(self.batch_file_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Ticker", "Last Modified"])
        self.console.info(f"Created batch file: {self.batch_file_path}")

    def validate_batch_file(self) -> bool:
        """
        Validate that the batch file exists and has the correct structure.

        Returns:
            True if valid, False otherwise
        """
        try:
            if not self.batch_file_path.exists():
                self.console.warning(
                    f"Batch file does not exist: {self.batch_file_path}",
                )
                return False

            # Check if file is readable and has correct headers
            df = pd.read_csv(self.batch_file_path)
            required_columns = {"Ticker", "Last Modified"}

            if not required_columns.issubset(set(df.columns)):
                self.console.error(
                    f"Batch file missing required columns: {required_columns}",
                )
                return False

            return True

        except Exception as e:
            self.console.error(f"Error validating batch file: {e}")
            return False

    def read_batch_file(self) -> pd.DataFrame:
        """
        Read and parse the batch CSV file.

        Returns:
            DataFrame with batch data, empty if file doesn't exist or is invalid
        """
        try:
            if not self.batch_file_path.exists():
                self.console.warning(
                    f"Batch file does not exist: {self.batch_file_path}",
                )
                return pd.DataFrame(columns=["Ticker", "Last Modified"])

            df = pd.read_csv(self.batch_file_path)

            # Handle empty file case
            if df.empty:
                return pd.DataFrame(columns=["Ticker", "Last Modified"])

            # Ensure required columns exist
            if "Ticker" not in df.columns or "Last Modified" not in df.columns:
                self.console.error(
                    "Batch file missing required columns: Ticker, Last Modified",
                )
                return pd.DataFrame(columns=["Ticker", "Last Modified"])

            # Clean up ticker names (uppercase, strip whitespace)
            df["Ticker"] = df["Ticker"].astype(str).str.strip().str.upper()

            return df

        except Exception as e:
            self.console.error(f"Error reading batch file: {e}")
            return pd.DataFrame(columns=["Ticker", "Last Modified"])

    def clean_old_entries(self) -> int:
        """
        Remove entries from batch file that are older than today.

        Returns:
            Number of entries removed
        """
        try:
            df = self.read_batch_file()

            if df.empty:
                return 0

            # Get today's date in YYYY-MM-DD format
            today = datetime.now().strftime("%Y-%m-%d")

            # Count original entries
            original_count = len(df)

            # Filter to keep only today's entries or entries with invalid dates
            df_cleaned = df[
                (df["Last Modified"].astype(str).str.strip() == today)
                | (df["Last Modified"].isna())
                | (df["Last Modified"].astype(str).str.strip() == "")
            ].copy()

            # Calculate removed count
            removed_count = original_count - len(df_cleaned)

            if removed_count > 0:
                # Write back the cleaned data
                df_cleaned.to_csv(self.batch_file_path, index=False)
                self.console.info(
                    f"Cleaned {removed_count} old entries from batch file",
                )

            return removed_count

        except Exception as e:
            self.console.error(f"Error cleaning old entries: {e}")
            return 0

    def get_processed_tickers_today(self) -> set[str]:
        """
        Get the set of tickers that have been processed today.

        Returns:
            Set of ticker symbols processed today
        """
        try:
            df = self.read_batch_file()

            if df.empty:
                return set()

            # Get today's date in YYYY-MM-DD format
            today = datetime.now().strftime("%Y-%m-%d")

            # Filter to today's entries
            today_entries = df[df["Last Modified"].astype(str).str.strip() == today]

            return set(today_entries["Ticker"].str.upper())

        except Exception as e:
            self.console.error(f"Error getting processed tickers: {e}")
            return set()

    def get_pending_tickers(self, all_tickers: list[str], batch_size: int) -> list[str]:
        """
        Get up to batch_size tickers that haven't been processed today.

        Args:
            all_tickers: Complete list of tickers to consider
            batch_size: Maximum number of tickers to return

        Returns:
            List of ticker symbols to process (up to batch_size)
        """
        try:
            # Get tickers already processed today
            processed_today = self.get_processed_tickers_today()

            # Filter out already processed tickers
            pending_tickers = [
                ticker.upper()
                for ticker in all_tickers
                if ticker.upper() not in processed_today
            ]

            # Limit to batch_size
            result = pending_tickers[:batch_size]

            self.console.info(
                f"Found {len(pending_tickers)} pending tickers, selecting {len(result)} for processing",
            )

            if len(result) < len(pending_tickers):
                self.console.info(
                    f"Remaining {len(pending_tickers) - len(result)} tickers will be processed in next batch",
                )

            return result

        except Exception as e:
            self.console.error(f"Error getting pending tickers: {e}")
            return []

    def get_tickers_needing_processing(
        self,
        all_tickers: list[str],
        batch_size: int,
        resume_check_fn: Callable,
    ) -> list[str]:
        """
        Get exactly batch_size tickers that need processing, considering both batch file
        status and resume analysis (existing files, freshness, etc.).

        Args:
            all_tickers: Complete list of tickers to consider
            batch_size: Exact number of tickers to return that need processing
            resume_check_fn: Function that takes (ticker, strategy_types) and returns
                           True if ticker needs processing, False if can be skipped

        Returns:
            List of ticker symbols that actually need processing (exactly batch_size or fewer if exhausted)
        """
        try:
            # Get tickers already processed today in batch file
            processed_today = self.get_processed_tickers_today()

            # Filter out already processed tickers from batch file
            pending_tickers = [
                ticker.upper()
                for ticker in all_tickers
                if ticker.upper() not in processed_today
            ]

            # Now filter by resume analysis - select tickers that actually need work
            tickers_needing_work = []
            checked_count = 0

            for ticker in pending_tickers:
                checked_count += 1

                # Check if this ticker actually needs processing using resume analysis
                if resume_check_fn(ticker):
                    tickers_needing_work.append(ticker)

                    # Stop when we have enough tickers that need work
                    if len(tickers_needing_work) >= batch_size:
                        break
                else:
                    self.console.debug(
                        f"Skipping {ticker} - already complete and fresh",
                    )

            self.console.info(
                f"Found {len(pending_tickers)} pending tickers, checked {checked_count}, "
                f"selected {len(tickers_needing_work)} that need processing",
            )

            if len(tickers_needing_work) < batch_size and checked_count < len(
                pending_tickers,
            ):
                remaining = len(pending_tickers) - checked_count
                self.console.info(
                    f"Remaining {remaining} tickers will be checked in next batch",
                )

            return tickers_needing_work

        except Exception as e:
            self.console.error(f"Error getting tickers needing processing: {e}")
            return []

    def update_ticker_status(self, ticker: str) -> bool:
        """
        Update the Last Modified date for a ticker to today's date.
        Creates a new row if the ticker doesn't exist.

        Args:
            ticker: Ticker symbol to update

        Returns:
            True if successful, False otherwise
        """
        try:
            ticker = ticker.strip().upper()
            today = datetime.now().strftime("%Y-%m-%d")

            df = self.read_batch_file()

            # Check if ticker already exists
            ticker_mask = df["Ticker"].str.upper() == ticker

            if ticker_mask.any():
                # Update existing entry
                df.loc[ticker_mask, "Last Modified"] = today
            else:
                # Add new entry
                new_row = pd.DataFrame({"Ticker": [ticker], "Last Modified": [today]})
                df = pd.concat([df, new_row], ignore_index=True)

            # Write back to file
            df.to_csv(self.batch_file_path, index=False)

            self.console.debug(f"Updated batch status for {ticker}")
            return True

        except Exception as e:
            self.console.error(f"Error updating ticker status for {ticker}: {e}")
            return False

    def get_batch_status(self, all_tickers: list[str]) -> dict:
        """
        Get comprehensive batch processing status.

        Args:
            all_tickers: Complete list of tickers to analyze

        Returns:
            Dictionary with batch processing statistics
        """
        try:
            processed_today = self.get_processed_tickers_today()
            pending_tickers = [
                ticker.upper()
                for ticker in all_tickers
                if ticker.upper() not in processed_today
            ]

            return {
                "total_tickers": len(all_tickers),
                "processed_today": len(processed_today),
                "pending": len(pending_tickers),
                "processed_list": list(processed_today),
                "pending_list": pending_tickers,
                "completion_rate": (
                    len(processed_today) / len(all_tickers) if all_tickers else 0
                ),
            }

        except Exception as e:
            self.console.error(f"Error getting batch status: {e}")
            return {
                "total_tickers": len(all_tickers),
                "processed_today": 0,
                "pending": len(all_tickers),
                "processed_list": [],
                "pending_list": all_tickers,
                "completion_rate": 0.0,
            }

    def display_batch_status(self, all_tickers: list[str]) -> None:
        """
        Display batch processing status to console.

        Args:
            all_tickers: Complete list of tickers to analyze
        """
        status = self.get_batch_status(all_tickers)

        completion_pct = status["completion_rate"] * 100

        self.console.heading("Batch Processing Status", level=2)
        self.console.info(f"Total tickers: {status['total_tickers']}")
        self.console.info(f"Processed today: {status['processed_today']}")
        self.console.info(f"Pending: {status['pending']}")
        self.console.info(f"Completion: {completion_pct:.1f}%")

        if status["processed_today"] > 0:
            processed_preview = ", ".join(status["processed_list"][:5])
            if len(status["processed_list"]) > 5:
                processed_preview += f" (and {len(status['processed_list']) - 5} more)"
            self.console.success(f"Processed: {processed_preview}")

    def get_batch_tickers(self) -> list[str]:
        """
        Get all tickers from the batch file.

        Returns:
            List of ticker symbols from batch file
        """
        try:
            df = self.read_batch_file()

            if df.empty:
                return []

            # Get unique ticker symbols
            tickers = df["Ticker"].dropna().unique().tolist()

            # Clean and uppercase ticker symbols
            return [ticker.strip().upper() for ticker in tickers if ticker.strip()]

        except Exception as e:
            self.console.error(f"Error reading tickers from batch file: {e}")
            return []
