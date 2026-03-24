from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import AnnotationStatus, AspectState, LabelSource


def enum_values(enum_cls):
    """Return Enum values for SQLAlchemy enum persistence."""
    return [item.value for item in enum_cls]


class Restaurant(Base):
    """Master restaurant data table."""

    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    reviews: Mapped[list["Review"]] = relationship(
        back_populates="restaurant", cascade="all, delete-orphan"
    )


class Review(Base):
    """Raw review records ingested from external sources."""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_review_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    review_text: Mapped[str] = mapped_column(Text, nullable=False)
    overall_sentiment: Mapped[int | None] = mapped_column(nullable=True)
    language_code: Mapped[str] = mapped_column(String(8), default="en", nullable=False)
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    business_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    restaurant: Mapped["Restaurant"] = relationship(back_populates="reviews")
    annotations: Mapped[list["ReviewAnnotation"]] = relationship(
        back_populates="review", cascade="all, delete-orphan"
    )


class ReviewAnnotation(Base):
    """Aspect-level annotation records for a review."""

    __tablename__ = "review_annotations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False
    )

    food_state: Mapped[AspectState] = mapped_column(
        Enum(AspectState, name="aspect_state", values_callable=enum_values), nullable=False
    )
    service_state: Mapped[AspectState] = mapped_column(
        Enum(AspectState, name="aspect_state", values_callable=enum_values), nullable=False
    )
    hygiene_state: Mapped[AspectState] = mapped_column(
        Enum(AspectState, name="aspect_state", values_callable=enum_values), nullable=False
    )
    parking_state: Mapped[AspectState] = mapped_column(
        Enum(AspectState, name="aspect_state", values_callable=enum_values), nullable=False
    )
    cleanliness_state: Mapped[AspectState] = mapped_column(
        Enum(AspectState, name="aspect_state", values_callable=enum_values), nullable=False
    )

    annotation_status: Mapped[AnnotationStatus] = mapped_column(
        Enum(AnnotationStatus, name="annotation_status", values_callable=enum_values),
        nullable=False,
        default=AnnotationStatus.DRAFT,
    )
    label_source: Mapped[LabelSource] = mapped_column(
        Enum(LabelSource, name="label_source", values_callable=enum_values),
        nullable=False,
        default=LabelSource.HEURISTIC,
    )

    annotator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    reviewer_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    review: Mapped[Review] = relationship(back_populates="annotations")


class TrainingRun(Base):
    """Record of model training runs and evaluation metrics."""

    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    training_samples: Mapped[int] = mapped_column(nullable=False)
    test_accuracy: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    test_f1: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    test_precision: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    test_recall: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    output_path: Mapped[str] = mapped_column(String(512), nullable=False)
    trained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

Index("idx_reviews_restaurant_id", Review.restaurant_id)
Index("ix_restaurants_name", Restaurant.name)

Index("idx_review_annotations_review_id", ReviewAnnotation.review_id)
Index("idx_review_annotations_status", ReviewAnnotation.annotation_status)
Index("idx_reviews_source", Review.source)
