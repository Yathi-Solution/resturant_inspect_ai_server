"""create reviews and review annotations tables

Revision ID: 20260323_0001
Revises:
Create Date: 2026-03-23 00:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260323_0001"
down_revision = None
branch_labels = None
depends_on = None


aspect_state = postgresql.ENUM(
    "positive",
    "negative",
    "mixed",
    "not_mentioned",
    name="aspect_state",
    create_type=False,
)

annotation_status = postgresql.ENUM(
    "draft",
    "reviewed",
    "approved",
    "rejected",
    name="annotation_status",
    create_type=False,
)

label_source = postgresql.ENUM(
    "heuristic",
    "manual",
    "heuristic_reviewed",
    name="label_source",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    # Clean up stale enum types from failed first-run attempts.
    op.execute("DROP TYPE IF EXISTS label_source")
    op.execute("DROP TYPE IF EXISTS annotation_status")
    op.execute("DROP TYPE IF EXISTS aspect_state")

    aspect_state.create(bind, checkfirst=True)
    annotation_status.create(bind, checkfirst=True)
    label_source.create(bind, checkfirst=True)

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("source_review_id", sa.String(length=255), nullable=True),
        sa.Column("review_text", sa.Text(), nullable=False),
        sa.Column("overall_sentiment", sa.Integer(), nullable=True),
        sa.Column("language_code", sa.String(length=8), nullable=False, server_default="en"),
        sa.Column("business_name", sa.String(length=255), nullable=True),
        sa.Column("business_location", sa.String(length=255), nullable=True),
        sa.Column(
            "ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("idx_reviews_source", "reviews", ["source"])

    op.create_table(
        "review_annotations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "review_id",
            sa.Integer(),
            sa.ForeignKey("reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("food_state", aspect_state, nullable=False),
        sa.Column("service_state", aspect_state, nullable=False),
        sa.Column("hygiene_state", aspect_state, nullable=False),
        sa.Column("parking_state", aspect_state, nullable=False),
        sa.Column("cleanliness_state", aspect_state, nullable=False),
        sa.Column("annotation_status", annotation_status, nullable=False, server_default="draft"),
        sa.Column("label_source", label_source, nullable=False, server_default="heuristic"),
        sa.Column("annotator_name", sa.String(length=100), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Numeric(4, 3), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("idx_review_annotations_review_id", "review_annotations", ["review_id"])
    op.create_index("idx_review_annotations_status", "review_annotations", ["annotation_status"])


def downgrade() -> None:
    op.drop_index("idx_review_annotations_status", table_name="review_annotations")
    op.drop_index("idx_review_annotations_review_id", table_name="review_annotations")
    op.drop_table("review_annotations")

    op.drop_index("idx_reviews_source", table_name="reviews")
    op.drop_table("reviews")

    bind = op.get_bind()
    label_source.drop(bind, checkfirst=True)
    annotation_status.drop(bind, checkfirst=True)
    aspect_state.drop(bind, checkfirst=True)
