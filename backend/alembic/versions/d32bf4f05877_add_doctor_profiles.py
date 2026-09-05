"""add_doctor_profiles

Revision ID: d32bf4f05877
Revises: 70d0ab155a14
Create Date: 2026-08-25 01:53:21.686462

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd32bf4f05877'
down_revision: Union[str, None] = '70d0ab155a14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('doctor_profiles',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('license_number', sa.String(), nullable=False),
    sa.Column('specialty', sa.String(), nullable=True),
    sa.Column('languages', sa.Text(), nullable=False),
    sa.Column('credential_filename', sa.String(), nullable=True),
    sa.Column('credential_path', sa.String(), nullable=True),
    sa.Column('uploaded_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )


def downgrade() -> None:
    op.drop_table('doctor_profiles')
    # ### end Alembic commands ###
