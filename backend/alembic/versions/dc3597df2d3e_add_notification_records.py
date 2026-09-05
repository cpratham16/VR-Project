"""add_notification_records

Revision ID: dc3597df2d3e
Revises: a6aceed8966b
Create Date: 2026-08-25 03:43:52.042972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc3597df2d3e'
down_revision: Union[str, None] = 'a6aceed8966b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('notification_records',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('alert_id', sa.UUID(), nullable=False),
    sa.Column('recipient_type', sa.String(), nullable=False),
    sa.Column('recipient_label', sa.String(), nullable=True),
    sa.Column('channel', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('content_preview', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['alert_id'], ['risk_alerts.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('notification_records')
    # ### end Alembic commands ###
