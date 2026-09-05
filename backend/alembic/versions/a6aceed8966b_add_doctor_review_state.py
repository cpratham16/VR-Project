"""add_doctor_review_state

Revision ID: a6aceed8966b
Revises: d32bf4f05877
Create Date: 2026-08-25 02:55:25.736917

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6aceed8966b'
down_revision: Union[str, None] = 'd32bf4f05877'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('doctor_profiles', sa.Column('review_status', sa.String(), server_default='pending', nullable=False))
    op.add_column('doctor_profiles', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('doctor_profiles', sa.Column('reviewed_by_admin_id', sa.UUID(), nullable=True))
    op.add_column('doctor_profiles', sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    op.create_foreign_key(None, 'doctor_profiles', 'users', ['reviewed_by_admin_id'], ['id'])
    op.execute("""
        UPDATE doctor_profiles dp
        SET review_status = 'approved', reviewed_at = COALESCE(dp.reviewed_at, NOW())
        FROM users u
        WHERE dp.user_id = u.id AND u.is_verified = true
    """)


def downgrade() -> None:
    op.drop_constraint(None, 'doctor_profiles', type_='foreignkey')
    op.drop_column('doctor_profiles', 'reviewed_at')
    op.drop_column('doctor_profiles', 'reviewed_by_admin_id')
    op.drop_column('doctor_profiles', 'rejection_reason')
    op.drop_column('doctor_profiles', 'review_status')
    # ### end Alembic commands ###
