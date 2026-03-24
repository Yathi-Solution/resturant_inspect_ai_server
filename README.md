---
title: Restaurant Inspector API
emoji: 🍽️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 🍽️ Restaurant Inspector

**Production-grade NLP annotation workflow and aspect-based sentiment analysis** for restaurant reviews.

Extracts structured insights across 5 dimensions using DistilBERT with a **human-in-the-loop annotation pipeline**.

## 🚀 Features

- **Multi-Aspect Sentiment**: 4-state labeling (positive/negative/mixed/not_mentioned) for 5 aspects
- **Annotation Workflow**: Draft → Review → Approve with full audit trails
- **Database-Backed**: PostgreSQL schema with SQLAlchemy ORM + Alembic migrations
- **Trained Model**: DistilBERT fine-tuned on 200 professionally approved annotations
- **Production-Ready**: FastAPI inference server with logged metrics
- **Reproducible**: Version-controlled schema and training pipeline

## 🧠 Technology Stack

- **Model**: DistilBERT-base-uncased (66M parameters, fine-tuned)
- **Database**: PostgreSQL (Neon hosted) with SQLAlchemy 2.0 + Alembic
- **ML Framework**: Hugging Face Transformers + PyTorch
- **API Framework**: FastAPI + Uvicorn
- **Data Source**: Yelp Polarity dataset (Hugging Face Datasets)
- **Python**: 3.11+

## � Aspect Analysis

The model scores reviews across 5 dimensions with 4-state sentiment:

| Aspect | States | Description |
|--------|--------|-------------|
| 🍕 **Food** | ✅ Positive / ❌ Negative / ⚖️ Mixed / ➖ Not Mentioned | Quality, taste, freshness |
| 👥 **Service** | ✅ Positive / ❌ Negative / ⚖️ Mixed / ➖ Not Mentioned | Staff, speed, attentiveness |
| 🧼 **Hygiene** | ✅ Positive / ❌ Negative / ⚖️ Mixed / ➖ Not Mentioned | Cleanliness, sanitation |
| 🅿️ **Parking** | ✅ Positive / ❌ Negative / ⚖️ Mixed / ➖ Not Mentioned | Availability, convenience |
| ✨ **Cleanliness** | ✅ Positive / ❌ Negative / ⚖️ Mixed / ➖ Not Mentioned | Ambiance, maintenance |

## 📦 Installation

### Prerequisites

- Python 3.11+
- PostgreSQL database (we use [Neon](https://neon.tech) for hosted Postgres)
- 2GB+ RAM for model training

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd resturant-inspector-server
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install sqlalchemy alembic psycopg2-binary datasets transformers torch scikit-learn python-dotenv fastapi uvicorn
```

### 4. Configure Database

Create `.env` file:

```env
DATABASE_URL=postgresql://user:password@host/database
```

### 5. Run Migrations

```bash
alembic upgrade head
```

## 🎯 Annotation Workflow

### Step 1: Bootstrap Reviews

Load Yelp reviews into database:

```bash
$env:PYTHONPATH='.'  # Windows PowerShell
python scripts/bootstrap_reviews.py --count 300
```

Result: 300 reviews in `reviews` table

### Step 2: Generate Draft Annotations

Create heuristic labels using keyword rules:

```bash
$env:PYTHONPATH='.'
python scripts/generate_draft_annotations.py --limit 300 --annotator "data_analyst_v1"
```

Result: 300 draft annotations with `status='draft'`

### Step 3: Approve Annotations

Review and approve annotations for training:

```bash
# View current status
$env:PYTHONPATH='.'
python scripts/approve_annotations.py --summary

# Approve first 200 drafts
python scripts/approve_annotations.py --approve-count 200 --reviewer "senior_analyst_v1"
```

Result: 200 annotations marked `status='approved'`

### Step 4: Train Model

Train DistilBERT on approved annotations:

```bash
$env:PYTHONPATH='.'
python scripts/train.py
```

This will:
1. Load 200 approved annotations from database
2. Split into 120 train / 40 val / 40 test
3. Fine-tune DistilBERT (3 epochs)
4. Evaluate on test set
5. Save model to `models/aspect-classifier/`
6. Log metrics to `training_runs` table

**Training time**: ~10-15 minutes (CPU) or ~2 minutes (GPU)

## 🏃 Running the API Server

### Start FastAPI Server

```bash
uvicorn main:app --reload
```

Server runs at: http://localhost:8000

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing the API

### Using curl

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "Amazing biryani but terrible parking and dirty bathrooms"}'
```

### Expected Response

```json
{
  "food": "positive",
  "service": "not_mentioned",
  "hygiene": "negative",
  "parking": "negative",
  "cleanliness": "negative"
}
```

## 🎨 Streamlit Admin Dashboard

**NEW!** Visual annotation management and monitoring tool for internal use.

### Quick Start

```bash
# One-command setup and launch (Windows)
.\start_dashboard.ps1
```

Or manually:

```bash
# Install Streamlit dependencies
pip install streamlit pandas plotly

# Apply latest migrations (includes restaurants table)
alembic upgrade head

# Start dashboard
streamlit run streamlit_app/Home.py
```

Opens at: **http://localhost:8501**

### Pages

- **🏠 Home**: System overview with quick stats and navigation
- **Annotations.py**: Review and approve AI-generated labels
  - Filter by restaurant, status, date, aspect
  - View AI predictions for all 5 aspects
  - Approve/reject individual annotations
  - Real-time status updates
  
- **Training.py**: Monitor model performance
  - Training run history with metrics (F1, Precision, Recall)
  - Performance trend charts over time
  - Training data quality statistics

### Database Structure

The dashboard uses a **normalized database** with proper foreign key relationships:

```
restaurants (master table)
├── id, name, address, phone
└── Referenced by reviews.restaurant_id

reviews
├── restaurant_id → restaurants.id
└── Review text + metadata

review_annotations
├── review_id → reviews.id
└── Aspect labels + approval status
```

Current restaurant: **Niloufer** (Hyderabad, India)

### Workflow

1. **View Annotations** → Filter and browse AI predictions
2. **Approve/Reject** → Update annotation status in database
3. **Train Model** → Run `python scripts/train.py` in terminal
4. **View Results** → Check Training page for metrics

### Use Cases

- **Client Demo**: Show professional annotation workflow with visual UI
- **Quality Control**: Manual review of model predictions
- **Data Curation**: Approve high-quality training data before model training
- **Progress Tracking**: Monitor annotation counts and training runs

**Note**: Streamlit runs locally for demos. FastAPI is deployed to Hugging Face Spaces for production inference.

See [`streamlit_app/README.md`](streamlit_app/README.md) for detailed usage guide.

---

## 📊 Model Performance

**Current Model** (trained on 200 approved samples):

```
Training samples:  120
Validation:        40
Test:              40

Test Precision:    9.2%
Test Recall:       77.1%
Test F1:           16.5%
```

**Why low precision?**
- Small dataset (200 samples total)
- Class imbalance (most reviews don't mention all aspects)
- Heuristic labels contain noise

**Improvement roadmap**:
- Approve 500+ annotations → F1 > 40%
- Tune per-aspect decision thresholds
- Try RoBERTa or ALBERT

## 📁 Project Structure

```
resturant-inspector-server/
├── alembic/                    # Database migrations
│   ├── versions/
│   │   ├── 20260323_0001_*.py  # Initial schema
│   │   └── 5eed963bbc03_*.py   # Training runs table
│   └── env.py
├── app/
│   ├── db/
│   │   ├── models.py           # Review, ReviewAnnotation, TrainingRun
│   │   ├── enums.py            # AspectState, AnnotationStatus, LabelSource
│   │   ├── session.py          # Database session factory
│   │   └── base.py
│   └── core/
│       └── labeling.py         # Heuristic labeling logic
├── scripts/
│   ├── bootstrap_reviews.py    # Load Yelp data
│   ├── generate_draft_annotations.py  # Create draft labels
│   ├── approve_annotations.py  # Approve workflow
│   └── train.py                # Train DistilBERT
├── models/
│   └── aspect-classifier/      # Trained model outputs
│       ├── model.safetensors
│       ├── config.json
│       ├── tokenizer.json
│       └── metadata.json
├── .env                        # DATABASE_URL
├── alembic.ini
├── PROJECT_STATUS.md           # Detailed project documentation
└── README.md
```

## 🗄️ Database Schema

### `reviews`
Stores raw review text from external sources

### `review_annotations`
Aspect-level annotations with audit trails
- **States**: draft → reviewed → approved → rejected
- **Sources**: heuristic, manual, heuristic_reviewed
- **Tracks**: annotator_name, reviewer_name, timestamps, confidence

### `training_runs`
Logs all model training runs with metrics

## 🛠️ Development Commands

### View Training History

```bash
$env:PYTHONPATH='.'
.\venv\Scripts\python -c "from app.db.session import SessionLocal; from app.db.models import TrainingRun; s = SessionLocal(); [print(f'Run {r.id}: F1={r.test_f1:.4f}') for r in s.query(TrainingRun).all()]; s.close()"
```

### Check Annotation Status

```bash
$env:PYTHONPATH='.'
python scripts/approve_annotations.py --summary
```

Output:
```
=== Annotation Status Summary ===
  approved: 200
  draft: 100
  TOTAL: 300 (66.7% approved)
```

### Approve More Annotations

```bash
python scripts/approve_annotations.py --approve-count 50 --reviewer "your_name"
```

## 🚀 Deploying to Production

### Option 1: Render

1. Push to GitHub
2. Create new Web Service on Render
3. Connect your repository
4. Set environment variable: `DATABASE_URL`
5. Build command: `pip install -r requirements.txt`
6. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Option 2: Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔧 Troubleshooting

### ModuleNotFoundError: No module named 'app'

Set PYTHONPATH before running scripts:

```powershell
# Windows PowerShell
$env:PYTHONPATH='.'

# Linux/Mac
export PYTHONPATH=.
```

### Database connection fails

Check `.env` file exists and `DATABASE_URL` is correct:
```bash
echo $env:DATABASE_URL  # Windows
echo $DATABASE_URL      # Linux/Mac
```

### Training runs out of memory

Reduce batch size in `scripts/train.py`:
```python
per_device_train_batch_size=4,  # default is 8
```

## 📚 Additional Resources

- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Detailed project overview and client responses
- **Alembic Docs**: https://alembic.sqlalchemy.org/
- **Hugging Face Transformers**: https://huggingface.co/docs/transformers
- **FastAPI Docs**: https://fastapi.tiangolo.com/

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-aspect`
3. Commit changes: `git commit -am 'Add new aspect'`
4. Push: `git push origin feature/new-aspect`
5. Submit Pull Request

## 📄 License

[Add license info]

## 👤 Contact

**Project**: Restaurant Inspector  
**Database**: Neon Postgres  
**Model**: DistilBERT (Hugging Face)  

---

**Built with** Python • PostgreSQL • Transformers • PyTorch • FastAPI
- **PARKING**: parking, no space
- **CLEANLINESS**: clean, messy, well-maintained

## 📝 Project Structure

```
resturant-inspector-server/
├── pyproject.toml          # Dependencies
├── train.py                # Training script
├── main.py                 # FastAPI application
├── README.md               # This file
├── .gitignore             # Git ignore rules
├── venv/                  # Virtual environment (not committed)
└── model/                 # Trained model (generated, not committed)
    ├── config.json
    ├── model.safetensors
    └── tokenizer files
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run linting: `ruff check --fix .`
5. Format code: `ruff format .`
6. Submit a pull request

## 📄 License

MIT License

## 🙏 Acknowledgments

- Hugging Face for Transformers library
- Yelp for the dataset
- FastAPI team for the framework

## 📞 Support

For issues or questions, please open a GitHub issue.

---

**Built with ❤️ using Python, FastAPI, and DistilBERT**
