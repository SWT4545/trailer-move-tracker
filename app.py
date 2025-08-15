"""
Smith & Williams Trucking - Restored Complete Version
All features integrated with proper navigation and real data
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
import time

# Page config
st.set_page_config(
    page_title="Smith & Williams Trucking",
    page_icon="🚛",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .logo-container { text-align: center; padding: 1rem; }
    .logo-img { max-width: 200px; margin: 0 auto; }
    .main { padding: 0; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; }
</style>
""", unsafe_allow_html=True)

# Database connection
def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

# Initialize database
def init_database():
    """Initialize all required database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create all necessary tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_name TEXT UNIQUE NOT NULL,
        company_name TEXT,
        phone TEXT,
        email TEXT,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS trailers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trailer_number TEXT UNIQUE NOT NULL,
        trailer_type TEXT DEFAULT 'Standard',
        current_location TEXT,
        status TEXT DEFAULT 'available',
        is_new INTEGER DEFAULT 0,
        notes TEXT,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        move_date TEXT,
        trailer_id INTEGER,
        origin TEXT,
        destination TEXT,
        client TEXT,
        driver TEXT,
        driver_name TEXT,
        driver_pay REAL DEFAULT 0,
        status TEXT DEFAULT 'pending',
        delivery_status TEXT DEFAULT 'Pending',
        delivery_location TEXT,
        delivery_date TIMESTAMP,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trailer_id) REFERENCES trailers(id)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_title TEXT UNIQUE,
        address TEXT,
        city TEXT,
        state TEXT,
        zip_code TEXT,
        is_base_location INTEGER DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user TEXT,
        action TEXT,
        details TEXT
    )''')
    
    conn.commit()
    conn.close()

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
                    "roles": ["Owner"],
                    "driver_name": "Brandon Smith",
                    "is_owner": True,
                    "permissions": ["ALL"]
                },
                "admin": {
                    "password": "admin123",
                    "roles": ["Admin"],
                    "permissions": ["ALL"]
                },
                "manager": {
                    "password": "manager123",
                    "roles": ["Manager"],
                    "permissions": ["manage_moves", "manage_trailers", "view_reports"]
                },
                "coordinator": {
                    "password": "coord123",
                    "roles": ["Coordinator"],
                    "permissions": ["manage_moves", "view_trailers"]
                },
                "JDuckett": {
                    "password": "driver123",
                    "roles": ["Driver"],
                    "driver_name": "Justin Duckett",
                    "permissions": ["view_own_moves"]
                },
                "CStrickland": {
                    "password": "driver123",
                    "roles": ["Driver"],
                    "driver_name": "Carl Strickland",
                    "permissions": ["view_own_moves"]
                }
            }
        }

# Authentication
def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def login():
    """Login page"""
    # Show logo
    logo_path = "swt_logo_white.png" if os.path.exists("swt_logo_white.png") else "swt_logo.png"
    if os.path.exists(logo_path):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo_path, use_container_width=True)
    
    st.title("Smith & Williams Trucking")
    st.subheader("Fleet Management System")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Login", type="primary")
        with col2:
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
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid password")
            else:
                st.error("User not found")

# Dashboard functions
def show_overview_metrics():
    """Show overview metrics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Total trailers
    cursor.execute("SELECT COUNT(*) FROM trailers")
    total_trailers = cursor.fetchone()[0]
    
    # Available trailers
    cursor.execute("SELECT COUNT(*) FROM trailers WHERE status = 'available'")
    available = cursor.fetchone()[0]
    
    # Active moves
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status IN ('pending', 'in_transit')")
    active_moves = cursor.fetchone()[0]
    
    # Completed moves
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'completed'")
    completed = cursor.fetchone()[0]
    
    with col1:
        st.metric("Total Trailers", total_trailers)
    with col2:
        st.metric("Available", available)
    with col3:
        st.metric("Active Moves", active_moves)
    with col4:
        st.metric("Completed", completed)
    
    conn.close()

def manage_trailers():
    """Trailer management"""
    st.subheader("Trailer Management")
    
    tab1, tab2, tab3 = st.tabs(["View Trailers", "Add Trailer", "Edit Trailer"])
    
    with tab1:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT trailer_number, trailer_type, current_location, status
            FROM trailers ORDER BY trailer_number
        """)
        data = cursor.fetchall()
        
        if data:
            df = pd.DataFrame(data, columns=['Trailer #', 'Type', 'Location', 'Status'])
            
            # Add status colors
            def color_status(val):
                colors = {
                    'available': 'background-color: #90EE90',
                    'in_transit': 'background-color: #FFD700',
                    'maintenance': 'background-color: #FF6B6B'
                }
                return colors.get(val, '')
            
            styled_df = df.style.applymap(color_status, subset=['Status'])
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.info("No trailers found")
        conn.close()
    
    with tab2:
        with st.form("add_trailer"):
            st.write("Add New Trailer")
            trailer_number = st.text_input("Trailer Number")
            trailer_type = st.selectbox("Type", ["Standard", "Refrigerated", "Flatbed"])
            location = st.text_input("Current Location")
            
            if st.form_submit_button("Add Trailer"):
                conn = get_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO trailers (trailer_number, trailer_type, current_location, status)
                        VALUES (?, ?, ?, 'available')
                    """, (trailer_number, trailer_type, location))
                    conn.commit()
                    st.success(f"Trailer {trailer_number} added successfully!")
                    time.sleep(1)
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Trailer number already exists")
                finally:
                    conn.close()
    
    with tab3:
        st.info("Select a trailer to edit from the view tab")

def manage_moves():
    """Move management"""
    st.subheader("Move Management")
    
    tab1, tab2, tab3 = st.tabs(["Active Moves", "Create Move", "Move History"])
    
    with tab1:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, move_date, origin, destination, driver_name, status
            FROM moves 
            WHERE status IN ('pending', 'in_transit')
            ORDER BY move_date DESC
        """)
        data = cursor.fetchall()
        
        if data:
            df = pd.DataFrame(data, columns=['ID', 'Date', 'Origin', 'Destination', 'Driver', 'Status'])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No active moves")
        conn.close()
    
    with tab2:
        with st.form("create_move"):
            st.write("Create New Move")
            col1, col2 = st.columns(2)
            
            with col1:
                move_date = st.date_input("Move Date", date.today())
                origin = st.text_input("Origin")
                destination = st.text_input("Destination")
            
            with col2:
                client = st.text_input("Client", value="Metro Logistics, Inc.")
                driver = st.text_input("Driver")
                driver_pay = st.number_input("Driver Pay", min_value=0.0, step=10.0)
            
            notes = st.text_area("Notes")
            
            if st.form_submit_button("Create Move"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO moves (move_date, origin, destination, client, driver, driver_name, driver_pay, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """, (str(move_date), origin, destination, client, driver, driver, driver_pay, notes))
                conn.commit()
                conn.close()
                st.success("Move created successfully!")
                time.sleep(1)
                st.rerun()
    
    with tab3:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT move_date, origin, destination, driver_name, status, driver_pay
            FROM moves 
            WHERE status = 'completed'
            ORDER BY move_date DESC
            LIMIT 50
        """)
        data = cursor.fetchall()
        
        if data:
            df = pd.DataFrame(data, columns=['Date', 'Origin', 'Destination', 'Driver', 'Status', 'Pay'])
            df['Pay'] = df['Pay'].apply(lambda x: f"${x:,.2f}" if x else "$0.00")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No completed moves")
        conn.close()

def manage_drivers():
    """Driver management"""
    st.subheader("Driver Management")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get driver data
    cursor.execute("""
        SELECT d.driver_name, d.company_name, d.phone, 
               COUNT(m.id) as total_moves,
               SUM(CASE WHEN m.status = 'completed' THEN m.driver_pay ELSE 0 END) as total_pay
        FROM drivers d
        LEFT JOIN moves m ON d.driver_name = m.driver_name
        GROUP BY d.id
        ORDER BY d.driver_name
    """)
    
    data = cursor.fetchall()
    
    if data:
        df = pd.DataFrame(data, columns=['Name', 'Company', 'Phone', 'Total Moves', 'Total Earnings'])
        df['Total Earnings'] = df['Total Earnings'].apply(lambda x: f"${x:,.2f}" if x else "$0.00")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No drivers found")
    
    conn.close()

def generate_reports():
    """Generate reports"""
    st.subheader("Reports")
    
    report_type = st.selectbox("Select Report Type", 
                               ["Daily Summary", "Weekly Report", "Monthly Report", "Driver Performance"])
    
    if st.button("Generate Report"):
        conn = get_connection()
        cursor = conn.cursor()
        
        if report_type == "Daily Summary":
            today = date.today()
            cursor.execute("""
                SELECT COUNT(*) as moves, SUM(driver_pay) as total_pay
                FROM moves 
                WHERE date(move_date) = date(?)
            """, (today,))
            
            result = cursor.fetchone()
            st.write(f"### Daily Summary for {today}")
            st.write(f"Total Moves: {result[0]}")
            st.write(f"Total Driver Pay: ${result[1] or 0:,.2f}")
        
        conn.close()

def show_owner_dashboard():
    """Owner dashboard with all features"""
    tabs = st.tabs(["📊 Overview", "🚛 Trailers", "📦 Moves", "👥 Drivers", "📈 Reports", "⚙️ Admin"])
    
    with tabs[0]:
        show_overview_metrics()
        
        # Recent activity
        st.subheader("Recent Activity")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT move_date, driver_name, origin, destination, status
            FROM moves
            ORDER BY created_at DESC
            LIMIT 5
        """)
        recent = cursor.fetchall()
        if recent:
            df = pd.DataFrame(recent, columns=['Date', 'Driver', 'Origin', 'Destination', 'Status'])
            st.dataframe(df, use_container_width=True)
        conn.close()
    
    with tabs[1]:
        manage_trailers()
    
    with tabs[2]:
        manage_moves()
    
    with tabs[3]:
        manage_drivers()
    
    with tabs[4]:
        generate_reports()
    
    with tabs[5]:
        st.subheader("System Administration")
        
        admin_tab1, admin_tab2, admin_tab3 = st.tabs(["Users", "Database", "Settings"])
        
        with admin_tab1:
            st.write("### User Management")
            conn = get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("SELECT id, username, role, active FROM users")
                users = cursor.fetchall()
                if users:
                    df = pd.DataFrame(users, columns=['ID', 'Username', 'Role', 'Active'])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No users in database. Users are managed via user_accounts.json")
            except:
                st.info("Users are managed via user_accounts.json file")
            
            conn.close()
        
        with admin_tab2:
            st.write("### Database Statistics")
            conn = get_connection()
            cursor = conn.cursor()
            
            stats = {}
            tables = ['users', 'drivers', 'trailers', 'moves', 'locations']
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[table] = cursor.fetchone()[0]
                except:
                    stats[table] = 0
            
            col1, col2 = st.columns(2)
            for i, (table, count) in enumerate(stats.items()):
                if i % 2 == 0:
                    col1.metric(f"{table.title()}", count)
                else:
                    col2.metric(f"{table.title()}", count)
            
            conn.close()
        
        with admin_tab3:
            st.write("### System Settings")
            st.info("System settings can be configured in the configuration files")

def show_manager_dashboard():
    """Manager dashboard"""
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
    """Coordinator dashboard"""
    tabs = st.tabs(["Moves", "Trailers", "Drivers"])
    
    with tabs[0]:
        manage_moves()
    with tabs[1]:
        manage_trailers()
    with tabs[2]:
        manage_drivers()

def show_driver_dashboard():
    """Driver dashboard"""
    st.subheader("Driver Portal")
    
    driver_name = st.session_state.get('user_data', {}).get('driver_name', 'Unknown')
    st.write(f"Welcome, {driver_name}")
    
    tabs = st.tabs(["My Moves", "Earnings", "Documents"])
    
    with tabs[0]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT move_date, origin, destination, status, driver_pay
            FROM moves
            WHERE driver_name = ?
            ORDER BY move_date DESC
        """, (driver_name,))
        
        moves = cursor.fetchall()
        if moves:
            df = pd.DataFrame(moves, columns=['Date', 'Origin', 'Destination', 'Status', 'Pay'])
            df['Pay'] = df['Pay'].apply(lambda x: f"${x:,.2f}" if x else "$0.00")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No moves found")
        conn.close()
    
    with tabs[1]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(driver_pay) as total, COUNT(*) as count
            FROM moves
            WHERE driver_name = ? AND status = 'completed'
        """, (driver_name,))
        
        result = cursor.fetchone()
        col1, col2 = st.columns(2)
        col1.metric("Total Earnings", f"${result[0] or 0:,.2f}")
        col2.metric("Completed Moves", result[1] or 0)
        conn.close()
    
    with tabs[2]:
        st.info("Document management coming soon")

def show_admin_dashboard():
    """Admin dashboard - same as owner"""
    show_owner_dashboard()

# Main dashboard router
def show_dashboard():
    """Main dashboard router"""
    role = st.session_state.get('role', 'User')
    username = st.session_state.get('user', 'User')
    
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title(f"Welcome, {username}")
    with col2:
        st.write(f"**Role:** {role}")
    with col3:
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()
    
    st.markdown("---")
    
    # Route to appropriate dashboard
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
        st.info("Welcome to Smith & Williams Trucking")

# Main app
def main():
    """Main application"""
    
    # Initialize database
    init_database()
    
    # Sidebar
    with st.sidebar:
        # Logo
        logo_path = "swt_logo_white.png" if os.path.exists("swt_logo_white.png") else "swt_logo.png"
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        
        st.markdown("---")
        
        # Show user info if logged in
        if check_authentication():
            st.write(f"**User:** {st.session_state.get('user', 'Unknown')}")
            st.write(f"**Role:** {st.session_state.get('role', 'Unknown')}")
            st.markdown("---")
            
            if st.button("🔄 Refresh"):
                st.rerun()
            
            if st.button("🗑️ Clear Cache"):
                st.cache_data.clear()
                st.success("Cache cleared!")
                time.sleep(1)
                st.rerun()
    
    # Main content
    if not check_authentication():
        login()
    else:
        show_dashboard()

if __name__ == "__main__":
    # Clear cache on startup
    st.cache_data.clear()
    main()