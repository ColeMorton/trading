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
            
            # Build response
            response = MACrossResponse(
                status="success",
                request_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                ticker=request.ticker,
                strategy_types=request.strategy_types,
                portfolios=results,
                total_portfolios=len(results),
                filtered_portfolios=len(results),  # No filtering applied in signal detection mode
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
            execution_id=execution_id,
            status="pending",
            message="Analysis task submitted"
        )
    
    def _execute_analysis(self, config: Dict[str, Any], log) -> List[PortfolioMetrics]:
        """
        Execute the actual MA Cross analysis using the core analyzer.
        
        Args:
            config: Strategy configuration dictionary
            log: Logging function
            
        Returns:
            List of PortfolioMetrics results
        """
        # Create analyzer instance
        analyzer = MACrossAnalyzer(log)
        results = []
        
        try:
            # Handle single ticker or portfolio
            if isinstance(config.get("TICKER"), str):
                # Single ticker analysis
                ticker = config["TICKER"]
                tickers = [ticker]
            elif config.get("PORTFOLIO"):
                # Load portfolio tickers from CSV
                import polars as pl
                portfolio_file = os.path.join("./csv/strategies", config["PORTFOLIO"])
                
                try:
                    portfolio_df = pl.read_csv(portfolio_file)
                    # Handle different column name variations
                    ticker_col = "Ticker" if "Ticker" in portfolio_df.columns else "TICKER"
                    tickers = portfolio_df[ticker_col].to_list()
                except Exception as e:
                    log(f"Error loading portfolio file: {str(e)}", "error")
                    return results
            else:
                log("No ticker or portfolio specified", "error")
                return results
            
            # Get strategy types to analyze
            strategy_types = config.get("STRATEGY_TYPES", ["SMA", "EMA"])
            
            # Process each ticker with each strategy type
            for ticker in tickers:
                for strategy_type in strategy_types:
                    try:
                        # Create analysis config
                        analysis_config = AnalysisConfig(
                            ticker=ticker,
                            use_sma=(strategy_type == "SMA"),
                            use_hourly=config.get("USE_HOURLY", False),
                            direction=config.get("DIRECTION", "Long"),
                            short_window=config.get("SHORT_WINDOW"),
                            long_window=config.get("LONG_WINDOW"),
                            windows=config.get("WINDOWS"),
                            use_years=config.get("USE_YEARS", False),
                            years=config.get("YEARS", 1.0)
                        )
                        
                        # Analyze ticker
                        ticker_result = analyzer.analyze_single(analysis_config)
                        
                        # Convert to PortfolioMetrics for each signal
                        if ticker_result.has_current_signal:
                            for signal in ticker_result.current_signals:
                                # Create metrics with minimal required fields
                                # Real backtest metrics would be populated by running full backtest
                                metrics = PortfolioMetrics(
                                    ticker=ticker,
                                    strategy_type=signal.ma_type,
                                    short_window=signal.short_window,
                                    long_window=signal.long_window,
                                    total_return=0.0,
                                    annual_return=0.0,
                                    sharpe_ratio=0.0,
                                    sortino_ratio=0.0,
                                    max_drawdown=0.0,
                                    total_trades=0,
                                    winning_trades=0,
                                    losing_trades=0,
                                    win_rate=0.0,
                                    profit_factor=0.0,
                                    expectancy=0.0,
                                    score=0.0,
                                    beats_bnh=0.0,
                                    has_open_trade=False,
                                    has_signal_entry=True  # Current signal detected
                                )
                                results.append(metrics)
                        
                    except Exception as e:
                        log(f"Error processing {ticker} with {strategy_type}: {str(e)}", "error")
                        continue
            
            return results
            
        finally:
            # Clean up analyzer resources
            analyzer.close()
    
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