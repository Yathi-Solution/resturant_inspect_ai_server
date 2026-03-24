"""create restaurants table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-24 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create restaurants table
    op.create_table(
        'restaurants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create index on restaurant name for faster lookups
    op.create_index('ix_restaurants_name', 'restaurants', ['name'])
    
    # Insert default restaurant "Niloufer"
    op.execute("""
        INSERT INTO restaurants (name, address) 
        VALUES ('Niloufer', 'Hyderabad, India')
    """)
    
    # Add restaurant_id column to reviews table
    op.add_column('reviews', sa.Column('restaurant_id', sa.Integer(), nullable=True))
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_reviews_restaurant_id',
        'reviews', 'restaurants',
        ['restaurant_id'], ['id']
    )
    
    # Migrate existing data: set restaurant_id based on restaurant_name
    op.execute("""
        UPDATE reviews 
        SET restaurant_id = (SELECT id FROM restaurants WHERE name = 'Niloufer')
        WHERE restaurant_name = 'Niloufer' OR restaurant_name = 'Demo Restaurant' OR restaurant_name IS NULL
    """)
    
    # Make restaurant_id NOT NULL after migration
    op.alter_column('reviews', 'restaurant_id', nullable=False)


def downgrade() -> None:
    # Remove foreign key
    op.drop_constraint('fk_reviews_restaurant_id', 'reviews', type_='foreignkey')
    
    # Drop restaurant_id column
    op.drop_column('reviews', 'restaurant_id')
    
    # Drop restaurants table
    op.drop_index('ix_restaurants_name', 'restaurants')
    op.drop_table('restaurants')
