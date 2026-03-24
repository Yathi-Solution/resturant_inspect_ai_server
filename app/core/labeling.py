from app.db.enums import AspectState

ASPECTS = ["food", "service", "hygiene", "parking", "cleanliness"]


def _state_from_keywords(
    text_lower: str, positive_words: list[str], negative_words: list[str]
) -> AspectState:
    has_positive = any(word in text_lower for word in positive_words)
    has_negative = any(word in text_lower for word in negative_words)

    if has_positive and has_negative:
        return AspectState.MIXED
    if has_positive:
        return AspectState.POSITIVE
    if has_negative:
        return AspectState.NEGATIVE
    return AspectState.NOT_MENTIONED


def infer_aspect_states(text: str, overall_sentiment: int | None = None) -> dict[str, AspectState]:
    """Infer draft tetralemma-style aspect labels from review text."""
    text_lower = text.lower()

    food_state = _state_from_keywords(
        text_lower,
        positive_words=["delicious", "tasty", "amazing", "excellent", "flavorful", "fresh"],
        negative_words=["terrible", "awful", "bland", "stale", "cold food", "overcooked"],
    )

    service_state = _state_from_keywords(
        text_lower,
        positive_words=["friendly", "attentive", "helpful", "great service", "prompt"],
        negative_words=["rude", "slow", "terrible service", "unfriendly", "ignored"],
    )

    hygiene_state = _state_from_keywords(
        text_lower,
        positive_words=["clean", "spotless", "sanitary", "hygienic"],
        negative_words=["dirty", "filthy", "gross", "disgusting", "unsanitary"],
    )

    cleanliness_state = _state_from_keywords(
        text_lower,
        positive_words=["clean", "tidy", "well-maintained", "neat"],
        negative_words=["dirty", "messy", "unkempt", "sticky floor"],
    )

    parking_mentioned = "parking" in text_lower
    if not parking_mentioned:
        parking_state = AspectState.NOT_MENTIONED
    else:
        has_parking_positive = any(
            word in text_lower
            for word in ["easy parking", "ample parking", "parking available", "good parking"]
        )
        has_parking_negative = any(
            word in text_lower for word in ["no parking", "parking nightmare", "parking issue"]
        )

        if has_parking_positive and has_parking_negative:
            parking_state = AspectState.MIXED
        elif has_parking_positive:
            parking_state = AspectState.POSITIVE
        elif has_parking_negative:
            parking_state = AspectState.NEGATIVE
        elif overall_sentiment == 0:
            parking_state = AspectState.NEGATIVE
        else:
            parking_state = AspectState.POSITIVE

    return {
        "food_state": food_state,
        "service_state": service_state,
        "hygiene_state": hygiene_state,
        "parking_state": parking_state,
        "cleanliness_state": cleanliness_state,
    }
