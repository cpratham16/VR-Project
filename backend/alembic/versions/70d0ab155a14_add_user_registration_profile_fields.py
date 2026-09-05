"""add_user_registration_profile_fields

Revision ID: 70d0ab155a14
Revises: bc0b86e173a5
Create Date: 2026-08-25 01:34:29.120970

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70d0ab155a14'
down_revision: Union[str, None] = 'bc0b86e173a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('full_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(), nullable=True))
    op.add_column('users', sa.Column('emergency_contact_phone', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'emergency_contact_phone')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'full_name')
    # ### end Alembic commands ###
