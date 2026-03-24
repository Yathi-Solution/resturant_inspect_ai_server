#!/usr/bin/env python
"""
Approve draft annotations for use in model training.

Marks ReviewAnnotation records as 'approved' after human review.
Maintains audit trail with reviewer_name and reviewed_at timestamp.
"""

import argparse
from datetime import datetime

from app.db.enums import AnnotationStatus
from app.db.models import ReviewAnnotation
from app.db.session import SessionLocal


def approve_by_id(annotation_ids: list[int], reviewer: str) -> int:
    """Approve specific annotations by ID."""
    session = SessionLocal()
    count = 0
    try:
        for aid in annotation_ids:
            ann = session.query(ReviewAnnotation).filter_by(id=aid).first()
            if ann and ann.annotation_status == AnnotationStatus.DRAFT:
                ann.annotation_status = AnnotationStatus.APPROVED
                ann.reviewed_at = datetime.utcnow()
                ann.reviewer_name = reviewer
                count += 1
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        return 0
    finally:
        session.close()
    return count


def approve_by_status(limit: int, reviewer: str) -> int:
    """Approve first N draft annotations."""
    session = SessionLocal()
    count = 0
    try:
        records = (
            session.query(ReviewAnnotation)
            .filter_by(annotation_status=AnnotationStatus.DRAFT)
            .limit(limit)
            .all()
        )
        for ann in records:
            ann.annotation_status = AnnotationStatus.APPROVED
            ann.reviewed_at = datetime.utcnow()
            ann.reviewer_name = reviewer
            count += 1
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        return 0
    finally:
        session.close()
    return count


def list_draft_annotations(limit: int = 10) -> None:
    """Display draft annotations for review."""
    session = SessionLocal()
    try:
        records = (
            session.query(ReviewAnnotation)
            .filter_by(annotation_status=AnnotationStatus.DRAFT)
            .limit(limit)
            .all()
        )
        for ann in records:
            print(
                f"ID={ann.id} | Review ID={ann.review_id} | "
                f"Food={ann.food_state.value} | "
                f"Service={ann.service_state.value} | "
                f"Source={ann.source.value}"
            )
    finally:
        session.close()


def get_status_summary() -> None:
    """Print annotation status distribution."""
    session = SessionLocal()
    try:
        result = session.query(ReviewAnnotation.annotation_status).all()
        from collections import Counter

        counts = Counter([r[0].value for r in result])
        print("\n=== Annotation Status Summary ===")
        for status, count in sorted(counts.items()):
            print(f"  {status}: {count}")
        total = sum(counts.values())
        approved_pct = (counts.get("approved", 0) / total * 100) if total > 0 else 0
        print(f"  TOTAL: {total} ({approved_pct:.1f}% approved)")
        print()
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Approve draft annotations for model training")
    parser.add_argument(
        "--approve-count",
        type=int,
        help="Approve first N draft annotations",
    )
    parser.add_argument(
        "--approve-ids",
        type=int,
        nargs="+",
        help="Approve specific annotation IDs",
    )
    parser.add_argument(
        "--reviewer",
        type=str,
        default="data_reviewer_v1",
        help="Reviewer name for audit trail (default: data_reviewer_v1)",
    )
    parser.add_argument(
        "--list",
        type=int,
        metavar="N",
        help="List first N draft annotations",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show annotation status summary",
    )

    args = parser.parse_args()

    if args.summary:
        get_status_summary()
    elif args.list:
        list_draft_annotations(args.list)
    elif args.approve_count:
        count = approve_by_status(args.approve_count, args.reviewer)
        print(f"Approved {count} annotations.")
        get_status_summary()
    elif args.approve_ids:
        count = approve_by_id(args.approve_ids, args.reviewer)
        print(f"Approved {count} annotations.")
        get_status_summary()
    else:
        parser.print_help()
