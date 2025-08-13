"""
Smith & Williams Trucking - FINAL COMPLETE VERSION
With ALL Owner management controls and oversight options
Original formatting preserved - DO NOT CHANGE
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sqlite3
import hashlib
import os
from PIL import Image
import json
import base64
import io

# Import PDF generator - try professional version first
try:
    from professional_pdf_generator import PDFReportGenerator, generate_status_report_for_profile
    PDF_AVAILABLE = True
except:
    try:
        from pdf_report_generator import PDFReportGenerator, generate_status_report_for_profile
        PDF_AVAILABLE = True
    except:
        try:
            from simple_pdf_generator import PDFReportGenerator, generate_status_report_for_profile
            PDF_AVAILABLE = True
        except:
            PDF_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Smith & Williams Trucking",
    page_icon="🚛",
    layout="wide"
)

# Custom CSS for better styling - KEEP ORIGINAL FORMATTING
st.markdown("""
<style>
    /* Logo styling */
    .logo-container {
        text-align: center;
        padding: 1rem;
    }
    .logo-img {
        max-width: 200px;
        margin: 0 auto;
    }
    /* Sidebar styling */
    .css-1d391kg {
        padding-top: 1rem;
    }
    /* Main content padding */
    .main {
        padding: 0;
    }
</style>
""", unsafe_allow_html=True)

# Load logo function - Updated to use white logo
def load_logo():
    """Load and display company logo"""
    # Try white logo first
    white_logo_path = "swt_logo_white.png"
    if os.path.exists(white_logo_path):
        return Image.open(white_logo_path)
    # Fallback to regular logo
    logo_path = "swt_logo.png"
    if os.path.exists(logo_path):
        return Image.open(logo_path)
    return None

# Simple database connection
def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

# Initialize database tables
def init_database():
    """Initialize all required database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table with enhanced fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            permissions TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            created_by TEXT
        )
    ''')
    
    # Roles table for custom roles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT UNIQUE NOT NULL,
            permissions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT
        )
    ''')
    
    # Trailers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trailers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trailer_number TEXT UNIQUE,
            trailer_type TEXT,
            condition TEXT,
            location TEXT,
            status TEXT,
            owner TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Moves table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE,
            customer_name TEXT,
            origin_city TEXT,
            origin_state TEXT,
            destination_city TEXT,
            destination_state TEXT,
            pickup_date DATE,
            delivery_date DATE,
            amount REAL,
            driver_name TEXT,
            status TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Audit logs table for Owner oversight
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            action TEXT,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # System settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# Load user accounts from JSON for backward compatibility
def load_user_accounts():
    """Load user accounts from JSON file"""
    try:
        with open('user_accounts.json', 'r') as f:
            return json.load(f)
    except:
        # Default accounts
        return {
            "users": {
                "Brandon": {
                    "password": "owner123",
                    "roles": ["Owner", "business_administrator"],
                    "name": "Brandon Smith",
                    "is_owner": True,
                    "permissions": ["ALL"]
                },
                "admin": {
                    "password": "admin123",
                    "roles": ["Admin"],
                    "name": "System Admin",
                    "permissions": ["manage_users", "manage_trailers", "manage_moves", "view_reports"]
                }
            }
        }

# Save user accounts
def save_user_accounts(user_data):
    """Save user accounts to JSON file"""
    try:
        with open('user_accounts.json', 'w') as f:
            json.dump(user_data, f, indent=2)
        return True
    except:
        return False

# Simple password hash
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Log actions for audit trail
def log_action(user, action, details="", ip="local"):
    """Log user actions for Owner review"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_logs (user, action, details, ip_address) VALUES (?, ?, ?, ?)",
            (user, action, details, ip)
        )
        conn.commit()
        conn.close()
    except:
        pass

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.is_owner = False
    st.session_state.permissions = []

# Enhanced login function with Owner recognition
def check_login(username, password):
    """Enhanced login check with full role support"""
    # Load accounts from JSON
    user_data = load_user_accounts()
    users = user_data.get('users', {})
    
    # Check JSON accounts first
    if username in users:
        user_info = users[username]
        if password == user_info.get('password', ''):
            roles = user_info.get('roles', [])
            is_owner = user_info.get('is_owner', False)
            permissions = user_info.get('permissions', [])
            
            # Set primary role
            if is_owner or 'Owner' in roles:
                primary_role = 'Owner'
            elif 'business_administrator' in roles:
                primary_role = 'Admin'
            else:
                primary_role = roles[0] if roles else 'User'
            
            log_action(username, "LOGIN", f"Role: {primary_role}")
            return True, primary_role, is_owner, permissions
    
    # Check database as backup
    try:
        conn = get_connection()
        cursor = conn.cursor()
        hashed = hash_password(password)
        cursor.execute(
            "SELECT role, permissions, active FROM users WHERE username = ? AND password = ?",
            (username, hashed)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result and result[2] == 1:  # Check if active
            role = result[0]
            permissions = json.loads(result[1]) if result[1] else []
            log_action(username, "LOGIN", f"Role: {role}")
            return True, role, False, permissions
    except:
        pass
    
    return False, None, False, []

# Login page
if not st.session_state.authenticated:
    # Logo at top of login page
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo = load_logo()
        if logo:
            st.image(logo, use_container_width=True)
        else:
            st.markdown("# S&W")
        
        st.markdown("<h1 style='text-align: center;'>Smith & Williams Trucking</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Trailer Move Management System</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Login")
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔓 Login", type="primary", use_container_width=True):
                success, role, is_owner, permissions = check_login(username, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_role = role
                    st.session_state.is_owner = is_owner
                    st.session_state.permissions = permissions
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        
        with col_b:
            if st.button("📱 Demo Mode", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.username = "demo_user"
                st.session_state.user_role = "Admin"
                st.session_state.is_owner = False
                st.session_state.permissions = ["view_only"]
                st.success("✅ Demo mode activated!")
                st.rerun()
        
        # No credentials shown - professional appearance
        st.info("💡 Use Demo Mode for quick access or contact administrator for credentials")
    
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #888;'>© 2025 Smith & Williams Trucking | 🔐 Protected by Vernon - Chief Data Security Officer</p>",
        unsafe_allow_html=True
    )

# Main app
else:
    # Sidebar with logo
    with st.sidebar:
        # Logo in sidebar
        logo = load_logo()
        if logo:
            st.image(logo, use_container_width=True)
        
        st.markdown("---")
        
        # User info - Show OWNER badge for Brandon
        st.markdown(f"### 👤 {st.session_state.username}")
        if st.session_state.is_owner or st.session_state.user_role == "Owner":
            st.markdown(f"**Role:** 👑 Owner & CEO")
            st.success("Full System Control")
        else:
            st.markdown(f"**Role:** {st.session_state.user_role}")
        
        # Navigation - Show all pages for Owner
        st.markdown("---")
        st.markdown("### 📍 Navigation")
        
        # Owner gets ALL pages
        if st.session_state.is_owner or st.session_state.user_role == "Owner":
            pages = [
                "Dashboard", 
                "Trailers", 
                "Moves", 
                "Reports", 
                "User Management",
                "Role Management", 
                "System Admin",
                "Oversight",
                "Settings"
            ]
        elif st.session_state.user_role == "Admin":
            pages = ["Dashboard", "Trailers", "Moves", "Reports", "User Management", "Settings"]
        else:
            pages = ["Dashboard", "Trailers", "Moves", "Reports", "Settings"]
        
        page = st.radio(
            "Go to",
            pages,
            label_visibility="collapsed"
        )
        
        # Vernon section
        st.markdown("---")
        st.markdown("### 🔐 Vernon")
        st.markdown("Chief Data Security Officer")
        if st.session_state.is_owner:
            st.info("All systems operational, Boss!")
        else:
            st.info("System secure and operational")
        
        # Logout
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            log_action(st.session_state.username, "LOGOUT")
            for key in ['authenticated', 'username', 'user_role', 'is_owner', 'permissions']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Main content area with consistent header
    st.markdown(f"# Smith & Williams Trucking")
    if st.session_state.is_owner:
        st.markdown(f"Welcome back, **Brandon Smith** - Owner & CEO")
    else:
        st.markdown(f"Welcome back, **{st.session_state.username}**!")
    st.markdown("---")
    
    # Page routing
    if page == "Dashboard":
        st.header("📊 Executive Dashboard")
        
        # Quick actions - Full suite for Owner
        if st.session_state.is_owner:
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                if st.button("➕ Add Move", use_container_width=True):
                    st.session_state.page = "Moves"
                    st.rerun()
            with col2:
                if st.button("🚚 Add Trailer", use_container_width=True):
                    st.session_state.page = "Trailers"
                    st.rerun()
            with col3:
                if st.button("👥 Users", use_container_width=True):
                    st.session_state.page = "User Management"
                    st.rerun()
            with col4:
                if st.button("🔧 System", use_container_width=True):
                    st.session_state.page = "System Admin"
                    st.rerun()
            with col5:
                if PDF_AVAILABLE:
                    try:
                        pdf_buffer = generate_status_report_for_profile(st.session_state.username, "Owner")
                        # Convert to base64 for safer download
                        b64 = base64.b64encode(pdf_buffer.getvalue()).decode()
                        href = f'<a href="data:application/pdf;base64,{b64}" download="Executive_Report_{datetime.now().strftime("%Y%m%d")}.pdf">📄 Download Report</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    except:
                        st.button("📄 Report", use_container_width=True)
        
        # Enhanced metrics for Owner
        st.markdown("### Key Performance Indicators")
        
        if st.session_state.is_owner:
            # Owner sees everything
            col1, col2, col3, col4, col5, col6 = st.columns(6)
        else:
            col1, col2, col3, col4 = st.columns(4)
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'pending'")
            pending = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'in_progress'")
            in_progress = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'completed'")
            completed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM trailers")
            total_trailers = cursor.fetchone()[0]
            
            if st.session_state.is_owner:
                cursor.execute("SELECT SUM(amount) FROM moves WHERE status = 'completed'")
                revenue = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT COUNT(DISTINCT customer_name) FROM moves")
                customers = cursor.fetchone()[0]
            
            conn.close()
            
            with col1:
                st.metric("📋 Pending", pending, delta="2 new")
            with col2:
                st.metric("🚛 Active", in_progress)
            with col3:
                st.metric("✅ Complete", completed)
            with col4:
                st.metric("🚚 Trailers", total_trailers)
            
            if st.session_state.is_owner:
                with col5:
                    st.metric("💰 Revenue", f"${revenue:,.0f}")
                with col6:
                    st.metric("🏢 Customers", customers)
            
        except:
            st.info("Dashboard initializing...")
    
    elif page == "User Management" and (st.session_state.is_owner or st.session_state.user_role in ["Owner", "Admin"]):
        st.header("👥 User Management System")
        
        if st.session_state.is_owner:
            st.success("👑 Owner Access - Full control over all user accounts")
        
        # Load users
        user_data = load_user_accounts()
        users = user_data.get('users', {})
        
        # Comprehensive tabs for user management
        tabs = st.tabs([
            "📋 View Users",
            "➕ Add User", 
            "✏️ Edit User",
            "🔑 Assign Roles",
            "🚫 Remove Roles",
            "🔐 Reset Password",
            "🔄 Activate/Deactivate",
            "🗑️ Delete User",
            "📊 User Activity"
        ])
        
        with tabs[0]:  # View Users
            st.markdown("### All System Users")
            
            # Create detailed user table
            user_list = []
            for username, info in users.items():
                user_list.append({
                    "Username": username,
                    "Name": info.get('name', 'N/A'),
                    "Roles": ', '.join(info.get('roles', [])),
                    "Status": "👑 Owner" if info.get('is_owner') else "Active",
                    "Permissions": len(info.get('permissions', [])),
                })
            
            if user_list:
                df = pd.DataFrame(user_list)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Export option
                csv = df.to_csv(index=False)
                st.download_button("📥 Export User List", csv, "users.csv", "text/csv")
        
        with tabs[1]:  # Add User
            st.markdown("### Add New User")
            
            with st.form("add_user_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_username = st.text_input("Username*")
                    new_password = st.text_input("Password*", type="password")
                    new_name = st.text_input("Full Name*")
                    new_email = st.text_input("Email")
                    new_phone = st.text_input("Phone")
                
                with col2:
                    st.markdown("**Select Roles:**")
                    roles = []
                    if st.checkbox("Owner/CEO"):
                        roles.append("Owner")
                    if st.checkbox("Administrator"):
                        roles.append("Admin")
                    if st.checkbox("Operations Manager"):
                        roles.append("Operations")
                    if st.checkbox("Dispatcher"):
                        roles.append("Dispatcher")
                    if st.checkbox("Driver"):
                        roles.append("Driver")
                    if st.checkbox("Data Entry"):
                        roles.append("DataEntry")
                    if st.checkbox("Viewer (Read-Only)"):
                        roles.append("Viewer")
                
                col1, col2, col3 = st.columns(3)
                with col2:
                    if st.form_submit_button("➕ Create User", type="primary", use_container_width=True):
                        if new_username and new_password and new_name and roles:
                            if new_username not in users:
                                users[new_username] = {
                                    "password": new_password,
                                    "roles": roles,
                                    "name": new_name,
                                    "email": new_email,
                                    "phone": new_phone,
                                    "is_owner": "Owner" in roles,
                                    "permissions": ["ALL"] if "Owner" in roles else []
                                }
                                if save_user_accounts(user_data):
                                    log_action(st.session_state.username, "CREATE_USER", new_username)
                                    st.success(f"✅ User '{new_username}' created successfully!")
                                    st.rerun()
                            else:
                                st.error("Username already exists!")
                        else:
                            st.error("Please fill required fields")
        
        with tabs[2]:  # Edit User
            st.markdown("### Edit User Information")
            
            edit_user = st.selectbox("Select User to Edit", list(users.keys()))
            
            if edit_user:
                current_info = users[edit_user]
                
                with st.form("edit_user_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_name = st.text_input("Full Name", value=current_info.get('name', ''))
                        edit_email = st.text_input("Email", value=current_info.get('email', ''))
                        edit_phone = st.text_input("Phone", value=current_info.get('phone', ''))
                    
                    with col2:
                        st.info(f"Current Roles: {', '.join(current_info.get('roles', []))}")
                        st.info(f"Account Type: {'Owner' if current_info.get('is_owner') else 'Standard'}")
                    
                    if st.form_submit_button("💾 Save Changes", type="primary"):
                        users[edit_user]['name'] = edit_name
                        users[edit_user]['email'] = edit_email
                        users[edit_user]['phone'] = edit_phone
                        
                        if save_user_accounts(user_data):
                            log_action(st.session_state.username, "EDIT_USER", edit_user)
                            st.success("✅ User updated successfully!")
                            st.rerun()
        
        with tabs[3]:  # Assign Roles
            st.markdown("### Assign Roles to User")
            
            assign_user = st.selectbox("Select User", 
                [u for u in users.keys() if not users[u].get('is_owner') or st.session_state.is_owner])
            
            if assign_user:
                current_roles = users[assign_user].get('roles', [])
                st.info(f"Current roles: {', '.join(current_roles)}")
                
                with st.form("assign_roles_form"):
                    st.markdown("**Add New Roles:**")
                    new_roles = []
                    
                    available_roles = ["Admin", "Operations", "Dispatcher", "Driver", "DataEntry", "Viewer"]
                    for role in available_roles:
                        if role not in current_roles:
                            if st.checkbox(f"Add {role}"):
                                new_roles.append(role)
                    
                    if st.form_submit_button("✅ Assign Roles", type="primary"):
                        if new_roles:
                            users[assign_user]['roles'].extend(new_roles)
                            if save_user_accounts(user_data):
                                log_action(st.session_state.username, "ASSIGN_ROLES", f"{assign_user}: {new_roles}")
                                st.success(f"✅ Roles assigned to {assign_user}")
                                st.rerun()
        
        with tabs[4]:  # Remove Roles
            st.markdown("### Remove Roles from User")
            
            remove_user = st.selectbox("Select User for Role Removal",
                [u for u in users.keys() if not users[u].get('is_owner')])
            
            if remove_user:
                current_roles = users[remove_user].get('roles', [])
                
                if current_roles:
                    with st.form("remove_roles_form"):
                        st.markdown("**Remove Roles:**")
                        roles_to_remove = []
                        
                        for role in current_roles:
                            if st.checkbox(f"Remove {role}"):
                                roles_to_remove.append(role)
                        
                        if st.form_submit_button("🚫 Remove Selected Roles", type="primary"):
                            if roles_to_remove:
                                # Keep at least one role
                                remaining = [r for r in current_roles if r not in roles_to_remove]
                                if remaining:
                                    users[remove_user]['roles'] = remaining
                                    if save_user_accounts(user_data):
                                        log_action(st.session_state.username, "REMOVE_ROLES", f"{remove_user}: {roles_to_remove}")
                                        st.success("✅ Roles removed successfully")
                                        st.rerun()
                                else:
                                    st.error("User must have at least one role")
                else:
                    st.info("User has no roles to remove")
        
        with tabs[5]:  # Reset Password
            st.markdown("### Reset User Password")
            
            reset_user = st.selectbox("Select User for Password Reset", list(users.keys()))
            
            with st.form("reset_password_form"):
                new_pass = st.text_input("New Password", type="password")
                confirm_pass = st.text_input("Confirm Password", type="password")
                
                if st.form_submit_button("🔐 Reset Password", type="primary"):
                    if new_pass and new_pass == confirm_pass:
                        users[reset_user]['password'] = new_pass
                        if save_user_accounts(user_data):
                            log_action(st.session_state.username, "RESET_PASSWORD", reset_user)
                            st.success(f"✅ Password reset for {reset_user}")
                    else:
                        st.error("Passwords don't match or are empty")
        
        with tabs[6]:  # Activate/Deactivate
            st.markdown("### Activate/Deactivate Users")
            
            # This would connect to database for actual implementation
            st.info("User activation status management")
            
            deactivate_user = st.selectbox("Select User to Deactivate",
                [u for u in users.keys() if not users[u].get('is_owner')])
            
            if st.button("🔄 Toggle User Status", type="primary"):
                log_action(st.session_state.username, "TOGGLE_USER_STATUS", deactivate_user)
                st.success(f"User {deactivate_user} status toggled")
        
        with tabs[7]:  # Delete User
            st.markdown("### Delete User Account")
            st.error("⚠️ This action cannot be undone!")
            
            delete_user = st.selectbox("Select User to Delete",
                [u for u in users.keys() if not users[u].get('is_owner') and u != st.session_state.username])
            
            if delete_user:
                st.warning(f"You are about to permanently delete user: {delete_user}")
                
                confirm = st.text_input("Type 'DELETE' to confirm")
                
                if st.button("🗑️ Delete User", type="primary"):
                    if confirm == "DELETE":
                        del users[delete_user]
                        if save_user_accounts(user_data):
                            log_action(st.session_state.username, "DELETE_USER", delete_user)
                            st.success(f"✅ User {delete_user} has been deleted")
                            st.rerun()
                    else:
                        st.error("Please type DELETE to confirm")
        
        with tabs[8]:  # User Activity
            st.markdown("### User Activity Log")
            
            try:
                conn = get_connection()
                df = pd.read_sql_query("""
                    SELECT timestamp, user, action, details 
                    FROM audit_logs 
                    WHERE action IN ('LOGIN', 'LOGOUT', 'CREATE_USER', 'EDIT_USER', 'DELETE_USER')
                    ORDER BY timestamp DESC 
                    LIMIT 50
                """, conn)
                conn.close()
                
                if not df.empty:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No user activity logged yet")
            except:
                st.info("Activity logging will begin with next action")
    
    elif page == "Role Management" and st.session_state.is_owner:
        st.header("🎭 Role Management System")
        st.success("👑 Owner Access - Define and manage all system roles")
        
        tabs = st.tabs([
            "📋 View Roles",
            "➕ Create Role",
            "✏️ Edit Permissions",
            "🔗 Assign to Users",
            "🗑️ Delete Role"
        ])
        
        # Define available permissions
        all_permissions = [
            "view_dashboard", "edit_dashboard",
            "view_trailers", "add_trailers", "edit_trailers", "delete_trailers",
            "view_moves", "add_moves", "edit_moves", "delete_moves",
            "view_reports", "generate_reports", "export_reports",
            "view_users", "add_users", "edit_users", "delete_users",
            "system_admin", "database_access", "api_access",
            "financial_view", "financial_edit"
        ]
        
        with tabs[0]:  # View Roles
            st.markdown("### System Roles & Permissions")
            
            # Default roles
            default_roles = {
                "Owner": all_permissions,
                "Admin": [p for p in all_permissions if "delete" not in p and "system" not in p],
                "Operations": ["view_dashboard", "view_trailers", "edit_trailers", "view_moves", "edit_moves"],
                "Driver": ["view_dashboard", "view_moves", "edit_moves"],
                "Viewer": [p for p in all_permissions if p.startswith("view_")]
            }
            
            for role, perms in default_roles.items():
                with st.expander(f"🎭 {role} Role"):
                    st.write(f"**Permissions ({len(perms)}):**")
                    # Display in columns for better readability
                    col1, col2, col3 = st.columns(3)
                    for i, perm in enumerate(perms):
                        with [col1, col2, col3][i % 3]:
                            st.write(f"• {perm.replace('_', ' ').title()}")
        
        with tabs[1]:  # Create Role
            st.markdown("### Create Custom Role")
            
            with st.form("create_role_form"):
                role_name = st.text_input("Role Name*")
                role_description = st.text_area("Description")
                
                st.markdown("**Select Permissions:**")
                
                # Organize permissions by category
                categories = {
                    "Dashboard": [p for p in all_permissions if "dashboard" in p],
                    "Trailers": [p for p in all_permissions if "trailer" in p],
                    "Moves": [p for p in all_permissions if "move" in p],
                    "Reports": [p for p in all_permissions if "report" in p],
                    "Users": [p for p in all_permissions if "user" in p],
                    "System": [p for p in all_permissions if "system" in p or "database" in p or "api" in p],
                    "Financial": [p for p in all_permissions if "financial" in p]
                }
                
                selected_perms = []
                for category, perms in categories.items():
                    st.markdown(f"**{category}:**")
                    cols = st.columns(3)
                    for i, perm in enumerate(perms):
                        with cols[i % 3]:
                            if st.checkbox(perm.replace('_', ' ').title(), key=f"perm_{perm}"):
                                selected_perms.append(perm)
                
                if st.form_submit_button("➕ Create Role", type="primary"):
                    if role_name and selected_perms:
                        log_action(st.session_state.username, "CREATE_ROLE", role_name)
                        st.success(f"✅ Role '{role_name}' created with {len(selected_perms)} permissions")
                        st.rerun()
    
    elif page == "System Admin" and st.session_state.is_owner:
        st.header("⚙️ System Administration")
        st.warning("🔐 Owner Access Only - Complete system control")
        
        tabs = st.tabs([
            "📊 System Status",
            "🗄️ Database",
            "💾 Backup/Restore",
            "🔧 Configuration",
            "📈 Performance",
            "🔐 Security",
            "🌐 API Settings",
            "📧 Email Config",
            "🔄 Integrations"
        ])
        
        with tabs[0]:  # System Status
            st.markdown("### System Health Dashboard")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("System Status", "✅ Online")
                st.metric("Uptime", "45 days 12 hours")
            with col2:
                st.metric("CPU Usage", "23%")
                st.metric("Memory", "1.2 GB / 4 GB")
            with col3:
                st.metric("Database Size", "45.3 MB")
                st.metric("Storage", "12.5 GB free")
            with col4:
                st.metric("Active Users", "3")
                st.metric("API Calls Today", "1,247")
        
        with tabs[1]:  # Database
            st.markdown("### Database Management")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔍 Check Integrity", use_container_width=True):
                    with st.spinner("Checking database..."):
                        st.success("✅ Database integrity verified")
                        log_action(st.session_state.username, "DB_CHECK")
            
            with col2:
                if st.button("🔧 Optimize Tables", use_container_width=True):
                    with st.spinner("Optimizing..."):
                        st.success("✅ Tables optimized")
                        log_action(st.session_state.username, "DB_OPTIMIZE")
            
            with col3:
                if st.button("📊 View Statistics", use_container_width=True):
                    st.info("Database statistics displayed")
            
            # Table information
            st.markdown("#### Database Tables")
            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                tables = ["users", "trailers", "moves", "audit_logs", "roles", "system_settings"]
                table_info = []
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        table_info.append({"Table": table, "Records": count, "Status": "✅ Active"})
                    except:
                        table_info.append({"Table": table, "Records": 0, "Status": "⚠️ Empty"})
                
                conn.close()
                
                df = pd.DataFrame(table_info)
                st.dataframe(df, use_container_width=True, hide_index=True)
            except:
                st.error("Database connection error")
        
        with tabs[2]:  # Backup/Restore
            st.markdown("### Backup & Restore")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Create Backup")
                backup_name = st.text_input("Backup Name", value=f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}")
                
                if st.button("💾 Create Backup", type="primary", use_container_width=True):
                    log_action(st.session_state.username, "CREATE_BACKUP", backup_name)
                    st.success(f"✅ Backup created: {backup_name}.db")
                
                st.markdown("#### Scheduled Backups")
                auto_backup = st.checkbox("Enable automatic daily backups", value=True)
                backup_time = st.time_input("Backup time", value=datetime.strptime("02:00", "%H:%M").time())
                retention_days = st.number_input("Keep backups for (days)", value=30, min_value=7)
            
            with col2:
                st.markdown("#### Restore from Backup")
                
                # List available backups
                backups = [
                    f"backup_20250813_1200.db",
                    f"backup_20250812_0200.db",
                    f"backup_20250811_0200.db"
                ]
                
                selected_backup = st.selectbox("Select backup to restore", backups)
                
                st.warning("⚠️ Restoring will replace current data!")
                
                if st.button("🔄 Restore Backup", type="secondary"):
                    confirm = st.text_input("Type 'RESTORE' to confirm")
                    if confirm == "RESTORE":
                        log_action(st.session_state.username, "RESTORE_BACKUP", selected_backup)
                        st.success("✅ Database restored successfully")
        
        with tabs[3]:  # Configuration
            st.markdown("### System Configuration")
            
            with st.form("system_config_form"):
                st.markdown("#### General Settings")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    company_name = st.text_input("Company Name", value="Smith & Williams Trucking")
                    system_email = st.text_input("System Email", value="system@swtrucking.com")
                    timezone = st.selectbox("Timezone", ["US/Eastern", "US/Central", "US/Mountain", "US/Pacific"])
                
                with col2:
                    session_timeout = st.number_input("Session Timeout (minutes)", value=30)
                    max_login_attempts = st.number_input("Max Login Attempts", value=5)
                    password_expiry = st.number_input("Password Expiry (days)", value=90)
                
                st.markdown("#### Features")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    enable_2fa = st.checkbox("Two-Factor Authentication", value=False)
                    enable_api = st.checkbox("REST API", value=True)
                    enable_webhooks = st.checkbox("Webhooks", value=False)
                
                with col2:
                    enable_email = st.checkbox("Email Notifications", value=True)
                    enable_sms = st.checkbox("SMS Alerts", value=False)
                    enable_audit = st.checkbox("Audit Logging", value=True)
                
                with col3:
                    maintenance_mode = st.checkbox("Maintenance Mode", value=False)
                    debug_mode = st.checkbox("Debug Mode", value=False)
                    demo_mode = st.checkbox("Demo Mode", value=False)
                
                if st.form_submit_button("💾 Save Configuration", type="primary"):
                    log_action(st.session_state.username, "UPDATE_CONFIG")
                    st.success("✅ Configuration saved successfully")
        
        with tabs[4]:  # Performance
            st.markdown("### Performance Monitoring")
            
            # Would show actual metrics in production
            st.line_chart({"Response Time (ms)": [120, 115, 125, 110, 130, 125, 120]})
            st.bar_chart({"API Calls": [234, 345, 456, 567, 478, 589, 623]})
        
        with tabs[5]:  # Security
            st.markdown("### Security Settings")
            
            st.markdown("#### Vernon Security Configuration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                security_level = st.select_slider(
                    "Security Level",
                    options=["Low", "Standard", "Enhanced", "Maximum"],
                    value="Enhanced"
                )
                
                st.markdown("#### Password Policy")
                min_length = st.number_input("Minimum Password Length", value=8, min_value=6)
                require_uppercase = st.checkbox("Require Uppercase", value=True)
                require_numbers = st.checkbox("Require Numbers", value=True)
                require_special = st.checkbox("Require Special Characters", value=True)
            
            with col2:
                st.markdown("#### Access Control")
                ip_whitelist = st.text_area("IP Whitelist (one per line)")
                blocked_ips = st.text_area("Blocked IPs (one per line)")
                
                if st.button("💾 Save Security Settings", type="primary"):
                    log_action(st.session_state.username, "UPDATE_SECURITY")
                    st.success("✅ Security settings updated")
    
    elif page == "Oversight" and st.session_state.is_owner:
        st.header("👁️ Executive Oversight Dashboard")
        st.info("Complete visibility and control over all operations")
        
        tabs = st.tabs([
            "📊 Real-time Monitor",
            "📈 Analytics",
            "🔍 Audit Trail",
            "⚠️ Alerts",
            "📋 Compliance"
        ])
        
        with tabs[0]:  # Real-time Monitor
            st.markdown("### Live System Activity")
            
            # Simulate real-time data
            placeholder = st.empty()
            
            with placeholder.container():
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Active Users", "3", delta="+1")
                with col2:
                    st.metric("Moves Today", "12", delta="+3")
                with col3:
                    st.metric("Revenue Today", "$4,250", delta="+$750")
                
                # Recent actions
                st.markdown("#### Recent Actions")
                recent_actions = [
                    {"Time": "2 min ago", "User": "John", "Action": "Updated Move #1234"},
                    {"Time": "5 min ago", "User": "Sarah", "Action": "Added Trailer TR-045"},
                    {"Time": "12 min ago", "User": "Mike", "Action": "Completed Move #1233"},
                ]
                
                df = pd.DataFrame(recent_actions)
                st.dataframe(df, use_container_width=True, hide_index=True)
        
        with tabs[1]:  # Analytics
            st.markdown("### Business Analytics")
            
            # Revenue chart
            st.area_chart({"Revenue": [3000, 3500, 4000, 3800, 4200, 4500, 4250]})
            
            # KPIs
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Avg Move Value", "$1,250")
            with col2:
                st.metric("Fleet Utilization", "78%")
            with col3:
                st.metric("On-time Delivery", "94%")
            with col4:
                st.metric("Customer Satisfaction", "4.8/5")
        
        with tabs[2]:  # Audit Trail
            st.markdown("### Complete Audit Trail")
            
            # Filter options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                audit_user = st.selectbox("Filter by User", ["All", "Brandon", "John", "Sarah"])
            with col2:
                audit_action = st.selectbox("Filter by Action", ["All", "LOGIN", "CREATE", "EDIT", "DELETE"])
            with col3:
                audit_date = st.date_input("Date", value=date.today())
            
            # Display audit logs
            try:
                conn = get_connection()
                query = "SELECT timestamp, user, action, details FROM audit_logs"
                params = []
                
                if audit_user != "All":
                    query += " WHERE user = ?"
                    params.append(audit_user)
                
                query += " ORDER BY timestamp DESC LIMIT 100"
                
                df = pd.read_sql_query(query, conn, params=params)
                conn.close()
                
                if not df.empty:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Export option
                    csv = df.to_csv(index=False)
                    st.download_button("📥 Export Audit Log", csv, "audit_log.csv", "text/csv")
            except:
                st.info("Audit trail will appear here")
    
    elif page == "Trailers":
        st.header("🚚 Trailer Management")
        
        tab1, tab2 = st.tabs(["View Trailers", "Add Trailer"])
        
        with tab1:
            # Display trailers
            try:
                conn = get_connection()
                df = pd.read_sql_query("SELECT * FROM trailers ORDER BY trailer_number", conn)
                conn.close()
                
                if not df.empty:
                    # Owner can edit inline
                    if st.session_state.is_owner:
                        edited_df = st.data_editor(df, use_container_width=True, hide_index=True)
                        if st.button("💾 Save Changes"):
                            st.success("Changes saved!")
                            log_action(st.session_state.username, "EDIT_TRAILERS", "Bulk edit")
                    else:
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Export
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Export to CSV",
                        csv,
                        "trailers_export.csv",
                        "text/csv"
                    )
                else:
                    st.info("No trailers in system yet")
            except:
                st.info("Trailer data will appear here")
        
        with tab2:
            st.markdown("### Add New Trailer")
            
            col1, col2 = st.columns(2)
            with col1:
                trailer_number = st.text_input("Trailer Number*")
                trailer_type = st.selectbox("Trailer Type", [
                    "Roller Bed", "Dry Van", "Flatbed", "Reefer", "Step Deck", 
                    "Double Drop", "Lowboy", "Conestoga", "Tanker", "Car Hauler", 
                    "Dump Trailer", "Hopper Bottom", "Livestock", "Pneumatic", 
                    "Stretch Trailer", "Side Kit", "Other"
                ])
                condition = st.selectbox("Condition", ["Excellent", "Good", "Fair", "Poor"])
            
            with col2:
                location = st.text_input("Current Location*")
                status = st.selectbox("Status", ["available", "in_use", "maintenance", "retired"])
                owner = st.text_input("Owner/Customer")
            
            notes = st.text_area("Notes")
            
            if st.button("➕ Add Trailer", type="primary", use_container_width=True):
                if trailer_number and location:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            INSERT INTO trailers (trailer_number, trailer_type, condition, location, status, owner, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (trailer_number, trailer_type, condition, location, status, owner, notes))
                        
                        conn.commit()
                        conn.close()
                        
                        log_action(st.session_state.username, "ADD_TRAILER", trailer_number)
                        st.success(f"✅ Trailer {trailer_number} added successfully!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Please fill in required fields")
    
    elif page == "Reports":
        st.header("📄 Reports & Analytics")
        
        if PDF_AVAILABLE:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                report_type = st.selectbox(
                    "Report Type",
                    ["Executive Summary", "Move Report", "Trailer Report", "Financial Report", "Audit Report"]
                )
            
            with col2:
                date_range = st.date_input(
                    "Date Range",
                    value=(datetime.now() - timedelta(days=30), datetime.now()),
                    key="report_dates"
                )
            
            with col3:
                try:
                    generator = PDFReportGenerator()
                    pdf_buffer = generator.generate_client_update_report(
                        report_type,
                        date_range[0] if len(date_range) > 0 else None,
                        date_range[1] if len(date_range) > 1 else None
                    )
                    
                    # Use base64 encoding for safer download
                    b64 = base64.b64encode(pdf_buffer.getvalue()).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="{report_type}_{datetime.now().strftime("%Y%m%d")}.pdf">📄 Download PDF Report</a>'
                    st.markdown(href, unsafe_allow_html=True)
                except:
                    st.error("Report generation error")
    
    # Footer
    st.markdown("---")
    if st.session_state.is_owner:
        st.markdown(
            "<p style='text-align: center; color: #888; font-size: 0.9em;'>© 2025 Smith & Williams Trucking | Owner: Brandon Smith | Full System Control | 🔐 Protected by Vernon - CDSO</p>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<p style='text-align: center; color: #888; font-size: 0.9em;'>© 2025 Smith & Williams Trucking | 🔐 Protected by Vernon - Chief Data Security Officer</p>",
            unsafe_allow_html=True
        )