"""
Fix for Streamlit Cloud deployment errors and UI improvements
"""

import streamlit as st
import sqlite3
import os

def fix_payment_page_errors():
    """Add error handling for payment page"""
    try:
        # Check database connection
        db_path = 'trailer_tracker_streamlined.db' if os.path.exists('trailer_tracker_streamlined.db') else 'trailer_data.db'
        conn = sqlite3.connect(db_path)
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return False

def clear_streamlit_cache():
    """Clear Streamlit cache to fix module import errors"""
    try:
        st.cache_data.clear()
        st.cache_resource.clear()
        return True
    except:
        return False

def add_mileage_preview_realtime():
    """Enhanced mileage calculator with real-time preview"""
    return {
        'show_preview': True,
        'auto_calculate': True,
        'display_format': 'inline'
    }