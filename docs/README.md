# Documentation

This folder contains comprehensive documentation for the Restaurant Inspector annotation workflow and training system.

## Documents

### 1. [Architecture](architecture.md)
**Database-backed annotation workflow architecture** showing the complete infrastructure for aspect-based sentiment analysis.

Topics covered:
- PostgreSQL database schema (Neon hosted)
- SQLAlchemy ORM + Alembic migrations
- Annotation workflow (draft → review → approve)
- Training pipeline with DistilBERT
- Model evaluation and metrics logging
- Audit trails and version control

**Diagram**: `architecture-diagram.png`

---

### 2. [Annotation Workflow](flow.md)
**Detailed workflow diagram** showing the complete annotation lifecycle from data ingestion to model training.

Topics covered:
- Data ingestion from Yelp dataset
- Heuristic draft annotation generation
- Human review and approval process
- Train/validation/test splits
- Model training on approved annotations
- Metrics logging to database
- Reproducible training pipeline

**Diagrams**: 
- `annotation-workflow.png` - Complete lifecycle flowchart
- `sequence-diagram.png` - Detailed interaction sequence

---

### 3. [System Components](system-components.md)
**Component-level breakdown** of the database schema, scripts, and training infrastructure.

Topics covered:
- Database Schema:
  - `reviews` table - raw review storage
  - `review_annotations` table - aspect labels with audit trails
  - `training_runs` table - metrics and model versioning
- Scripts:
  - `bootstrap_reviews.py` - data ingestion
  - `generate_draft_annotations.py` - heuristic labeling
  - `approve_annotations.py` - approval workflow
  - `train.py` - DistilBERT fine-tuning
- ORM Models and Enums
- Migration system with Alembic

**Diagram**: `system-components.png`

---

## Quick Reference

### Current System Status (March 2026)

**Database**: Neon Postgres
- 300 reviews ingested
- 200 approved annotations ready for training
- 3 training runs logged

**Model**: DistilBERT-base-uncased
- Trained on 120 samples (60% split)
- Test F1: 0.1646 (16.5%)
- Multi-label classification: 10 binary labels

**Schema Version**: 
- Migration 1: `20260323_0001` (reviews + review_annotations)
- Migration 2: `5eed963bbc03` (training_runs + reviewer_name)

---

## Documentation Standards

All diagrams are provided as **PNG images** for fast viewing. Raw Mermaid syntax is available in [mermaid-syntax.md](mermaid-syntax.md) for editing and regeneration.

---

### 4. [Mermaid Syntax](mermaid-syntax.md)
Raw Mermaid diagram code for all architecture diagrams. Use this to:
- Regenerate PNG diagrams
- Customize visualizations
- Create variations
- Edit diagram structure

---

## Diagram Files

All diagram PNG files in this folder:

- `architecture-diagram.png` - High-level system architecture (horizontal layout)
- `annotation-workflow.png` - Complete annotation lifecycle (5 phases)
- `sequence-diagram.png` - Detailed interaction flow with database
- `system-components.png` - Component-level view (horizontal layout)
- `database-schema.png` - ER diagram with table relationships

To regenerate diagrams: Copy Mermaid code from [mermaid-syntax.md](mermaid-syntax.md) to [mermaid.live](https://mermaid.live/) and export as PNG.

---

## Viewing

### Locally
Open any `.md` file in VS Code, GitHub Desktop, or any Markdown viewer.

### GitHub
Push to GitHub and view in the repository. Mermaid diagrams render automatically in GitHub Markdown.

```bash
# Example: Push docs to GitHub
git add docs/
git commit -m "Add comprehensive architecture documentation"
git push origin main
```

### Online Mermaid Editors
- [Mermaid Live Editor](https://mermaid.live/)
- [Mermaid Chart](https://www.mermaidchart.com/)

Copy syntax from `mermaid-syntax.md` to edit diagrams.

---

## API Documentation

For interactive API documentation, visit:
- **Swagger UI**: https://dpratapx-restaurant-inspector-api-dev.hf.space/docs
- **ReDoc**: https://dpratapx-restaurant-inspector-api-dev.hf.space/redoc

---

## Contributing

To update documentation:

1. Edit the relevant `.md` file
2. Update Mermaid syntax in `mermaid-syntax.md` if diagrams change
3. Regenerate diagram images if needed
4. Commit and push changes

---

## License

This documentation is part of the Restaurant Inspector project.
