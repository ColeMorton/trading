"""
Database table models using SQLModel.

This module defines the database tables as SQLModel classes,
combining SQLAlchemy ORM with Pydantic validation.
"""

from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class APIKey(SQLModel, table=True):
    """API key database table."""

    __tablename__ = "api_keys"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    key_hash: str = Field(max_length=255, unique=True, index=True)
    name: str = Field(max_length=255)
    scopes: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    rate_limit: int = Field(default=60)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: datetime | None = None

    def __repr__(self) -> str:
        return f"<APIKey(name={self.name}, scopes={self.scopes}, is_active={self.is_active})>"


class Job(SQLModel, table=True):
    """Job tracking database table."""

    __tablename__ = "jobs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    api_key_id: uuid.UUID = Field(foreign_key="api_keys.id", index=True)
    command_group: str = Field(max_length=50)
    command_name: str = Field(max_length=50)
    status: str = Field(default=JobStatus.PENDING.value, index=True, max_length=20)
    progress: int = Field(default=0, ge=0, le=100)
    parameters: dict = Field(default_factory=dict, sa_column=Column(JSON))
    result_path: str | None = Field(default=None, max_length=500)
    result_data: dict | None = Field(default=None, sa_column=Column(JSON))
    error_message: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    webhook_url: str | None = Field(default=None, max_length=500)
    webhook_headers: dict | None = Field(default=None, sa_column=Column(JSON))
    webhook_sent_at: datetime | None = None
    webhook_response_status: int | None = None

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, command={self.command_group}.{self.command_name}, status={self.status})>"
