"""
MA Cross Service

This module provides functionality for executing MA Cross strategy analysis
through the API. It handles both synchronous and asynchronous execution
of the MA Cross scanner.
"""

import os
import sys
import json
import uuid
import time
import asyncio
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from app.api.config import get_config
from app.api.models.ma_cross import (
    MACrossRequest, 
    MACrossResponse, 
    MACrossAsyncResponse,
    PortfolioMetrics
)
from app.api.services.script_executor import task_status
from app.tools.setup_logging import setup_logging


class MACrossServiceError(Exception):
    """Exception raised for errors in the MA Cross service."""
    pass


class MACrossService:
    """Service for executing MA Cross strategy analysis."""
    
    def __init__(self):
        """Initialize the MA Cross service."""
        self.config = get_config()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def analyze_portfolio(self, request: MACrossRequest) -> MACrossResponse:
        """
        Execute MA Cross analysis synchronously.
        
        Args:
            request: MACrossRequest model with analysis parameters
            
        Returns:
            MACrossResponse with analysis results
            
        Raises:
            MACrossServiceError: If analysis fails
        """
        log, log_close, _, _ = setup_logging(
            module_name='api',
            log_file=f'ma_cross_sync_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            log_subdir='ma_cross'
        )
        
        try:
            log(f"Starting synchronous MA Cross analysis for ticker(s): {request.ticker}")
            
            # Convert request to strategy config format
            strategy_config = request.to_strategy_config()
            log(f"Strategy config: {json.dumps(strategy_config, indent=2)}")
            
            # Add project root to Python path
            project_root = self.config["BASE_DIR"]
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # Import and run the scanner
            from app.ma_cross.tools.scanner_processing import process_ticker
            from app.tools.file_utils import is_file_from_today
            from app.utils import get_path, get_filename
            
            # Process analysis
            start_time = time.time()
            results = self._execute_analysis(strategy_config, log)
            execution_time = time.time() - start_time
            
            log(f"Analysis completed in {execution_time:.2f} seconds")
            
            # Build response
            response = MACrossResponse(
                status="completed",
                execution_time=execution_time,
                results=results
            )
            
            log_close()
            return response
            
        except Exception as e:
            error_msg = f"MA Cross analysis failed: {str(e)}"
            log(error_msg, "error")
            log(traceback.format_exc(), "error")
            log_close()
            raise MACrossServiceError(error_msg)
    
    def analyze_portfolio_async(self, request: MACrossRequest) -> MACrossAsyncResponse:
        """
        Execute MA Cross analysis asynchronously.
        
        Args:
            request: MACrossRequest model with analysis parameters
            
        Returns:
            MACrossAsyncResponse with execution ID for status tracking
        """
        # Generate unique execution ID
        execution_id = str(uuid.uuid4())
        
        # Initialize task status
        task_status[execution_id] = {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "progress": "Initializing analysis...",
            "results": None,
            "error": None
        }
        
        # Submit task to executor
        future = self.executor.submit(
            self._execute_async_analysis,
            execution_id,
            request
        )
        
        # Return immediate response with execution ID
        return MACrossAsyncResponse(
            execution_id=execution_id,
            status="pending",
            message="Analysis task submitted"
        )
    
    def _execute_analysis(self, config: Dict[str, Any], log) -> List[PortfolioMetrics]:
        """
        Execute the actual MA Cross analysis.
        
        Args:
            config: Strategy configuration dictionary
            log: Logging function
            
        Returns:
            List of PortfolioMetrics results
        """
        # Import required modules
        from app.ma_cross.tools.scanner_processing import (
            load_existing_results,
            process_ticker,
            export_results
        )
        from app.tools.get_data import load_json_portfolio
        
        results = []
        
        # Handle single ticker or portfolio
        if isinstance(config.get("TICKER"), str):
            # Single ticker analysis
            ticker = config["TICKER"]
            
            # Create synthetic portfolio entry
            portfolio_data = [{
                "ticker": ticker,
                "use_sma": config.get("STRATEGY_TYPES", ["SMA", "EMA"]) == ["SMA"],
                "short_window": config.get("SHORT_WINDOW", 10),
                "long_window": config.get("LONG_WINDOW", 30)
            }]
        else:
            # Portfolio analysis
            portfolio_file = os.path.join("./csv/strategies", config["PORTFOLIO"])
            portfolio_data = load_json_portfolio(portfolio_file)
        
        # Process each ticker configuration
        for item in portfolio_data:
            ticker = item.get("ticker", item.get("TICKER"))
            
            # Process with both SMA and EMA if not specified
            strategy_types = config.get("STRATEGY_TYPES", ["SMA", "EMA"])
            
            for strategy_type in strategy_types:
                try:
                    # Prepare row data for process_ticker
                    row = {
                        f"{strategy_type}_FAST": item.get("short_window", 10),
                        f"{strategy_type}_SLOW": item.get("long_window", 30)
                    }
                    
                    # Process ticker
                    result = process_ticker(ticker, row, config, log)
                    
                    # Convert to PortfolioMetrics
                    if result.get(strategy_type):
                        metrics = PortfolioMetrics(
                            ticker=ticker,
                            strategy_type=strategy_type,
                            short_window=row[f"{strategy_type}_FAST"],
                            long_window=row[f"{strategy_type}_SLOW"],
                            signal_active=result[strategy_type],
                            trades=0,  # These would be populated from actual backtest
                            win_rate=0.0,
                            expectancy_per_trade=0.0,
                            profit_factor=0.0,
                            sortino_ratio=0.0,
                            beats_bnh=0.0,
                            score=0.0
                        )
                        results.append(metrics)
                        
                except Exception as e:
                    log(f"Error processing {ticker} with {strategy_type}: {str(e)}", "error")
                    continue
        
        return results
    
    def _execute_async_analysis(self, execution_id: str, request: MACrossRequest) -> None:
        """
        Execute analysis in background thread.
        
        Args:
            execution_id: Unique ID for tracking execution
            request: Analysis request parameters
        """
        log, log_close, _, _ = setup_logging(
            module_name='api',
            log_file=f'ma_cross_async_{execution_id}.log',
            log_subdir='ma_cross'
        )
        
        try:
            # Update status
            task_status[execution_id]["status"] = "running"
            task_status[execution_id]["progress"] = "Starting analysis..."
            
            log(f"Starting async MA Cross analysis for execution {execution_id}")
            
            # Convert request to strategy config
            strategy_config = request.to_strategy_config()
            
            # Add project root to Python path
            project_root = self.config["BASE_DIR"]
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # Execute analysis
            start_time = time.time()
            results = self._execute_analysis(strategy_config, log)
            execution_time = time.time() - start_time
            
            # Update task status with results
            task_status[execution_id].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": execution_time,
                "results": [r.dict() for r in results],
                "progress": f"Analysis completed. Processed {len(results)} configurations."
            })
            
            log(f"Async analysis completed in {execution_time:.2f} seconds")
            
        except Exception as e:
            error_msg = f"Async MA Cross analysis failed: {str(e)}"
            log(error_msg, "error")
            log(traceback.format_exc(), "error")
            
            # Update task status with error
            task_status[execution_id].update({
                "status": "failed",
                "completed_at": datetime.now().isoformat(),
                "error": error_msg,
                "progress": "Analysis failed."
            })
        finally:
            log_close()
    
    def get_task_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get status of an async task.
        
        Args:
            execution_id: Unique execution ID
            
        Returns:
            Task status dictionary
            
        Raises:
            MACrossServiceError: If execution ID not found
        """
        if execution_id not in task_status:
            raise MACrossServiceError(f"Execution ID not found: {execution_id}")
        
        return task_status[execution_id]
    
    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """
        Clean up old task statuses.
        
        Args:
            max_age_hours: Maximum age of tasks to keep
            
        Returns:
            Number of tasks cleaned up
        """
        current_time = datetime.now()
        cleaned = 0
        
        for exec_id, status in list(task_status.items()):
            started_at = datetime.fromisoformat(status["started_at"])
            age_hours = (current_time - started_at).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                del task_status[exec_id]
                cleaned += 1
        
        return cleaned