"""Bootstrap review records from Yelp polarity into Postgres reviews table."""

import argparse

from datasets import load_dataset
from sqlalchemy import select

from app.db.models import Review
from app.db.session import SessionLocal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load Yelp reviews into the reviews table")
    parser.add_argument("--count", type=int, default=500, help="Number of records to import")
    parser.add_argument(
        "--source-split",
        type=str,
        default="train",
        choices=["train", "test"],
        help="Yelp split to load from",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    split_expr = f"{args.source_split}[:{args.count}]"
    print(f"Loading dataset split: {split_expr}")

    dataset = load_dataset("yelp_polarity", split=split_expr, trust_remote_code=True)

    inserted = 0
    skipped = 0

    with SessionLocal() as db:
        for i, row in enumerate(dataset):
            source_review_id = f"yelp_polarity_{args.source_split}_{i}"

            exists = db.scalar(
                select(Review.id).where(
                    Review.source == "yelp_polarity",
                    Review.source_review_id == source_review_id,
                )
            )
            if exists:
                skipped += 1
                continue

            review = Review(
                source="yelp_polarity",
                source_review_id=source_review_id,
                review_text=row["text"],
                overall_sentiment=row.get("label"),
                language_code="en",
            )
            db.add(review)
            inserted += 1

        db.commit()

    print(f"Done. Inserted={inserted}, Skipped(existing)={skipped}")


if __name__ == "__main__":
    main()
