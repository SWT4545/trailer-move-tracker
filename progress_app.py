"""
Read-Only Progress Dashboard
This can be run separately for read-only access to operational metrics
Run with: streamlit run progress_app.py
"""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import database as db
import progress_dashboard
import branding

# Page configuration
st.set_page_config(
    page_title="Progress Dashboard - Smith and Williams Trucking",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize database
db.init_database()

# Simple password protection for progress dashboard
def check_dashboard_password():
    """Check if user has the correct password for progress dashboard"""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # Use a different password for progress dashboard (could be stored in secrets)
        if st.session_state["dashboard_password"] == "progress123":  # Change this password
            st.session_state["dashboard_authenticated"] = True
            del st.session_state["dashboard_password"]
        else:
            st.session_state["dashboard_authenticated"] = False

    if "dashboard_authenticated" not in st.session_state:
        # First run, show input for password
        st.markdown(branding.get_header_html(), unsafe_allow_html=True)
        st.title("🔒 Progress Dashboard Access")
        st.text_input(
            "Enter Dashboard Password", 
            type="password", 
            on_change=password_entered, 
            key="dashboard_password"
        )
        st.info("This is a read-only view of operational metrics. No financial data is displayed.")
        return False
    elif not st.session_state["dashboard_authenticated"]:
        # Password not correct, show input + error
        st.markdown(branding.get_header_html(), unsafe_allow_html=True)
        st.title("🔒 Progress Dashboard Access")
        st.text_input(
            "Enter Dashboard Password", 
            type="password", 
            on_change=password_entered, 
            key="dashboard_password"
        )
        st.error("❌ Incorrect password")
        return False
    else:
        # Password correct
        return True

# Main app
def main():
    if not check_dashboard_password():
        st.stop()
    
    # Show the read-only progress dashboard
    progress_dashboard.show_progress_dashboard(read_only=True)
    
    # Add a minimal sidebar with logout option
    with st.sidebar:
        st.markdown(branding.LOGO_SVG, unsafe_allow_html=True)
        st.title("Smith and Williams")
        st.caption("Progress Dashboard")
        
        if st.button("🔒 Logout"):
            st.session_state["dashboard_authenticated"] = False
            st.rerun()
        
        st.markdown("---")
        st.info("This is a read-only view. For full access, use the main application.")

if __name__ == "__main__":
    main()