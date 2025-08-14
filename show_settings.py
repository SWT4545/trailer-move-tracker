"""
Settings page module for the Trailer Move Tracker
"""

import streamlit as st
import pandas as pd
import auth_config
import user_management

def show_settings_page():
    """Settings page for app configuration"""
    st.title("⚙️ Settings")
    
    # Check if user is admin or executive for user management tab
    user_role = st.session_state.get("user_role", "")
    username = st.session_state.get("user", "")
    
    if user_role in ["admin", "executive"]:
        tabs = st.tabs(["👥 User Management", "📧 Email Settings", "🎨 Branding", "📊 System Info"])
        
        # User Management Tab
        with tabs[0]:
            user_management.show_user_management()
        
        # Email Settings Tab
        with tabs[1]:
            st.subheader("📧 Email Configuration")
            
            col1, col2 = st.columns(2)
            with col1:
                st.text_input(
                    "Company Email (From)",
                    value="Smithandwilliamstrucking@gmail.com",
                    disabled=True,
                    help="Default company email for sending notifications"
                )
                st.text_input(
                    "CEO Email",
                    value="swtruckingceo@gmail.com",
                    disabled=True,
                    help="CEO Brandon Smith's email address"
                )
            
            with col2:
                st.text_input(
                    "Support Email",
                    value="support@smithwilliamstrucking.com",
                    help="Email for customer support"
                )
                st.text_input(
                    "Billing Email",
                    value="billing@smithwilliamstrucking.com",
                    help="Email for billing inquiries"
                )
            
            st.divider()
            st.info("""
            📧 **Email Integration Status:**
            - Company Email: Smithandwilliamstrucking@gmail.com
            - CEO Email: swtruckingceo@gmail.com
            - All system notifications will be sent from the company email
            """)
        
        # Branding Tab
        with tabs[2]:
            st.subheader("🎨 Branding Settings")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Company Logo**")
                if st.file_uploader("Upload new logo", type=['png', 'jpg', 'jpeg']):
                    st.success("Logo uploaded successfully!")
                
                st.write("**Company Colors**")
                primary_color = st.color_picker("Primary Color", "#FF6B35")
                secondary_color = st.color_picker("Secondary Color", "#004E89")
            
            with col2:
                st.write("**Company Information**")
                st.text_input("Company Name", value="Smith and Williams Trucking", disabled=True)
                st.text_input("Company Slogan", value="Your Trusted Transportation Partner")
                st.text_area("Company Address", value="123 Main Street\nDallas, TX 75201")
        
        # System Info Tab
        with tabs[3]:
            st.subheader("📊 System Information")
            
            # User statistics
            st.write("**User Statistics**")
            total_users = len(auth_config.USERS)
            
            role_counts = {}
            for user in auth_config.USERS.values():
                role = user['role']
                role_counts[role] = role_counts.get(role, 0) + 1
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Users", total_users)
            with col2:
                st.metric("Executives", role_counts.get('executive', 0))
            with col3:
                st.metric("Admins", role_counts.get('admin', 0))
            with col4:
                st.metric("Managers", role_counts.get('manager', 0))
            
            # Current user info
            st.divider()
            st.write("**Your Account Information**")
            user_data = auth_config.USERS.get(username, {})
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Username:** {username}")
                st.write(f"**Role:** {user_role}")
                st.write(f"**Name:** {user_data.get('name', 'N/A')}")
            
            with col2:
                st.write(f"**Email:** {user_data.get('email', 'N/A')}")
                st.write(f"**Title:** {user_data.get('title', 'N/A')}")
                
            # Executive-only credential view
            if user_role == 'executive':
                st.divider()
                if st.checkbox("Show All User Credentials (Executive Only)", key="show_creds"):
                    user_management.show_user_credentials()
    
    elif user_role == "manager":
        # Manager view - limited settings
        tabs = st.tabs(["📊 Dashboard Settings", "📧 Contact Info"])
        
        with tabs[0]:
            st.subheader("Dashboard Settings")
            st.info("Contact an administrator to modify system settings.")
        
        with tabs[1]:
            st.subheader("Contact Information")
            st.write("**Company Email:** Smithandwilliamstrucking@gmail.com")
            st.write("**CEO:** Brandon Smith (swtruckingceo@gmail.com)")
    
    else:
        # Viewer/Client - minimal settings
        st.info("You don't have permission to access settings. Contact your administrator for help.")
        st.write("**Support Email:** Smithandwilliamstrucking@gmail.com")