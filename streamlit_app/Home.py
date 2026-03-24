"""
Restaurant Inspector Admin Dashboard
=====================================

Internal tool for managing annotation workflow and monitoring training data quality.

Pages:
- 🏠 Home: Overview and statistics
- 📝 Annotations: Review and approve AI-generated labels
- 🎯 Training: Model training metrics and history
"""

import streamlit as st

st.set_page_config(
    page_title="Restaurant Inspector Admin",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🍽️ Restaurant Inspector Admin Dashboard")
st.markdown("""
Welcome to the Restaurant Inspector annotation management system.

### Quick Stats
""")

# Import database session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.db.models import Review, ReviewAnnotation, TrainingRun
from sqlalchemy import func

# Get stats from database
with SessionLocal() as session:
    total_reviews = session.query(func.count(Review.id)).scalar()
    total_annotations = session.query(func.count(ReviewAnnotation.id)).scalar()
    
    approved_count = session.query(func.count(ReviewAnnotation.id)).filter(
        ReviewAnnotation.annotation_status == 'approved'
    ).scalar()
    
    draft_count = session.query(func.count(ReviewAnnotation.id)).filter(
        ReviewAnnotation.annotation_status == 'draft'
    ).scalar()
    
    training_runs = session.query(func.count(TrainingRun.id)).scalar()

# Display metrics
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Reviews", total_reviews)

with col2:
    st.metric("Total Annotations", total_annotations)

with col3:
    st.metric("✅ Approved", approved_count)

with col4:
    st.metric("📝 Drafts", draft_count)

with col5:
    st.metric("🎯 Training Runs", training_runs)

st.markdown("---")

st.markdown("""
### System Overview

**Annotation Workflow:**
1. **Ingest Reviews** → Load from Yelp dataset or user submissions
2. **Generate Drafts** → AI automatically labels aspects
3. **Human Review** → Use the Annotations page to approve/reject
4. **Train Model** → Approved annotations used for training
5. **Deploy** → Updated model serves predictions

**Navigation:**
- Use the sidebar to navigate between pages
- **Annotations** page is the main workspace
- **Training** page shows model performance metrics

### Quick Actions
""")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    **📝 Review Annotations**
    
    Go to the Annotations page to:
    - Review AI-generated labels
    - Approve good predictions
    - Fix incorrect labels
    - Bulk approve high-confidence annotations
    """)

with col2:
    st.success("""
    **🎯 Training Status**
    
    Check the Training page for:
    - Model performance metrics
    - Training run history
    - Data quality statistics
    - F1, Precision, Recall scores
    """)

st.markdown("---")
st.caption("🔐 Internal Admin Tool - Dev Environment")
