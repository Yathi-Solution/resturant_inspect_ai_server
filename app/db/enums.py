from enum import Enum


class AspectState(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    NOT_MENTIONED = "not_mentioned"


class AnnotationStatus(str, Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class LabelSource(str, Enum):
    HEURISTIC = "heuristic"
    MANUAL = "manual"
    HEURISTIC_REVIEWED = "heuristic_reviewed"
