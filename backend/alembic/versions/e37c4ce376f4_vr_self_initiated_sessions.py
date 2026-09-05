"""vr_self_initiated_sessions

Revision ID: e37c4ce376f4
Revises: dc3597df2d3e
Create Date: 2026-08-25 04:20:01.161352

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e37c4ce376f4'
down_revision: Union[str, None] = 'dc3597df2d3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('vr_sessions', sa.Column('source', sa.String(), server_default='assigned', nullable=False))
    op.alter_column('vr_sessions', 'doctor_id',
               existing_type=sa.UUID(),
               nullable=True)


def downgrade() -> None:
    op.execute("DELETE FROM vr_sessions WHERE doctor_id IS NULL")
    op.alter_column('vr_sessions', 'doctor_id',
               existing_type=sa.UUID(),
               nullable=False)
    op.drop_column('vr_sessions', 'source')
