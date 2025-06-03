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
from app.api.utils.monitoring import get_metrics_collector
from app.api.utils.performance import get_request_optimizer, get_concurrent_executor
from app.tools.setup_logging import setup_logging

# Import interfaces
from app.core.interfaces import (
    LoggingInterface,
    ProgressTrackerInterface,
    StrategyExecutorInterface,
    StrategyAnalyzerInterface,
    CacheInterface,
    MonitoringInterface,
    ConfigurationInterface,
)
from app.core.types import StrategyParameters, TaskStatus


class MACrossServiceError(Exception):
    """Exception raised for errors in the MA Cross service."""
    pass


class MACrossService:
    """Service for executing MA Cross strategy analysis."""
    
    def __init__(
        self,
        logger: LoggingInterface,
        progress_tracker: ProgressTrackerInterface,
        strategy_executor: StrategyExecutorInterface,
        strategy_analyzer: StrategyAnalyzerInterface,
        cache: CacheInterface,
        monitoring: MonitoringInterface,
        configuration: ConfigurationInterface,
    ):
        """Initialize the MA Cross service with injected dependencies."""
        self.logger = logger
        self.progress_tracker = progress_tracker
        self.strategy_executor = strategy_executor
        self.strategy_analyzer = strategy_analyzer
        self.cache = cache
        self.monitoring = monitoring
        self.configuration = configuration
        
        # Legacy support - will be removed
        self.config = get_config()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.concurrent_executor = get_concurrent_executor()
        self.optimizer = get_request_optimizer()
        self.metrics = get_metrics_collector()
        
    async def analyze_portfolio(self, request: MACrossRequest) -> MACrossResponse:
        """
        Execute MA Cross analysis.
        
        Args:
            request: MACrossRequest model with analysis parameters
            
        Returns:
            MACrossResponse with analysis results
            
        Raises:
            MACrossServiceError: If analysis fails
        """
        # Check cache first
        # Handle ticker being either string or list
        ticker_str = request.ticker if isinstance(request.ticker, str) else ','.join(request.ticker)
        cache_key = f"ma_cross:{ticker_str}:{request.windows}:{':'.join(request.strategy_types)}"
        cached_result = await self.cache.get(cache_key)
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
            
            # Run the blocking analysis in a thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor,
                optimized_analysis,
                strategy_config,
                log
            )
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
            await self.cache.set(cache_key, response)
            
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
    
    def _execute_analysis(self, config: Dict[str, Any], log, progress_tracker: Optional[ProgressTrackerInterface] = None) -> List[PortfolioMetrics]:
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
        from app.strategies.ma_cross.tools.strategy_execution import execute_strategy
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
                
                log(f"execute_strategy returned {len(portfolios) if portfolios else 0} portfolios for {strategy_type}")
                if portfolios:
                    log(f"First portfolio keys: {list(portfolios[0].keys())}")
                
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
                    # Convert PortfolioMetrics objects to dictionaries for export
                    portfolio_dicts = []
                    for p in all_portfolios:
                        portfolio_dict = {
                            "Ticker": p.ticker,
                            "Strategy Type": p.strategy_type,
                            "Short Window": p.short_window,
                            "Long Window": p.long_window,
                            "Total Return [%]": p.total_return,
                            "Annual Returns": p.annual_return / 100.0,  # Convert back to decimal
                            "Sharpe Ratio": p.sharpe_ratio,
                            "Sortino Ratio": p.sortino_ratio,
                            "Max Drawdown [%]": p.max_drawdown,
                            "Total Trades": p.total_trades,
                            "Winning Trades": p.winning_trades,
                            "Losing Trades": p.losing_trades,
                            "Win Rate [%]": p.win_rate * 100.0,  # Convert back to percentage
                            "Profit Factor": p.profit_factor,
                            "Expectancy per Trade": p.expectancy,  # Map expectancy to the expected column name
                            "Score": p.score,
                            "Beats BNH [%]": p.beats_bnh,
                            "Has Open Trade": p.has_open_trade,
                            "Signal Entry": p.has_signal_entry
                        }
                        portfolio_dicts.append(portfolio_dict)
                    
                    export_best_portfolios(portfolio_dicts, config, log)
                    log(f"Successfully exported {len(portfolio_dicts)} best portfolios")
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
    
    async def _execute_analysis_async(
        self, 
        config: Dict[str, Any], 
        log, 
        execution_id: str, 
        progress_callback
    ) -> List[PortfolioMetrics]:
        """
        Execute the actual MA Cross analysis asynchronously with progress tracking.
        
        Args:
            config: Strategy configuration dictionary
            log: Logging function
            execution_id: Execution ID for tracking
            progress_callback: Async callback for progress updates
            
        Returns:
            List of PortfolioMetrics results
        """
        # Import the execute_strategy function from ma_cross module
        from app.strategies.ma_cross.tools.strategy_execution import execute_strategy
        from app.tools.project_utils import get_project_root
        
        # Ensure BASE_DIR is set in config
        if "BASE_DIR" not in config:
            config["BASE_DIR"] = get_project_root()
        
        # Get strategy types to analyze
        strategy_types = config.get("STRATEGY_TYPES", ["SMA", "EMA"])
        all_portfolios = []
        
        # Update progress for strategy types
        await progress_callback(20.0, f"Analyzing {len(strategy_types)} strategy types")
        
        try:
            # Execute strategy for each strategy type
            for i, strategy_type in enumerate(strategy_types):
                log(f"Executing {strategy_type} strategy analysis")
                
                # Update progress for each strategy
                progress = 20.0 + (i / len(strategy_types)) * 60.0
                await progress_callback(
                    progress,
                    f"Analyzing {strategy_type} strategy ({i+1}/{len(strategy_types)})"
                )
                
                # Execute the strategy in a thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                portfolios = await loop.run_in_executor(
                    self.executor,
                    execute_strategy,
                    config,
                    strategy_type,
                    log,
                    None  # No progress tracker for sync execution
                )
                
                log(f"execute_strategy returned {len(portfolios) if portfolios else 0} portfolios for {strategy_type}")
                
                if portfolios:
                    # Convert portfolio dictionaries to PortfolioMetrics objects
                    for portfolio in portfolios:
                        try:
                            # Extract metrics from portfolio dictionary (same logic as sync version)
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
            
            # Update progress for export phase
            await progress_callback(85.0, f"Processed {len(all_portfolios)} portfolios, exporting best results...")
            
            log(f"Total portfolios analyzed: {len(all_portfolios)}")
            
            # Export best portfolios if any were found
            if all_portfolios:
                try:
                    from app.tools.portfolio.collection import export_best_portfolios
                    log("Exporting best portfolios...")
                    # Convert PortfolioMetrics objects to dictionaries for export
                    portfolio_dicts = []
                    for p in all_portfolios:
                        portfolio_dict = {
                            "Ticker": p.ticker,
                            "Strategy Type": p.strategy_type,
                            "Short Window": p.short_window,
                            "Long Window": p.long_window,
                            "Total Return [%]": p.total_return,
                            "Annual Returns": p.annual_return / 100.0,  # Convert back to decimal
                            "Sharpe Ratio": p.sharpe_ratio,
                            "Sortino Ratio": p.sortino_ratio,
                            "Max Drawdown [%]": p.max_drawdown,
                            "Total Trades": p.total_trades,
                            "Winning Trades": p.winning_trades,
                            "Losing Trades": p.losing_trades,
                            "Win Rate [%]": p.win_rate * 100.0,  # Convert back to percentage
                            "Profit Factor": p.profit_factor,
                            "Expectancy per Trade": p.expectancy,  # Map expectancy to the expected column name
                            "Score": p.score,
                            "Beats BNH [%]": p.beats_bnh,
                            "Has Open Trade": p.has_open_trade,
                            "Signal Entry": p.has_signal_entry
                        }
                        portfolio_dicts.append(portfolio_dict)
                    
                    # Run export in thread pool
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        self.executor,
                        export_best_portfolios,
                        portfolio_dicts,
                        config,
                        log
                    )
                    
                    await progress_callback(95.0, f"Successfully exported {len(portfolio_dicts)} best portfolios")
                    log(f"Successfully exported {len(portfolio_dicts)} best portfolios")
                except Exception as e:
                    log(f"Failed to export best portfolios: {str(e)}", "error")
                    # Continue anyway - the analysis succeeded even if export failed
            
            return all_portfolios
            
        except Exception as e:
            log(f"Error in async portfolio analysis: {str(e)}", "error")
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
        # Run the async analysis in the event loop
        asyncio.run(self._run_async_analysis(execution_id, request))
    
    async def _run_async_analysis(self, execution_id: str, request: MACrossRequest) -> None:
        """
        Run the async analysis with proper async context.
        
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
            
            # Initialize progress tracking
            await self.progress_tracker.track(
                task_id=execution_id,
                operation="MA Cross Analysis",
                total_items=None
            )
            
            # Convert request to strategy config
            strategy_config = request.to_strategy_config()
            
            # Add project root to Python path
            project_root = self.config["BASE_DIR"]
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # Execute analysis with progress tracking
            start_time = time.time()
            
            # Update progress
            await self.progress_tracker.update(
                task_id=execution_id,
                progress=10.0,
                message="Initializing strategy analysis..."
            )
            
            # Create a progress callback for the execution
            async def progress_callback(progress: float, message: str):
                await self.progress_tracker.update(
                    task_id=execution_id,
                    progress=progress,
                    message=message
                )
            
            results = await self._execute_analysis_async(
                strategy_config, log, execution_id, progress_callback
            )
            execution_time = time.time() - start_time
            
            # Collect exported file paths
            portfolio_exports = self._collect_export_paths(strategy_config, request.strategy_types, log)
            
            # Count filtered portfolios
            filtered_count = 0
            if portfolio_exports and "portfolios_filtered" in portfolio_exports:
                filtered_count = len(portfolio_exports["portfolios_filtered"])
            
            # Create result structure that matches what frontend expects
            result_data = {
                "status": "success",
                "portfolios": [r.dict() for r in results],
                "portfolio_exports": portfolio_exports,
                "total_portfolios_analyzed": len(results),
                "total_portfolios_filtered": filtered_count,
                "execution_time": execution_time
            }
            
            # Complete progress tracking
            await self.progress_tracker.complete(
                task_id=execution_id,
                message=f"Analysis completed. Processed {len(results)} portfolios, filtered to {filtered_count}."
            )
            
            # Update task status with results
            task_status[execution_id].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": execution_time,
                "result": result_data,  # Frontend expects results in 'result' field
                "progress": f"Analysis completed. Processed {len(results)} portfolios, filtered to {filtered_count}."
            })
            
            log(f"Async analysis completed in {execution_time:.2f} seconds")
            
        except Exception as e:
            error_msg = f"Async MA Cross analysis failed: {str(e)}"
            log(error_msg, "error")
            log(traceback.format_exc(), "error")
            
            # Mark progress tracking as failed
            await self.progress_tracker.fail(
                task_id=execution_id,
                error=error_msg
            )
            
            # Update task status with error
            task_status[execution_id].update({
                "status": "failed",
                "completed_at": datetime.now().isoformat(),
                "error": error_msg,
                "progress": "Analysis failed."
            })
        finally:
            log_close()
    
    async def get_task_status(self, execution_id: str) -> Dict[str, Any]:
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
        
        # Get base status from task_status
        status = task_status[execution_id].copy()
        
        # Try to get enhanced progress data from progress tracker
        try:
            progress_status = await self.progress_tracker.get_status(execution_id)
            if progress_status:
                # Merge progress tracking data
                status.update({
                    "progress_percentage": progress_status.get("progress", 0.0),
                    "progress_message": progress_status.get("message", status.get("progress", "")),
                    "operation": progress_status.get("operation", "MA Cross Analysis"),
                    "progress_updated_at": progress_status.get("updated_at", "").isoformat() if progress_status.get("updated_at") else None
                })
        except Exception:
            # If progress tracker fails, continue with basic status
            pass
        
        return status
    
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