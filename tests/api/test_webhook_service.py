"""
Unit tests for WebhookService.

Tests webhook notification functionality including:
- Successful webhook delivery
- Timeout handling
- Connection error handling
- Custom headers
- Job completion notifications
- Database updates
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from app.api.models.tables import Job, JobStatus
from app.api.services.webhook_service import WebhookService


@pytest.mark.e2e
class TestWebhookService:
    """Test cases for WebhookService."""

    @pytest.mark.asyncio
    async def test_send_webhook_success(self):
        """Test successful webhook delivery with 200 response."""
        job_id = "test-job-123"
        webhook_url = "https://example.com/webhook"
        payload = {"status": "completed", "result": "success"}

        # Mock httpx response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"received": true}'

        with patch("app.api.services.webhook_service.httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_client.return_value = mock_client_instance

            status_code, response_text = await WebhookService.send_webhook(
                job_id=job_id,
                webhook_url=webhook_url,
                payload=payload,
            )

            assert status_code == 200
            assert response_text == '{"received": true}'
            mock_client_instance.post.assert_called_once()

            # Verify headers include job ID
            call_args = mock_client_instance.post.call_args
            headers = call_args.kwargs["headers"]
            assert headers["X-Job-ID"] == job_id
            assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_send_webhook_timeout(self):
        """Test webhook timeout handling."""
        job_id = "test-job-timeout"
        webhook_url = "https://slow-server.com/webhook"
        payload = {"status": "completed"}

        with patch("app.api.services.webhook_service.httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.side_effect = httpx.TimeoutException(
                "Request timeout",
            )
            mock_client.return_value = mock_client_instance

            status_code, response_text = await WebhookService.send_webhook(
                job_id=job_id,
                webhook_url=webhook_url,
                payload=payload,
                timeout=5,
            )

            assert status_code == 0
            assert response_text == "timeout"

    @pytest.mark.asyncio
    async def test_send_webhook_connection_error(self):
        """Test webhook connection error handling."""
        job_id = "test-job-error"
        webhook_url = "https://unreachable.com/webhook"
        payload = {"status": "completed"}

        with patch("app.api.services.webhook_service.httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.side_effect = httpx.ConnectError(
                "Connection refused",
            )
            mock_client.return_value = mock_client_instance

            status_code, response_text = await WebhookService.send_webhook(
                job_id=job_id,
                webhook_url=webhook_url,
                payload=payload,
            )

            assert status_code == 0
            assert "Connection refused" in response_text

    @pytest.mark.asyncio
    async def test_send_webhook_custom_headers(self):
        """Test webhook with custom headers."""
        job_id = "test-job-headers"
        webhook_url = "https://example.com/webhook"
        payload = {"status": "completed"}
        custom_headers = {
            "Authorization": "Bearer token123",
            "X-Custom-Header": "custom-value",
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        with patch("app.api.services.webhook_service.httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_client.return_value = mock_client_instance

            await WebhookService.send_webhook(
                job_id=job_id,
                webhook_url=webhook_url,
                payload=payload,
                headers=custom_headers,
            )

            # Verify custom headers were merged
            call_args = mock_client_instance.post.call_args
            headers = call_args.kwargs["headers"]
            assert headers["Authorization"] == "Bearer token123"
            assert headers["X-Custom-Header"] == "custom-value"
            assert headers["X-Job-ID"] == job_id  # Default header still present

    @pytest.mark.asyncio
    async def test_notify_job_completion_with_webhook(self):
        """Test full notification flow with webhook URL."""
        # Create mock job
        job = Mock(spec=Job)
        job.id = "job-123"
        job.status = JobStatus.COMPLETED
        job.command_group = "strategy"
        job.command_name = "run"
        job.progress = 100
        job.parameters = {"ticker": "AAPL"}
        job.result_path = "/path/to/result.csv"
        job.result_data = {"score": 1.5}
        job.error_message = None
        job.created_at = datetime(2025, 1, 1, 10, 0, 0)
        job.started_at = datetime(2025, 1, 1, 10, 0, 5)
        job.completed_at = datetime(2025, 1, 1, 10, 1, 0)
        job.webhook_url = "https://example.com/webhook"
        job.webhook_headers = None

        # Mock database manager
        mock_db_manager = Mock()
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_db_manager.get_async_session.return_value = mock_session

        # Mock webhook send
        with patch.object(
            WebhookService,
            "send_webhook",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = (200, "OK")

            await WebhookService.notify_job_completion(mock_db_manager, job)

            # Verify webhook was sent
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args.kwargs["job_id"] == "job-123"
            assert call_args.kwargs["webhook_url"] == "https://example.com/webhook"

            # Verify payload structure
            payload = call_args.kwargs["payload"]
            assert payload["job_id"] == "job-123"
            assert payload["status"] == JobStatus.COMPLETED
            assert payload["command_group"] == "strategy"
            assert payload["result_data"] == {"score": 1.5}

    @pytest.mark.asyncio
    async def test_notify_job_completion_without_webhook(self):
        """Test notification skips when no webhook URL."""
        # Create mock job without webhook URL
        job = Mock(spec=Job)
        job.id = "job-456"
        job.webhook_url = None

        mock_db_manager = Mock()

        with patch.object(
            WebhookService,
            "send_webhook",
            new_callable=AsyncMock,
        ) as mock_send:
            await WebhookService.notify_job_completion(mock_db_manager, job)

            # Verify webhook was NOT sent
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_job_completion_updates_database(self):
        """Test that job completion updates database with webhook status."""
        # Create mock job
        job = Mock(spec=Job)
        job.id = "job-789"
        job.status = JobStatus.COMPLETED
        job.command_group = "strategy"
        job.command_name = "sweep"
        job.progress = 100
        job.parameters = {}
        job.result_path = None
        job.result_data = None
        job.error_message = None
        job.created_at = datetime.utcnow()
        job.started_at = datetime.utcnow()
        job.completed_at = datetime.utcnow()
        job.webhook_url = "https://example.com/callback"
        job.webhook_headers = {"Authorization": "Bearer token"}

        # Mock database manager
        mock_db_manager = Mock()
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_db_manager.get_async_session.return_value = mock_session

        # Mock webhook send
        with patch.object(
            WebhookService,
            "send_webhook",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = (200, "Success")

            await WebhookService.notify_job_completion(mock_db_manager, job)

            # Verify database update was executed
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()
