"""milestone d ai tutor and subscriptions

Revision ID: 0d1a2b3c4e5f
Revises: 0cbebed2ada2
Create Date: 2026-10-22 13:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d1a2b3c4e5f'
down_revision: Union[str, None] = '0cbebed2ada2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create ai_tutor_interactions table
    op.create_table(
        'ai_tutor_interactions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('lesson_id', sa.Uuid(), nullable=True),
        sa.Column('mode', sa.String(length=50), nullable=False, server_default='EXPLAIN'),
        sa.Column('user_query', sa.Text(), nullable=False),
        sa.Column('tutor_response', sa.Text(), nullable=False),
        sa.Column('grounding_sources', sa.Text(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('ai_tutor_interactions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ai_tutor_interactions_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_ai_tutor_interactions_lesson_id'), ['lesson_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_ai_tutor_interactions_created_at'), ['created_at'], unique=False)

    # 2. Create student_subscriptions table
    op.create_table(
        'student_subscriptions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('tier', sa.String(length=20), nullable=False, server_default='FREE'),
        sa.Column('daily_tutor_quota', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('student_subscriptions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_student_subscriptions_user_id'), ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_table('student_subscriptions')
    op.drop_table('ai_tutor_interactions')
