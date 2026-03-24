"""
Annotations Review Page
=======================

Main workspace for reviewing and approving AI-generated annotations.
"""

import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import SessionLocal
from app.db.models import Review, ReviewAnnotation
from app.db.enums import AnnotationStatus, AspectState
from sqlalchemy import select, and_, or_

st.set_page_config(page_title="Annotations", page_icon="📝", layout="wide")

st.title("📝 Annotation Review & Approval")
st.markdown("Review AI-generated aspect labels and approve quality annotations for training.")

# Filters
st.sidebar.header("🔍 Filters")

# Status filter
status_options = {
    "Draft": AnnotationStatus.DRAFT,
    "Approved": AnnotationStatus.APPROVED,
    "Rejected": AnnotationStatus.REJECTED
}
selected_status = st.sidebar.multiselect(
    "Annotation Status",
    options=list(status_options.keys()),
    default=["Draft"]
)

# Restaurant filter
with SessionLocal() as session:
    from app.db.models import Restaurant
    restaurants = session.query(Restaurant.name).all()
    restaurant_list = [r[0] for r in restaurants]

selected_restaurant = st.sidebar.selectbox(
    "Restaurant",
    options=["All"] + restaurant_list
)

# Date range filter
date_range = st.sidebar.selectbox(
    "Date Range",
    options=["Last 7 days", "Last 30 days", "All time"]
)

# Aspect filter
aspect_filter = st.sidebar.multiselect(
    "Has Aspect Mentioned",
    options=["Food", "Service", "Hygiene", "Parking", "Cleanliness"],
    default=[]
)

# Confidence threshold (simulated for now)
show_high_confidence = st.sidebar.checkbox("High Confidence Only (≥80%)", value=False)

# Apply filters button
apply_filters = st.sidebar.button("🔄 Apply Filters", type="primary")

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Actions")
bulk_approve_count = st.sidebar.number_input("Bulk Approve Count", min_value=1, max_value=100, value=20)
if st.sidebar.button("✅ Bulk Approve Top N"):
    st.sidebar.success(f"Would approve top {bulk_approve_count} drafts")

# Main content area
tab1, tab2, tab3 = st.tabs(["📋 Review List", "📊 Statistics", "ℹ️ Help"])

with tab1:
    # Query database
    with SessionLocal() as session:
        from app.db.models import Restaurant
        query = session.query(
            ReviewAnnotation.id,
            ReviewAnnotation.review_id,
            ReviewAnnotation.food_state,
            ReviewAnnotation.service_state,
            ReviewAnnotation.hygiene_state,
            ReviewAnnotation.parking_state,
            ReviewAnnotation.cleanliness_state,
            ReviewAnnotation.annotation_status,
            ReviewAnnotation.annotator_name,
            ReviewAnnotation.created_at,
            Review.review_text,
            Restaurant.name.label('restaurant_name'),
            Review.overall_sentiment
        ).join(Review, ReviewAnnotation.review_id == Review.id
        ).join(Restaurant, Review.restaurant_id == Restaurant.id)
        
        # Apply status filter
        if selected_status:
            status_enums = [status_options[s] for s in selected_status]
            query = query.filter(ReviewAnnotation.annotation_status.in_(status_enums))
        
        # Apply restaurant filter
        if selected_restaurant != "All":
            query = query.filter(Restaurant.name == selected_restaurant)
        
        # Apply date range filter
        if date_range == "Last 7 days":
            cutoff = datetime.now() - timedelta(days=7)
            query = query.filter(ReviewAnnotation.created_at >= cutoff)
        elif date_range == "Last 30 days":
            cutoff = datetime.now() - timedelta(days=30)
            query = query.filter(ReviewAnnotation.created_at >= cutoff)
        
        results = query.order_by(ReviewAnnotation.created_at.desc()).limit(50).all()
    
    st.markdown(f"### Found {len(results)} annotations")
    
    if len(results) == 0:
        st.info("No annotations found with current filters. Try adjusting the filters.")
    else:
        # Display annotations
        for idx, row in enumerate(results):
            with st.expander(f"**ID: {row.id}** | {row.restaurant_name or 'Unknown'} | Status: {row.annotation_status.value}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("#### Review Text")
                    st.write(f"_{row.review_text}_")
                    
                    if row.overall_sentiment:
                        sentiment_emoji = "😊" if row.overall_sentiment > 0 else "😞"
                        st.caption(f"Overall Sentiment: {sentiment_emoji} {row.overall_sentiment}")
                
                with col2:
                    st.markdown("#### AI Predictions")
                    
                    # Display aspect states with emojis
                    aspects = {
                        "🍔 Food": row.food_state,
                        "👔 Service": row.service_state,
                        "🧼 Hygiene": row.hygiene_state,
                        "🚗 Parking": row.parking_state,
                        "✨ Cleanliness": row.cleanliness_state
                    }
                    
                    for aspect_name, state in aspects.items():
                        if state == AspectState.POSITIVE:
                            st.success(f"{aspect_name}: ✅ POSITIVE")
                        elif state == AspectState.NEGATIVE:
                            st.error(f"{aspect_name}: ❌ NEGATIVE")
                        elif state == AspectState.MIXED:
                            st.warning(f"{aspect_name}: ⚠️ MIXED")
                        else:
                            st.info(f"{aspect_name}: ⚪ NOT MENTIONED")
                
                # Action buttons
                st.markdown("---")
                action_col1, action_col2, action_col3, action_col4 = st.columns(4)
                
                with action_col1:
                    if st.button(f"✅ Approve", key=f"approve_{row.id}"):
                        with SessionLocal() as session:
                            annotation = session.query(ReviewAnnotation).filter_by(id=row.id).first()
                            if annotation:
                                annotation.annotation_status = AnnotationStatus.APPROVED
                                annotation.reviewer_name = "streamlit_admin"
                                session.commit()
                                st.success("Approved!")
                                st.rerun()
                
                with action_col2:
                    if st.button(f"❌ Reject", key=f"reject_{row.id}"):
                        with SessionLocal() as session:
                            annotation = session.query(ReviewAnnotation).filter_by(id=row.id).first()
                            if annotation:
                                annotation.annotation_status = AnnotationStatus.REJECTED
                                annotation.reviewer_name = "streamlit_admin"
                                session.commit()
                                st.success("Rejected!")
                                st.rerun()
                
                with action_col3:
                    if st.button(f"✏️ Edit", key=f"edit_{row.id}"):
                        st.info("Edit mode coming soon!")
                
                with action_col4:
                    st.caption(f"Created: {row.created_at.strftime('%Y-%m-%d %H:%M')}")
                    st.caption(f"By: {row.annotator_name}")

with tab2:
    st.markdown("### Annotation Statistics")
    
    with SessionLocal() as session:
        from sqlalchemy import func
        
        # Status breakdown
        status_counts = session.query(
            ReviewAnnotation.annotation_status,
            func.count(ReviewAnnotation.id)
        ).group_by(ReviewAnnotation.annotation_status).all()
        
        col1, col2, col3 = st.columns(3)
        for status, count in status_counts:
            if status == AnnotationStatus.DRAFT:
                col1.metric("📝 Draft", count)
            elif status == AnnotationStatus.APPROVED:
                col2.metric("✅ Approved", count)
            elif status == AnnotationStatus.REJECTED:
                col3.metric("❌ Rejected", count)
        
        st.markdown("---")
        
        # Aspect mention frequency
        st.markdown("#### Aspect Mention Frequency")
        
        aspects_data = {
            "Aspect": ["Food", "Service", "Hygiene", "Parking", "Cleanliness"],
            "Positive": [],
            "Negative": [],
            "Mixed": [],
            "Not Mentioned": []
        }
        
        for aspect in ["food_state", "service_state", "hygiene_state", "parking_state", "cleanliness_state"]:
            for state in [AspectState.POSITIVE, AspectState.NEGATIVE, AspectState.MIXED, AspectState.NOT_MENTIONED]:
                count = session.query(func.count(ReviewAnnotation.id)).filter(
                    getattr(ReviewAnnotation, aspect) == state
                ).scalar()
                
                if state == AspectState.POSITIVE:
                    aspects_data["Positive"].append(count)
                elif state == AspectState.NEGATIVE:
                    aspects_data["Negative"].append(count)
                elif state == AspectState.MIXED:
                    aspects_data["Mixed"].append(count)
                else:
                    aspects_data["Not Mentioned"].append(count)
        
        df = pd.DataFrame(aspects_data)
        st.dataframe(df, use_container_width=True)

with tab3:
    st.markdown("""
    ### How to Use This Page
    
    **Filtering:**
    - Use the sidebar filters to narrow down annotations
    - Select status (Draft/Approved/Rejected)
    - Filter by restaurant or date range
    - Apply filters to refresh the list
    
    **Reviewing:**
    - Click on an annotation to expand and review
    - Check if AI predictions match the review text
    - Look for keywords that justify the labels
    
    **Actions:**
    - ✅ **Approve**: Mark annotation as approved for training
    - ❌ **Reject**: Mark as rejected (won't be used)
    - ✏️ **Edit**: Modify labels before approving (coming soon)
    
    **Bulk Operations:**
    - Use the sidebar "Bulk Approve" for high-confidence batches
    - Saves time on obvious correct predictions
    
    **Tips:**
    - Start with high-confidence drafts
    - Manually review low ratings or edge cases
    - Check that aspect labels match review sentiment
    """)

st.markdown("---")
st.caption(f"Showing up to 50 results | Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
