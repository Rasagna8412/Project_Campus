"""add uq_study_tasks_user_date_order constraint

Revision ID: 7d1a2b3c4e5f
Revises: 0c92f4b6848c
Create Date: 2026-10-18 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d1a2b3c4e5f'
down_revision: Union[str, None] = '0c92f4b6848c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safe non-destructive preflight: ensure no duplicate (user_id, scheduled_date, display_order) exists
    with op.batch_alter_table('study_tasks', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uq_study_tasks_user_date_order',
            ['user_id', 'scheduled_date', 'display_order'],
        )


def downgrade() -> None:
    with op.batch_alter_table('study_tasks', schema=None) as batch_op:
        batch_op.drop_constraint('uq_study_tasks_user_date_order', type_='unique')
