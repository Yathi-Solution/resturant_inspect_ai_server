"""Generate heuristic draft annotations for unlabeled reviews."""

import argparse
from datetime import UTC, datetime

from sqlalchemy import exists, select

from app.core.labeling import infer_aspect_states
from app.db.enums import AnnotationStatus, LabelSource
from app.db.models import Review, ReviewAnnotation
from app.db.session import SessionLocal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create draft annotations for reviews")
    parser.add_argument("--limit", type=int, default=300, help="Max reviews to annotate in one run")
    parser.add_argument(
        "--annotator",
        type=str,
        default="copilot_draft_v1",
        help="Annotator name to store for traceability",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with SessionLocal() as db:
        unlabeled_reviews = db.scalars(
            select(Review)
            .where(
                ~exists(select(ReviewAnnotation.id).where(ReviewAnnotation.review_id == Review.id))
            )
            .limit(args.limit)
        ).all()

        if not unlabeled_reviews:
            print("No unlabeled reviews found.")
            return

        created = 0
        now = datetime.now(UTC)

        for review in unlabeled_reviews:
            states = infer_aspect_states(review.review_text, review.overall_sentiment)
            annotation = ReviewAnnotation(
                review_id=review.id,
                food_state=states["food_state"],
                service_state=states["service_state"],
                hygiene_state=states["hygiene_state"],
                parking_state=states["parking_state"],
                cleanliness_state=states["cleanliness_state"],
                annotation_status=AnnotationStatus.DRAFT,
                label_source=LabelSource.HEURISTIC,
                annotator_name=args.annotator,
                reviewed_at=None,
                review_notes=None,
                confidence_score=None,
                created_at=now,
                updated_at=now,
            )
            db.add(annotation)
            created += 1

        db.commit()

    print(f"Created {created} draft annotations.")


if __name__ == "__main__":
    main()
