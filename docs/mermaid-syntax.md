# Mermaid Diagram Syntax Reference

This file contains the Mermaid syntax for all Restaurant Inspector architecture diagrams.

**Last Updated**: March 24, 2026  
**System**: Database-backed annotation workflow with PostgreSQL + DistilBERT

---

## Architecture Diagram

Database-backed annotation workflow showing PostgreSQL, scripts, ORM, and training pipeline.
**Layout**: Horizontal (left-to-right) for better visibility in one view.

```mermaid
graph LR
    DS[Yelp Dataset<br/>HuggingFace] --> S1[bootstrap_reviews.py]
    S1 -->|INSERT| DB1[(reviews table<br/>300 rows)]
    
    DB1 --> S2[generate_draft<br/>_annotations.py]
    LAB[labeling.py<br/>Heuristics] -.->|Used by| S2
    S2 -->|INSERT| DB2[(review_annotations<br/>300 drafts)]
    
    DB2 --> S3[approve_<br/>annotations.py]
    S3 -->|UPDATE| DB2
    DB2 -->|200 approved| TR[train.py]
    
    TR --> ML[DistilBERT<br/>Fine-tune]
    ML --> EVAL[Evaluate<br/>Metrics]
    EVAL -->|Save| MODEL[model.safetensors<br/>config.json]
    EVAL -->|Log| DB3[(training_runs<br/>3 runs)]
    
    ORM[SQLAlchemy<br/>Models] -.->|Define| DB1
    ORM -.->|Define| DB2
    ORM -.->|Define| DB3
    
    style DB2 fill:#fff4e1,stroke:#333,stroke-width:2px
    style ML fill:#ffe1e1
    style MODEL fill:#e1ffe1
    style DB1 fill:#e1f5ff
    style DB2 fill:#e1f5ff
    style DB3 fill:#e1f5ff
```

---

## Annotation Workflow Diagram

Complete annotation lifecycle from ingestion to model training.

```mermaid
flowchart TD
    Start([Start]) --> Ingest
    
    subgraph "Phase 1: Data Ingestion"
        Ingest[Load Yelp Reviews<br/>bootstrap_reviews.py]
        Ingest --> DB1[(reviews table<br/>300 records)]
    end
    
    subgraph "Phase 2: Draft Annotation"
        DB1 --> Draft[Generate Heuristic Labels<br/>generate_draft_annotations.py]
        Draft --> Keywords[Keyword Matching<br/>5 aspects × 4 states]
        Keywords --> DB2[(review_annotations<br/>status=draft<br/>300 records)]
    end
    
    subgraph "Phase 3: Human Review"
        DB2 --> Review[Review Annotations<br/>approve_annotations.py]
        Review --> Decision{Quality Check}
        Decision -->|Approve| Approved[(status=approved<br/>200 records)]
        Decision -->|Reject| Rejected[(status=rejected)]
        Decision -->|Needs Work| DB2
    end
    
    subgraph "Phase 4: Model Training"
        Approved --> Load[Load Approved Data<br/>scripts/train.py]
        Load --> Transform[Transform Labels<br/>4-state → 10 binary]
        Transform --> Split[Split Data<br/>60/20/20]
        Split --> Train[Fine-tune DistilBERT<br/>3 epochs]
        Train --> Eval[Evaluate on Test Set<br/>Precision/Recall/F1]
    end
    
    subgraph "Phase 5: Model Persistence"
        Eval --> Save[Save Model<br/>models/aspect-classifier/]
        Eval --> Log[(training_runs table<br/>metrics logged)]
    end
    
    Save --> End([End])
    Log --> End
    
    style Ingest fill:#e1f5ff
    style Draft fill:#fff4e1
    style Review fill:#ffe1e1
    style Train fill:#e1ffe1
    style Save fill:#f0e1ff
```

---

## Sequence Diagram - Annotation Pipeline

Detailed sequence showing database interactions during annotation workflow.

```mermaid
sequenceDiagram
    participant Admin
    participant Scripts
    participant DB as PostgreSQL
    participant HF as HuggingFace
    participant Model as DistilBERT
    
    Note over Admin,Model: Phase 1: Data Ingestion
    Admin->>Scripts: python bootstrap_reviews.py --count 300
    Scripts->>HF: Load yelp_polarity dataset
    HF-->>Scripts: 300 review texts
    Scripts->>DB: INSERT INTO reviews
    DB-->>Scripts: 300 rows inserted
    
    Note over Admin,Model: Phase 2: Draft Generation
    Admin->>Scripts: python generate_draft_annotations.py
    Scripts->>DB: SELECT reviews WHERE no annotations
    DB-->>Scripts: 300 unlabeled reviews
    Scripts->>Scripts: infer_aspect_states()<br/>keyword matching
    Scripts->>DB: INSERT INTO review_annotations<br/>status=draft, source=heuristic
    DB-->>Scripts: 300 drafts created
    
    Note over Admin,Model: Phase 3: Approval
    Admin->>Scripts: python approve_annotations.py --list 10
    Scripts->>DB: SELECT * WHERE status=draft LIMIT 10
    DB-->>Scripts: Draft annotations
    Scripts-->>Admin: Display: ID, aspects, keywords
    
    Admin->>Scripts: python approve_annotations.py --approve-count 200
    Scripts->>DB: UPDATE review_annotations<br/>SET status=approved, reviewer_name=...<br/>WHERE status=draft LIMIT 200
    DB-->>Scripts: 200 rows updated
    Scripts-->>Admin: ✅ 200 annotations approved
    
    Note over Admin,Model: Phase 4: Training
    Admin->>Scripts: python scripts/train.py
    Scripts->>DB: SELECT * FROM review_annotations<br/>WHERE status=approved
    DB-->>Scripts: 200 approved annotations
    Scripts->>Scripts: Convert 4-state → 10 binary labels
    Scripts->>Scripts: Split 60/20/20 (120/40/40)
    Scripts->>Model: Load distilbert-base-uncased
    Model-->>Scripts: Model loaded (66M params)
    Scripts->>Model: Fine-tune(train_data, epochs=3)
    Model->>Model: Gradient descent + backprop
    Model-->>Scripts: Training complete
    Scripts->>Model: Evaluate(test_data)
    Model-->>Scripts: Metrics: F1=0.1646, Recall=0.7714
    
    Note over Admin,Model: Phase 5: Persistence
    Scripts->>Scripts: Save model weights
    Scripts-->>Scripts: models/aspect-classifier/
    Scripts->>DB: INSERT INTO training_runs<br/>(metrics, timestamp)
    DB-->>Scripts: Run ID=3 logged
    Scripts-->>Admin: ✅ Training complete!
```

---

## System Components Diagram

Component-level view with database at the center.

```mermaid
graph LR
    DS[Yelp Dataset] --> S1[bootstrap_reviews.py]
    S1 --> T1[(reviews table<br/>300 rows)]
    
    T1 --> S2[generate_draft<br/>_annotations.py]
    S2 --> T2[(review_annotations<br/>300 drafts)]
    
    T2 --> S3[approve_<br/>annotations.py]
    S3 --> T2
    
    T2 --> S4[train.py]
    S4 --> BERT[DistilBERT<br/>Classifier]
    BERT --> MODEL[Model Artifacts<br/>safetensors]
    BERT --> T3[(training_runs<br/>3 runs)]
    
    LAB[labeling.py] -.->|Used by| S2
    ORM[SQLAlchemy<br/>Models] -.->|Define| T1
    ORM -.->|Define| T2
    ORM -.->|Define| T3
    SESS[SessionLocal] -.->|Connect| T1
    SESS -.->|Connect| T2
    SESS -.->|Connect| T3
    
    style T1 fill:#e1f5ff
    style T2 fill:#fff4e1,stroke:#333,stroke-width:2px
    style T3 fill:#e1f5ff
    style BERT fill:#ffe1e1
    style MODEL fill:#e1ffe1
```

---

## Database Schema ER Diagram

Entity-relationship diagram showing table relationships.

```mermaid
erDiagram
    reviews ||--o{ review_annotations : "has many"
    
    reviews {
        int id PK
        string source
        string source_review_id
        text review_text
        int overall_sentiment
        string language_code
        timestamp ingested_at
        timestamp created_at
        timestamp updated_at
    }
    
    review_annotations {
        int id PK
        int review_id FK
        aspect_state food_state
        aspect_state service_state
        aspect_state hygiene_state
        aspect_state parking_state
        aspect_state cleanliness_state
        annotation_status status
        label_source source
        string annotator_name
        string reviewer_name
        text review_notes
        numeric confidence_score
        timestamp reviewed_at
        timestamp created_at
        timestamp updated_at
    }
    
    training_runs {
        int id PK
        string model_name
        int training_samples
        numeric test_accuracy
        numeric test_f1
        numeric test_precision
        numeric test_recall
        string output_path
        timestamp trained_at
        timestamp created_at
    }
```

---

## Usage Examples

### Rendering Diagrams

**In Markdown files** (GitHub, GitLab, VS Code with Mermaid extension):
````markdown
```mermaid
graph TB
    A[Start] --> B[End]
```
````

**In live documentation** (MkDocs, Docusaurus, etc.):
- Install mermaid plugin
- Use same syntax as above

**Online editors**:
- https://mermaid.live/ - Official live editor
- https://mermaid.ink/ - Generate PNG/SVG images

### Customization

**Color Schemes**:
```mermaid
style NodeName fill:#color,stroke:#color,stroke-width:2px
```

Common colors:
- Blue: `#e1f5ff` - Database/storage
- Red: `#ffe1e1` - Processing/computation
- Green: `#e1ffe1` - Output/results
- Yellow: `#fff4e1` - Key focus areas
- Purple: `#f0e1ff` - External services

**Node Shapes**:
- `[Text]` - Rectangle
- `(Text)` - Rounded rectangle
- `([Text])` - Stadium
- `[[Text]]` - Subroutine
- `[(Text)]` - Cylinder (database)
- `{Text}` - Diamond (decision)

**Line Types**:
- `-->` - Solid arrow
- `-.->` - Dotted arrow
- `==>` - Thick arrow
- `---` - Solid line (no arrow)

---

## Diagram Maintenance

**When to update**:
- Schema changes (new tables, columns)
- New scripts or components added
- Workflow changes (approval process, etc.)
- Migration updates

**How to update**:
1. Edit this file with new Mermaid syntax
2. Copy updated diagram to relevant .md file in `/docs`
3. Test rendering in VS Code or mermaid.live
4. Commit changes with descriptive message

**Version Control**:
- All diagrams versioned in Git
- Track changes alongside code
- Reference commit hash in architecture docs
