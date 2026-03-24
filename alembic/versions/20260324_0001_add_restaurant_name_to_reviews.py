"""add restaurant_name to reviews

Revision ID: a1b2c3d4e5f6
Revises: 5eed963bbc03
Create Date: 2026-03-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5eed963bbc03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add restaurant_name column to reviews table
    op.add_column('reviews', sa.Column('restaurant_name', sa.String(length=255), nullable=True))
    
    # Seed some default restaurant names for existing reviews
    op.execute("UPDATE reviews SET restaurant_name = 'Niloufer' WHERE restaurant_name IS NULL")


def downgrade() -> None:
    op.drop_column('reviews', 'restaurant_name')
