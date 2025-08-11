"""
User Management System
Allows owner and admins to manage users through the app interface
"""

import streamlit as st
import json
import os
from datetime import datetime

def load_users():
    """Load users from JSON file"""
    try:
        with open('user_accounts.json', 'r') as f:
            return json.load(f)
    except:
        # Return default structure if file doesn't exist
        return {
            "users": {
                "Brandon": {
                    "password": "owner123",
                    "roles": ["business_administrator"],
                    "name": "Brandon (Owner)",
                    "is_owner": True
                }
            }
        }

def save_users(user_data):
    """Save users to JSON file"""
    try:
        with open('user_accounts.json', 'w') as f:
            json.dump(user_data, f, indent=2)
        return True
    except:
        return False

def show_user_management():
    """Main user management interface for admins"""
    st.markdown("### 👥 User Management System")
    
    # Check if user is owner or admin
    is_owner = st.session_state.get('is_owner', False)
    role = st.session_state.get('user_role', '')
    
    if role != 'business_administrator':
        st.error("⛔ Access Denied - Administrator Only")
        return
    
    # Load current users
    user_data = load_users()
    users = user_data['users']
    
    tabs = st.tabs(["📋 Current Users", "➕ Add User", "✏️ Edit Roles", "🔐 Reset Password", "🗑️ Remove User"])
    
    with tabs[0]:  # Current Users
        st.markdown("#### All System Users")
        
        for username, info in users.items():
            is_user_owner = info.get('is_owner', False)
            icon = "👑" if is_user_owner else "👤"
            
            with st.expander(f"{icon} {username} - {info['name']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Name:** {info['name']}")
                    st.write(f"**Username:** {username}")
                    roles_text = ", ".join([r.replace('_', ' ').title() for r in info['roles']])
                    st.write(f"**Roles:** {roles_text}")
                
                with col2:
                    if is_user_owner:
                        st.success("🔒 Owner Account (Protected)")
                    else:
                        st.info("Regular User")
                    
                    # Show if user has dual roles
                    if len(info['roles']) > 1:
                        st.warning(f"🔄 Dual-Role User")
    
    with tabs[1]:  # Add User
        st.markdown("#### Add New User")
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username", help="Login username")
                new_password = st.text_input("Password", type="password", help="Initial password")
                new_name = st.text_input("Full Name", help="Display name")
            
            with col2:
                # Role selection - allow multiple
                st.markdown("**Select Roles:**")
                roles = []
                if st.checkbox("Business Administrator"):
                    roles.append("business_administrator")
                if st.checkbox("Operations Coordinator"):
                    roles.append("operations_coordinator")
                if st.checkbox("Driver"):
                    roles.append("driver")
                if st.checkbox("Viewer (Read-Only)"):
                    roles.append("viewer")
            
            if st.form_submit_button("➕ Create User", type="primary"):
                if new_username and new_password and new_name and roles:
                    if new_username not in users:
                        users[new_username] = {
                            "password": new_password,
                            "roles": roles,
                            "name": new_name,
                            "is_owner": False
                        }
                        if save_users(user_data):
                            st.success(f"✅ User '{new_username}' created successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to save user")
                    else:
                        st.error("Username already exists!")
                else:
                    st.error("Please fill all fields and select at least one role")
    
    with tabs[2]:  # Edit Roles
        st.markdown("#### Edit User Roles")
        
        # Select user to edit (exclude owner unless you are owner)
        editable_users = {}
        for username, info in users.items():
            if not info.get('is_owner', False) or is_owner:
                editable_users[username] = info
        
        if editable_users:
            selected_user = st.selectbox(
                "Select User to Edit",
                list(editable_users.keys()),
                format_func=lambda x: f"{x} - {editable_users[x]['name']}"
            )
            
            if selected_user:
                current_info = editable_users[selected_user]
                st.info(f"Current roles: {', '.join(current_info['roles'])}")
                
                with st.form("edit_roles_form"):
                    st.markdown("**Update Roles:**")
                    new_roles = []
                    
                    # Pre-check current roles
                    if st.checkbox("Business Administrator", value="business_administrator" in current_info['roles']):
                        new_roles.append("business_administrator")
                    if st.checkbox("Operations Coordinator", value="operations_coordinator" in current_info['roles']):
                        new_roles.append("operations_coordinator")
                    if st.checkbox("Driver", value="driver" in current_info['roles']):
                        new_roles.append("driver")
                    if st.checkbox("Viewer (Read-Only)", value="viewer" in current_info['roles']):
                        new_roles.append("viewer")
                    
                    if st.form_submit_button("💾 Update Roles", type="primary"):
                        if new_roles:
                            users[selected_user]['roles'] = new_roles
                            if save_users(user_data):
                                st.success(f"✅ Roles updated for '{selected_user}'!")
                                st.rerun()
                            else:
                                st.error("Failed to update roles")
                        else:
                            st.error("User must have at least one role")
    
    with tabs[3]:  # Reset Password
        st.markdown("#### Reset User Password")
        
        # Select user for password reset
        reset_user = st.selectbox(
            "Select User",
            [u for u in users.keys() if not users[u].get('is_owner', False) or is_owner],
            format_func=lambda x: f"{x} - {users[x]['name']}"
        )
        
        if reset_user:
            with st.form("reset_password_form"):
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                
                if st.form_submit_button("🔐 Reset Password", type="primary"):
                    if new_password and new_password == confirm_password:
                        users[reset_user]['password'] = new_password
                        if save_users(user_data):
                            st.success(f"✅ Password reset for '{reset_user}'!")
                        else:
                            st.error("Failed to reset password")
                    else:
                        st.error("Passwords don't match or are empty")
    
    with tabs[4]:  # Remove User
        st.markdown("#### Remove User")
        st.warning("⚠️ This action cannot be undone!")
        
        # Can't remove owner or yourself
        removable_users = {}
        current_user = st.session_state.get('username', '')
        
        for username, info in users.items():
            if username != current_user and not info.get('is_owner', False):
                removable_users[username] = info
        
        if removable_users:
            remove_user = st.selectbox(
                "Select User to Remove",
                list(removable_users.keys()),
                format_func=lambda x: f"{x} - {removable_users[x]['name']}"
            )
            
            if remove_user:
                st.error(f"⚠️ You are about to remove user: {remove_user}")
                
                if st.button("🗑️ Confirm Removal", type="primary"):
                    del users[remove_user]
                    if save_users(user_data):
                        st.success(f"✅ User '{remove_user}' has been removed")
                        st.rerun()
                    else:
                        st.error("Failed to remove user")
        else:
            st.info("No users available to remove")