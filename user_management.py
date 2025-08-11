"""
User Management Module for Executive/Admin Control
Clean, readable interface with training features
"""

import streamlit as st
import json
import os
from datetime import datetime
import secrets
import string
import auth_config
import pandas as pd

def generate_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def save_users_to_config(users_dict):
    """Save users back to auth_config.py file"""
    # Read the current file
    with open('auth_config.py', 'r') as f:
        lines = f.readlines()
    
    # Find the USERS section
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('USERS = {'):
            start_idx = i
        elif start_idx is not None and line.strip() == '}' and end_idx is None:
            # Find the closing brace for USERS
            end_idx = i
            break
    
    if start_idx is None or end_idx is None:
        st.error("Could not find USERS section in auth_config.py")
        return False
    
    # Build the new USERS section
    new_users_section = ["USERS = {\n"]
    for username, user_data in users_dict.items():
        new_users_section.append(f"    '{username}': {{\n")
        new_users_section.append(f"        'password': '{user_data['password']}',\n")
        new_users_section.append(f"        'role': '{user_data['role']}',\n")
        new_users_section.append(f"        'name': '{user_data['name']}'")
        if 'title' in user_data:
            new_users_section.append(f",\n        'title': '{user_data['title']}'")
        if 'email' in user_data:
            new_users_section.append(f",\n        'email': '{user_data['email']}'")
        new_users_section.append("\n    },\n")
    new_users_section.append("}\n")
    
    # Replace the old USERS section with the new one
    new_lines = lines[:start_idx] + new_users_section + lines[end_idx+1:]
    
    # Write back to file
    with open('auth_config.py', 'w') as f:
        f.writelines(new_lines)
    
    return True

def show_user_management():
    """Display comprehensive user management interface"""
    
    # Header with better spacing
    st.markdown("""
    <style>
    .user-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("👥 User Management System")
    st.markdown("Manage user accounts, roles, passwords, and training assignments")
    
    # Get current user role
    if 'user_role' not in st.session_state:
        st.error("User role not found in session")
        return
    
    user_role = st.session_state.user_role
    
    # Check permissions
    if user_role not in ['executive', 'admin']:
        st.error("You don't have permission to manage users")
        return
    
    # Reload users from auth_config
    import importlib
    importlib.reload(auth_config)
    current_users = auth_config.USERS.copy()
    
    # Create tabs with better names
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "👤 View Users", 
        "➕ Add User", 
        "✏️ Edit User", 
        "🔐 Passwords", 
        "🎓 Training", 
        "📊 Reports"
    ])
    
    # Tab 1: View Current Users - Clean card layout
    with tab1:
        st.subheader("System Users Overview")
        
        # Compact summary in a nice card
        with st.container():
            cols = st.columns(5)
            cols[0].metric("Total", len(current_users), delta=None)
            cols[1].metric("Executives", sum(1 for u in current_users.values() if u['role'] == 'executive'))
            cols[2].metric("Admins", sum(1 for u in current_users.values() if u['role'] == 'admin'))
            cols[3].metric("Managers", sum(1 for u in current_users.values() if u['role'] == 'manager'))
            cols[4].metric("Others", sum(1 for u in current_users.values() if u['role'] in ['viewer', 'client']))
        
        st.divider()
        
        # Display each user as a clean expandable section
        role_emojis = {
            'executive': '👑',
            'admin': '⚙️', 
            'manager': '📊',
            'viewer': '👁️',
            'client': '🤝'
        }
        
        for username, user_data in current_users.items():
            user_role_display = user_data['role']
            emoji = role_emojis.get(user_role_display, '👤')
            
            # Create a cleaner expander title
            expander_title = f"{emoji} **{user_data.get('name', username)}** ({username}) - {user_role_display.title()}"
            
            with st.expander(expander_title, expanded=False):
                # Use a two-column layout for better readability
                left_col, right_col = st.columns([3, 2])
                
                with left_col:
                    st.write(f"**Username:** `{username}`")
                    st.write(f"**Full Name:** {user_data.get('name', 'Not provided')}")
                    st.write(f"**Email:** {user_data.get('email', 'Not provided')}")
                    st.write(f"**Job Title:** {user_data.get('title', 'Not provided')}")
                    st.write(f"**Access Level:** {user_role_display.title()}")
                
                with right_col:
                    st.write("**Quick Actions:**")
                    
                    # Only show password to executives
                    if user_role == 'executive':
                        st.write("**Current Password:**")
                        st.code(user_data['password'])
                    
                    # Action buttons
                    if username != st.session_state.username:
                        if st.button(f"🔄 Reset Password", key=f"pwd_{username}"):
                            new_pwd = generate_password()
                            current_users[username]['password'] = new_pwd
                            if save_users_to_config(current_users):
                                st.success(f"Password reset! New: `{new_pwd}`")
                                st.balloons()
                                st.rerun()
                        
                        if user_role == 'executive':
                            if st.button(f"🗑️ Remove User", key=f"del_{username}"):
                                del current_users[username]
                                if save_users_to_config(current_users):
                                    st.success(f"User {username} removed")
                                    st.rerun()
    
    # Tab 2: Add New User - Cleaner form
    with tab2:
        st.header("Add New User Account")
        st.markdown("Create a new user account with role-based access")
        
        with st.form("add_user_form", clear_on_submit=True):
            st.subheader("User Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input(
                    "Username*", 
                    placeholder="john_smith",
                    help="Lowercase, no spaces"
                )
                new_name = st.text_input(
                    "Full Name*", 
                    placeholder="John Smith"
                )
                new_email = st.text_input(
                    "Email Address*", 
                    placeholder="john@company.com"
                )
            
            with col2:
                new_role = st.selectbox(
                    "User Role*",
                    ["viewer", "client", "manager", "admin"],
                    help="Select the appropriate access level"
                )
                new_title = st.text_input(
                    "Job Title", 
                    placeholder="Operations Manager"
                )
                
                st.markdown("**Password Options**")
                auto_password = st.checkbox("Generate secure password", value=True)
                
                if not auto_password:
                    new_password = st.text_input("Set Password", type="password")
                    confirm_password = st.text_input("Confirm Password", type="password")
            
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            with col2:
                submitted = st.form_submit_button(
                    "➕ Create User Account", 
                    use_container_width=True,
                    type="primary"
                )
            
            if submitted:
                # Validate inputs
                clean_username = new_username.lower().replace(' ', '_')
                
                if not all([clean_username, new_name, new_email]):
                    st.error("Please fill in all required fields (marked with *)")
                elif clean_username in current_users:
                    st.error(f"Username '{clean_username}' already exists")
                else:
                    # Handle password
                    if auto_password:
                        password = generate_password()
                    else:
                        if new_password != confirm_password:
                            st.error("Passwords don't match")
                            st.stop()
                        password = new_password
                    
                    # Create new user
                    new_user = {
                        'password': password,
                        'role': new_role,
                        'name': new_name,
                        'email': new_email
                    }
                    
                    if new_title:
                        new_user['title'] = new_title
                    
                    # Add to users
                    current_users[clean_username] = new_user
                    
                    # Save to config
                    if save_users_to_config(current_users):
                        st.success("✅ User created successfully!")
                        
                        # Display credentials in a nice format
                        st.info("### New User Credentials")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Username:** `{clean_username}`")
                            st.write(f"**Password:** `{password}`")
                        with col2:
                            st.write(f"**Role:** {new_role}")
                            st.write(f"**Email:** {new_email}")
                        
                        st.warning("⚠️ Share these credentials securely with the user")
    
    # Tab 3: Edit User - Clean interface
    with tab3:
        st.header("Edit User Details")
        
        # User selector
        edit_username = st.selectbox(
            "Select User to Edit",
            options=list(current_users.keys()),
            format_func=lambda x: f"{x} - {current_users[x].get('name', 'No name')}"
        )
        
        if edit_username:
            st.markdown("---")
            user_to_edit = current_users[edit_username]
            
            with st.form("edit_user_form"):
                st.subheader(f"Editing: {edit_username}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    edit_name = st.text_input("Full Name", value=user_to_edit.get('name', ''))
                    edit_email = st.text_input("Email", value=user_to_edit.get('email', ''))
                    edit_title = st.text_input("Job Title", value=user_to_edit.get('title', ''))
                
                with col2:
                    if user_role == 'executive':
                        edit_role = st.selectbox(
                            "Role", 
                            ["client", "viewer", "manager", "admin", "executive"],
                            index=["client", "viewer", "manager", "admin", "executive"].index(user_to_edit['role'])
                        )
                    else:
                        st.info(f"Current Role: {user_to_edit['role']}")
                        edit_role = user_to_edit['role']
                
                st.markdown("---")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
                
                with col3:
                    if user_role == 'executive' and edit_username != st.session_state.username:
                        delete_btn = st.form_submit_button("🗑️ Delete User", use_container_width=True)
                    else:
                        delete_btn = False
                
                if save_btn:
                    # Update user data
                    current_users[edit_username]['name'] = edit_name
                    current_users[edit_username]['email'] = edit_email
                    current_users[edit_username]['role'] = edit_role
                    if edit_title:
                        current_users[edit_username]['title'] = edit_title
                    
                    if save_users_to_config(current_users):
                        st.success(f"✅ User '{edit_username}' updated successfully!")
                        st.rerun()
                
                if delete_btn:
                    del current_users[edit_username]
                    if save_users_to_config(current_users):
                        st.success(f"User '{edit_username}' deleted")
                        st.rerun()
    
    # Tab 4: Password Management - Clean layout
    with tab4:
        st.header("Password Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Reset User Password")
            
            reset_username = st.selectbox(
                "Select User",
                options=list(current_users.keys()),
                key="pwd_reset_user"
            )
            
            if st.button("🔐 Generate New Password", use_container_width=True, type="primary"):
                new_pass = generate_password()
                current_users[reset_username]['password'] = new_pass
                
                if save_users_to_config(current_users):
                    st.success(f"✅ Password reset for '{reset_username}'")
                    st.info(f"**New Password:** `{new_pass}`")
                    st.warning("Share this password securely with the user")
        
        with col2:
            st.subheader("Set Custom Password")
            
            custom_user = st.selectbox(
                "Select User",
                options=list(current_users.keys()),
                key="pwd_custom_user"
            )
            
            custom_pass = st.text_input("New Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            
            if st.button("Set Password", use_container_width=True):
                if not custom_pass:
                    st.error("Please enter a password")
                elif len(custom_pass) < 8:
                    st.error("Password must be at least 8 characters")
                elif custom_pass != confirm_pass:
                    st.error("Passwords don't match")
                else:
                    current_users[custom_user]['password'] = custom_pass
                    if save_users_to_config(current_users):
                        st.success(f"✅ Password updated for '{custom_user}'")
    
    # Tab 5: Training Management
    with tab5:
        st.header("🎓 Training Management")
        st.markdown("Assign training modules and track completion")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Quick Training Links")
            
            st.markdown("**Direct Access URLs:**")
            st.code("http://localhost:8503?role=admin", language=None)
            st.code("http://localhost:8503?role=manager", language=None)
            st.code("http://localhost:8503?role=viewer", language=None)
            st.code("http://localhost:8503?role=client", language=None)
            
            if st.button("📚 Launch Training System", use_container_width=True):
                import subprocess
                import os
                import socket
                
                # Check if port 8503 is already in use
                def is_port_in_use(port):
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        try:
                            s.bind(('', port))
                            return False
                        except:
                            return True
                
                if is_port_in_use(8503):
                    st.success("✅ Training System is already running!")
                    st.info("🌐 Access it at: http://localhost:8503")
                else:
                    try:
                        # Launch the training system
                        if os.path.exists('training_system.py'):
                            # Launch in a new process
                            subprocess.Popen(
                                ['python', '-m', 'streamlit', 'run', 'training_system.py', '--server.port', '8503'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True
                            )
                            st.success("✅ Training System launching...")
                            st.info("🌐 It will be available at: http://localhost:8503")
                            st.info("⏳ Please wait a few seconds for it to start")
                            st.balloons()
                        else:
                            st.error("Training system file not found!")
                    except Exception as e:
                        st.error(f"Error launching training system: {str(e)}")
        
        with col2:
            st.subheader("Generate Training Assignment")
            
            train_user = st.selectbox(
                "Select User for Training",
                options=list(current_users.keys()),
                format_func=lambda x: f"{x} ({current_users[x]['role']})"
            )
            
            if st.button("🎯 Generate Training Link", use_container_width=True):
                user_role_train = current_users[train_user]['role']
                training_url = f"http://localhost:8503?role={user_role_train}&user={train_user}"
                
                st.success("Training link generated!")
                st.code(training_url, language=None)
                
                # Email template
                st.markdown("### 📧 Email Template")
                email_template = f"""
                Subject: Training Assignment - Trailer Move Tracker
                
                Dear {current_users[train_user].get('name', train_user)},
                
                Please complete your training for the Trailer Move Tracker system.
                
                Training Link: {training_url}
                
                Your login credentials:
                Username: {train_user}
                Password: {current_users[train_user]['password']}
                
                Please complete the training within 7 days.
                
                Best regards,
                {st.session_state.get('user_name', 'Administrator')}
                """
                st.text_area("Copy this email:", email_template, height=300)
    
    # Tab 6: Analytics and Reports
    with tab6:
        st.header("📊 User Analytics & Reports")
        
        # User statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Role Distribution")
            role_counts = {}
            for user in current_users.values():
                role = user['role']
                role_counts[role] = role_counts.get(role, 0) + 1
            
            for role, count in sorted(role_counts.items()):
                st.write(f"**{role.title()}:** {count} user(s)")
        
        with col2:
            st.subheader("Quick Stats")
            st.metric("Total Users", len(current_users))
            st.metric("With Email", sum(1 for u in current_users.values() if 'email' in u))
            st.metric("With Title", sum(1 for u in current_users.values() if 'title' in u))
        
        with col3:
            st.subheader("Export Options")
            
            if st.button("📥 Export User List (CSV)", use_container_width=True):
                # Create DataFrame
                user_list = []
                for username, data in current_users.items():
                    user_list.append({
                        'Username': username,
                        'Name': data.get('name', ''),
                        'Role': data['role'],
                        'Email': data.get('email', ''),
                        'Title': data.get('title', '')
                    })
                
                df = pd.DataFrame(user_list)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"users_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            if user_role == 'executive':
                if st.button("🔐 Export with Passwords", use_container_width=True):
                    # Create DataFrame with passwords
                    user_list = []
                    for username, data in current_users.items():
                        user_list.append({
                            'Username': username,
                            'Password': data['password'],
                            'Name': data.get('name', ''),
                            'Role': data['role'],
                            'Email': data.get('email', '')
                        })
                    
                    df = pd.DataFrame(user_list)
                    csv = df.to_csv(index=False)
                    
                    st.download_button(
                        label="Download Secure CSV",
                        data=csv,
                        file_name=f"users_secure_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                    st.warning("⚠️ This file contains passwords. Store securely!")

def show_user_credentials():
    """Show all user credentials for executive only"""
    if st.session_state.user_role != 'executive':
        st.error("Only executives can view all credentials")
        return
    
    st.subheader("🔐 All User Credentials")
    st.warning("⚠️ Sensitive information - Do not share or display publicly")
    
    # Reload users
    import importlib
    importlib.reload(auth_config)
    
    # Create a clean table
    credentials_data = []
    for username, user_data in auth_config.USERS.items():
        credentials_data.append({
            'Username': username,
            'Password': user_data['password'],
            'Role': user_data['role'],
            'Name': user_data.get('name', 'N/A'),
            'Email': user_data.get('email', 'N/A')
        })
    
    if not credentials_data:
        st.warning("No user credentials found in the system.")
        return
    
    # Display as dataframe
    df = pd.DataFrame(credentials_data)
    
    # Add a colored background to ensure visibility
    st.markdown("""
    <style>
    div[data-testid="stDataFrame"] > div {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 5px !important;
        padding: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display the dataframe
    st.dataframe(df, use_container_width=True, height=400, hide_index=True)
    
    # Also provide download option
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Credentials as CSV",
        data=csv,
        file_name="user_credentials.csv",
        mime="text/csv"
    )