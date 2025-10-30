"""Create API keys and jobs tables.

Revision ID: 001
Revises:
Create Date: 2025-10-19

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create api_keys table
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key_hash", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("scopes", postgresql.JSON, nullable=False),
        sa.Column("rate_limit", sa.Integer, nullable=False, default=60),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("last_used_at", sa.DateTime, nullable=True),
    )

    # Create jobs table
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("command_group", sa.String(50), nullable=False),
        sa.Column("command_name", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("progress", sa.Integer, nullable=False, default=0),
        sa.Column("parameters", postgresql.JSON, nullable=False),
        sa.Column("result_path", sa.String(500), nullable=True),
        sa.Column("result_data", postgresql.JSON, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.ForeignKeyConstraint(["api_key_id"], ["api_keys.id"], ondelete="CASCADE"),
    )

    # Create indexes
    op.create_index("ix_jobs_api_key_created", "jobs", ["api_key_id", "created_at"])
    op.create_index("ix_jobs_status_created", "jobs", ["status", "created_at"])


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index("ix_jobs_status_created", table_name="jobs")
    op.drop_index("ix_jobs_api_key_created", table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("api_keys")
