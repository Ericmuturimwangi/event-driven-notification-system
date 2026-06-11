"""add dlq replay and resolution tracking columns

Revision ID: bc5f9065b6ca
Revises: 2bef99e94736
Create Date: 2026-06-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc5f9065b6ca'
down_revision: Union[str, Sequence[str], None] = '2bef99e94736'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('failed_events', sa.Column('replayed_at', sa.DateTime(), nullable=True))
    op.add_column('failed_events', sa.Column('replay_event_id', sa.UUID(), nullable=True))
    op.add_column('failed_events', sa.Column('resolved_at', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_failed_events_resolved_at'), 'failed_events', ['resolved_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_failed_events_resolved_at'), table_name='failed_events')
    op.drop_column('failed_events', 'resolved_at')
    op.drop_column('failed_events', 'replay_event_id')
    op.drop_column('failed_events', 'replayed_at')
