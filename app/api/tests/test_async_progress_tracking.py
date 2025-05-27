"""
Comprehensive tests for async execution and progress tracking.
Tests SSE streaming, progress updates, and concurrent execution.
"""

import pytest
import asyncio
import json
import time
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.services.ma_cross_service import MACrossService
from app.api.models.ma_cross import MACrossRequest
from app.tools.progress_tracking import ProgressTracker


class TestAsyncExecutionWithProgress:
    """Test async execution with detailed progress tracking."""
    
    @pytest.fixture
    def service(self):
        """Create MA Cross service instance."""
        return MACrossService()
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    def test_progress_tracker_functionality(self):
        """Test ProgressTracker class functionality."""
        # Track progress updates
        updates = []
        
        def callback(data):
            updates.append(data)
        
        tracker = ProgressTracker(total_steps=10, callback=callback)
        
        # Update progress
        tracker.update(3, "data_download", "Downloading data...")
        tracker.update(5, "backtesting", "Running backtest...")
        tracker.update(8, "filtering", "Filtering portfolios...")
        tracker.update(10, "complete", "Analysis complete")
        
        # Verify updates
        assert len(updates) == 4
        assert updates[0]['phase'] == 'data_download'
        assert updates[1]['phase'] == 'backtesting'
        assert updates[2]['phase'] == 'filtering'
        assert updates[3]['phase'] == 'complete'
        
        # Check progress percentages
        assert updates[0]['percentage'] == 30.0
        assert updates[1]['percentage'] == 50.0
        assert updates[2]['percentage'] == 80.0
        assert updates[3]['percentage'] == 100.0
    
    @pytest.mark.asyncio
    async def test_async_execution_with_progress_updates(self, service):
        """Test async execution updates progress correctly."""
        # Mock execute_strategy to simulate progress
        def mock_execute_with_progress(config, strategy_type, log, progress_tracker=None):
            if progress_tracker:
                # Simulate progress updates
                progress_tracker.update(1, "initializing", f"Starting {strategy_type} analysis")
                time.sleep(0.1)
                progress_tracker.update(3, "data_download", "Downloading market data")
                time.sleep(0.1)
                progress_tracker.update(5, "calculating", "Calculating indicators")
                time.sleep(0.1)
                progress_tracker.update(8, "backtesting", "Running backtest")
                time.sleep(0.1)
                progress_tracker.update(10, "complete", "Analysis complete")
            
            return [{
                'Ticker': 'BTC-USD',
                'Strategy': strategy_type,
                'SMA_FAST': 20,
                'SMA_SLOW': 50,
                'Total_Return': 0.45
            }]
        
        with patch('app.api.services.ma_cross_service.execute_strategy', side_effect=mock_execute_with_progress):
            request = MACrossRequest(
                ticker="BTC-USD",
                windows=8,
                strategy_types=["SMA"],
                async_execution=True
            )
            
            response = service.analyze(request)
            execution_id = response.execution_id
            
            # Wait for execution to start
            await asyncio.sleep(0.5)
            
            # Check status updates
            status = service.get_status(execution_id)
            assert status is not None
            
            # Wait for completion
            await asyncio.sleep(1.0)
            
            final_status = service.get_status(execution_id)
            assert final_status['status'] == 'completed'
            assert final_status['progress'] == 100
    
    @pytest.mark.asyncio
    async def test_sse_stream_progress_events(self, async_client):
        """Test SSE stream delivers progress events correctly."""
        # Mock strategy execution with detailed progress
        with patch('app.api.services.ma_cross_service.execute_strategy') as mock:
            def execute_with_progress(*args, **kwargs):
                tracker = kwargs.get('progress_tracker')
                if tracker:
                    for i in range(1, 11):
                        tracker.update(i, f"phase_{i}", f"Step {i} of 10")
                        time.sleep(0.05)
                return []
            
            mock.side_effect = execute_with_progress
            
            # Start async analysis
            request_data = {
                "ticker": "BTC-USD",
                "windows": 8,
                "async_execution": True
            }
            
            response = await async_client.post("/api/ma-cross/analyze", json=request_data)
            execution_id = response.json()["execution_id"]
            
            # Collect SSE events
            events = []
            async with async_client.stream("GET", f"/api/ma-cross/stream/{execution_id}") as stream:
                async for line in stream.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data and data != "[DONE]":
                            events.append(json.loads(data))
                        elif data == "[DONE]":
                            break
            
            # Verify progress events
            progress_events = [e for e in events if 'progress_details' in e]
            assert len(progress_events) >= 5  # Should have multiple progress updates
            
            # Check progress increases
            progresses = [e['progress'] for e in progress_events]
            assert progresses == sorted(progresses)  # Monotonically increasing
            
            # Verify phase information
            phases = [e['progress_details']['phase'] for e in progress_events]
            assert len(set(phases)) > 1  # Multiple phases
    
    def test_progress_rate_limiting(self):
        """Test progress updates are rate limited."""
        updates = []
        
        def callback(data):
            updates.append({
                'time': time.time(),
                'data': data
            })
        
        tracker = ProgressTracker(callback=callback)
        tracker._update_interval = 0.1  # 100ms rate limit
        
        # Rapid updates
        start_time = time.time()
        for i in range(10):
            tracker.update(i, "test", f"Update {i}")
            time.sleep(0.02)  # 20ms between updates
        
        # Should have fewer updates due to rate limiting
        assert len(updates) < 10
        
        # Check time between updates
        for i in range(1, len(updates)):
            time_diff = updates[i]['time'] - updates[i-1]['time']
            assert time_diff >= 0.09  # Allow small margin
    
    @pytest.mark.asyncio
    async def test_concurrent_executions_with_progress(self, service):
        """Test multiple concurrent executions with independent progress."""
        execution_ids = []
        
        # Start multiple async analyses
        for i in range(3):
            request = MACrossRequest(
                ticker=f"TICKER{i}",
                windows=8,
                async_execution=True
            )
            response = service.analyze(request)
            execution_ids.append(response.execution_id)
        
        # Wait a bit for executions to progress
        await asyncio.sleep(0.5)
        
        # Check each has independent progress
        statuses = [service.get_status(eid) for eid in execution_ids]
        
        # All should be running or completed
        assert all(s['status'] in ['running', 'completed'] for s in statuses)
        
        # Each should have its own progress
        progresses = [s.get('progress', 0) for s in statuses]
        assert len(set(progresses)) > 1  # Different progress values
    
    def test_progress_callback_error_handling(self):
        """Test progress tracker handles callback errors gracefully."""
        def failing_callback(data):
            raise Exception("Callback error")
        
        # Should not crash the tracker
        tracker = ProgressTracker(callback=failing_callback)
        
        # These should complete without raising
        tracker.update(1, "test", "Update 1")
        tracker.update(2, "test", "Update 2")
        
        # Tracker should still work
        assert tracker.current_step == 2
        assert tracker.phase == "test"
    
    @pytest.mark.asyncio
    async def test_execution_cancellation(self, service):
        """Test handling of cancelled executions."""
        # Mock a slow execution
        with patch('app.api.services.ma_cross_service.execute_strategy') as mock:
            def slow_execution(*args, **kwargs):
                time.sleep(10)  # Very slow
                return []
            
            mock.side_effect = slow_execution
            
            request = MACrossRequest(
                ticker="BTC-USD",
                async_execution=True
            )
            
            response = service.analyze(request)
            execution_id = response.execution_id
            
            # Wait briefly
            await asyncio.sleep(0.1)
            
            # In a real implementation, we'd cancel here
            # For now, just verify it's running
            status = service.get_status(execution_id)
            assert status['status'] == 'running'
    
    def test_progress_phases_match_execution_flow(self, service):
        """Test that progress phases match actual execution flow."""
        recorded_phases = []
        
        def phase_recorder(data):
            recorded_phases.append(data['phase'])
        
        with patch('app.api.services.ma_cross_service.execute_strategy') as mock:
            def execute_with_phases(*args, **kwargs):
                tracker = kwargs.get('progress_tracker')
                if tracker:
                    tracker._callback = phase_recorder  # Override callback
                    tracker.update(1, "initializing", "Starting")
                    tracker.update(2, "data_download", "Downloading")
                    tracker.update(3, "indicator_calculation", "Calculating")
                    tracker.update(4, "backtesting", "Backtesting")
                    tracker.update(5, "filtering", "Filtering")
                    tracker.update(6, "exporting", "Exporting")
                    tracker.update(7, "complete", "Done")
                return []
            
            mock.side_effect = execute_with_phases
            
            request = MACrossRequest(ticker="BTC-USD")
            service._execute_analysis(request)
            
            # Verify expected phases
            expected_phases = [
                "initializing",
                "data_download",
                "indicator_calculation",
                "backtesting",
                "filtering",
                "exporting",
                "complete"
            ]
            
            assert recorded_phases == expected_phases


class TestProgressTrackingEdgeCases:
    """Test edge cases in progress tracking."""
    
    def test_progress_without_total_steps(self):
        """Test progress tracking without known total steps."""
        updates = []
        tracker = ProgressTracker(callback=lambda d: updates.append(d))
        
        # Update without total steps
        tracker.update(phase="processing", message="Working...")
        
        assert len(updates) == 1
        assert updates[0]['phase'] == 'processing'
        assert updates[0]['percentage'] == 0.0  # No percentage without total
    
    def test_progress_overflow(self):
        """Test progress updates beyond total steps."""
        updates = []
        tracker = ProgressTracker(total_steps=5, callback=lambda d: updates.append(d))
        
        # Update beyond total
        tracker.update(10, "overflow", "Too much progress")
        
        assert updates[-1]['percentage'] == 100.0  # Capped at 100%
    
    def test_progress_message_truncation(self):
        """Test very long progress messages are handled."""
        updates = []
        tracker = ProgressTracker(callback=lambda d: updates.append(d))
        
        # Very long message
        long_message = "A" * 1000
        tracker.update(1, "test", long_message)
        
        assert len(updates) == 1
        assert len(updates[0]['message']) == 1000  # Message preserved
    
    @pytest.mark.asyncio
    async def test_sse_connection_drop_handling(self, client):
        """Test SSE handles connection drops gracefully."""
        # Start async analysis
        request_data = {
            "ticker": "BTC-USD",
            "async_execution": True
        }
        
        response = client.post("/api/ma-cross/analyze", json=request_data)
        execution_id = response.json()["execution_id"]
        
        # Simulate connection drop by closing stream early
        with client.stream("GET", f"/api/ma-cross/stream/{execution_id}") as stream:
            # Read only first event then close
            for line in stream.iter_lines():
                if line.startswith("data: "):
                    break  # Close early
        
        # Execution should continue despite dropped connection
        time.sleep(0.5)
        status = client.get(f"/api/ma-cross/status/{execution_id}")
        assert status.status_code == 200