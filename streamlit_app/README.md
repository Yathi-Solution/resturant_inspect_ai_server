# Restaurant Inspector - Streamlit Admin Dashboard

Internal annotation management tool for the Restaurant Inspector project.

## Features

- **🏠 Home Dashboard**: Overview statistics and quick actions
- **📝 Annotations Page**: Review and approve AI-generated labels
- **🎯 Training Page**: Model performance metrics and training history

## Installation

### Prerequisites

1. Python 3.10+ with virtual environment activated
2. PostgreSQL database running (Neon or local)
3. Database migrations applied

### Install Dependencies

```bash
pip install streamlit pandas plotly
```

Or add to your existing environment:
```bash
pip install -r requirements.txt
```

## Running the App

### 1. Apply Database Migration (One-time)

```bash
# Add restaurant_name column to reviews table
alembic upgrade head
```

### 2. Start the Streamlit App

```bash
# From project root directory
cd streamlit_app
streamlit run Home.py
```

The app will open in your browser at: `http://localhost:8501`

### 3. (Optional) Run Backend API

If you need the FastAPI backend running:
```bash
# In a separate terminal
uvicorn main:app --reload --port 8000
```

## Usage Guide

### Annotations Workflow

1. **Filter Annotations**
   - Use sidebar filters to narrow down results
   - Filter by status (Draft/Approved/Rejected)
   - Filter by restaurant or date range
   
2. **Review AI Predictions**
   - Click on an annotation to expand
   - Review the text and predicted aspect labels
   - Check if predictions match the review content

3. **Approve/Reject**
   - Click ✅ Approve for correct predictions
   - Click ❌ Reject for incorrect or low-quality annotations
   - Bulk approve high-confidence drafts from sidebar

4. **Monitor Progress**
   - Check Statistics tab for approval rates
   - View aspect mention frequencies

### Training Metrics

1. **View Training History**
   - See all training runs with metrics
   - Compare performance over time
   
2. **Track Improvements**
   - Monitor F1, Precision, Recall trends
   - Identify if model is improving

3. **Understand Metrics**
   - Read the Information tab for metric explanations
   - Learn how to improve model performance

## File Structure

```
streamlit_app/
├── Home.py                    # Main entry point
└── pages/
    ├── 1_📝_Annotations.py    # Annotation review interface
    └── 2_🎯_Training.py        # Training metrics dashboard
```

## Configuration

The app reads directly from your database using the existing `app/db/session.py` connection.

Ensure your `.env` file has:
```
DATABASE_URL=postgresql://user:pass@host/database
```

## Tips for Demo

### Preparing for Client Demo

1. **Pre-Demo Checklist**
   ```bash
   # Ensure you have data
   python scripts/bootstrap_reviews.py --count 300
   python scripts/generate_draft_annotations.py --limit 300
   python scripts/approve_annotations.py --approve-count 200
   python scripts/train.py
   
   # Start the dashboard
   cd streamlit_app
   streamlit run Home.py
   ```

2. **Demo Flow**
   - Start with Home page showing overview stats
   - Navigate to Annotations page
   - Show filtering capabilities
   - Demonstrate approval workflow
   - Show bulk operations
   - Go to Training page
   - Show training history and metrics
   - Explain how metrics show model quality

3. **Key Points to Emphasize**
   - Professional annotation workflow
   - Quality control process
   - Audit trail (who approved, when)
   - Data-driven approach
   - Production-ready infrastructure

## Troubleshooting

**App won't start:**
- Check if port 8501 is available
- Ensure database connection is working
- Verify migrations are applied

**No data showing:**
- Run bootstrap and annotation generation scripts
- Check database has reviews and annotations
- Verify DATABASE_URL in .env

**Import errors:**
- Ensure you're in the project root when running
- Check virtual environment is activated
- Install missing dependencies

## Next Steps

After demo, consider adding:
- Edit annotation functionality
- Advanced filtering (by confidence score)
- Export annotations to CSV
- Batch operations with confirmation dialogs
- Authentication for production use
