"""
Training Metrics Page
=====================

View training run history, model performance, and data quality metrics.
"""

import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import SessionLocal
from app.db.models import TrainingRun, ReviewAnnotation
from sqlalchemy import func, desc

st.set_page_config(page_title="Training", page_icon="🎯", layout="wide")

st.title("🎯 Model Training Metrics")
st.markdown("Monitor training runs, model performance, and data quality.")

# Get training data
with SessionLocal() as session:
    # Get all training runs
    training_runs = session.query(TrainingRun).order_by(desc(TrainingRun.trained_at)).all()
    
    # Get annotation stats
    total_annotations = session.query(func.count(ReviewAnnotation.id)).scalar()
    approved_annotations = session.query(func.count(ReviewAnnotation.id)).filter(
        ReviewAnnotation.annotation_status == 'approved'
    ).scalar()
    draft_annotations = session.query(func.count(ReviewAnnotation.id)).filter(
        ReviewAnnotation.annotation_status == 'draft'
    ).scalar()

# Summary metrics
st.markdown("### Quick Stats")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Training Runs", len(training_runs))

with col2:
    st.metric("✅ Approved Annotations", approved_annotations)

with col3:
    st.metric("📝 Draft Annotations", draft_annotations)

with col4:
    if training_runs:
        latest_f1 = training_runs[0].test_f1 if training_runs[0].test_f1 else 0
        st.metric("Latest F1 Score", f"{latest_f1:.4f}")
    else:
        st.metric("Latest F1 Score", "N/A")

st.markdown("---")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["📊 Training History", "📈 Performance Trends", "ℹ️ Information"])

with tab1:
    st.markdown("### Training Run History")
    
    if not training_runs:
        st.info("No training runs found. Run `python scripts/train.py` to train the model.")
    else:
        # Create dataframe
        runs_data = []
        for run in training_runs:
            runs_data.append({
                "Run ID": run.id,
                "Model": run.model_name or "distilbert-base-uncased",
                "Training Samples": run.training_samples,
                "Test Accuracy": f"{run.test_accuracy:.4f}" if run.test_accuracy else "N/A",
                "Test F1": f"{run.test_f1:.4f}" if run.test_f1 else "N/A",
                "Test Precision": f"{run.test_precision:.4f}" if run.test_precision else "N/A",
                "Test Recall": f"{run.test_recall:.4f}" if run.test_recall else "N/A",
                "Output Path": run.output_path or "N/A",
                "Trained At": run.trained_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        df = pd.DataFrame(runs_data)
        st.dataframe(df, use_container_width=True)
        
        st.markdown("---")
        
        # Show details for latest run
        if training_runs:
            latest_run = training_runs[0]
            st.markdown("### Latest Training Run Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"""
                **Run ID:** {latest_run.id}
                
                **Model:** {latest_run.model_name or 'distilbert-base-uncased'}
                
                **Training Samples:** {latest_run.training_samples}
                
                **Trained At:** {latest_run.trained_at.strftime('%Y-%m-%d %H:%M:%S')}
                
                **Output Path:** `{latest_run.output_path or 'models/aspect-classifier/'}`
                """)
            
            with col2:
                st.success(f"""
                **Performance Metrics:**
                
                - **Accuracy:** {latest_run.test_accuracy:.4f} ({latest_run.test_accuracy*100:.2f}%)
                - **F1 Score:** {latest_run.test_f1:.4f} ({latest_run.test_f1*100:.2f}%)
                - **Precision:** {latest_run.test_precision:.4f} ({latest_run.test_precision*100:.2f}%)
                - **Recall:** {latest_run.test_recall:.4f} ({latest_run.test_recall*100:.2f}%)
                """)

with tab2:
    st.markdown("### Performance Trends Over Time")
    
    if len(training_runs) < 2:
        st.info("Need at least 2 training runs to show trends. Keep training!")
    else:
        # Prepare trend data
        trend_data = {
            "Run ID": [],
            "F1 Score": [],
            "Precision": [],
            "Recall": [],
            "Accuracy": []
        }
        
        for run in reversed(training_runs):  # Oldest first
            trend_data["Run ID"].append(f"Run {run.id}")
            trend_data["F1 Score"].append(run.test_f1 if run.test_f1 else 0)
            trend_data["Precision"].append(run.test_precision if run.test_precision else 0)
            trend_data["Recall"].append(run.test_recall if run.test_recall else 0)
            trend_data["Accuracy"].append(run.test_accuracy if run.test_accuracy else 0)
        
        df_trend = pd.DataFrame(trend_data)
        
        # Use Streamlit's native line chart
        st.line_chart(df_trend.set_index("Run ID"))
        
        st.markdown("---")
        
        # Show improvement/regression
        if len(training_runs) >= 2:
            latest = training_runs[0]
            previous = training_runs[1]
            
            st.markdown("### Change from Previous Run")
            
            col1, col2, col3, col4 = st.columns(4)
            
            def get_delta(current, previous):
                if current and previous:
                    delta = current - previous
                    return f"{delta:+.4f}"
                return "N/A"
            
            with col1:
                delta_f1 = get_delta(latest.test_f1, previous.test_f1)
                st.metric("F1 Score", f"{latest.test_f1:.4f}", delta=delta_f1)
            
            with col2:
                delta_precision = get_delta(latest.test_precision, previous.test_precision)
                st.metric("Precision", f"{latest.test_precision:.4f}", delta=delta_precision)
            
            with col3:
                delta_recall = get_delta(latest.test_recall, previous.test_recall)
                st.metric("Recall", f"{latest.test_recall:.4f}", delta=delta_recall)
            
            with col4:
                delta_accuracy = get_delta(latest.test_accuracy, previous.test_accuracy)
                st.metric("Accuracy", f"{latest.test_accuracy:.4f}", delta=delta_accuracy)

with tab3:
    st.markdown("""
    ### Understanding Training Metrics
    
    **Key Metrics Explained:**
    
    **F1 Score** (Harmonic mean of Precision and Recall)
    - Range: 0.0 to 1.0 (higher is better)
    - Current: ~0.16 (16.5%)
    - Target: >0.40 (40%)
    - **Interpretation:** Overall model quality balance
    
    **Precision** (True Positives / (True Positives + False Positives))
    - How many predicted labels are actually correct
    - High precision = fewer false alarms
    
    **Recall** (True Positives / (True Positives + False Negatives))
    - How many actual labels were found
    - Current: ~0.77 (77%)
    - High recall = catches most aspects
    
    **Accuracy** (Correct Predictions / Total Predictions)
    - Overall correctness across all labels
    
    ---
    
    ### How to Improve Performance
    
    1. **More Training Data**
       - Approve more annotations (target: 500+)
       - Current approved: {approved_annotations}
       
    2. **Better Quality Annotations**
       - Review and fix incorrect AI labels
       - Focus on edge cases and ambiguous reviews
       
    3. **Balanced Dataset**
       - Ensure good mix of positive/negative/mixed examples
       - Cover all 5 aspects evenly
       
    4. **Hyperparameter Tuning**
       - Adjust learning rate
       - Try different epochs
       - Experiment with batch size
    
    ---
    
    ### Training Pipeline
    
    ```bash
    # Run training
    python scripts/train.py
    
    # The script will:
    # 1. Load approved annotations from database
    # 2. Split into train/val/test (60/20/20)
    # 3. Fine-tune DistilBERT for 3 epochs
    # 4. Evaluate on test set
    # 5. Save model to models/aspect-classifier/
    # 6. Log metrics to training_runs table
    ```
    
    ---
    
    ### Current Model Details
    
    - **Architecture:** DistilBERT-base-uncased (66M parameters)
    - **Task:** Multi-label classification (10 binary labels)
    - **Framework:** Hugging Face Transformers + PyTorch
    - **Training Time:** ~10-15 minutes on CPU
    """)

st.markdown("---")
st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
