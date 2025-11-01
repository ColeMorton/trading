"""
Webhook notification service for job completion callbacks.
"""

import logging
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import update

from ..models.tables import Job


logger = logging.getLogger(__name__)


class WebhookService:
    """Service for sending webhook notifications."""

    @staticmethod
    async def send_webhook(
        job_id: str,
        webhook_url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> tuple[int, str]:
        """
        Send webhook notification with retry logic.

        Args:
            job_id: Job identifier
            webhook_url: Target webhook URL
            payload: JSON payload to send
            headers: Optional custom headers
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts

        Returns:
            Tuple of (status_code, response_text)
        """
        import asyncio

        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "TradingAPI-Webhook/1.0",
            "X-Job-ID": job_id,
        }

        if headers:
            default_headers.update(headers)

        last_error = None
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    if attempt > 0:
                        logger.info(
                            f"Retry attempt {attempt + 1}/{max_retries} for job {job_id} webhook to {webhook_url}"
                        )
                    else:
                        logger.info(
                            f"Sending webhook for job {job_id} to {webhook_url} "
                            f"(payload keys: {list(payload.keys())})"
                        )

                    response = await client.post(
                        webhook_url,
                        json=payload,
                        headers=default_headers,
                    )

                    logger.info(
                        f"Webhook delivered successfully for job {job_id}: "
                        f"status={response.status_code}, response_length={len(response.text)}"
                    )

                    return response.status_code, response.text

            except httpx.ConnectError as e:
                last_error = e
                logger.warning(
                    f"Webhook connection failed for job {job_id} (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    backoff_delay = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.info(f"Retrying in {backoff_delay}s...")
                    await asyncio.sleep(backoff_delay)
                else:
                    logger.error(
                        f"Webhook connection failed after {max_retries} attempts for job {job_id} to {webhook_url}: {e}. "
                        f"If using Docker, ensure 'host.docker.internal' is configured.",
                        exc_info=True,
                    )
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    f"Webhook timeout for job {job_id} (attempt {attempt + 1}/{max_retries})"
                )
                if attempt < max_retries - 1:
                    backoff_delay = 2**attempt
                    logger.info(f"Retrying in {backoff_delay}s...")
                    await asyncio.sleep(backoff_delay)
                else:
                    logger.error(
                        f"Webhook timeout after {max_retries} attempts for job {job_id} to {webhook_url}",
                        exc_info=True,
                    )
            except Exception as e:
                last_error = e
                logger.error(
                    f"Webhook error for job {job_id} (attempt {attempt + 1}/{max_retries}): {e}",
                    exc_info=True,
                )
                if attempt < max_retries - 1:
                    backoff_delay = 2**attempt
                    logger.info(f"Retrying in {backoff_delay}s...")
                    await asyncio.sleep(backoff_delay)

        # All retries failed
        error_msg = str(last_error) if last_error else "Unknown error"
        if isinstance(last_error, httpx.ConnectError):
            return 0, f"connection_error: {error_msg}"
        if isinstance(last_error, httpx.TimeoutException):
            return 0, "timeout"
        return 0, error_msg

    @staticmethod
    async def notify_job_completion(
        db_manager,
        job: Job,
    ) -> None:
        """
        Send webhook notification when job completes.

        Args:
            db_manager: Database manager
            job: Job model instance
        """
        import logging

        logger = logging.getLogger(__name__)

        if not job.webhook_url:
            return

        logger.info(f"Sending webhook for job {job.id} to {job.webhook_url}")

        # Build webhook payload
        payload = {
            "job_id": str(job.id),
            "status": job.status,
            "command_group": job.command_group,
            "command_name": job.command_name,
            "progress": job.progress,
            "parameters": job.parameters,
            "result_path": job.result_path,
            "result_data": job.result_data,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "webhook_sent_at": datetime.utcnow().isoformat(),
        }

        # Send webhook (non-blocking)
        status_code, _response_text = await WebhookService.send_webhook(
            job_id=str(job.id),
            webhook_url=job.webhook_url,
            payload=payload,
            headers=job.webhook_headers,
        )

        logger.info(f"Webhook for job {job.id} completed with status {status_code}")

        # Update job record with webhook delivery status
        async with db_manager.get_async_session() as session:
            await session.execute(
                update(Job)
                .where(Job.id == job.id)
                .values(
                    webhook_sent_at=datetime.utcnow(),
                    webhook_response_status=status_code,
                ),
            )
            await session.commit()
