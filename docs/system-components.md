# System Components

## Overview

The Restaurant Inspector system is built around a **database-backed annotation workflow** with PostgreSQL at its core. This document details each component's implementation, database schema, and interactions.

## Components Diagram

![System Components](system-components.png)

**Component Layers**: Data Source → Scripts → Database (PostgreSQL) → Training Pipeline → Model Artifacts
    
    subgraph "S Scripts Layer"
        S1[bootstrap_reviews.py<br/>Data Ingestion]
        S2[generate_draft_annotations.py<br/>Heuristic Labeling]
        S3[approve_annotations.py<br/>Approval Workflow]
        S4[train.py<br/>Model Training]
    end
    
    subgraph "ORM & Migrations"
        ORM[SQLAlchemy Models<br/>Review, ReviewAnnotation, TrainingRun]
        ENUM[Enums<br/>AspectState, AnnotationStatus, LabelSource]
        MIG[Alembic Migrations<br/>20260323_0001, 5eed963bbc03]
    end
    
    subgraph "Core Logic"
        LAB[app/core/labeling.py<br/>infer_aspect_states()]
        SESS[app/db/session.py<br/>SessionLocal factory]
    end
    
    subgraph "ML Components"
        BERT[DistilBERT<br/>distilbert-base-uncased<br/>66M parameters]
        TRANS[Transformers Library<br/>Trainer, Pipeline]
        EVAL[Metrics<br/>Precision, Recall, F1]
    end
    
    subgraph "Model Artifacts"
        MODEL[models/aspect-classifier/<br/>model.safetensors<br/>config.json<br/>metadata.json]
    end
    
    DS -->|Load| S1
    S1 -->|Insert| T1
    T1 -->|Read| S2
    LAB -->|Label logic| S2
    S2 -->|Insert drafts| T2
    T2 -->|Query drafts| S3
    S3 -->|Update approved| T2
    T2 -->|Query approved| S4
    S4 -->|Train| BERT
    BERT -->|Evaluate| EVAL
    EVAL -->|Save| MODEL
    EVAL -->|Log| T3
    
    ORM -->|Define| DB
    MIG -->|Migrate| DB
    ENUM -->|Types| ORM
    SESS -->|Connect| DB
    
    S1 & S2 & S3 & S4 -->|Use| ORM
    S4 -->|Use| TRANS
    
    style DB fill:#e1f5ff
    style BERT fill:#ffe1e1
    style MODEL fill:#e1ffe1
    style T2 fill:#fff4e1
```

---

## Database Components

### Component DB1: PostgreSQL (Neon)

**Platform**: Neon (https://neon.tech)
- **Type**: Serverless PostgreSQL 15
- **Connection**: Via `DATABASE_URL` environment variable
- **Features**: 
  - Auto-scaling compute
  - Branch-based workflows (future)
  - Point-in-time recovery
  - Connection pooling

**Connection String Format**:
```
postgresql://user:password@ep-xyz.us-east-1.aws.neon.tech/neondb?sslmode=require
```

**Access Pattern**:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(bind=engine)
```

---

### Component DB2: reviews Table

**Purpose**: Store raw review text from external sources

**Schema**:
```sql
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,                -- e.g., 'yelp_polarity'
    source_review_id VARCHAR(255),              -- External ID for dedup
    review_text TEXT NOT NULL,                  -- Raw review content
    overall_sentiment INTEGER,                  -- 0=negative, 1=positive
    language_code VARCHAR(8) DEFAULT 'en',
    business_name VARCHAR(255),
    business_location VARCHAR(255),
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_reviews_source ON reviews(source);
```

**Current State**:
- **Row Count**: 300
- **Source**: yelp_polarity
- **Average Length**: ~150 words/review

**Sample Row**:
```json
{
  "id": 1,
  "source": "yelp_polarity",
  "source_review_id": "train_0",
  "review_text": "The food was amazing! Best pasta I've had in years...",
  "overall_sentiment": 1,
  "language_code": "en",
  "ingested_at": "2026-03-23T18:45:00Z"
}
```

---

### Component DB3: review_annotations Table

**Purpose**: Store aspect-level labels with audit trails and workflow states

**Schema**:
```sql
-- Custom enum types
CREATE TYPE aspect_state AS ENUM ('positive', 'negative', 'mixed', 'not_mentioned');
CREATE TYPE annotation_status AS ENUM ('draft', 'reviewed', 'approved', 'rejected');
CREATE TYPE label_source AS ENUM ('heuristic', 'manual', 'heuristic_reviewed');

CREATE TABLE review_annotations (
    id SERIAL PRIMARY KEY,
    review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    
    -- 5 aspect labels (4-state each)
    food_state aspect_state NOT NULL,
    service_state aspect_state NOT NULL,
    hygiene_state aspect_state NOT NULL,
    parking_state aspect_state NOT NULL,
    cleanliness_state aspect_state NOT NULL,
    
    -- Workflow tracking
    annotation_status annotation_status NOT NULL DEFAULT 'draft',
    label_source label_source NOT NULL DEFAULT 'heuristic',
    
    -- Audit trail
    annotator_name VARCHAR(100) NOT NULL,        -- Who created it
    reviewer_name VARCHAR(100),                  -- Who approved it
    review_notes TEXT,                           -- Optional notes
    confidence_score NUMERIC(4,3),               -- 0.000-1.000
    reviewed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_review_annotations_review_id ON review_annotations(review_id);
CREATE INDEX idx_review_annotations_status ON review_annotations(annotation_status);
```

**Current State**:
- **Total Rows**: 300
- **Approved**: 200 (ready for training)
- **Draft**: 100 (not yet reviewed)

**Sample Row**:
```json
{
  "id": 1,
  "review_id": 1,
  "food_state": "positive",
  "service_state": "not_mentioned",
  "hygiene_state": "not_mentioned",
  "parking_state": "negative",
  "cleanliness_state": "mixed",
  "annotation_status": "approved",
  "label_source": "heuristic",
  "annotator_name": "senior_data_analyst_v1",
  "reviewer_name": "senior_data_analyst_v1",
  "reviewed_at": "2026-03-23T19:15:00Z"
}
```

**State Transitions**:
```
draft → reviewed → approved ✅
              ↓
           rejected ❌
```

---

### Component DB4: training_runs Table

**Purpose**: Log all model training runs with metrics for versioning and comparison

**Schema**:
```sql
CREATE TABLE training_runs (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,            -- e.g., 'distilbert-base-uncased'
    training_samples INTEGER NOT NULL,           -- Number of training examples
    test_accuracy NUMERIC(5,4) NOT NULL,         -- 0.0000-1.0000
    test_f1 NUMERIC(5,4) NOT NULL,              
    test_precision NUMERIC(5,4) NOT NULL,
    test_recall NUMERIC(5,4) NOT NULL,
    output_path VARCHAR(512) NOT NULL,           -- e.g., 'models/aspect-classifier'
    trained_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Current State**:
- **Total Runs**: 3
- **Best F1**: 0.1646 (Run #3)

**Sample Row**:
```json
{
  "id": 3,
  "model_name": "distilbert-base-uncased",
  "training_samples": 120,
  "test_accuracy": 0.0000,
  "test_f1": 0.1646,
  "test_precision": 0.0922,
  "test_recall": 0.7714,
  "output_path": "models/aspect-classifier",
  "trained_at": "2026-03-23T19:30:10Z"
}
```

---

## Script Components

### Component S1: bootstrap_reviews.py

**Purpose**: Ingest reviews from HuggingFace datasets into PostgreSQL

**File**: `scripts/bootstrap_reviews.py` (~80 lines)

**Key Functions**:

```python
def main(count: int, source_split: str = "train"):
    """Load Yelp reviews from HF and insert into database."""
    dataset = load_dataset("yelp_polarity", split=f"{source_split}[:{count}]")
    
    session = SessionLocal()
    inserted = 0
    skipped = 0
    
    for idx, row in enumerate(dataset):
        review = Review(
            source="yelp_polarity",
            source_review_id=f"{source_split}_{idx}",
            review_text=row["text"],
            overall_sentiment=row["label"]
        )
        
        # Check for duplicates
        existing = session.query(Review).filter_by(
            source_review_id=review.source_review_id
        ).first()
        
        if not existing:
            session.add(review)
            inserted += 1
        else:
            skipped += 1
    
    session.commit()
    print(f"Done. Inserted={inserted}, Skipped(existing)={skipped}")
```

**Usage**:
```bash
$env:PYTHONPATH='.'
python scripts/bootstrap_reviews.py --count 300 --source-split train
```

**Dependencies**:
- `datasets` (HuggingFace)
- `sqlalchemy`
- `app.db.models.Review`
- `app.db.session.SessionLocal`

---

### Component S2: generate_draft_annotations.py

**Purpose**: Generate heuristic labels for unlabeled reviews using keyword matching

**File**: `scripts/generate_draft_annotations.py` (~90 lines)

**Key Functions**:

```python
def main(limit: int, annotator: str):
    """Generate draft annotations for unlabeled reviews."""
    session = SessionLocal()
    
    # Find reviews without annotations
    reviews = (
        session.query(Review)
        .outerjoin(ReviewAnnotation)
        .filter(ReviewAnnotation.id == None)
        .limit(limit)
        .all()
    )
    
    for review in reviews:
        # Generate aspect labels using keyword rules
        aspect_states = infer_aspect_states(
            review.review_text,
            review.overall_sentiment
        )
        
        annotation = ReviewAnnotation(
            review_id=review.id,
            food_state=aspect_states["food"],
            service_state=aspect_states["service"],
            hygiene_state=aspect_states["hygiene"],
            parking_state=aspect_states["parking"],
            cleanliness_state=aspect_states["cleanliness"],
            annotation_status=AnnotationStatus.DRAFT,
            label_source=LabelSource.HEURISTIC,
            annotator_name=annotator
        )
        session.add(annotation)
    
    session.commit()
    print(f"Created {len(reviews)} draft annotations.")
```

**Usage**:
```bash
python scripts/generate_draft_annotations.py --limit 300 --annotator "analyst_v1"
```

**Dependencies**:
- `app.core.labeling.infer_aspect_states`
- `app.db.models.Review, ReviewAnnotation`
- `app.db.enums.AspectState, AnnotationStatus`

---

### Component S3: approve_annotations.py

**Purpose**: Human-in-the-loop approval workflow for draft annotations

**File**: `scripts/approve_annotations.py` (~120 lines)

**Key Functions**:

```python
def approve_by_count(limit: int, reviewer: str) -> int:
    """Approve first N draft annotations."""
    session = SessionLocal()
    records = (
        session.query(ReviewAnnotation)
        .filter_by(annotation_status=AnnotationStatus.DRAFT)
        .limit(limit)
        .all()
    )
    
    for ann in records:
        ann.annotation_status = AnnotationStatus.APPROVED
        ann.reviewer_name = reviewer
        ann.reviewed_at = datetime.utcnow()
    
    session.commit()
    return len(records)

def get_status_summary():
    """Print annotation status distribution."""
    session = SessionLocal()
    result = session.query(ReviewAnnotation.annotation_status).all()
    counts = Counter([r[0].value for r in result])
    
    print("\n=== Annotation Status Summary ===")
    for status, count in sorted(counts.items()):
        print(f"  {status}: {count}")
    total = sum(counts.values())
    approved_pct = (counts.get("approved", 0) / total * 100) if total > 0 else 0
    print(f"  TOTAL: {total} ({approved_pct:.1f}% approved)\n")
```

**Usage**:
```bash
# List drafts
python scripts/approve_annotations.py --list 10

# Approve in bulk
python scripts/approve_annotations.py --approve-count 200 --reviewer "reviewer_v1"

# Check status
python scripts/approve_annotations.py --summary
```

---

### Component S4: train.py

**Purpose**: Train DistilBERT on approved annotations and log metrics

**File**: `scripts/train.py` (~250 lines)

**Key Functions**:

```python
def load_approved_annotations():
    """Load approved annotations from database."""
    session = SessionLocal()
    records = (
        session.query(ReviewAnnotation)
        .filter_by(annotation_status=AnnotationStatus.APPROVED)
        .all()
    )
    
    data = []
    for ann in records:
        review_text = ann.review.review_text
        aspects = {
            "food": ann.food_state.value,
            "service": ann.service_state.value,
            "hygiene": ann.hygiene_state.value,
            "parking": ann.parking_state.value,
            "cleanliness": ann.cleanliness_state.value,
        }
        data.append({"text": review_text, "aspects": aspects})
    
    return data

def aspect_to_labels(aspect, state_value):
    """Convert 4-state label to binary labels."""
    labels = []
    if state_value == "positive":
        labels.append(f"{aspect}_positive")
    elif state_value == "negative":
        labels.append(f"{aspect}_negative")
    elif state_value == "mixed":
        labels.append(f"{aspect}_positive")
        labels.append(f"{aspect}_negative")
    # not_mentioned = no labels
    return labels

def train_model(model_name, output_dir):
    """Main training pipeline."""
    # 1. Load approved data
    data = load_approved_annotations()
    
    # 2. Convert 4-state → 10 binary labels
    texts = [d["text"] for d in data]
    all_labels = []
    for d in data:
        labels = []
        for aspect, state in d["aspects"].items():
            labels.extend(aspect_to_labels(aspect, state))
        all_labels.append(labels)
    
    # 3. Split 60/20/20
    X_train, X_temp, y_train, y_temp = train_test_split(
        texts, all_labels, test_size=0.4, random_state=42
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42
    )
    
    # 4. Encode labels
    mlb = MultiLabelBinarizer()
    y_train_enc = mlb.fit_transform(y_train)
    y_val_enc = mlb.transform(y_val)
    y_test_enc = mlb.transform(y_test)
    
    # 5. Load model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(mlb.classes_),
        problem_type="multi_label_classification"
    )
    
    # 6. Train
    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=3,
            per_device_train_batch_size=8,
            eval_strategy="epoch"
        ),
        train_dataset=AspectDataset(X_train, y_train_enc, tokenizer),
        eval_dataset=AspectDataset(X_val, y_val_enc, tokenizer),
        compute_metrics=compute_metrics
    )
    trainer.train()
    
    # 7. Evaluate
    test_results = trainer.evaluate(AspectDataset(X_test, y_test_enc, tokenizer))
    
    # 8. Save
    trainer.save_model(output_dir)
    
    # 9. Log to database
    log_training_run(
        model_name=model_name,
        training_samples=len(X_train),
        test_accuracy=test_results.get("eval_accuracy", 0),
        test_f1=test_results.get("eval_f1", 0),
        test_precision=test_results.get("eval_precision", 0),
        test_recall=test_results.get("eval_recall", 0),
        output_path=output_dir
    )
```

**Usage**:
```bash
python scripts/train.py --model distilbert-base-uncased --output-dir models/aspect-classifier
```

---

## ORM & Migration Components

### Component ORM1: SQLAlchemy Models

**File**: `app/db/models.py` (~120 lines)

**Key Classes**:

```python
class Review(Base):
    __tablename__ = "reviews"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    review_text: Mapped[str] = mapped_column(Text, nullable=False)
    overall_sentiment: Mapped[int | None] = mapped_column(nullable=True)
    
    annotations: Mapped[list["ReviewAnnotation"]] = relationship(
        back_populates="review", cascade="all, delete-orphan"
    )

class ReviewAnnotation(Base):
    __tablename__ = "review_annotations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"))
    
    food_state: Mapped[AspectState] = mapped_column(
        Enum(AspectState, values_callable=enum_values), nullable=False
    )
    # ... 4 more aspect states
    
    annotation_status: Mapped[AnnotationStatus] = mapped_column(
        Enum(AnnotationStatus, values_callable=enum_values), nullable=False
    )
    
    review: Mapped[Review] = relationship(back_populates="annotations")

class TrainingRun(Base):
    __tablename__ = "training_runs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    test_f1: Mapped[float] = mapped_column(Numeric(5,4), nullable=False)
    # ... more metrics
```

**Enum Helper**:
```python
def enum_values(enum_cls):
    """Return Enum values for PostgreSQL persistence."""
    return [item.value for item in enum_cls]
```

### Component ORM2: Enums

**File**: `app/db/enums.py` (~30 lines)

```python
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
```

### Component ORM3: Alembic Migrations

**Files**: `alembic/versions/*.py`

**Migration 1**: `20260323_0001_create_reviews_and_review_annotations.py`
```python
def upgrade():
    # Create enum types
    op.execute("CREATE TYPE aspect_state AS ENUM ('positive', 'negative', 'mixed', 'not_mentioned')")
    op.execute("CREATE TYPE annotation_status AS ENUM ('draft', 'reviewed', 'approved', 'rejected')")
    op.execute("CREATE TYPE label_source AS ENUM ('heuristic', 'manual', 'heuristic_reviewed')")
    
    # Create reviews table
    op.create_table('reviews', ...)
    
    # Create review_annotations table
    op.create_table('review_annotations', ...)
```

**Migration 2**: `5eed963bbc03_add_training_runs_table_and_reviewer_.py`
```python
def upgrade():
    # Add training_runs table
    op.create_table('training_runs', ...)
    
    # Add reviewer_name column
    op.add_column('review_annotations', 
        sa.Column('reviewer_name', sa.String(100), nullable=True))
```

**Usage**:
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Check current version
alembic current
```

---

## Core Logic Components

### Component CORE1: Heuristic Labeling

**File**: `app/core/labeling.py` (~100 lines)

**Key Function**:

```python
def infer_aspect_states(text: str, overall_sentiment: int | None) -> dict:
    """Generate 4-state labels for 5 aspects using keyword matching."""
    
    KEYWORDS = {
        "food": {
            "positive": ["delicious", "tasty", "amazing", "excellent", "flavorful", "fresh"],
            "negative": ["terrible", "bland", "awful", "disgusting", "stale", "rotten"]
        },
        "service": {
            "positive": ["friendly", "attentive", "excellent", "helpful", "polite"],
            "negative": ["rude", "slow", "terrible", "impolite", "ignoring"]
        },
        # ... hygiene, parking, cleanliness
    }
    
    text_lower = text.lower()
    states = {}
    
    for aspect, keywords in KEYWORDS.items():
        pos_match = any(kw in text_lower for kw in keywords["positive"])
        neg_match = any(kw in text_lower for kw in keywords["negative"])
        
        if pos_match and neg_match:
            states[aspect] = AspectState.MIXED
        elif pos_match:
            states[aspect] = AspectState.POSITIVE
        elif neg_match:
            states[aspect] = AspectState.NEGATIVE
        else:
            states[aspect] = AspectState.NOT_MENTIONED
    
    return states
```

---

## ML Components

### Component ML1: DistilBERT

**Model**: `distilbert-base-uncased` (HuggingFace)
- **Parameters**: 66 million
- **Layers**: 6 transformer blocks
- **Hidden Size**: 768
- **Attention Heads**: 12
- **Vocabulary**: 30,522 tokens
- **Max Sequence Length**: 512 (we use 128)

**Why DistilBERT?**
- 60% faster than BERT-base
- 40% smaller than BERT-base
- 97% of BERT-base performance
- CPU-friendly

### Component ML2: Transformers Library

**Library**: `transformers` by HuggingFace
**Version**: 4.x

**Key Classes Used**:
- `AutoTokenizer` - Tokenization
- `AutoModelForSequenceClassification` - Multi-label head
- `Trainer` - Training loop with mixed precision, checkpointing
- `TrainingArguments` - Hyperparameter configuration

### Component ML3: Evaluation Metrics

**Implementation**: `scripts/train.py::compute_metrics()`

```python
def compute_metrics(eval_pred, threshold=0.25):
    """Compute multi-label classification metrics."""
    predictions, labels = eval_pred
    predictions = (predictions > threshold).astype(int)
    
    # Exact match accuracy
    accuracy = np.mean(np.all(predictions == labels, axis=1))
    
    # Micro-averaged metrics
    precision = precision_score(labels, predictions, average="micro")
    recall = recall_score(labels, predictions, average="micro")
    f1 = f1_score(labels, predictions, average="micro")
    
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }
```

**Metrics Explanation**:
- **Accuracy**: % of samples with ALL labels correct (strict)
- **Precision**: TP / (TP + FP) across all labels
- **Recall**: TP / (TP + FN) across all labels
- **F1**: Harmonic mean of precision and recall

---

## Model Artifacts

### Component ART1: Saved Model Files

**Directory**: `models/aspect-classifier/`

**Files**:
```
models/aspect-classifier/
├── model.safetensors       # Model weights (255MB)
├── config.json             # Model architecture config
├── tokenizer.json          # Tokenizer vocabulary + merges
├── tokenizer_config.json   # Tokenizer settings
├── metadata.json           # Custom training metadata
├── training_args.bin       # Training hyperparameters (binary)
└── checkpoint-{N}/         # Intermediate checkpoints
```

**metadata.json**:
```json
{
  "model_name": "distilbert-base-uncased",
  "num_labels": 10,
  "label_names": [
    "cleanliness_negative", "cleanliness_positive",
    "food_negative", "food_positive",
    "hygiene_negative", "hygiene_positive",
    "parking_negative", "parking_positive",
    "service_negative", "service_positive"
  ],
  "training_samples": 120,
  "val_samples": 40,
  "test_samples": 40,
  "threshold": 0.25,
  "test_metrics": {
    "accuracy": 0.0,
    "precision": 0.0922,
    "recall": 0.7714,
    "f1": 0.1646
  }
}
```

---

## Component Interactions

### Interaction 1: Data Ingestion
```
Yelp Dataset → bootstrap_reviews.py → Review ORM → PostgreSQL reviews table
```

### Interaction 2: Draft Generation
```
reviews table → generate_draft_annotations.py → infer_aspect_states() → ReviewAnnotation ORM → review_annotations table (status=draft)
```

### Interaction 3: Approval
```
review_annotations (draft) → approve_annotations.py → UPDATE status=approved → review_annotations (approved)
```

### Interaction 4: Training
```
review_annotations (approved) → train.py → DistilBERT → Evaluation → Model files + training_runs table
```

---

## Summary Table

| Component | Type | Purpose | Input | Output |
|-----------|------|---------|-------|--------|
| PostgreSQL | Database | Store reviews & annotations | SQL queries | Rows |
| bootstrap_reviews.py | Script | Ingest data | Yelp dataset | 300 reviews |
| generate_draft_annotations.py | Script | Label data | Reviews | 300 drafts |
| approve_annotations.py | Script | Approve labels | Drafts | 200 approved |
| train.py | Script | Train model | Approved annotations | Trained model |
| SQLAlchemy | ORM | Database abstraction | Python classes | SQL queries |
| Alembic | Migration | Schema versioning | Migration files | SQL DDL |
| DistilBERT | Model | Multi-label classifier | Text | 10 probabilities |
| Transformers | Library | Training framework | Config + data | Trained weights |
    
    for i, (aspect, keywords) in enumerate(ASPECT_KEYWORDS.items()):
        for keyword in keywords:
            if keyword in text_lower:
                # Positive review → high score, negative → low score
                scores[i] = 0.9 if label == 1 else 0.1
                break
    
    return scores
```

**Example Transformation**:
```
Input:
  Text: "The food was amazing but service was terrible"
  Label: 0 (negative overall)

Output:
  [0.9, 0.1, 0.5, 0.5, 0.5]  # FOOD high, SERVICE low, others neutral
```

**Limitations**:
- Simplistic keyword matching
- No context understanding
- No negation handling ("not delicious" counted as positive)
- Future: Use ChatGPT/Claude for better labeling

---

### Component T4: DistilBERT Fine-tuning

**Purpose**: Adapt pretrained DistilBERT to restaurant aspect classification

**Base Model**: `distilbert-base-uncased`
- Parameters: 66M
- Layers: 6 transformer blocks
- Hidden size: 768
- Attention heads: 12
- Vocabulary: 30,522 tokens

**Fine-tuning Configuration**:

```python
from transformers import TrainingArguments, Trainer

training_args = TrainingArguments(
    output_dir="./model",
    num_train_epochs=2,
    per_device_train_batch_size=8,
    learning_rate=5e-5,
    warmup_steps=50,
    logging_steps=10,
    save_strategy="epoch",
    evaluation_strategy="no",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

trainer.train()
```

**Training Steps**:
1. Load pretrained DistilBERT weights
2. Replace classification head (768 → 5 outputs)
3. Freeze nothing (full fine-tuning)
4. Train for 2 epochs
5. Use AdamW optimizer (lr=5e-5)
6. Apply linear warmup (50 steps)

**Training Metrics**:
- Total steps: 376 (1500 samples / 8 batch size × 2 epochs)
- Training loss: 0.35 (final)
- Time: ~45 minutes on CPU
- GPU: Would take ~5 minutes on T4

**Model Architecture Changes**:
```
Before:
  DistilBERT → [768] → Classifier(2) → Binary sentiment

After:
  DistilBERT → [768] → Classifier(5) → Multi-label aspects
                        ↓
                    Sigmoid activation (independent probabilities)
```

---

### Component T5: Trained Model

**Purpose**: Serialized model artifact ready for deployment

**Output Files**:
```
./model/
├── config.json              # Model configuration
├── model.safetensors        # Model weights (255MB)
├── tokenizer.json          # Tokenizer vocabulary (680KB)
└── tokenizer_config.json   # Tokenizer settings
```

**config.json** (excerpt):
```json
{
  "model_type": "distilbert",
  "num_labels": 5,
  "hidden_size": 768,
  "num_attention_heads": 12,
  "num_hidden_layers": 6,
  "vocab_size": 30522,
  "max_position_embeddings": 512
}
```

**Model Size**:
- Total: 255MB
- Embeddings: 93MB (30522 × 768 × 4 bytes)
- Transformer layers: 150MB
- Classification head: 15KB (768 × 5 × 4 bytes)

**Format**: SafeTensors (recommended over pickle for security)

---

### Component T6: HF Hub Upload

**Purpose**: Deploy model to public repository for production access

**Script**: `upload_model.py`

```python
from huggingface_hub import HfApi, login
import os

# Login
token = os.getenv("HF_TOKEN")
login(token=token)

# Upload
api = HfApi()
api.create_repo("dpratapx/restaurant-inspector", repo_type="model", exist_ok=True)
api.upload_folder(
    folder_path="./model",
    repo_id="dpratapx/restaurant-inspector",
    repo_type="model",
)
```

**Repository**: https://huggingface.co/dpratapx/restaurant-inspector

**Benefits**:
- Version control (Git LFS for large files)
- CDN for fast worldwide downloads
- Model card for documentation
- Free hosting for public models
- Integration with Transformers library

---

## Production API (Live)

The production API runs continuously on HF Spaces, serving inference requests.

### Component P1: main.py

**Purpose**: FastAPI application entry point

**File**: `main.py` (120 lines)

**Structure**:
```python
# Imports
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import pipeline
from datetime import datetime

# App initialization
app = FastAPI(
    title="Restaurant Inspector",
    description="AI-powered restaurant review aspect analyzer",
    version="1.0.0",
)

# Pydantic models
class ReviewRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)

class AspectScores(BaseModel):
    FOOD: float
    SERVICE: float
    HYGIENE: float
    PARKING: float
    CLEANLINESS: float

class AnalysisResponse(BaseModel):
    review: str
    scores: AspectScores
    timestamp: str

# Model loading (at startup)
classifier = pipeline(
    "text-classification",
    model="dpratapx/restaurant-inspector",
    device=-1,
    top_k=None,
)

# Endpoints
@app.get("/")
async def root():
    return {"message": "Restaurant Inspector API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": classifier is not None}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_review(request: ReviewRequest):
    results = classifier(request.text)
    scores = {ASPECT_NAMES[i]: r['score'] for i, r in enumerate(results[0])}
    return AnalysisResponse(
        review=request.text,
        scores=AspectScores(**scores),
        timestamp=datetime.utcnow().isoformat()
    )
```

**Features**:
- CORS enabled (all origins)
- Auto-generated docs (`/docs`, `/redoc`)
- Input validation
- Error handling
- Type safety

---

### Component P2: Model Download

**Purpose**: Fetch trained model from HF Hub at startup

**Mechanism**:
- Triggered by `pipeline()` call
- Uses `transformers` library auto-download
- Caches in `~/.cache/huggingface/`
- Resumes interrupted downloads

**Download Process**:
1. Check cache: `~/.cache/huggingface/hub/models--dpratapx--restaurant-inspector`
2. If missing, fetch from CDN:
   ```
   https://cdn-lfs.huggingface.co/dpratapx/restaurant-inspector/...
   ```
3. Verify file hashes (SHA256)
4. Store locally for future use

**Cache Behavior**:
- First startup: Downloads all files (~260MB)
- Subsequent startups: Uses cached files (instant)
- Cache persists across container restarts (HF Spaces)

---

### Component P3: FastAPI Endpoints

**Purpose**: HTTP interface for client interactions

**Endpoints**:

1. **`GET /`** - Root/welcome
   - Returns API info
   - Used for basic connectivity test

2. **`GET /health`** - Health check
   - Returns server status
   - Checks model loaded
   - Used for monitoring/liveness probes

3. **`POST /analyze`** - Main inference endpoint
   - Accepts review text
   - Returns aspect scores
   - Validates input
   - Handles errors

4. **`GET /docs`** - Interactive API docs (auto-generated)
   - Swagger UI
   - Try endpoints directly
   - See request/response schemas

5. **`GET /redoc`** - Alternative docs (auto-generated)
   - ReDoc UI
   - Better for reading
   - Same info as `/docs`

**OpenAPI Spec**: Auto-generated at `/openapi.json`

---

### Component P4: Transformers Pipeline

**Purpose**: Abstraction layer for model inference

**Class**: `transformers.pipeline("text-classification")`

**Configuration**:
```python
classifier = pipeline(
    "text-classification",
    model="dpratapx/restaurant-inspector",
    device=-1,         # CPU mode
    top_k=None,        # Return all 5 scores
    return_all_scores=True,
)
```

**Internal Components**:
1. **Tokenizer**: Converts text → token IDs
2. **Model**: Runs inference
3. **Post-processor**: Formats outputs

**Usage**:
```python
results = classifier("The food was great")
# Returns: [{'label': 'LABEL_0', 'score': 0.92}, ...]
```

**Benefits**:
- Handles tokenization automatically
- Manages model device placement
- Batching support (if needed)
- Error handling
- Consistent interface

---

### Component P5: JSON Response

**Purpose**: Serialize predictions into standard API response

**Format** (`AnalysisResponse`):
```json
{
  "review": "Original review text",
  "scores": {
    "FOOD": 0.92,
    "SERVICE": 0.78,
    "HYGIENE": 0.65,
    "PARKING": 0.50,
    "CLEANLINESS": 0.71
  },
  "timestamp": "2026-03-23T10:30:45.123456"
}
```

**Fields**:
- `review`: Echo back input text (for client verification)
- `scores`: Object with 5 aspect scores (0-1 range)
- `timestamp`: ISO 8601 UTC timestamp

**Content-Type**: `application/json`

**Status Codes**:
- 200: Success
- 422: Validation error
- 503: Model not loaded

---

## Component Interactions

### Training → Production Flow

```
1. Developer runs train.py locally
2. Model trained on Yelp data with rule-based labels
3. Model saved to ./model/ directory
4. upload_model.py pushes to HF Hub
5. HF Hub stores model with version control
6. Production API downloads from HF Hub at startup
7. Cached locally for future requests
```

### Request → Response Flow

```
1. Client sends POST /analyze with review text
2. FastAPI validates request (Pydantic)
3. Text passed to Transformers pipeline
4. Pipeline tokenizes text
5. Model runs inference (CPU)
6. Pipeline formats outputs
7. FastAPI creates JSON response
8. Client receives aspect scores
```

---

## Technology Stack

### Training
- **Language**: Python 3.11
- **Framework**: PyTorch 2.10
- **ML Library**: Transformers 5.3
- **Data**: Datasets 4.8
- **Training**: Accelerate (for Trainer)

### Production
- **Runtime**: Docker (Python 3.11-slim)
- **Web Framework**: FastAPI 0.135
- **Server**: Uvicorn 0.42
- **ML Inference**: Transformers 5.3
- **Validation**: Pydantic 2.12
- **Platform**: HF Spaces (Docker SDK)

### Infrastructure
- **Model Storage**: Hugging Face Hub
- **Code Storage**: GitHub
- **Deployment**: Hugging Face Spaces
- **CDN**: HF Hub CDN (worldwide)

---

## File Structure

```
resturant-inspector-server/
├── main.py                 # Production API (P1, P3, P4, P5)
├── train.py                # Training script (T2, T3, T4)
├── upload_model.py         # Model upload (T6)
├── pyproject.toml          # Dependencies
├── Dockerfile              # HF Spaces deployment
├── README.md               # HF Spaces card
├── .env                    # Local secrets
├── .gitignore              # Git exclusions
├── docs/
│   ├── architecture.md
│   ├── flow.md
│   ├── system-components.md
│   └── mermaid-syntax.md
└── model/                  # Local model cache (T5)
    ├── config.json
    ├── model.safetensors
    ├── tokenizer.json
    └── tokenizer_config.json
```

---

## Deployment

### Local Development
```bash
# Train model
python train.py

# Upload to HF Hub
python upload_model.py

# Run API locally
uvicorn main:app --reload --port 8000
```

### Production (HF Spaces)
```bash
# Push code to HF Space
git remote add hf https://huggingface.co/spaces/dpratapx/restaurant-inspector-api-dev
git push hf main

# HF Spaces automatically:
# 1. Builds Docker image
# 2. Downloads model from HF Hub
# 3. Starts Uvicorn server
# 4. Exposes on port 7860
```

**URL**: https://dpratapx-restaurant-inspector-api-dev.hf.space

---

## Future Enhancements

### Training Pipeline
- [ ] Better labeling (LLM-based annotations)
- [ ] More training data (50K+ samples)
- [ ] Hyperparameter tuning
- [ ] Model evaluation metrics
- [ ] A/B testing framework

### Production API
- [ ] GPU inference (10x speedup)
- [ ] Request batching
- [ ] Response caching
- [ ] Rate limiting
- [ ] Authentication
- [ ] Monitoring/metrics (Prometheus)
- [ ] CI/CD pipeline
