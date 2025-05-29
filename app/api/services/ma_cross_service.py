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
from app.ma_cross.core import MACrossAnalyzer, AnalysisConfig
from app.api.utils.cache import get_cache
from app.api.utils.performance import get_concurrent_executor, get_request_optimizer
from app.api.utils.monitoring import get_metrics_collector
from app.tools.progress_tracking import ProgressTracker, create_progress_callback


class MACrossServiceError(Exception):
    """Exception raised for errors in the MA Cross service."""
    pass


class MACrossService:
    """Service for executing MA Cross strategy analysis."""
    
    def __init__(self):
        """Initialize the MA Cross service."""
        self.config = get_config()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.cache = get_cache()
        self.concurrent_executor = get_concurrent_executor()
        self.optimizer = get_request_optimizer()
        self.metrics = get_metrics_collector()
        
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
        # Check cache first
        cached_result = self.cache.get(request)
        if cached_result:
            return cached_result
        
        log, log_close, _, _ = setup_logging(
            module_name='api',
            log_file=f'ma_cross_sync_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            log_subdir='ma_cross'
        )
        
        try:
            # Record request metrics
            start_time = time.time()
            
            log(f"Starting synchronous MA Cross analysis for ticker(s): {request.ticker}")
            
            # Convert request to strategy config format
            strategy_config = request.to_strategy_config()
            log(f"Strategy config: {json.dumps(strategy_config, indent=2)}")
            
            # Add project root to Python path
            project_root = self.config["BASE_DIR"]
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # Use performance-optimized analysis
            optimized_analysis = self.optimizer.time_operation("ma_cross_analysis")(
                self._execute_analysis
            )
            
            results = optimized_analysis(strategy_config, log)
            execution_time = time.time() - start_time
            
            log(f"Analysis completed in {execution_time:.2f} seconds")
            
            # Collect exported file paths
            portfolio_exports = self._collect_export_paths(strategy_config, request.strategy_types, log)
            
            # Count filtered portfolios
            filtered_count = 0
            if portfolio_exports and "portfolios_filtered" in portfolio_exports:
                filtered_count = len(portfolio_exports["portfolios_filtered"])
            
            # Build response
            response = MACrossResponse(
                status="success",
                request_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                ticker=request.ticker,
                strategy_types=request.strategy_types,
                portfolios=results,
                portfolio_exports=portfolio_exports,
                total_portfolios_analyzed=len(results),
                total_portfolios_filtered=filtered_count,
                execution_time=execution_time
            )
            
            # Cache the result for future requests
            self.cache.set(request, response)
            
            # Record metrics
            self.metrics.record_request(
                endpoint="/api/ma-cross/analyze",
                method="POST",
                status_code=200,
                response_time=execution_time,
                client_ip="internal",  # Will be overridden by middleware
                user_agent="ma_cross_service"
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
            status="accepted",
            execution_id=execution_id,
            message="Analysis task submitted",
            status_url=f"/api/ma-cross/status/{execution_id}",
            stream_url=f"/api/ma-cross/stream/{execution_id}",
            timestamp=datetime.now(),
            estimated_time=60.0  # Estimate based on typical analysis time
        )
    
    def _execute_analysis(self, config: Dict[str, Any], log, progress_tracker: Optional[ProgressTracker] = None) -> List[PortfolioMetrics]:
        """
        Execute the actual MA Cross analysis using full portfolio analysis.
        
        This method now uses the execute_strategy function from the MA Cross module
        to perform complete backtesting and portfolio analysis.
        
        Args:
            config: Strategy configuration dictionary
            log: Logging function
            progress_tracker: Optional progress tracker for reporting status
            
        Returns:
            List of PortfolioMetrics results
        """
        # Import the execute_strategy function from ma_cross module
        from app.ma_cross.tools.strategy_execution import execute_strategy
        from app.tools.project_utils import get_project_root
        
        # Ensure BASE_DIR is set in config
        if "BASE_DIR" not in config:
            config["BASE_DIR"] = get_project_root()
        
        # Get strategy types to analyze
        strategy_types = config.get("STRATEGY_TYPES", ["SMA", "EMA"])
        all_portfolios = []
        
        # Update progress for strategy types
        if progress_tracker:
            progress_tracker.update(
                phase="initialization",
                message=f"Analyzing {len(strategy_types)} strategy types"
            )
        
        try:
            # Execute strategy for each strategy type
            for i, strategy_type in enumerate(strategy_types):
                log(f"Executing {strategy_type} strategy analysis")
                
                if progress_tracker:
                    progress_tracker.update(
                        phase=f"{strategy_type}_analysis",
                        message=f"Starting {strategy_type} analysis ({i+1}/{len(strategy_types)})"
                    )
                
                # Execute the strategy and get portfolio results
                portfolios = execute_strategy(config, strategy_type, log, progress_tracker)
                
                if portfolios:
                    # Convert portfolio dictionaries to PortfolioMetrics objects
                    for portfolio in portfolios:
                        try:
                            # Extract metrics from portfolio dictionary
                            # The best portfolio from get_best_portfolio uses SMA_FAST/SLOW or EMA_FAST/SLOW
                            
                            # Clean up strategy type if it has enum prefix
                            strategy_type_value = portfolio.get("Strategy Type", portfolio.get("MA Type", strategy_type))
                            if isinstance(strategy_type_value, str) and "StrategyTypeEnum." in strategy_type_value:
                                strategy_type_value = strategy_type_value.replace("StrategyTypeEnum.", "")
                            
                            # Determine window column names based on strategy type
                            if strategy_type_value == "SMA" or strategy_type == "SMA":
                                short_window = portfolio.get("SMA_FAST", portfolio.get("Short Window", 0))
                                long_window = portfolio.get("SMA_SLOW", portfolio.get("Long Window", 0))
                            else:  # EMA
                                short_window = portfolio.get("EMA_FAST", portfolio.get("Short Window", 0))
                                long_window = portfolio.get("EMA_SLOW", portfolio.get("Long Window", 0))
                            
                            # Convert to int, handling None values
                            short_window = int(short_window) if short_window is not None else 0
                            long_window = int(long_window) if long_window is not None else 0
                            
                            # Calculate winning/losing trades from total trades and win rate
                            total_trades = int(portfolio.get("Total Trades", 0))
                            win_rate_pct = float(portfolio.get("Win Rate [%]", 0.0))
                            winning_trades = int(total_trades * win_rate_pct / 100)
                            losing_trades = total_trades - winning_trades
                            
                            # Convert string values to appropriate types before comparisons
                            total_open_trades = portfolio.get("Total Open Trades", 0)
                            if isinstance(total_open_trades, str):
                                total_open_trades = int(total_open_trades) if total_open_trades.isdigit() else 0
                            
                            signal_entry = portfolio.get("Signal Entry", False)
                            if isinstance(signal_entry, str):
                                signal_entry_bool = signal_entry.lower() == "true"
                            else:
                                signal_entry_bool = bool(signal_entry)
                            
                            metrics = PortfolioMetrics(
                                ticker=portfolio.get("Ticker", ""),
                                strategy_type=strategy_type_value,
                                short_window=short_window,
                                long_window=long_window,
                                total_return=float(portfolio.get("Total Return [%]", 0.0)),
                                annual_return=float(portfolio.get("Ann. Return [%]", portfolio.get("Annual Returns", 0.0) * 100)),
                                sharpe_ratio=float(portfolio.get("Sharpe Ratio", 0.0)),
                                sortino_ratio=float(portfolio.get("Sortino Ratio", 0.0)),
                                max_drawdown=float(portfolio.get("Max Drawdown [%]", 0.0)),
                                total_trades=total_trades,
                                winning_trades=winning_trades,
                                losing_trades=losing_trades,
                                win_rate=win_rate_pct / 100.0,  # Convert percentage to decimal
                                profit_factor=float(portfolio.get("Profit Factor", 0.0)),
                                expectancy=float(portfolio.get("Expectancy", portfolio.get("Expectancy per Trade", 0.0))),
                                score=float(portfolio.get("Score", 0.0)),
                                beats_bnh=float(portfolio.get("Beats BNH [%]", 0.0)),
                                has_open_trade=bool(total_open_trades > 0),
                                has_signal_entry=signal_entry_bool
                            )
                            all_portfolios.append(metrics)
                        except (ValueError, TypeError, KeyError) as e:
                            log(f"Error converting portfolio to metrics: {str(e)}", "error")
                            continue
                else:
                    log(f"No portfolios returned for {strategy_type} strategy", "warning")
            
            log(f"Total portfolios analyzed: {len(all_portfolios)}")
            
            # Export best portfolios if any were found
            if all_portfolios:
                try:
                    from app.tools.portfolio.collection import export_best_portfolios
                    log("Exporting best portfolios...")
                    export_best_portfolios(all_portfolios, config, log)
                    log(f"Successfully exported {len(all_portfolios)} best portfolios")
                except Exception as e:
                    log(f"Failed to export best portfolios: {str(e)}", "error")
                    # Continue anyway - the analysis succeeded even if export failed
            
            return all_portfolios
            
        except Exception as e:
            log(f"Error in portfolio analysis: {str(e)}", "error")
            log(f"Error type: {type(e).__name__}", "error")
            import traceback
            log(traceback.format_exc(), "error")
            return []
    
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
            
            # Create progress tracker with callback
            progress_callback = create_progress_callback(execution_id, task_status)
            progress_tracker = ProgressTracker(callback=progress_callback)
            
            # Convert request to strategy config
            strategy_config = request.to_strategy_config()
            
            # Add project root to Python path
            project_root = self.config["BASE_DIR"]
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # Execute analysis with progress tracking
            start_time = time.time()
            results = self._execute_analysis(strategy_config, log, progress_tracker)
            execution_time = time.time() - start_time
            
            # Collect exported file paths
            portfolio_exports = self._collect_export_paths(strategy_config, request.strategy_types, log)
            
            # Count filtered portfolios
            filtered_count = 0
            if portfolio_exports and "portfolios_filtered" in portfolio_exports:
                filtered_count = len(portfolio_exports["portfolios_filtered"])
            
            # Update task status with results
            task_status[execution_id].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": execution_time,
                "results": [r.dict() for r in results],
                "portfolio_exports": portfolio_exports,
                "total_portfolios_analyzed": len(results),
                "total_portfolios_filtered": filtered_count,
                "progress": f"Analysis completed. Processed {len(results)} portfolios, filtered to {filtered_count}."
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
    
    def _collect_export_paths(self, config: Dict[str, Any], strategy_types: List[str], log) -> Dict[str, List[str]]:
        """
        Collect paths of exported portfolio CSV files.
        
        Args:
            config: Strategy configuration
            strategy_types: List of strategy types analyzed
            log: Logging function
            
        Returns:
            Dictionary with export paths organized by type
        """
        import os
        import glob
        
        export_paths = {
            "portfolios": [],
            "portfolios_filtered": []
        }
        
        try:
            # Get ticker list
            tickers = []
            if isinstance(config.get("TICKER"), str):
                tickers = [config["TICKER"]]
            elif isinstance(config.get("TICKER"), list):
                tickers = config["TICKER"]
            
            # Construct expected file paths for each ticker and strategy type
            for ticker in tickers:
                # Format ticker for filename (replace special characters)
                ticker_formatted = ticker.replace("-", "-").replace("/", "_")
                
                for strategy_type in strategy_types:
                    # Check for portfolio files
                    portfolio_pattern = f"csv/portfolios/{ticker_formatted}_*_{strategy_type}.csv"
                    portfolio_files = glob.glob(portfolio_pattern)
                    export_paths["portfolios"].extend(portfolio_files)
                    
                    # Check for filtered portfolio files
                    filtered_pattern = f"csv/portfolios_filtered/{ticker_formatted}_*_{strategy_type}.csv"
                    filtered_files = glob.glob(filtered_pattern)
                    export_paths["portfolios_filtered"].extend(filtered_files)
            
            # Remove duplicates and sort
            export_paths["portfolios"] = sorted(list(set(export_paths["portfolios"])))
            export_paths["portfolios_filtered"] = sorted(list(set(export_paths["portfolios_filtered"])))
            
            log(f"Found {len(export_paths['portfolios'])} portfolio files and {len(export_paths['portfolios_filtered'])} filtered files")
            
        except Exception as e:
            log(f"Error collecting export paths: {str(e)}", "error")
        
        return export_paths