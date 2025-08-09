"""
Standalone Progress Dashboard Viewer
This can be deployed separately or accessed via shareable link
"""

import streamlit as st
from datetime import datetime
import database as db
import progress_dashboard
import branding
import auth_config
from PIL import Image
import os

# Page configuration
page_icon = "📈"
if os.path.exists("swt_logo.png"):
    try:
        page_icon = Image.open("swt_logo.png")
    except:
        pass

st.set_page_config(
    page_title="Progress Dashboard - Smith and Williams Trucking",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize database
db.init_database()

def check_access():
    """Check if user has access via token or simplified password"""
    
    # Check for token in URL parameters
    query_params = st.query_params
    if 'token' in query_params:
        token = query_params['token']
        valid, token_data = auth_config.validate_share_token(token)
        if valid and token_data.get('type') == 'progress_dashboard':
            return True
        else:
            st.error("Invalid or expired access token")
            return False
    
    # Simple password check for direct access
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    if not st.session_state['authenticated']:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h2>🔒 Progress Dashboard Access</h2>
            <p>Please enter the access code to view the progress dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            access_code = st.text_input(
                "Access Code",
                type="password",
                placeholder="Enter access code",
                help="Contact administrator for access code"
            )
            
            if st.button("🔓 Access Dashboard", use_container_width=True):
                # Simple check - in production, use proper authentication
                if access_code in ['client123', 'progress2024']:  # Add your access codes
                    st.session_state['authenticated'] = True
                    st.rerun()
                else:
                    st.error("Invalid access code")
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666;">
            <p><small>This is a read-only view of the progress dashboard.</small></p>
            <p><small>No financial or sensitive information is displayed.</small></p>
            <p><small>© 2024 Smith and Williams Trucking</small></p>
        </div>
        """, unsafe_allow_html=True)
        
        return False
    
    return True

def main():
    if not check_access():
        st.stop()
    
    # Apply branding
    st.markdown(branding.CUSTOM_CSS, unsafe_allow_html=True)
    
    # Add header with logo
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown(branding.get_header_html(), unsafe_allow_html=True)
    
    # Add info bar
    st.info("""
    📊 **Read-Only Progress Dashboard** | 
    This view is updated in real-time | 
    No financial information displayed | 
    Contact admin for full access
    """)
    
    # Show the progress dashboard in read-only mode
    progress_dashboard.show_progress_dashboard(read_only=True)
    
    # Add footer
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <p style="color: #666;">
                <small>Last updated: {}</small><br>
                <small>© 2024 Smith and Williams Trucking. All rights reserved.</small>
            </p>
        </div>
        """.format(datetime.now().strftime('%Y-%m-%d %I:%M %p')), unsafe_allow_html=True)

if __name__ == "__main__":
    main()