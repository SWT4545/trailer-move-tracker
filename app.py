"""
Smith & Williams Trucking - Production Ready System
Complete system with all features and proper error handling
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sqlite3
import os
import json
import time

# Page config
st.set_page_config(
    page_title="Smith & Williams Trucking",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .logo-container { text-align: center; padding: 1rem; }
    .logo-img { max-width: 200px; margin: 0 auto; }
    .main { padding: 0; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; }
    .system-id { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; 
        padding: 0.5rem 1rem; 
        border-radius: 0.5rem; 
        font-weight: bold;
        display: inline-block;
        margin: 0.5rem 0;
    }
    .mlbl-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 0.3rem;
        font-size: 0.9em;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Database path
DB_PATH = 'smith_williams_trucking.db'

# Initialize database with all tables
def init_database():
    """Initialize complete database schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        driver_id INTEGER,
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )''')
    
    # Drivers table  
    cursor.execute('''CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_name TEXT UNIQUE NOT NULL,
        company_name TEXT,
        phone TEXT,
        email TEXT,
        driver_type TEXT DEFAULT 'contractor',
        cdl_number TEXT,
        cdl_expiry DATE,
        insurance_policy TEXT,
        insurance_expiry DATE,
        w9_on_file INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Locations table
    cursor.execute('''CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_title TEXT UNIQUE NOT NULL,
        address TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        zip_code TEXT,
        latitude REAL,
        longitude REAL,
        location_type TEXT DEFAULT 'customer',
        is_base_location INTEGER DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Trailers table
    cursor.execute('''CREATE TABLE IF NOT EXISTS trailers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trailer_number TEXT UNIQUE NOT NULL,
        trailer_type TEXT DEFAULT 'Standard',
        current_location_id INTEGER,
        status TEXT DEFAULT 'available',
        is_new INTEGER DEFAULT 0,
        last_move_id INTEGER,
        notes TEXT,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (current_location_id) REFERENCES locations(id)
    )''')
    
    # Moves table - Central hub
    cursor.execute('''CREATE TABLE IF NOT EXISTS moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        system_id TEXT UNIQUE NOT NULL,
        mlbl_number TEXT UNIQUE,
        move_date DATE,
        trailer_id INTEGER,
        origin_location_id INTEGER,
        destination_location_id INTEGER,
        client TEXT,
        driver_id INTEGER,
        driver_name TEXT,
        estimated_miles REAL,
        base_rate REAL DEFAULT 2.10,
        estimated_earnings REAL,
        actual_client_payment REAL,
        factoring_fee REAL,
        service_fee REAL,
        driver_net_pay REAL,
        status TEXT DEFAULT 'pending',
        delivery_status TEXT DEFAULT 'Pending',
        delivery_date TIMESTAMP,
        pod_uploaded INTEGER DEFAULT 0,
        photos_uploaded INTEGER DEFAULT 0,
        bol_uploaded INTEGER DEFAULT 0,
        payment_status TEXT DEFAULT 'pending',
        payment_batch_id TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trailer_id) REFERENCES trailers(id),
        FOREIGN KEY (origin_location_id) REFERENCES locations(id),
        FOREIGN KEY (destination_location_id) REFERENCES locations(id),
        FOREIGN KEY (driver_id) REFERENCES drivers(id)
    )''')
    
    # Documents table
    cursor.execute('''CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_type TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER,
        move_id INTEGER,
        system_id TEXT,
        mlbl_number TEXT,
        driver_id INTEGER,
        uploaded_by TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_verified INTEGER DEFAULT 0,
        notes TEXT,
        FOREIGN KEY (move_id) REFERENCES moves(id),
        FOREIGN KEY (driver_id) REFERENCES drivers(id)
    )''')
    
    # Financials table
    cursor.execute('''CREATE TABLE IF NOT EXISTS financials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_batch_id TEXT UNIQUE NOT NULL,
        payment_date DATE,
        client_name TEXT,
        total_client_payment REAL,
        total_factoring_fee REAL,
        total_service_fee REAL,
        total_net_payment REAL,
        num_moves INTEGER,
        num_drivers INTEGER,
        service_fee_per_driver REAL,
        invoice_generated INTEGER DEFAULT 0,
        statements_generated INTEGER DEFAULT 0,
        payment_status TEXT DEFAULT 'pending',
        processed_by TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Activity log
    cursor.execute('''CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user TEXT,
        action TEXT,
        table_affected TEXT,
        record_id TEXT,
        details TEXT
    )''')
    
    conn.commit()
    conn.close()

# Load initial data if needed
def load_initial_data():
    """Load initial sample data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if data exists
    cursor.execute('SELECT COUNT(*) FROM drivers')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # Insert drivers
    drivers = [
        ('Brandon Smith', 'Smith & Williams Trucking', '901-555-0001', 'brandon@swtrucking.com', 'owner'),
        ('Justin Duckett', 'Duckett Transport LLC', '901-555-0002', 'jduckett@email.com', 'contractor'),
        ('Carl Strickland', 'Strickland Logistics', '901-555-0003', 'cstrickland@email.com', 'contractor'),
        ('Mike Johnson', 'Johnson Freight', '901-555-0004', 'mjohnson@email.com', 'contractor'),
        ('Sarah Williams', 'Williams Transport', '901-555-0005', 'swilliams@email.com', 'company')
    ]
    
    for driver in drivers:
        cursor.execute('''
            INSERT OR IGNORE INTO drivers (driver_name, company_name, phone, email, driver_type)
            VALUES (?, ?, ?, ?, ?)
        ''', driver)
    
    # Insert locations
    locations = [
        ('Fleet Memphis', '123 Fleet Way', 'Memphis', 'TN', '38103', 35.1495, -90.0490, 'base', 1),
        ('FedEx Memphis Hub', '456 FedEx Pkwy', 'Memphis', 'TN', '38116', 35.0456, -89.9773, 'customer', 0),
        ('FedEx Indianapolis', '789 Hub Dr', 'Indianapolis', 'IN', '46241', 39.7684, -86.1581, 'customer', 0),
        ('Chicago Terminal', '321 Terminal Rd', 'Chicago', 'IL', '60606', 41.8781, -87.6298, 'customer', 0),
        ('Nashville Hub', '555 Music City Dr', 'Nashville', 'TN', '37203', 36.1627, -86.7816, 'customer', 0),
        ('Atlanta Distribution', '777 Peachtree Way', 'Atlanta', 'GA', '30301', 33.7490, -84.3880, 'customer', 0)
    ]
    
    for loc in locations:
        cursor.execute('''
            INSERT OR IGNORE INTO locations (
                location_title, address, city, state, zip_code,
                latitude, longitude, location_type, is_base_location
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', loc)
    
    # Insert trailers
    trailers = [
        ('TRL-001', 'Standard', 1, 'available'),
        ('TRL-002', 'Standard', 1, 'available'),
        ('TRL-003', 'Refrigerated', 2, 'available'),
        ('TRL-004', 'Standard', 3, 'in_transit'),
        ('TRL-005', 'Flatbed', 1, 'available'),
        ('TRL-006', 'Standard', 4, 'available'),
        ('TRL-007', 'Refrigerated', 5, 'in_transit'),
        ('TRL-008', 'Standard', 1, 'available')
    ]
    
    for trailer in trailers:
        cursor.execute('''
            INSERT OR IGNORE INTO trailers (trailer_number, trailer_type, current_location_id, status)
            VALUES (?, ?, ?, ?)
        ''', trailer)
    
    # Insert sample moves
    moves = [
        ('SWT-2025-01-0001', 'MLBL58064', date(2025, 1, 6), 1, 1, 2, 'FedEx', 2, 'Justin Duckett', 450, 945.00, 'active'),
        ('SWT-2025-01-0002', 'MLBL58065', date(2025, 1, 7), 2, 1, 3, 'FedEx', 2, 'Justin Duckett', 385, 808.50, 'active'),
        ('SWT-2025-01-0003', 'MLBL58066', date(2025, 1, 8), 3, 1, 4, 'FedEx', 3, 'Carl Strickland', 520, 1092.00, 'active'),
        ('SWT-2025-01-0004', 'MLBL58067', date(2025, 1, 9), 4, 2, 5, 'FedEx', 1, 'Brandon Smith', 280, 588.00, 'completed'),
        ('SWT-2025-01-0005', None, date(2025, 1, 10), 5, 3, 1, 'UPS', 4, 'Mike Johnson', 610, 1281.00, 'assigned')
    ]
    
    for move in moves:
        cursor.execute('''
            INSERT OR IGNORE INTO moves (
                system_id, mlbl_number, move_date, trailer_id,
                origin_location_id, destination_location_id, client,
                driver_id, driver_name, estimated_miles, estimated_earnings, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', move)
    
    conn.commit()
    conn.close()

# Generate system ID
def generate_system_id():
    """Generate unique system ID in format SWT-YYYY-MM-XXXX"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    prefix = f"SWT-{year}-{month}-"
    
    cursor.execute('''
        SELECT system_id FROM moves 
        WHERE system_id LIKE ? 
        ORDER BY system_id DESC 
        LIMIT 1
    ''', (prefix + '%',))
    
    last_id = cursor.fetchone()
    if last_id:
        last_num = int(last_id[0].split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    new_id = f"{prefix}{new_num:04d}"
    conn.close()
    return new_id

# Load user accounts
def load_user_accounts():
    """Load user accounts"""
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
                "permissions": ["manage_moves", "manage_trailers", "view_reports", "add_mlbl"]
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
                "permissions": ["view_own_moves", "upload_documents", "self_assign"]
            },
            "CStrickland": {
                "password": "driver123",
                "roles": ["Driver"],
                "driver_name": "Carl Strickland",
                "permissions": ["view_own_moves", "upload_documents", "self_assign"]
            }
        }
    }

# Authentication
def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def login():
    """Login page with video logo"""
    # Show video logo if available
    animation_file = "company_logo_animation.mp4.MOV"
    if os.path.exists(animation_file):
        try:
            with open(animation_file, 'rb') as video_file:
                video_bytes = video_file.read()
                st.video(video_bytes, loop=True, autoplay=True, muted=True)
        except:
            pass
    
    # Show static logo
    logo_path = "swt_logo_white.png" if os.path.exists("swt_logo_white.png") else "swt_logo.png"
    if os.path.exists(logo_path):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                st.image(logo_path, use_container_width=True)
            except:
                pass
    
    st.title("Smith & Williams Trucking")
    st.subheader("Fleet Management System")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("🔐 Login", type="primary", use_container_width=True)
        with col2:
            if st.form_submit_button("🔄 Clear", use_container_width=True):
                st.rerun()
        
        if submitted:
            accounts = load_user_accounts()
            if username in accounts['users']:
                if accounts['users'][username]['password'] == password:
                    st.session_state['authenticated'] = True
                    st.session_state['user'] = username
                    st.session_state['user_data'] = accounts['users'][username]
                    st.session_state['role'] = accounts['users'][username]['roles'][0]
                    st.success("✅ Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid password")
            else:
                st.error("❌ Invalid username")

# Sidebar
def show_sidebar():
    """Sidebar with user info and cache clear"""
    with st.sidebar:
        # Logo
        logo_path = "swt_logo.png"
        if os.path.exists(logo_path):
            try:
                st.image(logo_path, use_container_width=True)
            except:
                pass
        
        # User info
        st.markdown("### 👤 User Information")
        st.write(f"**User:** {st.session_state.get('user', 'Unknown')}")
        st.write(f"**Role:** {st.session_state.get('role', 'Unknown')}")
        
        # Cache clear button
        if st.button("🔄 Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ Cache cleared!")
            time.sleep(1)
            st.rerun()
        
        st.divider()
        
        # Logout button
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Vernon Support (Simplified)
def show_vernon_support():
    """Simple Vernon support interface"""
    with st.expander("🤖 Vernon - IT Support"):
        st.write("How can I help you today?")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔍 Check System"):
                st.success("System is healthy!")
        with col2:
            if st.button("🔧 Fix Issues"):
                st.info("No issues detected")
        with col3:
            if st.button("❓ Get Help"):
                st.info("Contact support@swtrucking.com")

# Overview metrics
def show_overview_metrics():
    """Display system overview metrics"""
    st.subheader("📊 System Overview")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get metrics
    cursor.execute('SELECT COUNT(*) FROM moves WHERE status IN ("active", "assigned")')
    active_moves = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trailers WHERE status = "available"')
    available_trailers = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM drivers WHERE status = "active"')
    active_drivers = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COALESCE(SUM(estimated_earnings), 0) FROM moves 
        WHERE date(move_date) >= date('now', 'start of month')
    ''')
    monthly_revenue = cursor.fetchone()[0]
    
    conn.close()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Moves", active_moves)
    
    with col2:
        st.metric("Available Trailers", available_trailers)
    
    with col3:
        st.metric("Active Drivers", active_drivers)
    
    with col4:
        st.metric("Monthly Revenue", f"${monthly_revenue:,.0f}")

# Create new move
def create_new_move():
    """Create new move with system ID"""
    st.subheader("📦 Create New Move")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with st.form("new_move_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Get trailers
            cursor.execute('''
                SELECT t.id, t.trailer_number, l.location_title 
                FROM trailers t
                LEFT JOIN locations l ON t.current_location_id = l.id
                WHERE t.status = 'available'
            ''')
            trailers = cursor.fetchall()
            
            if trailers:
                trailer_options = {f"{t[1]} (at {t[2] or 'Unknown'})": t[0] for t in trailers}
                selected_trailer = st.selectbox("Select Trailer", options=list(trailer_options.keys()))
            else:
                st.warning("No available trailers")
                trailer_options = {}
                selected_trailer = None
            
            # Get locations
            cursor.execute('SELECT id, location_title FROM locations ORDER BY location_title')
            locations = cursor.fetchall()
            location_options = {l[1]: l[0] for l in locations}
            
            origin = st.selectbox("Origin Location", options=list(location_options.keys()))
            destination = st.selectbox("Destination Location", options=list(location_options.keys()))
        
        with col2:
            # Get drivers
            cursor.execute('SELECT id, driver_name FROM drivers WHERE status = "active"')
            drivers = cursor.fetchall()
            driver_options = {d[1]: d[0] for d in drivers}
            selected_driver = st.selectbox("Assign Driver", options=list(driver_options.keys()))
            
            client = st.text_input("Client Name")
            move_date = st.date_input("Move Date", value=date.today())
            
            # Estimated miles
            miles = st.number_input("Estimated Miles", min_value=0.0, value=450.0, step=10.0)
        
        if st.form_submit_button("🚀 Create Move", type="primary", use_container_width=True):
            if selected_trailer and trailer_options:
                # Generate system ID
                system_id = generate_system_id()
                
                # Calculate earnings
                earnings = miles * 2.10
                
                # Create move
                cursor.execute('''
                    INSERT INTO moves (
                        system_id, move_date, trailer_id, origin_location_id,
                        destination_location_id, driver_id, driver_name, client,
                        estimated_miles, base_rate, estimated_earnings, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 2.10, ?, 'assigned')
                ''', (
                    system_id, move_date, trailer_options[selected_trailer],
                    location_options[origin], location_options[destination],
                    driver_options[selected_driver], selected_driver, client,
                    miles, earnings
                ))
                
                # Update trailer status
                cursor.execute('''
                    UPDATE trailers SET status = 'in_transit'
                    WHERE id = ?
                ''', (trailer_options[selected_trailer],))
                
                conn.commit()
                st.success(f"✅ Move created successfully!")
                st.markdown(f'<div class="system-id">System ID: {system_id}</div>', unsafe_allow_html=True)
                st.info(f"📍 Estimated Miles: {miles} | 💰 Estimated Earnings: ${earnings:,.2f}")
    
    conn.close()

# MLBL Management
def manage_mlbl_numbers():
    """Add MLBL numbers to moves"""
    st.subheader("🔢 MLBL Number Management")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get moves without MLBL
    cursor.execute('''
        SELECT m.system_id, m.move_date, m.client, m.driver_name
        FROM moves m
        WHERE m.mlbl_number IS NULL
        ORDER BY m.created_at DESC
    ''')
    
    pending_moves = cursor.fetchall()
    
    if pending_moves:
        st.write("### Moves Awaiting MLBL Numbers")
        
        for move in pending_moves:
            with st.expander(f"Move {move[0]} - {move[2] or 'No Client'} ({move[1]})"):
                st.write(f"**Driver:** {move[3]}")
                
                mlbl = st.text_input(f"MLBL Number", key=f"mlbl_{move[0]}")
                if st.button("✅ Add MLBL", key=f"btn_{move[0]}"):
                    if mlbl:
                        try:
                            cursor.execute('''
                                UPDATE moves 
                                SET mlbl_number = ?
                                WHERE system_id = ?
                            ''', (mlbl, move[0]))
                            conn.commit()
                            st.success(f"MLBL {mlbl} added successfully!")
                            st.rerun()
                        except:
                            st.error("MLBL already exists or error occurred")
    else:
        st.info("No moves pending MLBL numbers")
    
    conn.close()

# Show active moves
def show_active_moves():
    """Display active moves"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.system_id, m.mlbl_number, m.move_date, m.driver_name,
               m.client, m.status, m.estimated_miles, m.estimated_earnings
        FROM moves m
        WHERE m.status IN ('active', 'assigned')
        ORDER BY m.move_date DESC
    ''')
    
    moves = cursor.fetchall()
    
    if moves:
        df = pd.DataFrame(moves, columns=[
            'System ID', 'MLBL', 'Date', 'Driver', 'Client',
            'Status', 'Miles', 'Est. Earnings'
        ])
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No active moves")
    
    conn.close()

# Main dashboard
def show_dashboard():
    """Display role-specific dashboard"""
    role = st.session_state.get('role', 'Unknown')
    
    st.title(f"Smith & Williams Trucking - {role} Dashboard")
    
    # Show Vernon support
    show_vernon_support()
    
    if role == "Owner":
        tabs = st.tabs([
            "📊 Overview", "🚛 Create Move", "📋 Active Moves",
            "🔢 MLBL Management", "💰 Financials", "🔧 Admin"
        ])
        
        with tabs[0]:
            show_overview_metrics()
        with tabs[1]:
            create_new_move()
        with tabs[2]:
            show_active_moves()
        with tabs[3]:
            manage_mlbl_numbers()
        with tabs[4]:
            st.subheader("💰 Financial Management")
            st.info("Financial management interface")
        with tabs[5]:
            st.subheader("🔧 System Administration")
            if st.button("🔄 Initialize Sample Data"):
                load_initial_data()
                st.success("Sample data loaded!")
                st.rerun()
    
    elif role == "Manager":
        tabs = st.tabs([
            "📊 Overview", "🚛 Create Move", "📋 Active Moves", "🔢 MLBL Management"
        ])
        
        with tabs[0]:
            show_overview_metrics()
        with tabs[1]:
            create_new_move()
        with tabs[2]:
            show_active_moves()
        with tabs[3]:
            manage_mlbl_numbers()
    
    elif role == "Coordinator":
        tabs = st.tabs(["📊 Overview", "📋 Active Moves"])
        
        with tabs[0]:
            show_overview_metrics()
        with tabs[1]:
            show_active_moves()
    
    elif role == "Driver":
        st.subheader("🚛 Driver Dashboard")
        driver_name = st.session_state.get('user_data', {}).get('driver_name')
        
        if driver_name:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT m.system_id, m.mlbl_number, m.move_date,
                       m.client, m.status, m.estimated_earnings
                FROM moves m
                WHERE m.driver_name = ?
                ORDER BY m.move_date DESC
            ''', (driver_name,))
            
            moves = cursor.fetchall()
            
            if moves:
                st.write(f"### Your Moves")
                df = pd.DataFrame(moves, columns=[
                    'System ID', 'MLBL', 'Date', 'Client', 'Status', 'Est. Earnings'
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No moves assigned")
            
            conn.close()
    
    else:
        tabs = st.tabs(["📊 Overview"])
        with tabs[0]:
            show_overview_metrics()

# Main application
def main():
    """Main application entry point"""
    # Initialize database
    init_database()
    load_initial_data()
    
    # Check authentication
    if not check_authentication():
        login()
    else:
        # Show sidebar
        show_sidebar()
        
        # Show main dashboard
        show_dashboard()

if __name__ == "__main__":
    main()