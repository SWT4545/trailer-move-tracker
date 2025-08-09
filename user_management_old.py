"""
User Management Module for Executive/Admin Control
"""

import streamlit as st
import json
import os
from datetime import datetime
import secrets
import string
import auth_config

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
    st.title("👥 User Management System")
    
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
    
    # Add spacing and cleaner layout
    st.markdown("---")
    
    # Create tabs for different management functions
    tabs = st.tabs(["👤 Current Users", "➕ Add User", "✏️ Edit User", "🔐 Passwords", "📊 Analytics", "🎓 Training"])
    
    # Tab 1: View Current Users
    with tabs[0]:
        st.subheader("Current System Users")
        st.markdown("""View and manage all user accounts in the system.""")
        
        # Create a cleaner table layout
        st.markdown("### User Accounts")
        
        # Use expander for each user for cleaner look
        for username, user_data in current_users.items():
            role_colors = {
                'executive': '🔴',
                'admin': '🟠', 
                'manager': '🟡',
                'viewer': '🟢',
                'client': '🔵'
            }
            
            with st.expander(f"{role_colors.get(user_data['role'], '⚪')} **{username}** - {user_data.get('name', 'N/A')}"): 
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Username:**", username)
                    st.write("**Full Name:**", user_data.get('name', 'N/A'))
                
                with col2:
                    st.write("**Role:**", user_data['role'].title())
                    st.write("**Email:**", user_data.get('email', 'Not set'))
                
                with col3:
                    if user_role == 'executive':
                        st.write("**Password:**")
                        st.code(user_data['password'])
                    
                    if username != st.session_state.username:
                        if st.button(f"🔒 Lock User", key=f"lock_{username}"):
                            st.warning("User lock feature coming soon")
        
            
            # Color code by role
            role_colors = {
                'executive': '🔴',
                'admin': '🟠',
                'manager': '🟡',
                'viewer': '🟢',
                'client': '🔵'
            }
            
            col1.write(f"{username}")
            col2.write(user_data.get('name', 'N/A'))
            col3.write(f"{role_colors.get(user_data['role'], '⚪')} {user_data['role']}")
            col4.write(user_data.get('email', 'N/A'))
            
            if user_role == 'executive':
                # Only executives can see passwords
                col5.write(f"`{user_data['password']}`")
            else:
                col5.write("*****")
            
            # Action buttons
            with col6:
                if username != st.session_state.username:  # Can't lock yourself out
                    if st.button("🔒 Lock", key=f"lock_{username}"):
                        # Add locked flag
                        current_users[username]['locked'] = True
                        save_users_to_config(current_users)
                        st.success(f"User {username} locked")
                        st.rerun()
    
    # Tab 2: Add New User
    with tabs[1]:
        st.subheader("Add New User")
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username (lowercase, no spaces)")
                new_name = st.text_input("Full Name")
                new_email = st.text_input("Email Address")
            
            with col2:
                new_role = st.selectbox("Role", ["viewer", "client", "manager", "admin"])
                new_title = st.text_input("Job Title (optional)")
                auto_password = st.checkbox("Generate secure password", value=True)
                
                if not auto_password:
                    new_password = st.text_input("Password", type="password")
                    confirm_password = st.text_input("Confirm Password", type="password")
            
            submitted = st.form_submit_button("➕ Create User", use_container_width=True)
            
            if submitted:
                # Validate username
                clean_username = new_username.lower().replace(' ', '_')
                
                if not clean_username:
                    st.error("Username is required")
                elif clean_username in current_users:
                    st.error(f"Username '{clean_username}' already exists")
                elif not new_name:
                    st.error("Full name is required")
                elif not new_email:
                    st.error("Email is required")
                else:
                    # Generate or validate password
                    if auto_password:
                        password = generate_password()
                    else:
                        if new_password != confirm_password:
                            st.error("Passwords don't match")
                            st.stop()
                        elif len(new_password) < 8:
                            st.error("Password must be at least 8 characters")
                            st.stop()
                        else:
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
                        st.success(f"✅ User '{clean_username}' created successfully!")
                        
                        # Display credentials
                        st.info(f"""
                        **New User Credentials:**
                        - Username: `{clean_username}`
                        - Password: `{password}`
                        - Role: {new_role}
                        
                        Please share these credentials securely with the user.
                        """)
                        
                        # Log the creation
                        with open('user_audit.log', 'a') as f:
                            f.write(f"{datetime.now()}: User '{clean_username}' created by {st.session_state.username}\n")
    
    # Tab 3: Edit User
    with tabs[2]:
        st.subheader("Edit User Details")
        
        # Select user to edit
        edit_username = st.selectbox("Select User to Edit", list(current_users.keys()))
        
        if edit_username:
            user_to_edit = current_users[edit_username]
            
            with st.form("edit_user_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    edit_name = st.text_input("Full Name", value=user_to_edit.get('name', ''))
                    edit_email = st.text_input("Email", value=user_to_edit.get('email', ''))
                
                with col2:
                    # Only executive can change roles
                    if user_role == 'executive':
                        edit_role = st.selectbox("Role", 
                            ["client", "viewer", "manager", "admin", "executive"],
                            index=["client", "viewer", "manager", "admin", "executive"].index(user_to_edit['role']))
                    else:
                        st.info(f"Current Role: {user_to_edit['role']}")
                        edit_role = user_to_edit['role']
                    
                    edit_title = st.text_input("Job Title", value=user_to_edit.get('title', ''))
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True)
                with col2:
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
    
    # Tab 4: Password Reset
    with tabs[3]:
        st.subheader("Password Management")
        
        reset_username = st.selectbox("Select User for Password Reset", list(current_users.keys()))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔐 Generate New Password", use_container_width=True):
                new_pass = generate_password()
                current_users[reset_username]['password'] = new_pass
                
                if save_users_to_config(current_users):
                    st.success(f"✅ Password reset for '{reset_username}'")
                    st.info(f"New Password: `{new_pass}`")
                    
                    # Log the reset
                    with open('user_audit.log', 'a') as f:
                        f.write(f"{datetime.now()}: Password reset for '{reset_username}' by {st.session_state.username}\n")
        
        with col2:
            custom_pass = st.text_input("Or set custom password:", type="password")
            if st.button("Set Custom Password", use_container_width=True):
                if len(custom_pass) < 8:
                    st.error("Password must be at least 8 characters")
                else:
                    current_users[reset_username]['password'] = custom_pass
                    if save_users_to_config(current_users):
                        st.success(f"✅ Password updated for '{reset_username}'")
    
    # Tab 5: User Analytics
    with tabs[4]:
        st.subheader("User Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Count users by role
        role_counts = {}
        for user in current_users.values():
            role = user['role']
            role_counts[role] = role_counts.get(role, 0) + 1
        
        with col1:
            st.metric("Total Users", len(current_users))
        
        with col2:
            st.metric("Admins", role_counts.get('admin', 0) + role_counts.get('executive', 0))
        
        with col3:
            st.metric("Managers", role_counts.get('manager', 0))
        
        with col4:
            st.metric("Viewers", role_counts.get('viewer', 0) + role_counts.get('client', 0))
        
        # Show role distribution
        st.divider()
        st.write("**Role Distribution:**")
        for role, count in sorted(role_counts.items()):
            st.write(f"- {role.capitalize()}: {count} user(s)")
        
        # Show recent activity if log exists
        if os.path.exists('user_audit.log'):
            st.divider()
            st.write("**Recent User Management Activity:**")
            with open('user_audit.log', 'r') as f:
                lines = f.readlines()[-10:]  # Last 10 activities
                for line in lines:
                    st.text(line.strip())

def show_user_credentials():
    """Show all user credentials for executive only"""
    if st.session_state.user_role != 'executive':
        st.error("Only executives can view all credentials")
        return
    
    st.subheader("🔐 All User Credentials")
    st.warning("⚠️ This information is highly sensitive. Do not share or display publicly.")
    
    # Reload users
    import importlib
    importlib.reload(auth_config)
    
    # Create a table of all credentials
    credentials_data = []
    for username, user_data in auth_config.USERS.items():
        credentials_data.append({
            'Username': username,
            'Password': user_data['password'],
            'Role': user_data['role'],
            'Name': user_data.get('name', 'N/A'),
            'Email': user_data.get('email', 'N/A')
        })
    
    # Display as dataframe
    import pandas as pd
    df = pd.DataFrame(credentials_data)
    st.dataframe(df, use_container_width=True)
    
    # Export option
    if st.button("📥 Export to CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Credentials CSV",
            data=csv,
            file_name=f"user_credentials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )