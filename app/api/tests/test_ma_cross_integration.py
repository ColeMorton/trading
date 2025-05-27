"""
Integration tests for MA Cross API endpoints.
Tests the full workflow from request to response including actual execution.
"""

import pytest
import asyncio
import json
import time
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.api.main import app
from app.api.models.ma_cross import MACrossRequest, MACrossResponse


class TestMACrossAPIIntegration:
    """Integration tests for MA Cross API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.fixture
    def mock_strategy_execution(self):
        """Mock the actual strategy execution to speed up tests."""
        with patch('app.api.services.ma_cross_service.execute_strategy') as mock:
            # Return realistic but fast results
            mock.return_value = [
                {
                    'Ticker': 'BTC-USD',
                    'Strategy': 'SMA',
                    'SMA_FAST': 20,
                    'SMA_SLOW': 50,
                    'Total_Return': 0.45,
                    'Sharpe_Ratio': 1.8,
                    'Max_Drawdown': -0.15,
                    'Win_Rate': 0.65,
                    'Num_Trades': 25
                }
            ]
            yield mock
    
    def test_sync_analysis_endpoint(self, client, mock_strategy_execution):
        """Test synchronous MA Cross analysis endpoint."""
        request_data = {
            "ticker": "BTC-USD",
            "windows": 8,
            "strategy_types": ["SMA"],
            "async_execution": False
        }
        
        response = client.post("/api/ma-cross/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["success"] is True
        assert data["execution_id"] is not None
        assert data["ticker"] == "BTC-USD"
        assert data["strategy_types"] == ["SMA"]
        assert "portfolios" in data
        assert len(data["portfolios"]) > 0
        
        # Verify portfolio data
        portfolio = data["portfolios"][0]
        assert portfolio["ticker"] == "BTC-USD"
        assert portfolio["strategy"] == "SMA"
        assert portfolio["fast_window"] == 20
        assert portfolio["slow_window"] == 50
        assert portfolio["total_return"] == 0.45
    
    def test_async_analysis_endpoint(self, client, mock_strategy_execution):
        """Test asynchronous MA Cross analysis endpoint."""
        request_data = {
            "ticker": ["BTC-USD", "ETH-USD"],
            "windows": 8,
            "strategy_types": ["SMA", "EMA"],
            "async_execution": True
        }
        
        response = client.post("/api/ma-cross/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return execution info for async
        assert data["success"] is True
        assert data["execution_id"] is not None
        assert data["ticker"] == ["BTC-USD", "ETH-USD"]
        assert data["strategy_types"] == ["SMA", "EMA"]
        assert data["message"] == "Analysis started"
    
    def test_status_endpoint(self, client):
        """Test execution status endpoint."""
        # First start an async analysis
        request_data = {
            "ticker": "BTC-USD",
            "async_execution": True
        }
        
        response = client.post("/api/ma-cross/analyze", json=request_data)
        execution_id = response.json()["execution_id"]
        
        # Check status
        status_response = client.get(f"/api/ma-cross/status/{execution_id}")
        
        assert status_response.status_code == 200
        status = status_response.json()
        
        assert status["execution_id"] == execution_id
        assert status["status"] in ["pending", "running", "completed", "failed"]
        assert "progress" in status
        assert "message" in status
    
    def test_sse_progress_streaming(self, client, mock_strategy_execution):
        """Test SSE progress streaming during analysis."""
        # Start async analysis
        request_data = {
            "ticker": "BTC-USD",
            "windows": 8,
            "async_execution": True
        }
        
        response = client.post("/api/ma-cross/analyze", json=request_data)
        execution_id = response.json()["execution_id"]
        
        # Connect to SSE stream
        with client as c:
            with c.stream("GET", f"/api/ma-cross/stream/{execution_id}") as stream:
                events = []
                for line in stream.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data and data != "[DONE]":
                            events.append(json.loads(data))
                        if data == "[DONE]":
                            break
                
                # Verify we received progress updates
                assert len(events) > 0
                
                # Check event structure
                for event in events:
                    assert "status" in event
                    assert "progress" in event
                    if "progress_details" in event:
                        details = event["progress_details"]
                        assert "phase" in details
                        assert "message" in details
    
    def test_multiple_tickers_analysis(self, client, mock_strategy_execution):
        """Test analysis with multiple tickers."""
        mock_strategy_execution.return_value = [
            {
                'Ticker': 'BTC-USD',
                'Strategy': 'SMA',
                'SMA_FAST': 20,
                'SMA_SLOW': 50,
                'Total_Return': 0.45
            },
            {
                'Ticker': 'ETH-USD',
                'Strategy': 'SMA',
                'SMA_FAST': 20,
                'SMA_SLOW': 50,
                'Total_Return': 0.38
            }
        ]
        
        request_data = {
            "ticker": ["BTC-USD", "ETH-USD"],
            "strategy_types": ["SMA"]
        }
        
        response = client.post("/api/ma-cross/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["portfolios"]) == 2
        tickers = [p["ticker"] for p in data["portfolios"]]
        assert "BTC-USD" in tickers
        assert "ETH-USD" in tickers
    
    def test_error_handling(self, client):
        """Test API error handling."""
        # Test with invalid ticker format
        request_data = {
            "ticker": "",  # Empty ticker
            "windows": 8
        }
        
        response = client.post("/api/ma-cross/analyze", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_default_parameters(self, client, mock_strategy_execution):
        """Test analysis with default parameters."""
        request_data = {
            "ticker": "BTC-USD"
            # No other parameters - should use defaults
        }
        
        response = client.post("/api/ma-cross/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should use default strategy types
        assert data["strategy_types"] == ["SMA", "EMA"]
        assert data["windows"] == 252  # Default
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_client, mock_strategy_execution):
        """Test handling of concurrent analysis requests."""
        # Create multiple concurrent requests
        requests = [
            {"ticker": f"TICKER{i}", "windows": 8, "async_execution": True}
            for i in range(5)
        ]
        
        # Send all requests concurrently
        tasks = [
            async_client.post("/api/ma-cross/analyze", json=req)
            for req in requests
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        
        # All should have unique execution IDs
        execution_ids = [r.json()["execution_id"] for r in responses]
        assert len(set(execution_ids)) == 5  # All unique
    
    def test_csv_export_verification(self, client, mock_strategy_execution):
        """Test that CSV exports are reported correctly."""
        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=['BTC-USD_D_SMA.csv']):
            
            request_data = {
                "ticker": "BTC-USD",
                "strategy_types": ["SMA"]
            }
            
            response = client.post("/api/ma-cross/analyze", json=request_data)
            data = response.json()
            
            assert "portfolio_exports" in data
            assert "portfolios" in data["portfolio_exports"]
            assert len(data["portfolio_exports"]["portfolios"]) > 0


class TestMACrossAPIEdgeCases:
    """Test edge cases and error scenarios."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_invalid_strategy_type(self, client):
        """Test with invalid strategy type."""
        request_data = {
            "ticker": "BTC-USD",
            "strategy_types": ["INVALID"]
        }
        
        response = client.post("/api/ma-cross/analyze", json=request_data)
        
        # Should either validate or handle gracefully
        assert response.status_code in [200, 422]
    
    def test_extremely_large_window(self, client):
        """Test with very large window parameter."""
        request_data = {
            "ticker": "BTC-USD",
            "windows": 10000  # Very large
        }
        
        response = client.post("/api/ma-cross/analyze", json=request_data)
        
        # Should handle gracefully
        assert response.status_code in [200, 422]
    
    def test_nonexistent_execution_id(self, client):
        """Test status check for non-existent execution."""
        response = client.get("/api/ma-cross/status/nonexistent-id-12345")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Execution not found"
    
    def test_special_characters_in_ticker(self, client):
        """Test tickers with special characters."""
        request_data = {
            "ticker": "BTC-USD",  # Hyphen is valid
            "windows": 8
        }
        
        response = client.post("/api/ma-cross/analyze", json=request_data)
        assert response.status_code == 200
    
    def test_timeout_handling(self, client):
        """Test handling of long-running analyses."""
        with patch('app.api.services.ma_cross_service.execute_strategy') as mock:
            # Simulate slow execution
            def slow_execution(*args, **kwargs):
                time.sleep(2)  # Simulate delay
                return []
            
            mock.side_effect = slow_execution
            
            request_data = {
                "ticker": "BTC-USD",
                "async_execution": True  # Use async to avoid blocking
            }
            
            response = client.post("/api/ma-cross/analyze", json=request_data)
            
            assert response.status_code == 200
            assert response.json()["message"] == "Analysis started"


class TestMACrossAPIPerformance:
    """Performance-related tests."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_response_time(self, client):
        """Test API response time is reasonable."""
        with patch('app.api.services.ma_cross_service.execute_strategy') as mock:
            mock.return_value = []
            
            start_time = time.time()
            
            request_data = {
                "ticker": "BTC-USD",
                "windows": 8
            }
            
            response = client.post("/api/ma-cross/analyze", json=request_data)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 5.0  # Should respond within 5 seconds
    
    def test_large_portfolio_serialization(self, client):
        """Test serialization of large portfolio results."""
        with patch('app.api.services.ma_cross_service.execute_strategy') as mock:
            # Create many portfolio results
            large_results = [
                {
                    'Ticker': f'TICKER{i}',
                    'Strategy': 'SMA',
                    'SMA_FAST': 20,
                    'SMA_SLOW': 50,
                    'Total_Return': 0.1 * i,
                    'Sharpe_Ratio': 1.0 + (i * 0.1),
                    'Max_Drawdown': -0.1,
                    'Win_Rate': 0.5 + (i * 0.01),
                    'Num_Trades': 20 + i
                }
                for i in range(100)  # 100 portfolios
            ]
            
            mock.return_value = large_results
            
            request_data = {
                "ticker": [f"TICKER{i}" for i in range(100)],
                "windows": 8
            }
            
            response = client.post("/api/ma-cross/analyze", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["portfolios"]) == 100
            
            # Verify data integrity
            for i, portfolio in enumerate(data["portfolios"]):
                assert portfolio["ticker"] == f"TICKER{i}"
                assert portfolio["total_return"] == pytest.approx(0.1 * i)