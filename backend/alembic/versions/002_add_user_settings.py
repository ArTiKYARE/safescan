"""Add settings column to users table

Revision ID: 002_add_user_settings
Revises: 001_initial
Create Date: 2026-04-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = '002_add_user_settings'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('settings', postgresql.JSONB(), nullable=True, server_default='{}'),
    )


def downgrade() -> None:
    op.drop_column('users', 'settings')
