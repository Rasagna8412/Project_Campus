"""milestone 7 spaced repetition review items and logs

Revision ID: 0cbebed2ada2
Revises: 7d1a2b3c4e5f
Create Date: 2026-10-19 09:07:06.780005

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0cbebed2ada2'
down_revision: Union[str, None] = '7d1a2b3c4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create review_items table
    op.create_table(
        'review_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('topic_id', sa.Uuid(), nullable=False),
        sa.Column('subject_id', sa.Uuid(), nullable=False),
        sa.Column('repetition_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ease_factor', sa.Float(), nullable=False, server_default='2.50'),
        sa.Column('interval_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='LEARNING'),
        sa.Column('last_reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('review_items', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_review_items_user_topic', ['user_id', 'topic_id'])
        batch_op.create_index('idx_review_items_user_due', ['user_id', 'due_date', 'status'], unique=False)
        batch_op.create_index('idx_review_items_user_subject', ['user_id', 'subject_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_review_items_due_date'), ['due_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_review_items_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_review_items_subject_id'), ['subject_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_review_items_topic_id'), ['topic_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_review_items_user_id'), ['user_id'], unique=False)

    # 2. Create review_logs table
    op.create_table(
        'review_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('review_item_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('quality_score', sa.Integer(), nullable=False),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('scheduled_interval_days', sa.Integer(), nullable=False),
        sa.Column('next_interval_days', sa.Integer(), nullable=False),
        sa.Column('ease_factor_before', sa.Float(), nullable=False),
        sa.Column('ease_factor_after', sa.Float(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['review_item_id'], ['review_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('review_logs', schema=None) as batch_op:
        batch_op.create_index('idx_review_logs_user_reviewed', ['user_id', 'reviewed_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_review_logs_review_item_id'), ['review_item_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_review_logs_user_id'), ['user_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('review_logs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_review_logs_user_id'))
        batch_op.drop_index(batch_op.f('ix_review_logs_review_item_id'))
        batch_op.drop_index('idx_review_logs_user_reviewed')

    op.drop_table('review_logs')

    with op.batch_alter_table('review_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_review_items_user_id'))
        batch_op.drop_index(batch_op.f('ix_review_items_topic_id'))
        batch_op.drop_index(batch_op.f('ix_review_items_subject_id'))
        batch_op.drop_index(batch_op.f('ix_review_items_status'))
        batch_op.drop_index(batch_op.f('ix_review_items_due_date'))
        batch_op.drop_index('idx_review_items_user_subject')
        batch_op.drop_index('idx_review_items_user_due')
        batch_op.drop_constraint('uq_review_items_user_topic', type_='unique')

    op.drop_table('review_items')
