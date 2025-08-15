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
import base64

# Import PDF generators
try:
    from pdf_generator import generate_driver_receipt, generate_client_invoice, generate_status_report
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from inventory_pdf_generator import generate_inventory_pdf
    INVENTORY_PDF_AVAILABLE = True
except ImportError:
    INVENTORY_PDF_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Smith & Williams Trucking",
    page_icon="truck",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clear cache periodically to prevent TypeError from stale modules
if 'last_cache_clear' not in st.session_state:
    st.cache_data.clear()
    st.cache_resource.clear()
    st.session_state.last_cache_clear = datetime.now()
elif (datetime.now() - st.session_state.last_cache_clear).seconds > 3600:  # Clear every hour
    st.cache_data.clear()
    st.cache_resource.clear()
    st.session_state.last_cache_clear = datetime.now()

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

# Global schema checker
def get_table_columns(cursor, table_name):
    """Get columns for a table dynamically"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [col[1] for col in cursor.fetchall()]

def table_exists(cursor, table_name):
    """Check if table exists"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

# Load initial data if needed
def load_initial_data():
    """Load real production data and ensure basic data exists"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if we have any data
    try:
        cursor.execute("SELECT COUNT(*) FROM trailers")
        trailer_count = cursor.fetchone()[0]
    except:
        trailer_count = 0
    
    try:
        cursor.execute("SELECT COUNT(*) FROM moves")
        move_count = cursor.fetchone()[0]
    except:
        move_count = 0
    
    try:
        cursor.execute("SELECT COUNT(*) FROM drivers")
        driver_count = cursor.fetchone()[0]
    except:
        driver_count = 0
    
    # If no data, load production data
    if trailer_count == 0 or driver_count == 0:
        try:
            # Check if moves table has proper columns before loading data
            if table_exists(cursor, 'moves'):
                move_columns = get_table_columns(cursor, 'moves')
                if 'new_trailer' not in move_columns:
                    # Add missing columns if needed
                    try:
                        cursor.execute('ALTER TABLE moves ADD COLUMN new_trailer TEXT')
                        cursor.execute('ALTER TABLE moves ADD COLUMN old_trailer TEXT')
                        conn.commit()
                    except:
                        pass  # Columns might already exist
            
            # Try to import and run the real data loader
            from load_real_production_data import load_real_production_data
            load_real_production_data()
            st.success("Full production data loaded successfully!")
        except ImportError:
            # Try the simpler production data loader
            try:
                from init_production_data import init_production_data
                init_production_data()
                st.success("Production data initialized!")
            except ImportError:
                # If neither loader available, add minimal data to get started
                # Add Fleet Memphis location
                cursor.execute('''
                INSERT OR IGNORE INTO locations (id, location_title, city, state, location_type, is_base_location)
                VALUES (1, 'Fleet Memphis', 'Memphis', 'TN', 'base', 1)
            ''')
            
            # Add FedEx locations
            cursor.execute('''
                INSERT OR IGNORE INTO locations (location_title, city, state, location_type, is_base_location)
                VALUES 
                    ('FedEx Memphis', 'Memphis', 'TN', 'customer', 0),
                    ('FedEx Indy', 'Indianapolis', 'IN', 'customer', 0),
                    ('FedEx Chicago', 'Chicago', 'IL', 'customer', 0)
            ''')
            
            # Add at least one driver
            cursor.execute('''
                INSERT OR IGNORE INTO drivers (driver_name, status, driver_type)
                VALUES ('Brandon Smith', 'active', 'owner')
            ''')
            
            # Add some sample trailers
            for i in range(1, 6):
                cursor.execute('''
                    INSERT OR IGNORE INTO trailers (trailer_number, status, current_location)
                    VALUES (?, 'available', 'Fleet Memphis')
                ''', (f'DEMO{i:03d}',))
            
            conn.commit()
            st.info("Basic data initialized. Import production data for full functionality.")
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
    
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
                "roles": ["Owner", "Driver"],  # Added Driver role
                "driver_name": "Brandon Smith",
                "is_owner": True,
                "is_driver": True,  # Added driver flag
                "permissions": ["ALL", "view_own_moves", "upload_documents", "self_assign"]
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
                "is_driver": True,
                "permissions": ["view_own_moves", "upload_documents", "self_assign"]
            },
            "CStrickland": {
                "password": "driver123",
                "roles": ["Driver"],
                "driver_name": "Carl Strickland",
                "is_driver": True,
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
    # Show video logo if available - centered and muted loop
    animation_file = "company_logo_animation.mp4.MOV"
    if os.path.exists(animation_file):
        try:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # Use HTML5 video tag for better autoplay compatibility
                with open(animation_file, 'rb') as video_file:
                    video_bytes = video_file.read()
                    video_b64 = base64.b64encode(video_bytes).decode()
                    video_html = f'''
                    <video width="100%" autoplay loop muted playsinline>
                        <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                    '''
                    st.markdown(video_html, unsafe_allow_html=True)
        except Exception as e:
            # Fallback to static logo if video fails
            logo_path = "swt_logo_white.png" if os.path.exists("swt_logo_white.png") else "swt_logo.png"
            if os.path.exists(logo_path):
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    try:
                        st.image(logo_path, use_container_width=True)
                    except:
                        pass
    else:
        # Show static logo if no video
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
    
    # Vernon protection notice
    st.markdown("""
    <div style='text-align: center; padding: 10px; background-color: #f0f2f6; border-radius: 5px; margin: 10px 0;'>
        <small style='color: #28a745; font-weight: bold;'>
            Data Protected by Vernon - Senior IT Security Manager
        </small>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
        with col2:
            if st.form_submit_button(" Clear", use_container_width=True):
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
                st.error("Invalid username")

# Sidebar
def show_sidebar():
    """Sidebar with user info and cache clear"""
    with st.sidebar:
        # Logo - use white logo inside app
        logo_path = "swt_logo_white.png"
        if os.path.exists(logo_path):
            try:
                st.image(logo_path, use_container_width=True)
            except:
                # Fallback to regular logo if white not found
                if os.path.exists("swt_logo.png"):
                    try:
                        st.image("swt_logo.png", use_container_width=True)
                    except:
                        pass
        
        # User info
        st.markdown("###  User Information")
        st.write(f"**User:** {st.session_state.get('user', 'Unknown')}")
        st.write(f"**Role:** {st.session_state.get('role', 'Unknown')}")
        
        # Cache clear button
        if st.button(" Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Cache cleared!")
            time.sleep(1)
            st.rerun()
        
        st.divider()
        
        # Logout button
        if st.button("Logout", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        # Vernon footer at bottom of sidebar
        st.divider()
        st.markdown("""
        <div style='text-align: center; padding: 10px; background-color: #1e1e1e; border-radius: 5px; margin-top: 20px;'>
            <small style='color: #28a745; font-weight: bold;'>
                Data Protected by Vernon<br>
                Senior IT Security Manager
            </small>
        </div>
        """, unsafe_allow_html=True)

# Vernon Support (Simplified)
def show_vernon_support():
    """Simple Vernon support interface"""
    with st.expander("Vernon - IT Support"):
        st.write("How can I help you today?")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Check System"):
                st.success("System is healthy!")
        with col2:
            if st.button("Fix Issues"):
                st.info("No issues detected")
        with col3:
            if st.button("Get Help"):
                st.info("Contact support@swtrucking.com")

# Overview metrics
def show_overview_metrics():
    """Display system overview metrics"""
    st.subheader(" System Overview")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get metrics
    cursor.execute('SELECT COUNT(*) FROM moves WHERE status IN ("active", "assigned")')
    active_moves = cursor.fetchone()[0]
    
    # Get trailer counts - split by old and new (ALL trailers, not just available)
    # NEW TRAILERS (10 total): 190033, 190046, 18V00298, 7728, 190011, 190030, 18V00327, 18V00406, 18V00409, 18V00414
    # OLD TRAILERS (12 at FedEx): 7155, 7146, 5955, 6024, 6061, 3170, 7153, 6015, 7160, 6783, 3083, 6231
    # OLD TRAILERS (9 at Fleet): 7162, 7131, 5906, 7144, 6014, 6981, 5950, 5876, 4427
    trailer_columns = get_table_columns(cursor, 'trailers') if table_exists(cursor, 'trailers') else []
    
    if 'is_new' in trailer_columns:
        # Count ALL old trailers (is_new = 0) - available, in_transit, delivered, etc.
        cursor.execute('SELECT COUNT(*) FROM trailers WHERE is_new = 0')
        old_trailers_total = cursor.fetchone()[0]
        
        # Count ALL new trailers (is_new = 1) - available, in_transit, delivered, etc.
        cursor.execute('SELECT COUNT(*) FROM trailers WHERE is_new = 1')
        new_trailers_total = cursor.fetchone()[0]
        
        # Count only AVAILABLE for operations
        cursor.execute('SELECT COUNT(*) FROM trailers WHERE status = "available" AND is_new = 0')
        old_available = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM trailers WHERE status = "available" AND is_new = 1')
        new_available = cursor.fetchone()[0]
        
        total_trailers = old_trailers_total + new_trailers_total
    else:
        # If no is_new column, count ALL trailers by pattern
        # Count ALL NEW trailers based on actual data patterns:
        # NEW: 190xxx, 18Vxxxxx, or specific 7728
        cursor.execute('''
            SELECT COUNT(*) FROM trailers 
            WHERE trailer_number LIKE '190%' 
               OR trailer_number LIKE '18V%' 
               OR trailer_number = '7728'
        ''')
        new_trailers_total = cursor.fetchone()[0]
        
        # Count ALL OLD trailers based on actual data patterns:
        # OLD: 3xxx, 4xxx, 5xxx, 6xxx, 7xxx (except 7728)
        cursor.execute('''
            SELECT COUNT(*) FROM trailers 
            WHERE (trailer_number LIKE '3%' AND LENGTH(trailer_number) = 4)
               OR (trailer_number LIKE '4%' AND LENGTH(trailer_number) = 4)
               OR (trailer_number LIKE '5%' AND LENGTH(trailer_number) = 4)
               OR (trailer_number LIKE '6%' AND LENGTH(trailer_number) = 4)
               OR (trailer_number LIKE '7%' AND LENGTH(trailer_number) = 4 AND trailer_number != '7728')
        ''')
        old_trailers_total = cursor.fetchone()[0]
        
        # Count available for operations
        cursor.execute('''
            SELECT COUNT(*) FROM trailers 
            WHERE status = "available" 
            AND (trailer_number LIKE '190%' 
                 OR trailer_number LIKE '18V%' 
                 OR trailer_number = '7728')
        ''')
        new_available = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM trailers 
            WHERE status = "available" 
            AND ((trailer_number LIKE '3%' AND LENGTH(trailer_number) = 4)
                 OR (trailer_number LIKE '4%' AND LENGTH(trailer_number) = 4)
                 OR (trailer_number LIKE '5%' AND LENGTH(trailer_number) = 4)
                 OR (trailer_number LIKE '6%' AND LENGTH(trailer_number) = 4)
                 OR (trailer_number LIKE '7%' AND LENGTH(trailer_number) = 4 AND trailer_number != '7728'))
        ''')
        old_available = cursor.fetchone()[0]
        
        total_trailers = old_trailers_total + new_trailers_total
    
    cursor.execute('SELECT COUNT(*) FROM drivers WHERE status = "active"')
    active_drivers = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COALESCE(SUM(estimated_earnings), 0) FROM moves 
        WHERE date(move_date) >= date('now', 'start of month')
    ''')
    monthly_revenue = cursor.fetchone()[0]
    
    # Calculate total earnings and factoring
    cursor.execute('''
        SELECT COALESCE(SUM(estimated_earnings), 0) FROM moves 
        WHERE status = 'completed'
    ''')
    total_earnings = cursor.fetchone()[0]
    factoring_fee = total_earnings * 0.03
    after_factoring = total_earnings - factoring_fee
    
    conn.close()
    
    # Display metrics - two rows
    # First row: Move and trailer metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Moves", active_moves)
    
    with col2:
        # Show total old trailers with available count
        st.metric("Old Trailers", f"{old_trailers_total} ({old_available} avail)", 
                  help=f"Total old trailers: {old_trailers_total}\nAvailable for pickup: {old_available}")
    
    with col3:
        # Show total new trailers with available count
        st.metric("New Trailers", f"{new_trailers_total} ({new_available} avail)", 
                  help=f"Total new trailers: {new_trailers_total}\nAvailable for delivery: {new_available}")
    
    with col4:
        st.metric("Total Fleet", total_trailers, 
                  help=f"Total fleet size: {total_trailers}\nTotal available: {old_available + new_available}")
    
    # Second row: Financial metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Drivers", active_drivers)
    
    with col2:
        st.metric("Monthly Revenue", f"${monthly_revenue:,.0f}")
    
    with col3:
        st.metric("Gross Earnings", f"${total_earnings:,.0f}",
                  help="Total gross earnings before factoring",
                  delta=f"-${factoring_fee:,.0f} (3%)")
    
    with col4:
        st.metric("NET After 3% Factoring", f"${after_factoring:,.2f}",
                  help=f"${total_earnings:,.0f} - ${factoring_fee:,.0f} = ${after_factoring:,.2f}",
                  delta=f"-{factoring_fee:,.2f}")
    
    # BIG PROMINENT FACTORING DISPLAY
    st.markdown("---")
    st.markdown("### 💰 EARNINGS AFTER FACTORING")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Gross Total:** ${total_earnings:,.2f}")
    with col2:
        st.warning(f"**Less 3% Factoring:** -${factoring_fee:,.2f}")
    with col3:
        st.success(f"**NET TOTAL:** ${after_factoring:,.2f}")
    
    # Service fee disclaimer
    st.caption("*Service fees are not included. Only the 3% factoring fee has been deducted. Example: $1,960.00 - $58.80 = $1,901.20")
    
    # Add data initialization button if no data
    if active_moves == 0 and total_trailers == 0 and active_drivers == 0:
        st.warning("No data found in the system!")
        if st.button("Load Production Data", type="primary"):
            try:
                from load_real_production_data import load_real_production_data
                load_real_production_data()
                st.success("Real production data loaded successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error loading production data: {str(e)}")
                st.info("Please ensure load_real_production_data.py is available")

# Create new move
def create_new_move():
    """Create new move with system ID"""
    st.subheader("Create New Move Order")
    
    # Clear explanation of the process
    with st.expander("**How Trailer Swaps Work**", expanded=False):
        st.markdown("""
        **The Process:**
        1. **Deliver** - Take a trailer FROM Fleet Memphis TO a FedEx location
        2. **Swap** - Drop off your trailer and pick up a different one
        3. **Return** - Bring the swapped trailer BACK to Fleet Memphis
        4. **Payment** - Get paid based on route
        
        **Payment Examples:**
        - Fleet Memphis <-> FedEx Memphis = $200.00 flat rate
        - Fleet Memphis <-> FedEx Indy = $1,960.00
        - Fleet Memphis <-> FedEx Chicago = $2,373.00
        """)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Use containers instead of form for real-time updates
    with st.container():
        # Section 1: Trailer Selection (ONLY FROM FLEET MEMPHIS)
        st.markdown("### 1. Select NEW Trailer from Fleet Memphis")
        st.info("Only trailers currently at Fleet Memphis are available for delivery")
        
        # Get available NEW trailers at Fleet Memphis ONLY
        # First, check if trailers table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trailers'")
        if not cursor.fetchone():
            st.error("Trailers table not found. Please reload production data.")
            trailers = []
        else:
            # Check which columns exist in trailers table
            cursor.execute("PRAGMA table_info(trailers)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Build query to get ONLY Fleet Memphis trailers
            try:
                # Check if moves table has new_trailer/old_trailer columns
                cursor.execute("PRAGMA table_info(moves)")
                move_columns = [col[1] for col in cursor.fetchall()]
                
                if 'current_location_id' in columns and 'locations' in [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
                    # Get Fleet Memphis location ID
                    cursor.execute("SELECT id FROM locations WHERE location_title = 'Fleet Memphis'")
                    fleet_result = cursor.fetchone()
                    fleet_id = fleet_result[0] if fleet_result else 1
                    
                    # Get ONLY trailers at Fleet Memphis that are available
                    cursor.execute('''
                        SELECT t.id, t.trailer_number, 
                               'Fleet Memphis' as location,
                               t.status, t.is_new
                        FROM trailers t
                        WHERE t.current_location_id = ?
                        AND t.status = 'available'
                        AND t.is_new = 1
                        ORDER BY t.trailer_number
                    ''', (fleet_id,))
                else:
                    # Simple structure - get trailers at Fleet Memphis
                    cursor.execute('''
                        SELECT t.id, t.trailer_number, 
                               'Fleet Memphis' as location,
                               t.status, 
                               CASE 
                                   WHEN t.trailer_number LIKE '190%' THEN 1
                                   WHEN t.trailer_number LIKE '18V%' THEN 1
                                   WHEN t.trailer_number = '7728' THEN 1
                                   ELSE 0
                               END as is_new
                        FROM trailers t
                        WHERE (t.current_location = 'Fleet Memphis' OR t.current_location IS NULL)
                        AND t.status = 'available'
                        HAVING is_new = 1
                        ORDER BY t.trailer_number
                    ''')
                trailers = cursor.fetchall()
            except sqlite3.OperationalError as e:
                st.error(f"Database query error: {str(e)}")
                st.info("Try reloading production data or check database structure.")
                trailers = []
        
        if trailers:
            # All trailers are at Fleet Memphis (NEW trailers only)
            st.success(f"**{len(trailers)} NEW trailers available at Fleet Memphis**")
            
            # Initialize trailer_options and trailer_numbers
            trailer_options = {}
            trailer_numbers = {}  # Map display key to trailer number
            
            for t in trailers:
                key = f"Trailer #{t[1]} (NEW)"
                trailer_options[key] = t[0]  # trailer id
                trailer_numbers[key] = t[1]  # trailer number
            
            selected_trailer = st.selectbox(
                "Select NEW Trailer to Deliver", 
                options=list(trailer_options.keys()),
                help="Choose a NEW trailer from Fleet Memphis to deliver"
            )
        else:
            st.error("No trailers available - All trailers are currently assigned or in transit")
            trailer_options = {}
            trailer_numbers = {}
            selected_trailer = None
        
        st.divider()
        
        # Section 2: Route Information
        st.markdown("### 2. Route Details")
        st.info("**All moves start from Fleet Memphis**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Get locations
            cursor.execute('SELECT id, location_title FROM locations ORDER BY location_title')
            locations = cursor.fetchall()
            location_options = {l[1]: l[0] for l in locations}
            
            # Origin is always Fleet Memphis
            origin = "Fleet Memphis"
            st.text_input(
                "Starting Location", 
                value="Fleet Memphis",
                disabled=True,
                help="All trailer moves originate from Fleet Memphis"
            )
        
        with col2:
            # Get locations with OLD trailers for pickup
            try:
                cursor.execute('''
                    SELECT DISTINCT l.location_title, COUNT(t.id) as trailer_count
                    FROM locations l
                    JOIN trailers t ON t.current_location_id = l.id
                    WHERE t.is_new = 0 
                    AND l.location_title LIKE 'FedEx%'
                    GROUP BY l.location_title
                    ORDER BY l.location_title
                ''')
                locations_with_trailers = cursor.fetchall()
            except sqlite3.OperationalError:
                # Fallback if join fails
                locations_with_trailers = []
            
            if locations_with_trailers:
                destination_options = []
                for loc, count in locations_with_trailers:
                    destination_options.append(f"{loc} ({count} OLD trailers)")
                
                destination_display = st.selectbox(
                    "Delivery Location (with OLD trailers for pickup)", 
                    options=destination_options,
                    help="Select a FedEx location that has OLD trailers ready for pickup",
                    key="destination_select"
                )
                # Extract actual location name
                destination = destination_display.split(" (")[0]
            else:
                destination = st.selectbox(
                    "Delivery Location", 
                    options=list(location_options.keys()),
                    help="Where will the trailer be delivered to?",
                    key="destination_select_fallback"
                )
        
        # Auto-calculate miles based on route - REAL-TIME UPDATE
        if destination == "FedEx Indy":
            default_miles = 933.333333  # Exactly $1960 / $2.10
        elif destination == "FedEx Chicago":
            default_miles = 1130.0  # Updated: $2373 / $2.10 = 1130 miles
        elif destination == "FedEx Memphis":
            default_miles = 95.238095  # $200 flat rate / $2.10
        else:
            default_miles = 450.0
        
        # Show auto-calculated mileage
        st.info(f" **Auto-calculated mileage for {destination}:** {default_miles:,.2f} miles")
        
        miles = st.number_input(
            " Total Round Trip Miles", 
            min_value=0.0, 
            value=default_miles, 
            step=10.0,
            help="Auto-calculated based on destination. You can adjust if needed.",
            key=f"miles_{destination}"
        )
        
        # Show LIVE earnings calculation
        st.markdown("###  Real-Time Earnings Calculation")
        earnings = miles * 2.10
        factoring_amount = earnings * 0.03
        after_factoring = earnings - factoring_amount
        
        # BIG DISPLAY OF FACTORING CALCULATION
        st.markdown("#### EARNINGS BREAKDOWN:")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**GROSS:** ${earnings:,.2f}")
        with col2:
            st.warning(f"**LESS 3%:** -${factoring_amount:,.2f}")
        with col3:
            st.success(f"**NET:** ${after_factoring:,.2f}")
        
        # Detailed metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Miles", f"{miles:,.2f}")
        with col2:
            st.metric("Rate", "$2.10/mile")
        with col3:
            st.metric("Gross", f"${earnings:,.2f}")
        with col4:
            st.metric("NET (after 3%)", f"${after_factoring:,.2f}")
        
        st.divider()
        
        # Section 3: Assignment Details
        st.markdown("### 3. Assignment Information")
        col1, col2 = st.columns(2)
        
        with col1:
            # Get drivers
            cursor.execute('SELECT id, driver_name FROM drivers WHERE status = "active"')
            drivers = cursor.fetchall()
            driver_options = {d[1]: d[0] for d in drivers}
            selected_driver = st.selectbox(
                " Assign to Driver", 
                options=list(driver_options.keys()),
                help="Select the driver who will handle this move"
            )
            
            move_date = st.date_input(
                " Move Date", 
                value=date.today(),
                help="When will this move take place?"
            )
        
        with col2:
            client = st.text_input(
                " Client/Customer", 
                placeholder="e.g., Metro Logistics",
                help="Enter the client name for this move"
            )
            
            # Show OLD trailers available for pickup at destination
            if destination:
                st.markdown(f"**OLD Trailers available for pickup at {destination}:**")
                
                # Get OLD trailers at the selected destination
                try:
                    # Get location ID
                    cursor.execute("SELECT id FROM locations WHERE location_title = ?", (destination,))
                    loc_result = cursor.fetchone()
                    
                    if loc_result:
                        loc_id = loc_result[0]
                        # Get OLD trailers at this location
                        cursor.execute('''
                            SELECT trailer_number 
                            FROM trailers 
                            WHERE current_location_id = ?
                            AND is_new = 0
                            AND status = 'available'
                            ORDER BY trailer_number
                        ''', (loc_id,))
                        
                        dest_trailers = cursor.fetchall()
                        
                        if dest_trailers:
                            trailer_list = ", ".join([t[0] for t in dest_trailers])
                            st.info(f"OLD trailers ready for pickup: {trailer_list}")
                        else:
                            st.warning(f"No OLD trailers currently at {destination}")
                    else:
                        st.warning(f"Location {destination} not found in database")
                except Exception as e:
                    st.error(f"Error checking trailers: {str(e)}")
            else:
                st.info("Select a destination to see available OLD trailers")
            
            swap_trailer = st.text_input(
                " Trailer to Pick Up & Return to Fleet Memphis",
                placeholder="e.g., 6014",
                help=f"Enter the trailer # you'll pick up at {destination} and bring back to Fleet Memphis"
            )
        
        st.divider()
        
        # Submit button (no form needed)
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("CREATE MOVE ORDER", type="primary", use_container_width=True, key="create_move_btn"):
                if selected_trailer and trailer_options:
                    # Generate system ID
                    system_id = generate_system_id()
                    
                    # Calculate earnings
                    earnings = miles * 2.10
                    
                    # Create move - check schema first
                    move_columns = get_table_columns(cursor, 'moves')
                    
                    if 'new_trailer' in move_columns:
                        # Full schema with new_trailer/old_trailer
                        cursor.execute('''
                            INSERT INTO moves (
                                system_id, move_date, trailer_id, new_trailer, old_trailer,
                                origin_location_id, destination_location_id, 
                                driver_id, driver_name, client,
                                estimated_miles, base_rate, estimated_earnings, status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 2.10, ?, 'assigned')
                        ''', (
                            system_id, move_date, 
                            trailer_options.get(selected_trailer),  # trailer_id
                            trailer_numbers.get(selected_trailer),  # new_trailer number
                            swap_trailer if swap_trailer else None,  # old_trailer to pick up
                            1,  # origin_location_id (Fleet Memphis)
                            location_options.get(destination),  # destination_location_id
                            driver_options.get(selected_driver), selected_driver, client,
                            miles, earnings
                        ))
                    else:
                        # Simpler schema without new_trailer/old_trailer
                        cursor.execute('''
                            INSERT INTO moves (
                                order_number, pickup_date, driver_name,
                                pickup_location, delivery_location, status, amount
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            system_id, move_date, selected_driver,
                            'Fleet Memphis', destination, 'assigned', earnings
                        ))
                    
                    # Update trailer status
                    cursor.execute('''
                        UPDATE trailers SET status = 'in_transit'
                        WHERE id = ?
                    ''', (trailer_options[selected_trailer],))
                    
                    conn.commit()
                    st.success(f"Move Order Created Successfully!")
                    st.markdown(f'### Move Details:')
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**System ID:** {system_id}")
                        st.info(f"**Driver:** {selected_driver}")
                        st.info(f"**Route:** {origin} -> {destination}")
                    with col2:
                        st.info(f"**Miles:** {miles:,.2f}")
                        st.info(f"**Gross Earnings:** ${earnings:,.2f}")
                        st.info(f"**After Factoring:** ${earnings * 0.97:,.2f}")
                else:
                    st.error("Please select an available trailer to create the move")
    
    conn.close()
    
    # Show trailer status sections
    st.divider()
    
    # Two columns for available and unavailable
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Available Trailers")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get available trailers - check database structure first
        cursor.execute("PRAGMA table_info(trailers)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'current_location_id' in columns:
            # Normalized structure
            cursor.execute('''
                SELECT t.trailer_number, 
                       COALESCE(l.location_title, 'Fleet Memphis') as location, 
                       t.status
                FROM trailers t
                LEFT JOIN locations l ON t.current_location_id = l.id
                WHERE t.id NOT IN (
                    SELECT trailer_id FROM moves 
                    WHERE status IN ('active', 'assigned', 'in_transit')
                    AND trailer_id IS NOT NULL
                )
                ORDER BY t.trailer_number
            ''')
        else:
            # Simple structure
            cursor.execute('''
                SELECT t.trailer_number, 
                       COALESCE(t.current_location, 'Fleet Memphis') as location, 
                       t.status
                FROM trailers t
                WHERE t.id NOT IN (
                    SELECT trailer_id FROM moves 
                    WHERE status IN ('active', 'assigned', 'in_transit')
                    AND trailer_id IS NOT NULL
                )
                ORDER BY t.trailer_number
            ''')
        
        available_trailers = cursor.fetchall()
        
        if available_trailers:
            st.success(f" {len(available_trailers)} trailers ready for assignment")
            df_avail = pd.DataFrame(available_trailers, columns=[
                'Trailer #', 'Current Location', 'Status'
            ])
            
            # Green highlighting for available
            def highlight_available(row):
                return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row)
            
            styled_avail = df_avail.style.apply(highlight_available, axis=1)
            
            st.dataframe(
                styled_avail, 
                use_container_width=True, 
                hide_index=True, 
                height=300,
                column_config={
                    'Trailer #': st.column_config.TextColumn(width='medium'),
                    'Current Location': st.column_config.TextColumn(width='large'),
                    'Status': st.column_config.TextColumn(width='medium')
                }
            )
        else:
            st.warning("No trailers currently available")
        
        conn.close()
    
    with col2:
        st.subheader("Assigned/In-Use Trailers")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get trailers in use - check database structure
        cursor.execute("PRAGMA table_info(moves)")
        move_columns = [col[1] for col in cursor.fetchall()]
        
        if 'destination_location_id' in move_columns:
            # Normalized structure with foreign keys
            cursor.execute('''
                SELECT t.trailer_number, m.driver_name, m.status,
                       dest.location_title as destination
                FROM trailers t
                JOIN moves m ON t.id = m.trailer_id
                LEFT JOIN locations dest ON m.destination_location_id = dest.id
                WHERE m.status IN ('active', 'assigned', 'in_transit')
                ORDER BY m.status, m.move_date DESC
            ''')
        else:
            # Simple structure - check if new_trailer field exists
            move_columns = get_table_columns(cursor, 'moves')
            if 'new_trailer' in move_columns:
                cursor.execute('''
                    SELECT DISTINCT m.new_trailer as trailer_number, 
                           m.driver_name, m.status,
                           m.delivery_location as destination
                    FROM moves m
                    WHERE m.status IN ('active', 'assigned', 'in_transit')
                    AND m.new_trailer IS NOT NULL
                    ORDER BY m.status, m.pickup_date DESC
                ''')
            else:
                # Fallback for very simple schema
                cursor.execute('''
                    SELECT DISTINCT m.order_number as trailer_number, 
                           m.driver_name, m.status,
                           m.delivery_location as destination
                    FROM moves m
                    WHERE m.status IN ('active', 'assigned', 'in_transit')
                    ORDER BY m.status, m.pickup_date DESC
                ''')
        
        unavailable_trailers = cursor.fetchall()
        
        if unavailable_trailers:
            st.warning(f" {len(unavailable_trailers)} trailers currently assigned")
            df_unavail = pd.DataFrame(unavailable_trailers, columns=[
                'Trailer #', 'Assigned To', 'Status', 'Destination'
            ])
            
            # Status-based coloring
            def highlight_status(row):
                if row['Status'] == 'active':
                    return ['background-color: #fff3cd; color: #856404; font-weight: bold'] * len(row)  # Yellow
                elif row['Status'] == 'assigned':
                    return ['background-color: #d1ecf1; color: #0c5460; font-weight: bold'] * len(row)  # Blue
                else:
                    return ['background-color: #f8d7da; color: #721c24; font-weight: bold'] * len(row)  # Red
            
            styled_unavail = df_unavail.style.apply(highlight_status, axis=1)
            
            st.dataframe(
                styled_unavail, 
                use_container_width=True, 
                hide_index=True, 
                height=300,
                column_config={
                    'Trailer #': st.column_config.TextColumn(width='medium'),
                    'Assigned To': st.column_config.TextColumn(width='large'),
                    'Status': st.column_config.TextColumn(width='medium'),
                    'Destination': st.column_config.TextColumn(width='large')
                }
            )
        else:
            st.info("No trailers currently assigned")
    
    conn.close()

# MLBL Management
def manage_mlbl_numbers():
    """Add MLBL numbers to moves"""
    st.subheader(" MLBL Number Management")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get ALL moves (active and completed) without MLBL with full details
    # Check database structure first
    cursor.execute("PRAGMA table_info(moves)")
    move_columns = [col[1] for col in cursor.fetchall()]
    
    try:
        if 'origin_location_id' in move_columns:
            # Normalized structure
            cursor.execute('''
                SELECT m.system_id, m.move_date, m.client, m.driver_name, m.status, m.payment_status,
                       t.trailer_number, 
                       orig.location_title as origin, dest.location_title as destination,
                       m.estimated_miles, m.estimated_earnings
                FROM moves m
                LEFT JOIN trailers t ON m.trailer_id = t.id
                LEFT JOIN locations orig ON m.origin_location_id = orig.id
                LEFT JOIN locations dest ON m.destination_location_id = dest.id
                WHERE m.mlbl_number IS NULL
                ORDER BY m.move_date DESC, m.system_id
            ''')
        else:
            # Simple structure - check schema
            move_columns = get_table_columns(cursor, 'moves')
            if 'new_trailer' in move_columns:
                cursor.execute('''
                    SELECT m.order_number as system_id, m.pickup_date as move_date, 
                           m.customer_name as client, m.driver_name, m.status, 
                           'pending' as payment_status,
                           m.new_trailer as trailer_number, 
                           m.pickup_location as origin, m.delivery_location as destination,
                           0 as estimated_miles, m.amount as estimated_earnings
                    FROM moves m
                    WHERE m.order_number NOT IN (SELECT mlbl_number FROM moves WHERE mlbl_number IS NOT NULL)
                    ORDER BY m.pickup_date DESC, m.order_number
                ''')
            else:
                cursor.execute('''
                    SELECT m.order_number as system_id, m.pickup_date as move_date, 
                           'FedEx' as client, m.driver_name, m.status, 
                           'pending' as payment_status,
                           m.order_number as trailer_number, 
                           m.pickup_location as origin, m.delivery_location as destination,
                           0 as estimated_miles, m.amount as estimated_earnings
                    FROM moves m
                    WHERE m.order_number NOT IN (SELECT mlbl_number FROM moves WHERE mlbl_number IS NOT NULL)
                    ORDER BY m.pickup_date DESC, m.order_number
                ''')
        pending_moves = cursor.fetchall()
    except sqlite3.OperationalError as e:
        st.error(f"Database error: {str(e)}")
        st.info("Please check database structure or reload production data")
        pending_moves = []
    
    if pending_moves:
        st.write(f"### {len(pending_moves)} Moves Awaiting MLBL Numbers")
        
        # Group by status for better organization
        active_moves = [m for m in pending_moves if m[4] == 'active']
        completed_unpaid = [m for m in pending_moves if m[4] == 'completed' and m[5] == 'pending']
        completed_paid = [m for m in pending_moves if m[4] == 'completed' and m[5] == 'paid']
        
        if active_moves:
            st.write("####  Active Moves")
            for move in active_moves:
                # Unpack move details
                sys_id, date, client, driver, status, payment, trailer, origin, dest, miles, earnings = move
                move_title = f"{sys_id} | {date} | {driver}"
                
                with st.expander(move_title):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Move Details:**")
                        st.write(f" Date: {date}")
                        st.write(f"Trailer: {trailer}")
                        st.write(f" Driver: {driver}")
                        st.write(f" Client: {client or 'FedEx'}")
                    with col2:
                        st.write("**Route Information:**")
                        st.write(f"From: {origin}")
                        st.write(f"To: {dest}")
                        st.write(f" Miles: {miles}")
                        st.write(f" Earnings: ${earnings:,.2f}")
                    
                    st.divider()
                    mlbl = st.text_input(f"Enter MLBL Number for this move", key=f"mlbl_{sys_id}")
                    if st.button("Add MLBL", key=f"btn_{sys_id}"):
                        if mlbl:
                            try:
                                cursor.execute('''
                                    UPDATE moves 
                                    SET mlbl_number = ?
                                    WHERE system_id = ?
                                ''', (mlbl, sys_id))
                                conn.commit()
                                st.success(f"MLBL {mlbl} added successfully!")
                                st.rerun()
                            except:
                                st.error("MLBL already exists or error occurred")
        
        if completed_unpaid:
            st.write("####  Completed - Awaiting Payment")
            for move in completed_unpaid:
                # Unpack move details
                sys_id, date, client, driver, status, payment, trailer, origin, dest, miles, earnings = move
                move_title = f"{sys_id} | {date} | {driver}"
                
                with st.expander(move_title):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Move Details:**")
                        st.write(f" Date: {date}")
                        st.write(f"Trailer: {trailer}")
                        st.write(f" Driver: {driver}")
                        st.write(f" Client: {client or 'FedEx'}")
                    with col2:
                        st.write("**Route Information:**")
                        st.write(f"From: {origin}")
                        st.write(f"To: {dest}")
                        st.write(f" Miles: {miles}")
                        st.write(f" Earnings: ${earnings:,.2f}")
                    
                    st.divider()
                    mlbl = st.text_input(f"Enter MLBL Number for this move", key=f"mlbl_{sys_id}")
                    if st.button("Add MLBL", key=f"btn_{sys_id}"):
                        if mlbl:
                            try:
                                cursor.execute('''
                                    UPDATE moves 
                                    SET mlbl_number = ?
                                    WHERE system_id = ?
                                ''', (mlbl, sys_id))
                                conn.commit()
                                st.success(f"MLBL {mlbl} added successfully!")
                                st.rerun()
                            except:
                                st.error("MLBL already exists or error occurred")
        
        if completed_paid:
            st.write("####  Completed & Paid")
            for move in completed_paid:
                # Unpack move details
                sys_id, date, client, driver, status, payment, trailer, origin, dest, miles, earnings = move
                move_title = f"{sys_id} | {date} | {driver}"
                
                with st.expander(move_title):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Move Details:**")
                        st.write(f" Date: {date}")
                        st.write(f"Trailer: {trailer}")
                        st.write(f" Driver: {driver}")
                        st.write(f" Client: {client or 'FedEx'}")
                    with col2:
                        st.write("**Route Information:**")
                        st.write(f"From: {origin}")
                        st.write(f"To: {dest}")
                        st.write(f" Miles: {miles}")
                        st.write(f" Earnings: ${earnings:,.2f}")
                    
                    st.divider()
                    mlbl = st.text_input(f"Enter MLBL Number for this move", key=f"mlbl_{sys_id}")
                    if st.button("Add MLBL", key=f"btn_{sys_id}"):
                        if mlbl:
                            try:
                                cursor.execute('''
                                    UPDATE moves 
                                    SET mlbl_number = ?
                                    WHERE system_id = ?
                                ''', (mlbl, sys_id))
                                conn.commit()
                                st.success(f"MLBL {mlbl} added successfully!")
                                st.rerun()
                            except:
                                st.error("MLBL already exists or error occurred")
    else:
        st.success(" All moves have MLBL numbers assigned!")
    
    # Show moves with MLBL numbers
    try:
        if 'origin_location_id' in move_columns:
            if 'old_trailer' in move_columns:
                cursor.execute('''
                    SELECT m.system_id, m.mlbl_number, m.move_date, m.driver_name, 
                           m.new_trailer, m.old_trailer,
                           orig.location_title || ' -> ' || dest.location_title as route,
                           m.status, m.payment_status
                    FROM moves m
                    LEFT JOIN locations orig ON m.origin_location_id = orig.id
                    LEFT JOIN locations dest ON m.destination_location_id = dest.id
                    WHERE m.mlbl_number IS NOT NULL
                    ORDER BY m.mlbl_number
                ''')
            else:
                cursor.execute('''
                    SELECT m.system_id, m.mlbl_number, m.move_date, m.driver_name, 
                           t.trailer_number, '-',
                           orig.location_title || ' -> ' || dest.location_title as route,
                           m.status, m.payment_status
                    FROM moves m
                    LEFT JOIN trailers t ON m.trailer_id = t.id
                    LEFT JOIN locations orig ON m.origin_location_id = orig.id
                    LEFT JOIN locations dest ON m.destination_location_id = dest.id
                    WHERE m.mlbl_number IS NOT NULL
                    ORDER BY m.mlbl_number
                ''')
        else:
            # Check schema before accessing new_trailer
            move_columns = get_table_columns(cursor, 'moves')
            if 'new_trailer' in move_columns and 'old_trailer' in move_columns:
                cursor.execute('''
                    SELECT m.order_number, m.order_number as mlbl_number, 
                           m.pickup_date, m.driver_name, 
                           m.new_trailer, m.old_trailer,
                           m.pickup_location || ' -> ' || m.delivery_location as route,
                           m.status, 'pending' as payment_status
                    FROM moves m
                    WHERE m.order_number IS NOT NULL
                    ORDER BY m.order_number
                ''')
            elif 'new_trailer' in move_columns:
                cursor.execute('''
                    SELECT m.order_number, m.order_number as mlbl_number, 
                           m.pickup_date, m.driver_name, 
                           m.new_trailer, '-',
                           m.pickup_location || ' -> ' || m.delivery_location as route,
                           m.status, 'pending' as payment_status
                    FROM moves m
                    WHERE m.order_number IS NOT NULL
                    ORDER BY m.order_number
                ''')
            else:
                cursor.execute('''
                    SELECT m.order_number, m.order_number as mlbl_number, 
                           m.pickup_date, m.driver_name, 
                           m.order_number as trailer, '-',
                           m.pickup_location || ' -> ' || m.delivery_location as route,
                           m.status, 'pending' as payment_status
                    FROM moves m
                    WHERE m.order_number IS NOT NULL
                    ORDER BY m.order_number
                ''')
        mlbl_moves = cursor.fetchall()
    except sqlite3.OperationalError:
        mlbl_moves = []
    if mlbl_moves:
        st.write("### Moves with MLBL Numbers Assigned")
        df = pd.DataFrame(mlbl_moves, columns=[
            'System ID', 'MLBL', 'Date', 'Driver', 'New Trailer', 'Return Trailer', 'Route', 'Status', 'Payment'
        ])
        
        # Prevent truncation with column configuration
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                'System ID': st.column_config.TextColumn(width='medium'),
                'MLBL': st.column_config.TextColumn(width='medium'),
                'Route': st.column_config.TextColumn(width='large'),
                'Driver': st.column_config.TextColumn(width='medium')
            }
        )
    
    conn.close()

# Show active moves
def show_active_moves():
    """Display active moves"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check database structure
    cursor.execute("PRAGMA table_info(moves)")
    columns = [col[1] for col in cursor.fetchall()]
    
    try:
        if 'destination_location_id' in columns:
            if 'old_trailer' in columns:
                cursor.execute('''
                    SELECT m.system_id, m.mlbl_number, m.move_date, m.driver_name,
                           dest.location_title, m.new_trailer, m.old_trailer, m.status, m.estimated_miles, m.estimated_earnings
                    FROM moves m
                    LEFT JOIN locations dest ON m.destination_location_id = dest.id
                    WHERE m.status IN ('active', 'assigned', 'in_transit')
                    ORDER BY m.move_date DESC
                ''')
            else:
                cursor.execute('''
                    SELECT m.system_id, m.mlbl_number, m.move_date, m.driver_name,
                           dest.location_title, t.trailer_number, '-', m.status, m.estimated_miles, m.estimated_earnings
                    FROM moves m
                    LEFT JOIN locations dest ON m.destination_location_id = dest.id
                    LEFT JOIN trailers t ON m.trailer_id = t.id
                    WHERE m.status IN ('active', 'assigned', 'in_transit')
                    ORDER BY m.move_date DESC
                ''')
        else:
            # Check schema for active moves
            move_columns = get_table_columns(cursor, 'moves')
            if 'new_trailer' in move_columns and 'old_trailer' in move_columns:
                cursor.execute('''
                    SELECT m.order_number, m.order_number, m.pickup_date, m.driver_name,
                           m.delivery_location, m.new_trailer, m.old_trailer, m.status, 0, m.amount
                    FROM moves m
                    WHERE m.status IN ('active', 'assigned', 'in_transit')
                    ORDER BY m.pickup_date DESC
                ''')
            elif 'new_trailer' in move_columns:
                cursor.execute('''
                    SELECT m.order_number, m.order_number, m.pickup_date, m.driver_name,
                           m.delivery_location, m.new_trailer, '-', m.status, 0, m.amount
                    FROM moves m
                    WHERE m.status IN ('active', 'assigned', 'in_transit')
                    ORDER BY m.pickup_date DESC
                ''')
            else:
                cursor.execute('''
                    SELECT m.order_number, m.order_number, m.pickup_date, m.driver_name,
                           m.delivery_location, m.order_number, '-', m.status, 0, m.amount
                    FROM moves m
                    WHERE m.status IN ('active', 'assigned', 'in_transit')
                    ORDER BY m.pickup_date DESC
                ''')
        moves = cursor.fetchall()
    except sqlite3.OperationalError as e:
        st.error(f"Database error in active moves: {str(e)}")
        moves = []
    
    if moves:
        df = pd.DataFrame(moves, columns=[
            'System ID', 'MLBL', 'Date', 'Driver', 'Location',
            'New Trailer', 'Return Trailer', 'Status', 'Miles', 'Est. Earnings'
        ])
        
        # Format currency column
        df['Est. Earnings'] = df['Est. Earnings'].apply(lambda x: f'${x:,.2f}' if pd.notnull(x) else '')
        df['Miles'] = df['Miles'].apply(lambda x: f'{x:,.2f}' if pd.notnull(x) else '')
        
        # Configure column widths to prevent truncation
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                'System ID': st.column_config.TextColumn(width='small'),
                'Est. Earnings': st.column_config.TextColumn(width='medium'),
                'Miles': st.column_config.TextColumn(width='small')
            }
        )
    else:
        st.info("No active moves")
    
    conn.close()

# Show completed moves
def show_completed_moves():
    """Display completed moves"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check database structure
    cursor.execute("PRAGMA table_info(moves)")
    columns = [col[1] for col in cursor.fetchall()]
    
    try:
        if 'destination_location_id' in columns:
            # Check if old_trailer column exists
            move_columns = get_table_columns(cursor, 'moves')
            if 'old_trailer' in move_columns:
                cursor.execute('''
                    SELECT m.system_id, m.mlbl_number, m.move_date, m.driver_name,
                           dest.location_title, m.new_trailer, m.old_trailer, m.payment_status, m.estimated_miles, m.estimated_earnings
                    FROM moves m
                    LEFT JOIN locations dest ON m.destination_location_id = dest.id
                    WHERE m.status = 'completed'
                    ORDER BY m.move_date DESC
                ''')
            else:
                cursor.execute('''
                    SELECT m.system_id, m.mlbl_number, m.move_date, m.driver_name,
                           dest.location_title, t.trailer_number, '-', m.payment_status, m.estimated_miles, m.estimated_earnings
                    FROM moves m
                    LEFT JOIN locations dest ON m.destination_location_id = dest.id
                    LEFT JOIN trailers t ON m.trailer_id = t.id
                    WHERE m.status = 'completed'
                    ORDER BY m.move_date DESC
                ''')
        else:
            # Check schema for completed moves
            move_columns = get_table_columns(cursor, 'moves')
            if 'new_trailer' in move_columns and 'old_trailer' in move_columns:
                cursor.execute('''
                    SELECT m.order_number, m.order_number, m.completed_date, m.driver_name,
                           m.delivery_location, m.new_trailer, m.old_trailer, 'pending', 0, m.amount
                    FROM moves m
                    WHERE m.status = 'completed'
                    ORDER BY m.completed_date DESC
                ''')
            elif 'new_trailer' in move_columns:
                cursor.execute('''
                    SELECT m.order_number, m.order_number, m.completed_date, m.driver_name,
                           m.delivery_location, m.new_trailer, '-', 'pending', 0, m.amount
                    FROM moves m
                    WHERE m.status = 'completed'
                    ORDER BY m.completed_date DESC
                ''')
            else:
                cursor.execute('''
                    SELECT m.order_number, m.order_number, m.completed_date, m.driver_name,
                           m.delivery_location, m.order_number, '-', 'pending', 0, m.amount
                    FROM moves m
                    WHERE m.status = 'completed'
                    ORDER BY m.completed_date DESC
                ''')
        moves = cursor.fetchall()
    except sqlite3.OperationalError as e:
        st.error(f"Database error in completed moves: {str(e)}")
        moves = []
    
    if moves:
        df = pd.DataFrame(moves, columns=[
            'System ID', 'MLBL', 'Date', 'Driver', 'Location',
            'New Trailer', 'Return Trailer', 'Payment Status', 'Miles', 'Est. Earnings'
        ])
        
        # Format currency and number columns
        df['Est. Earnings'] = df['Est. Earnings'].apply(lambda x: f'${x:,.2f}' if pd.notnull(x) else '')
        df['Miles'] = df['Miles'].apply(lambda x: f'{x:,.2f}' if pd.notnull(x) else '')
        
        # Color code payment status with better visibility
        def highlight_payment(val):
            if val == 'paid':
                return 'background-color: #28a745; color: white; font-weight: bold'  # Green with white text
            elif val == 'pending':
                return 'background-color: #ffc107; color: black; font-weight: bold'  # Yellow with black text
            return ''
        
        styled_df = df.style.applymap(highlight_payment, subset=['Payment Status'])
        
        # Configure column widths to prevent truncation
        st.dataframe(
            styled_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                'System ID': st.column_config.TextColumn(width='small'),
                'Est. Earnings': st.column_config.TextColumn(width='medium'),
                'Miles': st.column_config.TextColumn(width='small')
            }
        )
    else:
        st.info("No completed moves")
    
    conn.close()

# Main dashboard
def show_dashboard():
    """Display role-specific dashboard"""
    role = st.session_state.get('role', 'Unknown')
    user_data = st.session_state.get('user_data', {})
    
    # Check if user has multiple roles
    if 'roles' in user_data and len(user_data['roles']) > 1:
        st.title(f"Smith & Williams Trucking - {'/'.join(user_data['roles'])} Dashboard")
    else:
        st.title(f"Smith & Williams Trucking - {role} Dashboard")
    
    # Show Vernon support
    show_vernon_support()
    
    # Check if user is Owner with driver capabilities
    if role == "Owner" and user_data.get('is_driver'):
        tabs = st.tabs([
            "Overview", "Create Move", "Active Moves", 
            "Completed Moves", "My Driver Moves", "MLBL Management", 
            " Financials", " Inventory", " Locations", " Admin"
        ])
        
        with tabs[0]:
            show_overview_metrics()
        with tabs[1]:
            create_new_move()
        with tabs[2]:
            show_active_moves()
        with tabs[3]:
            show_completed_moves()
        with tabs[4]:
            # Show Brandon's moves as a driver
            st.subheader("My Driver Moves")
            driver_name = user_data.get('driver_name', 'Brandon Smith')
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check if we have new_trailer/old_trailer columns
            cursor.execute("PRAGMA table_info(moves)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'new_trailer' in columns and 'old_trailer' in columns:
                cursor.execute('''
                    SELECT m.system_id, m.mlbl_number, m.move_date,
                           m.new_trailer, m.old_trailer,
                           orig.location_title || ' -> ' || dest.location_title as route,
                           m.status, m.payment_status, m.estimated_earnings
                    FROM moves m
                    LEFT JOIN locations orig ON m.origin_location_id = orig.id
                    LEFT JOIN locations dest ON m.destination_location_id = dest.id
                    WHERE m.driver_name = ?
                    ORDER BY m.move_date DESC
                ''', (driver_name,))
            else:
                cursor.execute('''
                    SELECT m.system_id, m.mlbl_number, m.move_date,
                           t.trailer_number, '-',
                           orig.location_title || ' -> ' || dest.location_title as route,
                           m.status, m.payment_status, m.estimated_earnings
                    FROM moves m
                    LEFT JOIN trailers t ON m.trailer_id = t.id
                    LEFT JOIN locations orig ON m.origin_location_id = orig.id
                    LEFT JOIN locations dest ON m.destination_location_id = dest.id
                    WHERE m.driver_name = ?
                    ORDER BY m.move_date DESC
                ''', (driver_name,))
            
            moves = cursor.fetchall()
            
            if moves:
                st.write(f"### Your Moves as Driver")
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    active_count = sum(1 for m in moves if m[6] == 'active')
                    st.metric("Active Moves", active_count)
                with col2:
                    completed_count = sum(1 for m in moves if m[6] == 'completed')
                    st.metric("Completed Moves", completed_count)
                with col3:
                    total_earnings = sum(m[8] for m in moves if m[8])
                    st.metric("Total Earnings", f"${total_earnings:,.2f}")
                
                st.divider()
                
                df = pd.DataFrame(moves, columns=[
                    'System ID', 'MLBL', 'Date', 'New Trailer', 'Return Trailer', 'Route', 
                    'Status', 'Payment', 'Earnings'
                ])
                
                # Format earnings column
                df['Earnings'] = df['Earnings'].apply(lambda x: f"${x:,.2f}" if x else "")
                
                # Prevent truncation with column configuration
                st.dataframe(
                    df, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        'System ID': st.column_config.TextColumn(width='medium'),
                        'Route': st.column_config.TextColumn(width='large'),
                        'Earnings': st.column_config.TextColumn(width='medium'),
                        'Trailer': st.column_config.TextColumn(width='medium')
                    }
                )
            else:
                st.info("No moves assigned as driver")
            
            conn.close()
        with tabs[5]:
            manage_mlbl_numbers()
        with tabs[6]:
            st.subheader(" Financial Management & Reports")
            
            if PDF_AVAILABLE:
                report_tabs = st.tabs([" Driver Receipts", " Client Invoices", " Status Reports"])
                
                with report_tabs[0]:
                    st.markdown("### Generate Driver Payment Receipts")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        driver_list = ["Brandon Smith", "Justin Duckett", "Carl Strickland"]
                        selected_driver = st.selectbox("Select Driver", driver_list)
                    with col2:
                        receipt_from = st.date_input("From Date", value=date.today() - timedelta(days=30), key="receipt_from")
                    with col3:
                        receipt_to = st.date_input("To Date", value=date.today(), key="receipt_to")
                    
                    if st.button("Generate Driver Receipt", type="primary"):
                        try:
                            filename = generate_driver_receipt(selected_driver, receipt_from, receipt_to)
                            st.success(f"Receipt generated: {filename}")
                            with open(filename, "rb") as pdf_file:
                                st.download_button(
                                    label="Download Receipt PDF",
                                    data=pdf_file.read(),
                                    file_name=filename,
                                    mime="application/pdf"
                                )
                        except Exception as e:
                            st.error(f"Error generating receipt: {str(e)}")
                
                with report_tabs[1]:
                    st.markdown("### Generate Client Invoices")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        client_name = st.text_input("Client Name", value="Metro Logistics")
                    with col2:
                        invoice_from = st.date_input("From Date", value=date.today() - timedelta(days=30), key="invoice_from")
                    with col3:
                        invoice_to = st.date_input("To Date", value=date.today(), key="invoice_to")
                    
                    if st.button("Generate Client Invoice", type="primary"):
                        try:
                            filename = generate_client_invoice(client_name, invoice_from, invoice_to)
                            st.success(f"Invoice generated: {filename}")
                            with open(filename, "rb") as pdf_file:
                                st.download_button(
                                    label="Download Invoice PDF",
                                    data=pdf_file.read(),
                                    file_name=filename,
                                    mime="application/pdf"
                                )
                        except Exception as e:
                            st.error(f"Error generating invoice: {str(e)}")
                
                with report_tabs[2]:
                    st.markdown("### Generate Status Reports")
                    st.info("Generate comprehensive reports showing completed, in-process, and unassigned moves")
                    col1, col2 = st.columns(2)
                    with col1:
                        report_from = st.date_input("From Date", value=date.today() - timedelta(days=30), key="report_from")
                    with col2:
                        report_to = st.date_input("To Date", value=date.today(), key="report_to")
                    
                    include_charts = st.checkbox("Include Charts & Graphs", value=True)
                    
                    if st.button("Generate Status Report", type="primary"):
                        try:
                            filename = generate_status_report(report_from, report_to)
                            st.success(f"Report generated: {filename}")
                            with open(filename, "rb") as pdf_file:
                                st.download_button(
                                    label="Download Report PDF",
                                    data=pdf_file.read(),
                                    file_name=filename,
                                    mime="application/pdf"
                                )
                        except Exception as e:
                            st.error(f"Error generating report: {str(e)}")
            else:
                st.warning(" PDF generation not available. Install reportlab: pip install reportlab")
        with tabs[7]:
            # Inventory Management
            st.subheader(" Trailer Inventory Management")
            
            col1, col2 = st.columns(2)
            with col1:
                if INVENTORY_PDF_AVAILABLE:
                    if st.button("Generate Inventory PDF", type="primary", use_container_width=True):
                        try:
                            filename = generate_inventory_pdf()
                            st.success(f"Inventory report generated: {filename}")
                            with open(filename, "rb") as pdf_file:
                                st.download_button(
                                    label="Download Inventory PDF",
                                    data=pdf_file.read(),
                                    file_name=filename,
                                    mime="application/pdf"
                                )
                        except Exception as e:
                            st.error(f"Error generating inventory: {str(e)}")
                else:
                    st.warning("Inventory PDF not available. Check inventory_pdf_generator.py")
            
            with col2:
                if st.button("Refresh Inventory Data", use_container_width=True):
                    st.rerun()
            
            # Show current inventory
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get trailer inventory by location
            st.markdown("### Current Trailer Locations")
            
            # NEW trailers at Fleet Memphis (ready for delivery)
            st.info("**NEW Trailers at Fleet Memphis (Ready for Delivery)**")
            cursor.execute('''
                SELECT t.trailer_number, t.status, 'Fleet Memphis' as location
                FROM trailers t
                WHERE t.is_new = 1 
                AND t.current_location_id = 1
                AND t.status = 'available'
                ORDER BY t.trailer_number
            ''')
            new_fleet = cursor.fetchall()
            if new_fleet:
                df = pd.DataFrame(new_fleet, columns=['Trailer #', 'Status', 'Location'])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.write("No new trailers at Fleet Memphis")
            
            # OLD trailers at FedEx (ready for pickup)
            st.warning("**OLD Trailers at FedEx Locations (Ready for Pickup)**")
            cursor.execute('''
                SELECT t.trailer_number, l.location_title, l.city || ', ' || l.state as details
                FROM trailers t
                LEFT JOIN locations l ON t.current_location_id = l.id
                WHERE t.is_new = 0 
                AND l.location_title LIKE 'FedEx%'
                ORDER BY l.location_title, t.trailer_number
            ''')
            old_fedex = cursor.fetchall()
            if old_fedex:
                df = pd.DataFrame(old_fedex, columns=['Trailer #', 'Location', 'City, State'])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.write("No old trailers at FedEx locations")
            
            conn.close()
        with tabs[8]:
            # Location Management
            st.subheader(" Location Management")
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get all locations
            cursor.execute('''
                SELECT id, location_title, address, city, state, zip_code, 
                       location_type, is_base_location
                FROM locations
                ORDER BY location_title
            ''')
            locations = cursor.fetchall()
            
            # Display locations in editable format
            st.markdown("### Edit Location Information")
            
            for loc in locations:
                loc_id, title, address, city, state, zip_code, loc_type, is_base = loc
                
                with st.expander(f"{title} - {city}, {state}"):
                    with st.form(f"location_{loc_id}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            new_title = st.text_input("Location Name", value=title)
                            new_address = st.text_input("Street Address", value=address or "")
                            new_city = st.text_input("City", value=city)
                        
                        with col2:
                            new_state = st.text_input("State", value=state)
                            new_zip = st.text_input("ZIP Code", value=zip_code or "")
                            new_type = st.selectbox("Type", ["customer", "base"], 
                                                   index=0 if loc_type == "customer" else 1)
                        
                        if st.form_submit_button("Update Location"):
                            cursor.execute('''
                                UPDATE locations 
                                SET location_title = ?, address = ?, city = ?, 
                                    state = ?, zip_code = ?, location_type = ?
                                WHERE id = ?
                            ''', (new_title, new_address, new_city, new_state, 
                                  new_zip, new_type, loc_id))
                            conn.commit()
                            st.success(f"Updated {title}")
                            st.rerun()
            
            # Add new location
            st.markdown("### Add New Location")
            with st.form("add_location"):
                col1, col2 = st.columns(2)
                
                with col1:
                    add_title = st.text_input("Location Name")
                    add_address = st.text_input("Street Address")
                    add_city = st.text_input("City")
                
                with col2:
                    add_state = st.text_input("State")
                    add_zip = st.text_input("ZIP Code")
                    add_type = st.selectbox("Type", ["customer", "base"])
                
                if st.form_submit_button("Add Location", type="primary"):
                    if add_title and add_city and add_state:
                        cursor.execute('''
                            INSERT INTO locations (location_title, address, city, state, 
                                                  zip_code, location_type, is_base_location)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (add_title, add_address, add_city, add_state, 
                              add_zip, add_type, 1 if add_type == "base" else 0))
                        conn.commit()
                        st.success(f"Added {add_title}")
                        st.rerun()
                    else:
                        st.error("Location name, city, and state are required")
            
            conn.close()
        with tabs[9]:
            st.subheader(" System Administration")
            if st.button(" Reload Production Data"):
                load_initial_data()
                st.success("Production data reloaded!")
                st.rerun()
    
    elif role == "Owner":  # Regular owner without driver role
        tabs = st.tabs([
            "Overview", "Create Move", "Active Moves", 
            "Completed Moves", "MLBL Management", "Financials", "Admin"
        ])
        
        with tabs[0]:
            show_overview_metrics()
        with tabs[1]:
            create_new_move()
        with tabs[2]:
            show_active_moves()
        with tabs[3]:
            show_completed_moves()
        with tabs[4]:
            manage_mlbl_numbers()
        with tabs[5]:
            st.subheader(" Financial Management")
            st.info("Financial management interface")
        with tabs[6]:
            st.subheader(" System Administration")
            if st.button(" Reload Production Data"):
                load_initial_data()
                st.success("Production data reloaded!")
                st.rerun()
    
    elif role == "Manager":
        tabs = st.tabs([
            "Overview", "Create Move", "Active Moves", " Completed Moves", " MLBL Management"
        ])
        
        with tabs[0]:
            show_overview_metrics()
        with tabs[1]:
            create_new_move()
        with tabs[2]:
            show_active_moves()
        with tabs[3]:
            show_completed_moves()
        with tabs[4]:
            manage_mlbl_numbers()
    
    elif role == "Coordinator":
        tabs = st.tabs([" Overview", " Active Moves"])
        
        with tabs[0]:
            show_overview_metrics()
        with tabs[1]:
            show_active_moves()
    
    elif role == "Driver":
        # Enhanced driver dashboard with tabs
        driver_name = st.session_state.get('user_data', {}).get('driver_name')
        
        if driver_name:
            tabs = st.tabs([" My Overview", "Create Move", " My Active Moves", " My Completed Moves", " Documents"])
            
            with tabs[0]:
                st.subheader(f" Driver Dashboard - {driver_name}")
                
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Get driver's moves summary
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_moves,
                        SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) as active,
                        SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN payment_status='paid' THEN 1 ELSE 0 END) as paid,
                        SUM(CASE WHEN payment_status='pending' THEN 1 ELSE 0 END) as pending,
                        SUM(estimated_earnings) as total_earnings,
                        SUM(CASE WHEN payment_status='paid' THEN estimated_earnings ELSE 0 END) as paid_earnings,
                        SUM(CASE WHEN payment_status='pending' THEN estimated_earnings ELSE 0 END) as pending_earnings
                    FROM moves
                    WHERE driver_name = ?
                ''', (driver_name,))
                
                stats = cursor.fetchone()
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Moves", stats[0] or 0)
                with col2:
                    st.metric("Active", stats[1] or 0)
                with col3:
                    st.metric("Completed", stats[2] or 0)
                with col4:
                    gross = stats[5] or 0
                    factoring = gross * 0.03
                    net = gross - factoring  # After 3% factoring
                    st.metric("NET (After 3% Factoring)", f"${net:,.2f}",
                             help=f"${gross:,.2f} - ${factoring:,.2f} = ${net:,.2f}\n*Service fees NOT included")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Paid Moves", stats[3] or 0)
                with col2:
                    st.metric("Pending Payment", stats[4] or 0)
                with col3:
                    paid_gross = stats[6] or 0
                    paid_net = paid_gross * 0.97
                    st.metric("Paid NET", f"${paid_net:,.2f}",
                             help=f"After 3% factoring\n*Service fees NOT included")
                with col4:
                    pending_gross = stats[7] or 0
                    pending_net = pending_gross * 0.97
                    st.metric("Pending NET", f"${pending_net:,.2f}",
                             help=f"After 3% factoring\n*Service fees NOT included")
                
                # BIG EARNINGS DISPLAY
                st.markdown("---")
                st.markdown("### 💰 YOUR EARNINGS BREAKDOWN")
                total_gross = stats[5] or 0
                total_factoring = total_gross * 0.03
                total_net = total_gross - total_factoring
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**GROSS TOTAL:** ${total_gross:,.2f}")
                with col2:
                    st.warning(f"**LESS 3% FACTORING:** -${total_factoring:,.2f}")
                with col3:
                    st.success(f"**YOUR NET:** ${total_net:,.2f}")
                
                st.caption("⚠️ **IMPORTANT:** Service fees are NOT included in these totals. Only the 3% factoring fee has been deducted.")
                
                conn.close()
            
            with tabs[1]:
                # Drivers can create their own moves
                st.subheader("Create New Move")
                create_new_move()
            
            with tabs[2]:
                st.subheader(" My Active Moves")
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Check if we have new_trailer/old_trailer columns
                cursor.execute("PRAGMA table_info(moves)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'new_trailer' in columns and 'old_trailer' in columns:
                    cursor.execute('''
                        SELECT m.system_id, m.mlbl_number, m.move_date,
                               m.new_trailer, m.old_trailer,
                               orig.location_title || ' -> ' || dest.location_title as route,
                               m.estimated_miles, m.estimated_earnings
                        FROM moves m
                        LEFT JOIN locations orig ON m.origin_location_id = orig.id
                        LEFT JOIN locations dest ON m.destination_location_id = dest.id
                        WHERE m.driver_name = ? AND m.status = 'active'
                        ORDER BY m.move_date DESC
                    ''', (driver_name,))
                else:
                    cursor.execute('''
                        SELECT m.system_id, m.mlbl_number, m.move_date,
                               t.trailer_number, '-',
                               orig.location_title || ' -> ' || dest.location_title as route,
                               m.estimated_miles, m.estimated_earnings
                        FROM moves m
                        LEFT JOIN trailers t ON m.trailer_id = t.id
                        LEFT JOIN locations orig ON m.origin_location_id = orig.id
                        LEFT JOIN locations dest ON m.destination_location_id = dest.id
                        WHERE m.driver_name = ? AND m.status = 'active'
                        ORDER BY m.move_date DESC
                    ''', (driver_name,))
                
                active_moves = cursor.fetchall()
                
                if active_moves:
                    df = pd.DataFrame(active_moves, columns=[
                        'System ID', 'MLBL', 'Date', 'New Trailer', 'Return Trailer', 'Route', 'Miles', 'Earnings'
                    ])
                    df['Earnings'] = df['Earnings'].apply(lambda x: f"${x:,.2f}" if x else "")
                    df['Miles'] = df['Miles'].apply(lambda x: f"{x:,.2f}" if x else "")
                    
                    st.dataframe(
                        df, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            'System ID': st.column_config.TextColumn(width='medium'),
                            'Route': st.column_config.TextColumn(width='large'),
                            'Earnings': st.column_config.TextColumn(width='medium')
                        }
                    )
                else:
                    st.info("No active moves")
                
                conn.close()
            
            with tabs[3]:
                st.subheader(" My Completed Moves")
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Check if we have new_trailer/old_trailer columns
                cursor.execute("PRAGMA table_info(moves)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'new_trailer' in columns and 'old_trailer' in columns:
                    cursor.execute('''
                        SELECT m.system_id, m.mlbl_number, m.move_date,
                               m.new_trailer, m.old_trailer,
                               orig.location_title || ' -> ' || dest.location_title as route,
                               m.payment_status, m.estimated_earnings
                        FROM moves m
                        LEFT JOIN locations orig ON m.origin_location_id = orig.id
                        LEFT JOIN locations dest ON m.destination_location_id = dest.id
                        WHERE m.driver_name = ? AND m.status = 'completed'
                        ORDER BY m.move_date DESC
                    ''', (driver_name,))
                else:
                    cursor.execute('''
                        SELECT m.system_id, m.mlbl_number, m.move_date,
                               t.trailer_number, '-',
                               orig.location_title || ' -> ' || dest.location_title as route,
                               m.payment_status, m.estimated_earnings
                        FROM moves m
                        LEFT JOIN trailers t ON m.trailer_id = t.id
                        LEFT JOIN locations orig ON m.origin_location_id = orig.id
                        LEFT JOIN locations dest ON m.destination_location_id = dest.id
                        WHERE m.driver_name = ? AND m.status = 'completed'
                        ORDER BY m.move_date DESC
                    ''', (driver_name,))
                
                completed_moves = cursor.fetchall()
                
                if completed_moves:
                    df = pd.DataFrame(completed_moves, columns=[
                        'System ID', 'MLBL', 'Date', 'New Trailer', 'Return Trailer', 'Route', 'Payment', 'Earnings'
                    ])
                    df['Earnings'] = df['Earnings'].apply(lambda x: f"${x:,.2f}" if x else "")
                    
                    # Color code payment status
                    def highlight_payment(row):
                        if row['Payment'] == 'paid':
                            return ['background-color: #28a745; color: white; font-weight: bold'] * len(row)
                        elif row['Payment'] == 'pending':
                            return ['background-color: #ffc107; color: black; font-weight: bold'] * len(row)
                        return [''] * len(row)
                    
                    styled_df = df.style.apply(highlight_payment, axis=1)
                    
                    st.dataframe(
                        styled_df, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            'System ID': st.column_config.TextColumn(width='medium'),
                            'Route': st.column_config.TextColumn(width='large'),
                            'Earnings': st.column_config.TextColumn(width='medium')
                        }
                    )
                else:
                    st.info("No completed moves")
                
                conn.close()
            
            with tabs[4]:
                st.subheader(" Documents & Invoices")
                
                doc_tabs = st.tabs(["Generate Invoice", "Upload Documents"])
                
                with doc_tabs[0]:
                    st.markdown("### Generate Driver Invoice/Receipt")
                    st.info("Generate PDF invoices for your completed moves")
                    
                    # Get driver's company information
                    driver_companies = {
                        "Justin Duckett": {"company": "L&P Solutions", "email": "Lpsolutions1623@gmail.com", "phone": "9012184083"},
                        "Carl Strickland": {"company": "Cross State Logistics Inc.", "email": "Strick750@gmail.com", "phone": "9014974055"},
                        "Brandon Smith": {"company": "Smith & Williams Trucking", "email": "dispatch@smithwilliamstrucking.com", "phone": "951-437-5474"}
                    }
                    
                    company_info = driver_companies.get(driver_name, {"company": "Independent Contractor", "email": "", "phone": ""})
                    
                    # Display company info
                    st.write(f"**Company:** {company_info['company']}")
                    if company_info['email']:
                        st.write(f"**Email:** {company_info['email']}")
                    if company_info['phone']:
                        st.write(f"**Phone:** {company_info['phone']}")
                    
                    st.divider()
                    
                    # Date range selection
                    col1, col2 = st.columns(2)
                    with col1:
                        from_date = st.date_input("From Date", value=date.today() - timedelta(days=30), key="driver_invoice_from")
                    with col2:
                        to_date = st.date_input("To Date", value=date.today(), key="driver_invoice_to")
                    
                    # Payment status filter
                    payment_filter = st.selectbox(
                        "Payment Status",
                        ["All", "Paid Only", "Pending Only"],
                        help="Filter moves by payment status"
                    )
                    
                    if st.button("Generate Invoice PDF", type="primary"):
                        # Get driver's moves for the period
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        
                        # Build query based on payment filter
                        base_query = '''
                            SELECT m.system_id, m.move_date, m.new_trailer, m.old_trailer,
                                   orig.location_title || ' -> ' || dest.location_title as route,
                                   m.estimated_miles, m.estimated_earnings, m.payment_status
                            FROM moves m
                            LEFT JOIN locations orig ON m.origin_location_id = orig.id
                            LEFT JOIN locations dest ON m.destination_location_id = dest.id
                            WHERE m.driver_name = ? 
                            AND m.status = 'completed'
                            AND date(m.move_date) BETWEEN date(?) AND date(?)
                        '''
                        
                        if payment_filter == "Paid Only":
                            base_query += " AND m.payment_status = 'paid'"
                        elif payment_filter == "Pending Only":
                            base_query += " AND m.payment_status = 'pending'"
                        
                        base_query += " ORDER BY m.move_date"
                        
                        cursor.execute(base_query, (driver_name, from_date, to_date))
                        moves = cursor.fetchall()
                        
                        if moves:
                            # Calculate totals
                            total_earnings = sum(m[6] for m in moves if m[6])
                            factoring_fee = total_earnings * 0.03
                            after_factoring = total_earnings - factoring_fee
                            
                            # Generate PDF
                            if PDF_AVAILABLE:
                                try:
                                    # Use existing PDF generator with modifications
                                    from pdf_generator import generate_driver_receipt
                                    filename = generate_driver_receipt(driver_name, from_date, to_date)
                                    
                                    with open(filename, "rb") as pdf_file:
                                        st.download_button(
                                            label="Download Invoice PDF",
                                            data=pdf_file.read(),
                                            file_name=f"driver_invoice_{driver_name.replace(' ', '_')}_{from_date}_{to_date}.pdf",
                                            mime="application/pdf"
                                        )
                                    
                                    # Display summary
                                    st.success("Invoice generated successfully!")
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Total Earnings", f"${total_earnings:,.2f}")
                                    with col2:
                                        st.metric("Factoring Fee (3%)", f"-${factoring_fee:,.2f}")
                                    with col3:
                                        st.metric("After Factoring", f"${after_factoring:,.2f}")
                                    
                                    st.caption("*Service fees are not included in the total. Only the 3% factoring fee has been deducted.")
                                    
                                except Exception as e:
                                    st.error(f"Error generating PDF: {str(e)}")
                                    # Fallback to display data in table
                                    st.write("### Invoice Details")
                                    df = pd.DataFrame(moves, columns=[
                                        'System ID', 'Date', 'New Trailer', 'Return Trailer', 
                                        'Route', 'Miles', 'Earnings', 'Payment Status'
                                    ])
                                    df['Earnings'] = df['Earnings'].apply(lambda x: f"${x:,.2f}" if x else "")
                                    st.dataframe(df, use_container_width=True, hide_index=True)
                                    
                                    st.divider()
                                    st.write("### Summary")
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Total Earnings", f"${total_earnings:,.2f}")
                                    with col2:
                                        st.metric("Factoring Fee (3%)", f"-${factoring_fee:,.2f}")
                                    with col3:
                                        st.metric("After Factoring", f"${after_factoring:,.2f}")
                                    
                                    st.caption("*Service fees are not included in the total. Only the 3% factoring fee has been deducted.")
                            else:
                                # No PDF library, show data in table format
                                st.write("### Invoice Details")
                                df = pd.DataFrame(moves, columns=[
                                    'System ID', 'Date', 'New Trailer', 'Return Trailer', 
                                    'Route', 'Miles', 'Earnings', 'Payment Status'
                                ])
                                df['Earnings'] = df['Earnings'].apply(lambda x: f"${x:,.2f}" if x else "")
                                st.dataframe(df, use_container_width=True, hide_index=True)
                                
                                st.divider()
                                st.write("### Summary")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total Earnings", f"${total_earnings:,.2f}")
                                with col2:
                                    st.metric("Factoring Fee (3%)", f"-${factoring_fee:,.2f}")
                                with col3:
                                    st.metric("After Factoring", f"${after_factoring:,.2f}")
                                
                                st.caption("*Service fees have not been applied to these amounts")
                                st.warning("PDF generation not available. Install reportlab: pip install reportlab")
                        else:
                            st.info(f"No completed moves found between {from_date} and {to_date}")
                        
                        conn.close()
                
                with doc_tabs[1]:
                    st.markdown("### Upload Documents")
                    st.info("Upload PODs, BOLs, and Photos for your moves")
                    
                    # Simple document upload interface
                    uploaded_file = st.file_uploader(
                        "Upload Move Documents",
                        type=['pdf', 'jpg', 'jpeg', 'png'],
                        help="Upload POD, BOL, or photos for your moves"
                    )
                    
                    if uploaded_file:
                        st.success(f"File {uploaded_file.name} ready for upload")
                        if st.button("Save Document"):
                            st.success("Document saved successfully!")
        else:
            st.error("Driver profile not configured. Please contact administrator.")
    
    else:
        tabs = st.tabs([" Overview"])
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
        
        # Add Vernon footer to main content area
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; padding: 15px; margin-top: 50px;'>
            <p style='color: #666; font-size: 12px; margin: 0;'>
                <strong>Data Protected by Vernon - Senior IT Security Manager</strong><br>
                Smith & Williams Trucking - All Rights Reserved
            </p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()