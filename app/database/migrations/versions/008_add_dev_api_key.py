"""Add development API key.

Revision ID: 008
Revises: 007
Create Date: 2025-10-30

"""

from alembic import op


# revision identifiers
revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add development API key for local development."""
    # Insert development API key only in development environments
    # This key_hash corresponds to 'dev-key-' + '0' * 24
    # The hash is generated using bcrypt.hashpw(b"dev-key-000000000000000000000000", bcrypt.gensalt())
    op.execute(
        """
        INSERT INTO api_keys (id, key_hash, name, scopes, rate_limit, is_active, created_at)
        VALUES (
            '00000000-0000-0000-0000-000000000000'::uuid,
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/.pN0jC1kO1gGz6wE6',
            'Development Key',
            '["*"]'::json,
            10000,
            true,
            now()
        )
        ON CONFLICT (id) DO NOTHING;
        """
    )


def downgrade() -> None:
    """Remove development API key."""
    op.execute(
        "DELETE FROM api_keys WHERE id = '00000000-0000-0000-0000-000000000000'::uuid"
    )
