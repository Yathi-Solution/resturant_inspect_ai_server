"""remove restaurant_name column from reviews

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-24 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the deprecated restaurant_name column from reviews table
    # We now use restaurant_id foreign key instead
    op.drop_column('reviews', 'restaurant_name')


def downgrade() -> None:
    # Re-add restaurant_name column if we need to rollback
    op.add_column('reviews', sa.Column('restaurant_name', sa.String(length=255), nullable=True))
