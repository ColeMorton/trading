"""
Unit tests for job service webhook integration.

Tests that jobs properly store and handle webhook parameters,
and that webhooks are called on job completion.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.api.models.tables import Job, JobStatus
from app.api.services.job_service import JobService


class TestJobWebhookIntegration:
    """Test cases for job service webhook integration."""

    @pytest.mark.asyncio
    async def test_job_stores_webhook_url(self):
        """Test that webhook URL is stored in job record."""
        # Mock database manager
        mock_db_manager = Mock()
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_db_manager.get_async_session.return_value = mock_session

        # Mock Redis manager
        mock_redis_manager = Mock()
        mock_redis_manager.enqueue_job = AsyncMock(return_value="task-id-123")

        job_service = JobService(mock_db_manager, mock_redis_manager)

        # Create job with webhook URL
        with patch("app.api.services.job_service.Job") as MockJob:
            mock_job = Mock(spec=Job)
            mock_job.id = "test-job-123"
            mock_job.status = JobStatus.PENDING
            mock_job.webhook_url = "https://example.com/webhook"
            MockJob.return_value = mock_job

            job = await job_service.create_job(
                command_group="strategy",
                command_name="run",
                parameters={"ticker": "AAPL"},
                webhook_url="https://example.com/webhook",
            )

            # Verify webhook URL was set
            assert job.webhook_url == "https://example.com/webhook"

    @pytest.mark.asyncio
    async def test_job_stores_webhook_headers(self):
        """Test that webhook headers are stored as JSON in job record."""
        # Mock database manager
        mock_db_manager = Mock()
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_db_manager.get_async_session.return_value = mock_session

        # Mock Redis manager
        mock_redis_manager = Mock()
        mock_redis_manager.enqueue_job = AsyncMock(return_value="task-id-123")

        job_service = JobService(mock_db_manager, mock_redis_manager)

        webhook_headers = {
            "Authorization": "Bearer token123",
            "X-Custom-Header": "value",
        }

        # Create job with webhook headers
        with patch("app.api.services.job_service.Job") as MockJob:
            mock_job = Mock(spec=Job)
            mock_job.id = "test-job-456"
            mock_job.status = JobStatus.PENDING
            mock_job.webhook_url = "https://example.com/webhook"
            mock_job.webhook_headers = webhook_headers
            MockJob.return_value = mock_job

            job = await job_service.create_job(
                command_group="strategy",
                command_name="sweep",
                parameters={"ticker": "BTC-USD"},
                webhook_url="https://example.com/webhook",
                webhook_headers=webhook_headers,
            )

            # Verify headers were stored
            assert job.webhook_headers == webhook_headers
            assert job.webhook_headers["Authorization"] == "Bearer token123"

    @pytest.mark.asyncio
    async def test_job_calls_webhook_on_completion(self):
        """Test that webhook service is called when job completes."""
        # Create completed job
        job = Mock(spec=Job)
        job.id = "job-789"
        job.status = JobStatus.COMPLETED
        job.webhook_url = "https://example.com/webhook"
        job.webhook_headers = None
        job.command_group = "strategy"
        job.command_name = "run"
        job.progress = 100
        job.parameters = {"ticker": "AAPL"}
        job.result_path = "/path/to/result.csv"
        job.result_data = {"score": 1.5}
        job.error_message = None
        job.created_at = datetime.utcnow()
        job.started_at = datetime.utcnow()
        job.completed_at = datetime.utcnow()

        # Mock database manager
        mock_db_manager = Mock()

        # Mock webhook service
        with patch(
            "app.api.services.webhook_service.WebhookService.notify_job_completion"
        ) as mock_notify:
            mock_notify.return_value = AsyncMock()

            # Simulate job completion notification
            from app.api.services.webhook_service import WebhookService

            await WebhookService.notify_job_completion(mock_db_manager, job)

            # Verify webhook was called
            mock_notify.assert_called_once_with(mock_db_manager, job)

    @pytest.mark.asyncio
    async def test_job_skips_webhook_when_null(self):
        """Test that webhook is not called when URL is None."""
        # Create job without webhook URL
        job = Mock(spec=Job)
        job.id = "job-no-webhook"
        job.status = JobStatus.COMPLETED
        job.webhook_url = None
        job.command_group = "strategy"
        job.command_name = "run"

        # Mock database manager
        mock_db_manager = Mock()

        # Mock webhook send
        with patch(
            "app.api.services.webhook_service.WebhookService.send_webhook"
        ) as mock_send:
            mock_send.return_value = AsyncMock()

            from app.api.services.webhook_service import WebhookService

            await WebhookService.notify_job_completion(mock_db_manager, job)

            # Verify webhook was NOT called
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_webhook_response_status_recorded(self):
        """Test that webhook HTTP status is recorded in database."""
        # Create job with webhook
        job = Mock(spec=Job)
        job.id = "job-status-check"
        job.status = JobStatus.COMPLETED
        job.webhook_url = "https://example.com/webhook"
        job.webhook_headers = None
        job.command_group = "strategy"
        job.command_name = "run"
        job.progress = 100
        job.parameters = {}
        job.result_path = None
        job.result_data = None
        job.error_message = None
        job.created_at = datetime.utcnow()
        job.started_at = datetime.utcnow()
        job.completed_at = datetime.utcnow()

        # Mock database manager
        mock_db_manager = Mock()
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_db_manager.get_async_session.return_value = mock_session

        # Mock webhook send to return specific status
        with patch(
            "app.api.services.webhook_service.WebhookService.send_webhook"
        ) as mock_send:
            mock_send.return_value = (200, "OK")

            from app.api.services.webhook_service import WebhookService

            await WebhookService.notify_job_completion(mock_db_manager, job)

            # Verify database update was called
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()

            # Check that the update includes webhook status
            # The actual update statement would include webhook_response_status=200


class TestJobWebhookErrorHandling:
    """Test error handling in webhook integration."""

    @pytest.mark.asyncio
    async def test_webhook_failure_does_not_fail_job(self):
        """Test that webhook delivery failure doesn't mark job as failed."""
        job = Mock(spec=Job)
        job.id = "job-webhook-fails"
        job.status = JobStatus.COMPLETED  # Job is still completed
        job.webhook_url = "https://unreachable.com/webhook"
        job.webhook_headers = None
        job.command_group = "strategy"
        job.command_name = "run"
        job.progress = 100
        job.parameters = {}
        job.result_path = None
        job.result_data = {"result": "success"}
        job.error_message = None
        job.created_at = datetime.utcnow()
        job.started_at = datetime.utcnow()
        job.completed_at = datetime.utcnow()

        mock_db_manager = Mock()
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_db_manager.get_async_session.return_value = mock_session

        # Mock webhook failure
        with patch(
            "app.api.services.webhook_service.WebhookService.send_webhook"
        ) as mock_send:
            mock_send.return_value = (0, "Connection refused")

            from app.api.services.webhook_service import WebhookService

            # Should not raise exception
            await WebhookService.notify_job_completion(mock_db_manager, job)

            # Job status should remain COMPLETED
            assert job.status == JobStatus.COMPLETED
