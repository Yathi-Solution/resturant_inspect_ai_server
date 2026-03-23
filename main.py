"""
Restaurant Inspector API.
Analyzes restaurant reviews and provides scores for various aspects.
"""

from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import pipeline

# Initialize FastAPI app
app = FastAPI(
    title="Restaurant Inspector",
    description="AI-powered restaurant review aspect analyzer",
    version="1.0.0",
)

# Aspect names mapping
ASPECT_NAMES = ["FOOD", "SERVICE", "HYGIENE", "PARKING", "CLEANLINESS"]

# Load model at startup (once!)
print("🚀 Loading model...")
try:
    classifier = pipeline(
        "text-classification",
        model="dpratapx/restaurant-inspector",
        device=-1,  # CPU mode
        top_k=None,  # Return all scores
    )
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    print("⚠️  Make sure you've run 'python train.py' first!")
    classifier = None


# Request/Response models
class ReviewRequest(BaseModel):
    """Request model for review analysis."""

    text: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Restaurant review text to analyze",
        examples=["Great food but terrible parking and dirty bathrooms"],
    )


class AspectScores(BaseModel):
    """Aspect scores model."""

    FOOD: float = Field(..., ge=0.0, le=1.0, description="Food quality score (0-1)")
    SERVICE: float = Field(..., ge=0.0, le=1.0, description="Service quality score (0-1)")
    HYGIENE: float = Field(..., ge=0.0, le=1.0, description="Hygiene score (0-1)")
    PARKING: float = Field(..., ge=0.0, le=1.0, description="Parking availability score (0-1)")
    CLEANLINESS: float = Field(..., ge=0.0, le=1.0, description="Cleanliness score (0-1)")


class AnalysisResponse(BaseModel):
    """Response model for review analysis."""

    review: str = Field(..., description="Original review text")
    scores: AspectScores = Field(..., description="Aspect scores")
    timestamp: str = Field(..., description="Analysis timestamp (ISO 8601)")


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Restaurant Inspector API",
        "version": "1.0.0",
        "endpoints": {
            "POST /analyze": "Analyze a restaurant review",
            "GET /health": "Health check",
            "GET /docs": "API documentation",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    model_status = "ready" if classifier is not None else "not_loaded"
    return {
        "status": "healthy" if model_status == "ready" else "degraded",
        "model": model_status,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_review(request: ReviewRequest):
    """
    Analyze a restaurant review and return aspect scores.

    Args:
        request: ReviewRequest with review text

    Returns:
        AnalysisResponse with scores for each aspect

    Raises:
        HTTPException: If model not loaded or analysis fails
    """
    if classifier is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please run 'python train.py' first.",
        )

    try:
        # Get predictions
        results = classifier(request.text)

        # Parse scores - results is a list of lists of dicts
        # Format: [[{'label': 'LABEL_0', 'score': 0.9}, ...]]
        scores_dict = {}

        if isinstance(results[0], list):
            # top_k=None returns list of all labels with scores
            for item in results[0]:
                label_idx = int(item["label"].split("_")[1])
                if 0 <= label_idx < len(ASPECT_NAMES):
                    aspect_name = ASPECT_NAMES[label_idx]
                    scores_dict[aspect_name] = round(item["score"], 3)
        else:
            # Fallback for different pipeline output format
            for i, aspect_name in enumerate(ASPECT_NAMES):
                scores_dict[aspect_name] = 0.5  # Default score

        # Ensure all aspects are present
        for aspect in ASPECT_NAMES:
            if aspect not in scores_dict:
                scores_dict[aspect] = 0.5

        return AnalysisResponse(
            review=request.text,
            scores=AspectScores(**scores_dict),
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
