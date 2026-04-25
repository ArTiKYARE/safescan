"""add celery_task_id to scans

Revision ID: 003_add_celery_task_id
Revises: 002_add_user_settings
Create Date: 2026-04-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_celery_task_id'
down_revision: Union[str, None] = '002_add_user_settings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('scans', sa.Column('celery_task_id', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('scans', 'celery_task_id')
