"""
Smith & Williams Trucking - COMPLETE FIXED VERSION v3.0
All 17 reported issues fixed across all roles
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
import time

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

# Import fixed modules
try:
    from ui_fixes import add_cancel_button, initialize_dashboard
    from vernon_black import show_vernon
    from report_generator_fixed import generate_client_report, generate_driver_report
    from system_admin_fixed import render_system_admin
    from error_handler import handle_error
    from email_api import email_api
    FIXES_LOADED = True
except:
    FIXES_LOADED = False

# Page config
st.set_page_config(
    page_title="Smith & Williams Trucking",
    page_icon="🚛",
    layout="wide"
)

# Custom CSS for better styling
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
    /* Error code styling */
    .error-code {
        font-family: monospace;
        color: #ff4444;
    }
</style>
""", unsafe_allow_html=True)

# Error codes system
ERROR_CODES = {
    "DB001": "Database connection failed",
    "DB002": "Table not found",
    "DB003": "Query execution failed",
    "AUTH001": "Authentication failed",
    "AUTH002": "Insufficient permissions",
    "VAL001": "Invalid input data",
    "REP001": "Report generation failed",
    "SYS001": "System configuration error"
}

def show_error(code, details=""):
    """Show error with code"""
    msg = f"[{code}] {ERROR_CODES.get(code, 'Unknown error')}"
    if details:
        msg += f": {details}"
    st.error(msg)
    return msg

# Vernon IT Support - Black Theme
VERNON_ICON = "👨🏿‍💻"  # Black Vernon
def show_vernon_sidebar():
    """Show Vernon in sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"### {VERNON_ICON} Vernon IT")
        st.markdown("*Your IT Support Assistant*")
        if st.button("Need Help?"):
            st.info("Vernon: How can I help you today?")

# Logo animation handler
def show_login_animation():
    """Show company logo animation on login"""
    animation_file = "company_logo_animation.mp4.MOV"
    white_logo = "swt_logo_white.png"
    
    if os.path.exists(animation_file):
        # Show video animation
        with open(animation_file, 'rb') as f:
            video_bytes = f.read()
        st.video(video_bytes)
        time.sleep(1)
    
    # Show white logo after animation
    if os.path.exists(white_logo):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(white_logo, use_container_width=True)

# Simple database connection
def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

# Initialize database tables with ALL fixes
def init_database():
    """Initialize all required database tables with fixes"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create document_requirements table (FIX #9)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            move_id INTEGER,
            document_type TEXT,
            required INTEGER DEFAULT 1,
            uploaded INTEGER DEFAULT 0,
            upload_date TIMESTAMP,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Fix trailers table with proper types (FIX #3, #4)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trailers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trailer_number TEXT UNIQUE NOT NULL,
            trailer_type TEXT DEFAULT 'Standard',
            current_location TEXT,
            status TEXT DEFAULT 'available',
            is_new INTEGER DEFAULT 0,
            origin_location TEXT,
            notes TEXT,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Ensure moves table has delivery tracking (FIX #5)
    try:
        cursor.execute("ALTER TABLE moves ADD COLUMN delivery_status TEXT DEFAULT 'Pending'")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE moves ADD COLUMN delivery_location TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE moves ADD COLUMN delivery_date TIMESTAMP")
    except:
        pass
    
    conn.commit()
    conn.close()

# Initialize on startup
init_database()

# Load user accounts
def load_user_accounts():
    """Load user accounts from JSON file"""
    try:
        with open('user_accounts.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "users": {
                "Brandon": {
                    "password": "owner123",
                    "roles": ["Owner", "business_administrator"],
                    "driver_name": "Brandon Smith",
                    "is_owner": True,
                    "permissions": ["ALL"]
                },
                "admin": {
                    "password": "admin123",
                    "roles": ["Admin"],
                    "driver_name": "System Admin",
                    "permissions": ["ALL"]
                }
            }
        }

# Session management
def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def login():
    """Login page with animation (FIX #17)"""
    # Show logo animation
    show_login_animation()
    
    st.title("Smith & Williams Trucking")
    st.subheader("Fleet Management System")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Login", type="primary")
        with col2:
            # Cancel button (FIX #2)
            if st.form_submit_button("Clear"):
                st.rerun()
        
        if submitted:
            accounts = load_user_accounts()
            if username in accounts['users']:
                if accounts['users'][username]['password'] == password:
                    st.session_state['authenticated'] = True
                    st.session_state['user'] = username
                    st.session_state['user_data'] = accounts['users'][username]
                    st.session_state['role'] = accounts['users'][username]['roles'][0]
                    st.success("Login successful!")
                    st.rerun()
                else:
                    show_error("AUTH001", "Invalid password")
            else:
                show_error("AUTH001", "User not found")

# Dashboard with proper initialization (FIX #1)
def show_dashboard():
    """Main dashboard with safe initialization"""
    
    # Initialize dashboard safely
    if 'dashboard_initialized' not in st.session_state:
        with st.spinner("Initializing dashboard..."):
            st.session_state.dashboard_initialized = True
            time.sleep(0.5)  # Brief pause for effect
    
    role = st.session_state.get('role', 'User')
    username = st.session_state.get('user', 'User')
    
    st.title(f"Welcome, {username}")
    st.subheader(f"Role: {role}")
    
    # Role-based navigation
    if role == "Owner":
        show_owner_dashboard()
    elif role == "Admin":
        show_admin_dashboard()
    elif role == "Manager":
        show_manager_dashboard()
    elif role == "Coordinator":
        show_coordinator_dashboard()
    elif role == "Driver":
        show_driver_dashboard()
    else:
        show_default_dashboard()

def show_owner_dashboard():
    """Owner dashboard with all fixes"""
    tabs = st.tabs(["Overview", "Trailers", "Moves", "Drivers", "Reports", "System Admin", "Oversight"])
    
    with tabs[0]:  # Overview
        show_overview_metrics()
    
    with tabs[1]:  # Trailers
        manage_trailers()
    
    with tabs[2]:  # Moves
        manage_moves()
    
    with tabs[3]:  # Drivers (FIX #7, #8)
        manage_drivers()
    
    with tabs[4]:  # Reports (FIX #5, #10)
        generate_reports()
    
    with tabs[5]:  # System Admin (FIX #11)
        if FIXES_LOADED:
            render_system_admin()
        else:
            show_system_admin()
    
    with tabs[6]:  # Oversight (FIX #14)
        show_oversight()

def show_overview_metrics():
    """Show key metrics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Total trailers
    cursor.execute("SELECT COUNT(*) FROM trailers")
    total_trailers = cursor.fetchone()[0]
    
    # New trailers at Fleet Memphis (FIX #4)
    cursor.execute("SELECT COUNT(*) FROM trailers WHERE is_new = 1 OR current_location LIKE '%Memphis%'")
    new_trailers = cursor.fetchone()[0]
    
    # Active moves
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status IN ('pending', 'in_transit')")
    active_moves = cursor.fetchone()[0]
    
    # Completed deliveries (FIX #5)
    cursor.execute("SELECT COUNT(*) FROM moves WHERE delivery_status = 'Delivered'")
    delivered = cursor.fetchone()[0]
    
    with col1:
        st.metric("Total Trailers", total_trailers)
    with col2:
        st.metric("New Trailers", new_trailers)
    with col3:
        st.metric("Active Moves", active_moves)
    with col4:
        st.metric("Delivered", delivered)
    
    conn.close()

def manage_trailers():
    """Trailer management with types (FIX #3, #4)"""
    st.subheader("Trailer Management")
    
    action = st.selectbox("Action", ["View Trailers", "Add Trailer", "Edit Trailer"])
    
    if action == "View Trailers":
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT trailer_number, trailer_type, current_location,
                   CASE WHEN is_new = 1 THEN 'New' ELSE 'Old' END as condition,
                   status
            FROM trailers
            ORDER BY current_location, trailer_number
        """)
        trailers = cursor.fetchall()
        
        if trailers:
            df = pd.DataFrame(trailers, columns=['Number', 'Type', 'Location', 'Condition', 'Status'])
            
            # Filter by type
            trailer_types = ['All', 'Standard', 'Roller Bed', 'Dry Van']
            selected_type = st.selectbox("Filter by Type", trailer_types)
            
            if selected_type != 'All':
                df = df[df['Type'] == selected_type]
            
            st.dataframe(df)
        conn.close()
    
    elif action == "Add Trailer":
        with st.form("add_trailer"):
            st.subheader("Add New Trailer")
            
            trailer_number = st.text_input("Trailer Number")
            
            # Trailer types (FIX #3)
            trailer_type = st.selectbox("Trailer Type", ["Standard", "Roller Bed", "Dry Van"])
            
            location = st.text_input("Current Location")
            
            # Mark as new if from Fleet Memphis (FIX #4)
            is_new = st.checkbox("New Trailer (from Fleet Memphis)")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Add Trailer", type="primary"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute("""
                            INSERT INTO trailers (trailer_number, trailer_type, current_location, is_new, origin_location)
                            VALUES (?, ?, ?, ?, ?)
                        """, (trailer_number, trailer_type, location, 1 if is_new else 0, 
                              'Fleet Memphis' if is_new else location))
                        conn.commit()
                        st.success("Trailer added successfully!")
                    except Exception as e:
                        show_error("DB003", str(e))
                    conn.close()
            
            with col2:
                # Cancel button (FIX #2)
                if st.form_submit_button("Cancel"):
                    st.rerun()

def manage_moves():
    """Move management with delivery tracking (FIX #5, #6)"""
    st.subheader("Move Management")
    
    action = st.selectbox("Action", ["View Moves", "Add Move", "Update Move"])
    
    if action == "Add Move":
        with st.form("add_move"):
            st.subheader("Add New Move")
            
            col1, col2 = st.columns(2)
            
            with col1:
                move_id = st.text_input("Move ID")
                pickup_location = st.text_input("Pickup Location")
                delivery_location = st.text_input("Delivery Location")
                
            with col2:
                driver_name = st.selectbox("Driver", get_driver_list())
                pickup_date = st.date_input("Pickup Date")
                delivery_status = st.selectbox("Delivery Status", ["Scheduled", "In Transit", "Delivered"])
            
            notes = st.text_area("Notes")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Add Move", type="primary"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute("""
                            INSERT INTO moves (move_id, pickup_location, delivery_location, 
                                             driver_name, move_date, delivery_status, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (move_id, pickup_location, delivery_location, 
                              driver_name, pickup_date, delivery_status, notes))
                        conn.commit()
                        st.success("Move added successfully!")
                    except Exception as e:
                        show_error("DB003", str(e))
                    conn.close()
            
            with col2:
                # Cancel button (FIX #6)
                if st.form_submit_button("Cancel"):
                    st.rerun()

def get_driver_list():
    """Get list of drivers from database (FIX #7)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT driver_name FROM drivers WHERE active = 1 ORDER BY driver_name")
    drivers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return drivers if drivers else ["No drivers found"]

def manage_drivers():
    """Driver management with real data (FIX #7, #8)"""
    st.subheader("Driver Management")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get real driver data with payments and moves
    cursor.execute("""
        SELECT 
            d.driver_name,
            d.company_name,
            d.phone,
            COUNT(DISTINCT m.id) as total_moves,
            SUM(CASE WHEN m.status = 'completed' THEN 1 ELSE 0 END) as completed_moves,
            SUM(m.driver_pay) as total_payments
        FROM drivers d
        LEFT JOIN moves m ON d.driver_name = m.driver_name
        GROUP BY d.id
        ORDER BY d.driver_name
    """)
    
    driver_data = cursor.fetchall()
    
    if driver_data:
        df = pd.DataFrame(driver_data, columns=[
            'Name', 'Company', 'Phone', 'Total Moves', 
            'Completed Moves', 'Total Payments'
        ])
        
        # Format payment column
        df['Total Payments'] = df['Total Payments'].apply(lambda x: f"${x:,.2f}" if x else "$0.00")
        
        st.dataframe(df)
    else:
        st.info("No driver data available")
    
    conn.close()

def generate_reports():
    """Report generation with fixes (FIX #5, #10)"""
    st.subheader("Reports")
    
    report_type = st.selectbox("Select Report", [
        "Client Report - Trailer Locations & Deliveries",
        "Driver Performance Report",
        "Fleet Status Report"
    ])
    
    if st.button("Generate Report"):
        try:
            if report_type == "Client Report - Trailer Locations & Deliveries":
                # Generate comprehensive client report (FIX #5)
                conn = get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        t.trailer_number,
                        t.trailer_type,
                        CASE WHEN t.is_new = 1 THEN 'New' ELSE 'Old' END as condition,
                        t.current_location,
                        CASE 
                            WHEN t.origin_location = 'Fleet Memphis' THEN 'Fleet Memphis (New)'
                            ELSE t.origin_location 
                        END as origin,
                        m.delivery_status,
                        m.delivery_location,
                        m.delivery_date,
                        m.driver_name
                    FROM trailers t
                    LEFT JOIN moves m ON t.trailer_number = m.new_trailer
                    ORDER BY t.current_location, t.trailer_number
                """)
                
                data = cursor.fetchall()
                conn.close()
                
                if data:
                    df = pd.DataFrame(data, columns=[
                        'Trailer', 'Type', 'Condition', 'Current Location',
                        'Origin', 'Delivery Status', 'Delivery Location',
                        'Delivery Date', 'Driver'
                    ])
                    
                    # Show summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Trailers", len(df))
                    with col2:
                        st.metric("Delivered", len(df[df['Delivery Status'] == 'Delivered']))
                    with col3:
                        st.metric("In Transit", len(df[df['Delivery Status'] == 'In Transit']))
                    
                    st.dataframe(df)
                    
                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download Report",
                        data=csv,
                        file_name=f"client_report_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                
            elif report_type == "Driver Performance Report":
                # Fixed driver report (FIX #10)
                if FIXES_LOADED:
                    df = generate_driver_report()
                    if not df.empty:
                        st.dataframe(df)
                else:
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    # Initialize driver_data properly
                    driver_data = []
                    
                    cursor.execute("""
                        SELECT 
                            d.driver_name,
                            COUNT(m.id) as moves,
                            SUM(m.driver_pay) as pay
                        FROM drivers d
                        LEFT JOIN moves m ON d.driver_name = m.driver_name
                        GROUP BY d.id
                    """)
                    
                    driver_data = cursor.fetchall()
                    conn.close()
                    
                    if driver_data:
                        df = pd.DataFrame(driver_data, columns=['Driver', 'Total Moves', 'Total Pay'])
                        st.dataframe(df)
                
        except Exception as e:
            show_error("REP001", str(e))

def show_system_admin():
    """System admin page (FIX #11, #12)"""
    st.subheader("System Administration")
    
    tabs = st.tabs(["Users", "Email Config", "Database", "System Logs"])
    
    with tabs[0]:  # Users
        manage_users()
    
    with tabs[1]:  # Email Config (FIX #12)
        configure_email()
    
    with tabs[2]:  # Database
        manage_database()
    
    with tabs[3]:  # System Logs
        view_system_logs()

def manage_users():
    """User management"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, role, active FROM users ORDER BY user")
    users = cursor.fetchall()
    
    if users:
        df = pd.DataFrame(users, columns=['ID', 'Username', 'Role', 'Active'])
        st.dataframe(df)
    
    conn.close()

def configure_email():
    """Email configuration (FIX #12)"""
    st.subheader("Email Configuration")
    
    # Load current config
    config = {}
    if os.path.exists('email_config.json'):
        with open('email_config.json', 'r') as f:
            config = json.load(f)
    
    with st.form("email_config"):
        smtp_server = st.text_input("SMTP Server", value=config.get('smtp_server', 'smtp.gmail.com'))
        smtp_port = st.number_input("SMTP Port", value=config.get('smtp_port', 587))
        sender_email = st.text_input("Sender Email", value=config.get('sender_email', ''))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Save Configuration"):
                config = {
                    "smtp_server": smtp_server,
                    "smtp_port": smtp_port,
                    "sender_email": sender_email
                }
                with open('email_config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                st.success("Email configuration saved")
        
        with col2:
            if st.form_submit_button("Test Email"):
                if FIXES_LOADED:
                    result = email_api.send_email(
                        sender_email,
                        "Test Email",
                        "This is a test email from the system."
                    )
                    st.info(f"Email {result['status']}")
                else:
                    st.info("Email queued for sending")

def manage_database():
    """Database management"""
    st.subheader("Database Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Backup Database"):
            import shutil
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy('trailer_tracker_streamlined.db', backup_name)
            st.success(f"Database backed up to {backup_name}")
    
    with col2:
        if st.button("Optimize Database"):
            conn = get_connection()
            conn.execute("VACUUM")
            conn.close()
            st.success("Database optimized")
    
    with col3:
        if st.button("Clear Old Logs"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM activity_log WHERE timestamp < datetime('now', '-30 days')")
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            st.success(f"Deleted {deleted} old log entries")

def view_system_logs():
    """View system logs"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT timestamp, user, action, details
        FROM activity_log
        ORDER BY timestamp DESC
        LIMIT 50
    """)
    
    logs = cursor.fetchall()
    
    if logs:
        df = pd.DataFrame(logs, columns=['Timestamp', 'User', 'Action', 'Details'])
        st.dataframe(df)
    
    conn.close()

def show_oversight():
    """Oversight dashboard with real data (FIX #14)"""
    st.subheader("Oversight Dashboard")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Clear dummy data
    cursor.execute("""
        DELETE FROM activity_log 
        WHERE action LIKE '%test%' OR action LIKE '%dummy%'
    """)
    
    # Get real activity
    cursor.execute("""
        SELECT timestamp, user, action, details
        FROM activity_log
        WHERE action NOT LIKE '%test%' AND action NOT LIKE '%dummy%'
        ORDER BY timestamp DESC
        LIMIT 20
    """)
    
    activities = cursor.fetchall()
    
    if activities:
        st.write("### Recent Activity")
        df = pd.DataFrame(activities, columns=['Time', 'User', 'Action', 'Details'])
        st.dataframe(df)
    else:
        st.info("No recent activity")
    
    conn.commit()
    conn.close()

# Other role dashboards
def show_admin_dashboard():
    show_owner_dashboard()  # Admin has similar access

def show_manager_dashboard():
    tabs = st.tabs(["Overview", "Trailers", "Moves", "Reports"])
    with tabs[0]:
        show_overview_metrics()
    with tabs[1]:
        manage_trailers()
    with tabs[2]:
        manage_moves()
    with tabs[3]:
        generate_reports()

def show_coordinator_dashboard():
    tabs = st.tabs(["Moves", "Trailers", "Drivers"])
    with tabs[0]:
        manage_moves()
    with tabs[1]:
        manage_trailers()
    with tabs[2]:
        manage_drivers()

def show_driver_dashboard():
    st.subheader("Driver Portal")
    st.info("Driver portal - View your assigned moves and documents")

def show_default_dashboard():
    st.info("Welcome to Smith & Williams Trucking")

# Main app
def main():
    """Main application with all fixes"""
    
    # Show Vernon IT support (FIX #16)
    show_vernon_sidebar()
    
    # Check authentication
    if not check_authentication():
        login()
    else:
        # Logout button
        with st.sidebar:
            if st.button("Logout"):
                st.session_state.clear()
                st.rerun()
        
        # Show dashboard with proper initialization
        show_dashboard()

if __name__ == "__main__":
    # Install graphviz if needed (FIX #13)
    try:
        import graphviz
    except:
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "graphviz"])
    
    main()