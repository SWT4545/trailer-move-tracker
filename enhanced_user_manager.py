"""
Enhanced User and Driver Management System
Complete CRUD operations for users and drivers
"""

import streamlit as st
import json
import os
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib

def load_users():
    """Load users from JSON file"""
    user_file = 'user_accounts.json'
    if os.path.exists(user_file):
        with open(user_file, 'r') as f:
            return json.load(f)
    return {'users': {}}

def save_users(user_data):
    """Save users to JSON file"""
    try:
        with open('user_accounts.json', 'w') as f:
            json.dump(user_data, f, indent=2)
        return True
    except:
        return False

def get_driver_info():
    """Get driver information from database"""
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        query = """
            SELECT name, phone, email, status, active, created_at 
            FROM drivers 
            ORDER BY name
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def update_driver_info(driver_name, phone=None, email=None, status=None):
    """Update driver information in database"""
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if phone is not None:
            updates.append("phone = ?")
            params.append(phone)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        
        if updates:
            params.append(driver_name)
            query = f"UPDATE drivers SET {', '.join(updates)} WHERE name = ?"
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        st.error(f"Error updating driver: {str(e)}")
        return False

def deactivate_driver(driver_name):
    """Deactivate a driver (soft delete)"""
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE drivers SET active = 0, status = 'inactive' WHERE name = ?", (driver_name,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def reactivate_driver(driver_name):
    """Reactivate a deactivated driver"""
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE drivers SET active = 1, status = 'available' WHERE name = ?", (driver_name,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def show_enhanced_user_management():
    """Enhanced user and driver management interface"""
    st.title("👥 User & Driver Management")
    
    # Check admin access
    if st.session_state.get('user_role') != 'business_administrator':
        st.error("⛔ Administrator Access Required")
        return
    
    # Main tabs
    main_tabs = st.tabs(["👤 User Management", "🚛 Driver Management", "📊 Overview"])
    
    # USER MANAGEMENT TAB
    with main_tabs[0]:
        user_data = load_users()
        users = user_data['users']
        is_owner = users.get(st.session_state.get('username', ''), {}).get('is_owner', False)
        
        user_tabs = st.tabs(["📋 View All", "➕ Add", "✏️ Edit", "🔐 Password", "🗑️ Remove"])
        
        # View All Users
        with user_tabs[0]:
            st.markdown("### All System Users")
            
            # Search/filter
            search = st.text_input("🔍 Search users", placeholder="Type to filter...")
            
            for username, info in users.items():
                # Filter by search
                if search and search.lower() not in username.lower() and search.lower() not in info['name'].lower():
                    continue
                
                is_user_owner = info.get('is_owner', False)
                icon = "👑" if is_user_owner else "👤"
                
                with st.expander(f"{icon} {username} - {info['name']}", expanded=False):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Name:** {info['name']}")
                        st.write(f"**Username:** {username}")
                        st.write(f"**Email:** {info.get('email', 'Not set')}")
                        st.write(f"**Phone:** {info.get('phone', 'Not set')}")
                    
                    with col2:
                        roles_text = ", ".join([r.replace('_', ' ').title() for r in info['roles']])
                        st.write(f"**Roles:** {roles_text}")
                        
                        if len(info['roles']) > 1:
                            st.warning("🔄 Dual-Role User")
                        
                        if info.get('client_company'):
                            st.info(f"🏢 Client: {info['client_company']}")
                    
                    with col3:
                        if is_user_owner:
                            st.success("🔒 Owner")
                        elif info.get('active', True):
                            st.success("✅ Active")
                        else:
                            st.error("❌ Inactive")
        
        # Add User
        with user_tabs[1]:
            st.markdown("### Add New User")
            
            with st.form("add_user_enhanced", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_username = st.text_input("Username*", help="Login username")
                    new_password = st.text_input("Password*", type="password")
                    new_name = st.text_input("Full Name*")
                    new_email = st.text_input("Email", placeholder="user@example.com")
                    new_phone = st.text_input("Phone", placeholder="(555) 123-4567")
                
                with col2:
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
                    if st.checkbox("Client Viewer"):
                        roles.append("client_viewer")
                    
                    # Client company for client viewers
                    client_company = ""
                    if "client_viewer" in roles:
                        client_company = st.text_input("Client Company Name*", 
                                                      help="Enter company name for client filtering")
                
                if st.form_submit_button("➕ Create User", type="primary", use_container_width=True):
                    if new_username and new_password and new_name and roles:
                        if new_username not in users:
                            # Check client viewer has company
                            if "client_viewer" in roles and not client_company:
                                st.error("Client viewers must have a company name!")
                            else:
                                users[new_username] = {
                                    "password": new_password,
                                    "roles": roles,
                                    "name": new_name,
                                    "email": new_email or "",
                                    "phone": new_phone or "",
                                    "client_company": client_company if "client_viewer" in roles else "",
                                    "is_owner": False,
                                    "active": True,
                                    "created_at": datetime.now().isoformat()
                                }
                                
                                if save_users(user_data):
                                    # If driver role, add to drivers table
                                    if "driver" in roles:
                                        try:
                                            conn = sqlite3.connect('trailer_tracker_streamlined.db')
                                            cursor = conn.cursor()
                                            cursor.execute("""
                                                INSERT OR IGNORE INTO drivers (name, phone, email, status, active)
                                                VALUES (?, ?, ?, 'available', 1)
                                            """, (new_name, new_phone or '', new_email or ''))
                                            conn.commit()
                                            conn.close()
                                        except:
                                            pass
                                    
                                    st.success(f"✅ User '{new_username}' created!")
                                    st.rerun()
                        else:
                            st.error("Username already exists!")
                    else:
                        st.error("Please fill required fields (*)")
        
        # Edit User
        with user_tabs[2]:
            st.markdown("### Edit User Information")
            
            editable_users = {u: i for u, i in users.items() 
                            if not i.get('is_owner') or is_owner}
            
            if editable_users:
                selected_user = st.selectbox(
                    "Select User to Edit",
                    list(editable_users.keys()),
                    format_func=lambda x: f"{x} - {editable_users[x]['name']}"
                )
                
                if selected_user:
                    current_info = editable_users[selected_user]
                    
                    with st.form("edit_user_info", clear_on_submit=False):
                        st.markdown(f"**Editing: {selected_user}**")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            new_name = st.text_input("Full Name", value=current_info['name'])
                            new_email = st.text_input("Email", value=current_info.get('email', ''))
                            new_phone = st.text_input("Phone", value=current_info.get('phone', ''))
                        
                        with col2:
                            st.markdown("**Update Roles:**")
                            new_roles = []
                            
                            if st.checkbox("Business Administrator", 
                                         value="business_administrator" in current_info['roles']):
                                new_roles.append("business_administrator")
                            if st.checkbox("Operations Coordinator", 
                                         value="operations_coordinator" in current_info['roles']):
                                new_roles.append("operations_coordinator")
                            if st.checkbox("Driver", 
                                         value="driver" in current_info['roles']):
                                new_roles.append("driver")
                            if st.checkbox("Viewer", 
                                         value="viewer" in current_info['roles']):
                                new_roles.append("viewer")
                            if st.checkbox("Client Viewer", 
                                         value="client_viewer" in current_info['roles']):
                                new_roles.append("client_viewer")
                            
                            # Client company
                            if "client_viewer" in new_roles:
                                client_company = st.text_input("Client Company", 
                                                              value=current_info.get('client_company', ''))
                            else:
                                client_company = ""
                            
                            # Active status
                            is_active = st.checkbox("Active User", 
                                                   value=current_info.get('active', True))
                        
                        if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                            if new_name and new_roles:
                                users[selected_user].update({
                                    'name': new_name,
                                    'email': new_email,
                                    'phone': new_phone,
                                    'roles': new_roles,
                                    'client_company': client_company,
                                    'active': is_active
                                })
                                
                                if save_users(user_data):
                                    # Update driver info if has driver role
                                    if "driver" in new_roles:
                                        update_driver_info(new_name, new_phone, new_email)
                                    
                                    st.success(f"✅ Updated {selected_user}")
                                    st.rerun()
                            else:
                                st.error("Name and at least one role required")
        
        # Password Reset
        with user_tabs[3]:
            st.markdown("### Reset Password")
            
            reset_users = [u for u in users.keys() 
                          if not users[u].get('is_owner') or is_owner]
            
            reset_user = st.selectbox(
                "Select User",
                reset_users,
                format_func=lambda x: f"{x} - {users[x]['name']}"
            )
            
            if reset_user:
                with st.form("reset_pwd", clear_on_submit=True):
                    new_pwd = st.text_input("New Password", type="password")
                    confirm_pwd = st.text_input("Confirm Password", type="password")
                    
                    if st.form_submit_button("🔐 Reset Password", type="primary"):
                        if new_pwd and new_pwd == confirm_pwd:
                            users[reset_user]['password'] = new_pwd
                            if save_users(user_data):
                                st.success(f"✅ Password reset for {reset_user}")
                        else:
                            st.error("Passwords must match and not be empty")
        
        # Remove User
        with user_tabs[4]:
            st.markdown("### Remove User")
            st.warning("⚠️ This permanently removes the user")
            
            current_user = st.session_state.get('username', '')
            removable = {u: i for u, i in users.items() 
                        if u != current_user and not i.get('is_owner')}
            
            if removable:
                remove_user = st.selectbox(
                    "Select User to Remove",
                    list(removable.keys()),
                    format_func=lambda x: f"{x} - {removable[x]['name']}"
                )
                
                if remove_user:
                    st.error(f"Removing: {remove_user} - {removable[remove_user]['name']}")
                    
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        if st.button("🗑️ Confirm Remove", type="primary"):
                            # Deactivate driver if has driver role
                            if "driver" in users[remove_user]['roles']:
                                deactivate_driver(users[remove_user]['name'])
                            
                            del users[remove_user]
                            if save_users(user_data):
                                st.success(f"✅ Removed {remove_user}")
                                st.rerun()
    
    # DRIVER MANAGEMENT TAB
    with main_tabs[1]:
        st.markdown("### 🚛 Driver Information Management")
        
        driver_tabs = st.tabs(["📋 View Drivers", "✏️ Edit Info", "🔄 Status", "📞 Contact List"])
        
        with driver_tabs[0]:
            st.markdown("#### All Drivers")
            
            drivers_df = get_driver_info()
            if not drivers_df.empty:
                for _, driver in drivers_df.iterrows():
                    status_color = "🟢" if driver['status'] == 'available' else "🔴"
                    active_status = "✅" if driver.get('active', True) else "❌"
                    
                    with st.expander(f"{status_color} {driver['name']} {active_status}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Name:** {driver['name']}")
                            st.write(f"**Phone:** {driver.get('phone', 'Not set')}")
                            st.write(f"**Email:** {driver.get('email', 'Not set')}")
                        
                        with col2:
                            st.write(f"**Status:** {driver['status']}")
                            st.write(f"**Active:** {'Yes' if driver.get('active', True) else 'No'}")
                            st.write(f"**Added:** {driver.get('created_at', 'Unknown')}")
            else:
                st.info("No drivers in system")
        
        with driver_tabs[1]:
            st.markdown("#### Edit Driver Information")
            
            drivers_df = get_driver_info()
            if not drivers_df.empty:
                driver_names = drivers_df['name'].tolist()
                selected_driver = st.selectbox("Select Driver", driver_names)
                
                if selected_driver:
                    driver_info = drivers_df[drivers_df['name'] == selected_driver].iloc[0]
                    
                    with st.form("edit_driver", clear_on_submit=False):
                        phone = st.text_input("Phone Number", 
                                            value=driver_info.get('phone', ''))
                        email = st.text_input("Email Address", 
                                            value=driver_info.get('email', ''))
                        status = st.selectbox("Status", 
                                            ['available', 'busy', 'off_duty'],
                                            index=['available', 'busy', 'off_duty'].index(
                                                driver_info.get('status', 'available')))
                        
                        if st.form_submit_button("💾 Update Driver", type="primary"):
                            if update_driver_info(selected_driver, phone, email, status):
                                st.success(f"✅ Updated {selected_driver}")
                                st.rerun()
        
        with driver_tabs[2]:
            st.markdown("#### Driver Status Management")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 🔴 Deactivate Driver")
                active_drivers = get_driver_info()
                if not active_drivers.empty:
                    active_drivers = active_drivers[active_drivers['active'] == 1]
                    if not active_drivers.empty:
                        deactivate_name = st.selectbox(
                            "Select driver to deactivate",
                            active_drivers['name'].tolist(),
                            key="deactivate"
                        )
                        
                        if st.button("🔴 Deactivate", type="primary"):
                            if deactivate_driver(deactivate_name):
                                st.success(f"✅ {deactivate_name} deactivated")
                                st.rerun()
            
            with col2:
                st.markdown("##### 🟢 Reactivate Driver")
                inactive_drivers = get_driver_info()
                if not inactive_drivers.empty:
                    inactive_drivers = inactive_drivers[inactive_drivers['active'] == 0]
                    if not inactive_drivers.empty:
                        reactivate_name = st.selectbox(
                            "Select driver to reactivate",
                            inactive_drivers['name'].tolist(),
                            key="reactivate"
                        )
                        
                        if st.button("🟢 Reactivate", type="primary"):
                            if reactivate_driver(reactivate_name):
                                st.success(f"✅ {reactivate_name} reactivated")
                                st.rerun()
        
        with driver_tabs[3]:
            st.markdown("#### 📞 Driver Contact List")
            
            drivers_df = get_driver_info()
            if not drivers_df.empty:
                # Show as a formatted contact list
                for _, driver in drivers_df.iterrows():
                    if driver.get('active', True):
                        st.markdown(f"""
                        **{driver['name']}**  
                        📱 {driver.get('phone', 'No phone')}  
                        📧 {driver.get('email', 'No email')}  
                        Status: {driver['status']}
                        """)
                        st.divider()
    
    # OVERVIEW TAB
    with main_tabs[2]:
        st.markdown("### 📊 System Overview")
        
        user_data = load_users()
        users = user_data['users']
        drivers_df = get_driver_info()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_users = len(users)
            st.metric("Total Users", total_users)
        
        with col2:
            active_users = len([u for u in users.values() if u.get('active', True)])
            st.metric("Active Users", active_users)
        
        with col3:
            total_drivers = len(drivers_df) if not drivers_df.empty else 0
            st.metric("Total Drivers", total_drivers)
        
        with col4:
            if not drivers_df.empty:
                available_drivers = len(drivers_df[drivers_df['status'] == 'available'])
            else:
                available_drivers = 0
            st.metric("Available Drivers", available_drivers)
        
        st.divider()
        
        # Role distribution
        st.markdown("#### Role Distribution")
        role_counts = {}
        for user in users.values():
            for role in user['roles']:
                role_counts[role] = role_counts.get(role, 0) + 1
        
        for role, count in role_counts.items():
            st.write(f"• **{role.replace('_', ' ').title()}:** {count} users")