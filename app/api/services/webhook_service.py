"""
Webhook notification service for job completion callbacks.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.tables import Job, JobStatus

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
    ) -> tuple[int, str]:
        """
        Send webhook notification.

        Args:
            job_id: Job identifier
            webhook_url: Target webhook URL
            payload: JSON payload to send
            headers: Optional custom headers
            timeout: Request timeout in seconds

        Returns:
            Tuple of (status_code, response_text)
        """
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "TradingAPI-Webhook/1.0",
            "X-Job-ID": job_id,
        }

        if headers:
            default_headers.update(headers)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(f"Sending webhook for job {job_id} to {webhook_url}")
                
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers=default_headers,
                )
                
                logger.info(
                    f"Webhook sent for job {job_id}: "
                    f"status={response.status_code}"
                )
                
                return response.status_code, response.text

        except httpx.TimeoutException:
            logger.error(f"Webhook timeout for job {job_id} to {webhook_url}")
            return 0, "timeout"
        except Exception as e:
            logger.error(
                f"Webhook error for job {job_id}: {e}",
                exc_info=True
            )
            return 0, str(e)

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
        if not job.webhook_url:
            return

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
        status_code, response_text = await WebhookService.send_webhook(
            job_id=str(job.id),
            webhook_url=job.webhook_url,
            payload=payload,
            headers=job.webhook_headers,
        )

        # Update job record with webhook delivery status
        async with db_manager.get_async_session() as session:
            await session.execute(
                update(Job)
                .where(Job.id == job.id)
                .values(
                    webhook_sent_at=datetime.utcnow(),
                    webhook_response_status=status_code,
                )
            )
            await session.commit()

