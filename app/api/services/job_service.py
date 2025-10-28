"""
Job management service for creating, updating, and querying jobs.
"""

from datetime import datetime, timedelta
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.schemas import JobUpdate
from ..models.tables import Job, JobStatus


class JobService:
    """Service for managing job records."""

    @staticmethod
    async def create_job(
        db: AsyncSession,
        api_key_id: str,
        command_group: str,
        command_name: str,
        parameters: dict,
        webhook_url: str | None = None,
        webhook_headers: dict | None = None,
    ) -> Job:
        """
        Create a new job record.

        Args:
            db: Database session
            api_key_id: API key identifier
            command_group: Command group name
            command_name: Command name
            parameters: Job parameters
            webhook_url: Optional webhook URL for completion notification
            webhook_headers: Optional custom headers for webhook

        Returns:
            Created job model
        """
        job = Job(
            id=uuid.uuid4(),
            api_key_id=(
                api_key_id
                if isinstance(api_key_id, uuid.UUID)
                else uuid.UUID(api_key_id)
            ),
            command_group=command_group,
            command_name=command_name,
            status=JobStatus.PENDING.value,
            parameters=parameters,
            created_at=datetime.utcnow(),
            webhook_url=webhook_url,
            webhook_headers=webhook_headers,
        )

        db.add(job)
        await db.commit()
        await db.refresh(job)

        return job

    @staticmethod
    async def get_job(db: AsyncSession, job_id: str) -> Job | None:
        """
        Get job by ID.

        Args:
            db: Database session
            job_id: Job identifier

        Returns:
            Job model or None
        """
        result = await db.execute(select(Job).where(Job.id == uuid.UUID(job_id)))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_job(
        db: AsyncSession,
        job_id: str,
        update: JobUpdate,
    ) -> Job | None:
        """
        Update job with new data.

        Args:
            db: Database session
            job_id: Job identifier
            update: Update data

        Returns:
            Updated job model or None
        """
        job = await JobService.get_job(db, job_id)
        if not job:
            return None

        # Update fields
        update_data = update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)

        await db.commit()
        await db.refresh(job)

        return job

    @staticmethod
    async def list_jobs(
        db: AsyncSession,
        api_key_id: str | None = None,
        status: JobStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        """
        List jobs with optional filtering.

        Args:
            db: Database session
            api_key_id: Filter by API key
            status: Filter by status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of job models
        """
        query = select(Job).order_by(Job.created_at.desc())

        if api_key_id:
            query = query.where(
                Job.api_key_id
                == (
                    api_key_id
                    if isinstance(api_key_id, uuid.UUID)
                    else uuid.UUID(api_key_id)
                ),
            )

        if status:
            query = query.where(Job.status == status.value)

        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def cancel_job(db: AsyncSession, job_id: str) -> Job | None:
        """
        Cancel a job.

        Args:
            db: Database session
            job_id: Job identifier

        Returns:
            Updated job model or None
        """
        update = JobUpdate(status=JobStatus.CANCELLED, completed_at=datetime.utcnow())
        return await JobService.update_job(db, job_id, update)

    @staticmethod
    async def cleanup_old_jobs(db: AsyncSession) -> int:
        """
        Clean up old completed jobs.

        Args:
            db: Database session

        Returns:
            Number of jobs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=settings.JOB_CLEANUP_DAYS)

        result = await db.execute(
            select(Job).where(
                Job.completed_at < cutoff_date,
                Job.status.in_(
                    [
                        JobStatus.COMPLETED.value,
                        JobStatus.FAILED.value,
                        JobStatus.CANCELLED.value,
                    ],
                ),
            ),
        )

        jobs_to_delete = list(result.scalars().all())
        count = len(jobs_to_delete)

        for job in jobs_to_delete:
            await db.delete(job)

        await db.commit()

        return count
