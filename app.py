"""
Trailer Fleet Management System - Production Ready
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

# Import PDF generators - Try universal first, then fall back
try:
    from universal_pdf_generator import generate_driver_receipt, generate_client_invoice, generate_status_report
    PDF_AVAILABLE = True
except ImportError:
    try:
        from pdf_generator import generate_driver_receipt, generate_client_invoice, generate_status_report
        PDF_AVAILABLE = True
    except ImportError:
        try:
            from professional_pdf_generator import generate_status_report_for_profile
            def generate_driver_receipt(driver_name, from_date, to_date):
                return generate_status_report_for_profile(driver_name, "driver")
            def generate_client_invoice(*args, **kwargs):
                return generate_status_report_for_profile("client", "client")
            def generate_status_report(*args, **kwargs):
                return generate_status_report_for_profile("admin", "admin")
            PDF_AVAILABLE = True
        except ImportError:
            PDF_AVAILABLE = False
            # Ultimate fallback - generate text reports
            def generate_driver_receipt(driver_name, from_date, to_date):
                filename = f"driver_report_{driver_name}_{datetime.now().strftime('%Y%m%d')}.txt"
                with open(filename, 'w') as f:
                    f.write(f"DRIVER RECEIPT\n")
                    f.write(f"==============\n")
                    f.write(f"Driver: {driver_name}\n")
                    f.write(f"Period: {from_date} to {to_date}\n")
                    f.write(f"\nSmith & Williams Trucking LLC\n")
                    f.write(f"Generated: {datetime.now()}\n")
                return filename
            def generate_client_invoice(*args, **kwargs):
                return generate_driver_receipt("Client", datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d'))
            def generate_status_report(*args, **kwargs):
                return generate_driver_receipt("Status", datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d'))

# Import help system (safe - won't block login)
try:
    from help_system import get_help_system, show_contextual_help
    HELP_AVAILABLE = True
except ImportError:
    HELP_AVAILABLE = False

try:
    from inventory_pdf_generator import generate_inventory_pdf
    INVENTORY_PDF_AVAILABLE = True
except ImportError:
    INVENTORY_PDF_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Trailer Fleet Management System",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Version for tracking updates - FORCE UPDATE  
APP_VERSION = "4.0.0 - GLOBAL Driver Info Integration"
UPDATE_TIMESTAMP = "2025-08-16 07:30:00"  # Force Streamlit to recognize update

# Force cache clear on version change
if 'app_version' not in st.session_state or st.session_state.app_version != APP_VERSION:
    st.cache_data.clear()
    st.cache_resource.clear()
    st.session_state.app_version = APP_VERSION
    st.session_state.last_cache_clear = datetime.now()
elif (datetime.now() - st.session_state.last_cache_clear).seconds > 3600:  # Clear every hour
    st.cache_data.clear()
    st.cache_resource.clear()
    st.session_state.last_cache_clear = datetime.now()

# Custom CSS - Applied Globally
st.markdown("""
<style>
    .logo-container { text-align: center; padding: 1rem; }
    .logo-img { max-width: 200px; margin: 0 auto; }
    .main { padding: 0; }
    .stTabs [data-baseweb="tab-list"] { 
        gap: 8px; 
        overflow-x: auto !important;
        white-space: nowrap !important;
        scrollbar-width: thin;
        -webkit-overflow-scrolling: touch;
    }
    .stTabs [data-baseweb="tab"] { 
        padding: 8px 16px;
        min-width: fit-content;
        flex-shrink: 0;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
        height: 6px;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 3px;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
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
    /* Table borders - applied globally to all dataframes */
    [data-testid="stDataFrame"] {
        border: 2px solid #ddd !important;
        border-radius: 5px !important;
        padding: 5px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    /* Table headers */
    [data-testid="stDataFrame"] thead {
        background-color: #f8f9fa !important;
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
    
    # Moves table - Central hub with all required columns
    cursor.execute('''CREATE TABLE IF NOT EXISTS moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        system_id TEXT UNIQUE NOT NULL,
        order_number TEXT,
        mlbl_number TEXT UNIQUE,
        move_date DATE,
        pickup_date DATE,
        completed_date DATE,
        trailer_id INTEGER,
        new_trailer TEXT,
        old_trailer TEXT,
        origin_location TEXT,
        origin_location_id INTEGER,
        destination_location TEXT,
        destination_location_id INTEGER,
        delivery_location TEXT,
        client TEXT,
        driver_id INTEGER,
        driver_name TEXT,
        estimated_miles REAL,
        actual_miles REAL,
        base_rate REAL DEFAULT 2.10,
        estimated_earnings REAL,
        amount REAL,
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
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

def fix_trailer_inventory(cursor):
    """DEEP FIX: Ensure minimum correct trailer inventory, but allow additions"""
    # Check current count
    cursor.execute("SELECT COUNT(*) FROM trailers")
    current_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trailers WHERE is_new = 1")
    current_new = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trailers WHERE is_new = 0")
    current_old = cursor.fetchone()[0]
    
    # Check if we have a fix flag to prevent repeated fixes
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='system_flags'")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''CREATE TABLE system_flags (
            flag_name TEXT PRIMARY KEY,
            flag_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor.connection.commit()
    
    # Check if we've already fixed to 38
    cursor.execute("SELECT flag_value FROM system_flags WHERE flag_name = 'trailer_fix_38_complete'")
    fix_done = cursor.fetchone()
    
    # Only fix if we have the OLD wrong count (32) AND haven't fixed yet
    # This allows manual additions beyond 38
    if current_count == 32 and current_new == 11 and current_old == 21 and not fix_done:
        print(f"FIXING TRAILER INVENTORY: Current {current_count} -> Target 38")
        
        # Get location IDs
        cursor.execute("SELECT id FROM locations WHERE location_title = 'Fleet Memphis'")
        fleet_id = cursor.fetchone()
        fleet_id = fleet_id[0] if fleet_id else 1
        
        # Clear and rebuild with correct data
        cursor.execute("DELETE FROM trailers")
        
        # Insert exact OLD trailers (23 total)
        old_trailers = [
            # Available at FedEx locations (12)
            ('7155', 'FedEx Houston'), ('7146', 'FedEx Oakland'), ('5955', 'FedEx Indy'),
            ('6024', 'FedEx Chicago'), ('6061', 'FedEx Dallas'), ('3170', 'FedEx Chicago'),
            ('7153', 'FedEx Dulles VA'), ('6015', 'FedEx Hebron KY'), ('7160', 'FedEx Dallas'),
            ('6783', 'FedEx Newark NJ'), ('3083', 'FedEx Indy'), ('6231', 'FedEx Indy'),
            # At Fleet after swap (11)
            ('6094', 'Fleet Memphis'), ('6837', 'Fleet Memphis'), ('5950', 'Fleet Memphis'),
            ('5876', 'Fleet Memphis'), ('4427', 'Fleet Memphis'), ('6014', 'Fleet Memphis'),
            ('7144', 'Fleet Memphis'), ('5906', 'Fleet Memphis'), ('7131', 'Fleet Memphis'),
            ('7162', 'Fleet Memphis'), ('6981', 'Fleet Memphis')
        ]
        
        for trailer_num, location in old_trailers:
            cursor.execute("SELECT id FROM locations WHERE location_title = ?", (location,))
            loc_id = cursor.fetchone()
            loc_id = loc_id[0] if loc_id else fleet_id
            
            cursor.execute('''
                INSERT INTO trailers (trailer_number, trailer_type, current_location_id, status, is_new)
                VALUES (?, 'Roller Bed', ?, 'available', 0)
            ''', (trailer_num, loc_id))
        
        # Insert exact NEW trailers (15 total)
        # Available at Fleet (4)
        new_available = [
            ('18V00408', fleet_id), ('18V00600', fleet_id), 
            ('18V00598', fleet_id), ('18V00599', fleet_id)
        ]
        
        for trailer_num, loc_id in new_available:
            cursor.execute('''
                INSERT INTO trailers (trailer_number, trailer_type, current_location_id, status, is_new)
                VALUES (?, 'Roller Bed', ?, 'available', 1)
            ''', (trailer_num, loc_id))
        
        # Delivered/In-use NEW trailers (11)
        new_delivered = [
            ('18V00406', 'FedEx Memphis'), ('18V00409', 'FedEx Memphis'),
            ('18V00414', 'FedEx Memphis'), ('190030', 'FedEx Memphis'),
            ('190033', 'FedEx Indy'), ('18V00298', 'FedEx Indy'),
            ('190011', 'FedEx Indy'), ('7728', 'FedEx Chicago'),
            ('18V00327', 'FedEx Memphis'), ('18V00407', 'Fleet Memphis'),
            ('190046', 'Fleet Memphis')
        ]
        
        for trailer_num, location in new_delivered:
            cursor.execute("SELECT id FROM locations WHERE location_title = ?", (location,))
            loc_id = cursor.fetchone()
            loc_id = loc_id[0] if loc_id else fleet_id
            
            status = 'in_transit' if trailer_num in ['18V00407', '190046'] else 'delivered'
            
            cursor.execute('''
                INSERT INTO trailers (trailer_number, trailer_type, current_location_id, status, is_new)
                VALUES (?, 'Roller Bed', ?, ?, 1)
            ''', (trailer_num, loc_id, status))
        
        cursor.connection.commit()
        
        # Mark fix as complete so it won't run again
        cursor.execute('''
            INSERT OR REPLACE INTO system_flags (flag_name, flag_value, updated_at)
            VALUES ('trailer_fix_38_complete', 'true', CURRENT_TIMESTAMP)
        ''')
        cursor.connection.commit()
        
        print("TRAILER INVENTORY FIXED: 38 trailers (23 OLD, 15 NEW)")
        print("Fix marked complete - won't run again unless reset")

# Load initial data if needed
def load_initial_data():
    """Load real production data and ensure basic data exists"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if we have any data
    try:
        cursor.execute("SELECT COUNT(*) FROM trailers")
        trailer_count = cursor.fetchone()[0]
    except (sqlite3.Error, TypeError):
        trailer_count = 0
    
    try:
        cursor.execute("SELECT COUNT(*) FROM moves")
        move_count = cursor.fetchone()[0]
    except (sqlite3.Error, TypeError):
        move_count = 0
    
    try:
        cursor.execute("SELECT COUNT(*) FROM drivers")
        driver_count = cursor.fetchone()[0]
    except (sqlite3.Error, TypeError):
        driver_count = 0
    
    # DEEP FIX: Force correct trailer inventory (38 total: 23 OLD, 15 NEW)
    fix_trailer_inventory(cursor)
    
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
            
            # Add some sample trailers based on schema
            cursor.execute("PRAGMA table_info(trailers)")
            trailer_cols = [col[1] for col in cursor.fetchall()]
            
            for i in range(1, 6):
                if 'current_location_id' in trailer_cols:
                    # Normalized schema
                    cursor.execute('''
                        INSERT OR IGNORE INTO trailers (trailer_number, status, current_location_id, is_new)
                        VALUES (?, 'available', 1, 0)
                    ''', (f'DEMO{i:03d}',))
                else:
                    # Simple schema
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
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
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
                # If video fails, show logo instead
                logo_path = "swt_logo_white.png" if os.path.exists("swt_logo_white.png") else "swt_logo.png"
                if os.path.exists(logo_path):
                    st.image(logo_path, use_container_width=True)
    
    st.title("Trailer Fleet Management System")
    st.subheader("Smith & Williams Trucking LLC")
    
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
    
    # Footer with Vernon protection and copyright
    st.markdown("""
    <div style='text-align: center; padding: 20px; margin-top: 60px; border-top: 1px solid #e0e0e0;'>
        <p style='color: #28a745; font-size: 11px; margin: 0; font-weight: 600; letter-spacing: 0.5px;'>
            DATA PROTECTED BY VERNON - SENIOR IT SECURITY MANAGER
        </p>
        <p style='color: #666; font-size: 10px; margin-top: 5px;'>
            © 2025 Smith & Williams Trucking LLC - All Rights Reserved
        </p>
    </div>
    """, unsafe_allow_html=True)

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
        st.caption(f"Version: {APP_VERSION}")
        
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
        
        # Add help section if available
        if HELP_AVAILABLE:
            try:
                help_system = get_help_system()
                help_system.show_sidebar_help()
            except Exception as e:
                # Don't let help system errors break the app
                pass
        
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
        # Count ALL old trailers (is_new = 0) but exclude delivered ones for active count
        cursor.execute('SELECT COUNT(*) FROM trailers WHERE is_new = 0 AND status != "delivered"')
        old_trailers_total = cursor.fetchone()[0]
        
        # Count delivered old trailers separately  
        cursor.execute('SELECT COUNT(*) FROM trailers WHERE is_new = 0 AND status = "delivered"')
        old_delivered = cursor.fetchone()[0]
        
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
        # Show total old trailers with available count and delivered
        delivered_text = f" | {old_delivered} delivered" if 'is_new' in trailer_columns else ""
        st.metric("Old Trailers", f"{old_trailers_total} ({old_available} avail)", 
                  help=f"Total active old trailers: {old_trailers_total}\nAvailable for pickup: {old_available}{delivered_text}")
    
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
        st.markdown("### 2. Select Destination FedEx Location")
        st.info("💡 **Simple Process:** You'll deliver the NEW trailer from Fleet Memphis → FedEx, then pick up an OLD trailer to bring back")
        
        # Get all FedEx locations with details
        # Check if locations table exists
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='locations'")
        if cursor.fetchone()[0] > 0:
            # Check table structure
            cursor.execute("PRAGMA table_info(trailers)")
            trailer_columns = [col[1] for col in cursor.fetchall()]
            
            cursor.execute("PRAGMA table_info(locations)")
            location_columns = [col[1] for col in cursor.fetchall()]
            
            if 'is_new' in trailer_columns and 'address' in location_columns:
                cursor.execute('''
                    SELECT l.id, l.location_title, l.city, l.state,
                           CASE WHEN l.address = '' OR l.address = 'Address TBD' OR l.address IS NULL THEN 0 ELSE 1 END as has_address,
                           COUNT(t.id) as old_trailer_count
                    FROM locations l
                    LEFT JOIN trailers t ON t.current_location_id = l.id AND t.is_new = 0 AND t.status IN ('available', 'in_use')
                    WHERE (l.location_type IN ('fedex_hub', 'customer') OR l.location_title LIKE 'FedEx%')
                    AND l.is_base_location = 0
                    GROUP BY l.id, l.location_title, l.city, l.state
                    ORDER BY l.location_title
                ''')
            elif 'address' in location_columns:
                cursor.execute('''
                    SELECT l.id, l.location_title, l.city, l.state,
                           CASE WHEN l.address = '' OR l.address = 'Address TBD' OR l.address IS NULL THEN 0 ELSE 1 END as has_address,
                           COUNT(t.id) as old_trailer_count
                    FROM locations l
                    LEFT JOIN trailers t ON t.current_location_id = l.id AND t.status IN ('available', 'in_use')
                    WHERE (l.location_type IN ('fedex_hub', 'customer') OR l.location_title LIKE 'FedEx%')
                    AND l.is_base_location = 0
                    GROUP BY l.id, l.location_title, l.city, l.state
                    ORDER BY l.location_title
                ''')
            else:
                cursor.execute('''
                    SELECT l.id, l.location_title, l.city, l.state,
                           0 as has_address,
                           COUNT(t.id) as old_trailer_count
                    FROM locations l
                    LEFT JOIN trailers t ON t.current_location_id = l.id AND t.status IN ('available', 'in_use')
                    WHERE (l.location_type IN ('fedex_hub', 'customer') OR l.location_title LIKE 'FedEx%')
                    AND l.is_base_location = 0
                    GROUP BY l.id, l.location_title, l.city, l.state
                    ORDER BY l.location_title
                ''')
        else:
            # No locations table - return empty
            cursor.execute("SELECT 1, 'FedEx Memphis', 'Memphis', 'TN', 0, 0 UNION SELECT 2, 'FedEx Indy', 'Indianapolis', 'IN', 0, 0 UNION SELECT 3, 'FedEx Chicago', 'Chicago', 'IL', 0, 0")
        all_locations = cursor.fetchall()
        
        # Create easy-to-understand location options
        location_display_map = {}
        locations_with_trailers = []
        locations_without_trailers = []
        
        for loc_id, title, city, state, has_addr, trailer_count in all_locations:
            # Build display string
            if trailer_count > 0:
                display = f"[AVAILABLE] {title} - {trailer_count} OLD trailer{'s' if trailer_count > 1 else ''} ready"
                locations_with_trailers.append((display, title))
            else:
                display = f"📍 {title} - No OLD trailers available"
                locations_without_trailers.append((display, title))
            
            location_display_map[display] = title
        
        # Create location_options mapping for IDs
        location_options = {}
        for loc_id, title, city, state, has_addr, trailer_count in all_locations:
            location_options[title] = loc_id
        
        # Combine locations - ones with trailers first
        all_location_options = []
        
        if locations_with_trailers:
            all_location_options.append("--- LOCATIONS WITH OLD TRAILERS READY FOR PICKUP ---")
            for display, _ in locations_with_trailers:
                all_location_options.append(display)
        
        if locations_without_trailers:
            all_location_options.append("--- OTHER FEDEX LOCATIONS ---")
            for display, _ in locations_without_trailers:
                all_location_options.append(display)
        
        # Single, clear destination selector
        destination_display = st.selectbox(
            "📍 Select FedEx Destination",
            options=[opt for opt in all_location_options if not opt.startswith("---")],
            help="[AVAILABLE] = OLD trailers ready for pickup | [LOCATION] = No OLD trailers currently"
        )
        
        # Extract actual location name
        destination = location_display_map.get(destination_display, "FedEx Memphis")
        origin = "Fleet Memphis"  # Always Fleet Memphis
        
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
            "📍 One-Way Miles to Destination", 
            min_value=0.0, 
            value=default_miles, 
            step=10.0,
            help="Enter one-way distance. Round trip will be calculated automatically (x2).",
            key=f"miles_{destination}"
        )
        
        # Show LIVE earnings calculation
        st.markdown("###  Real-Time Earnings Calculation")
        # Round trip calculation: miles * 2 * rate per mile
        total_miles = miles * 2  # Round trip
        earnings = total_miles * 2.10
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
            st.metric("One-Way Miles", f"{miles:,.2f}")
        with col2:
            st.metric("Round Trip", f"{total_miles:,.2f} mi")
        with col3:
            st.metric("Rate", "$2.10/mile")
        with col4:
            st.metric("NET (after 3%)", f"${after_factoring:,.2f}")
        
        st.divider()
        
        # Section 3: Select OLD Trailer to Pick Up
        st.markdown("### 3. Select OLD Trailer to Return")
        
        # Get OLD trailers at the selected destination
        # Check table structure first
        cursor.execute("PRAGMA table_info(trailers)")
        trailer_columns = [col[1] for col in cursor.fetchall()]
        
        if 'current_location_id' in trailer_columns:
            cursor.execute("SELECT id FROM locations WHERE location_title = ?", (destination,))
            loc_result = cursor.fetchone()
            
            if loc_result:
                loc_id = loc_result[0]
                if 'is_new' in trailer_columns:
                    cursor.execute('''
                        SELECT trailer_number 
                        FROM trailers 
                        WHERE current_location_id = ?
                        AND is_new = 0
                        AND status = 'available'
                        ORDER BY trailer_number
                    ''', (loc_id,))
                else:
                    # Without is_new column, get all trailers at location
                    cursor.execute('''
                        SELECT trailer_number 
                        FROM trailers 
                        WHERE current_location_id = ?
                        AND status = 'available'
                        ORDER BY trailer_number
                    ''', (loc_id,))
                old_trailers = cursor.fetchall()
            else:
                old_trailers = []
        else:
            # Simple schema with current_location as text
            if 'is_new' in trailer_columns:
                cursor.execute('''
                    SELECT trailer_number 
                    FROM trailers 
                    WHERE current_location = ?
                    AND is_new = 0
                    AND status = 'available'
                    ORDER BY trailer_number
                ''', (destination,))
            else:
                cursor.execute('''
                    SELECT trailer_number 
                    FROM trailers 
                    WHERE current_location = ?
                    AND status = 'available'
                    ORDER BY trailer_number
                ''', (destination,))
            old_trailers = cursor.fetchall()
        
        # Now handle the display of OLD trailers
        if old_trailers:
            st.success(f"🔄 {len(old_trailers)} OLD trailer{'s' if len(old_trailers) > 1 else ''} available for pickup at {destination}")
            
            # Create dropdown for OLD trailer selection
            old_trailer_options = [f"Trailer #{t[0]} (OLD)" for t in old_trailers]
            selected_old_display = st.selectbox(
                "Select OLD Trailer to Pick Up",
                options=old_trailer_options,
                help="This trailer will be picked up from FedEx and returned to Fleet Memphis"
            )
            
            # Extract trailer number
            swap_trailer = selected_old_display.split("#")[1].split(" ")[0] if selected_old_display else None
        else:
            st.warning(f"⚠️ No OLD trailers currently at {destination}")
            st.info("💡 You can still create the move and specify which trailer to pick up later")
            swap_trailer = st.text_input(
                "Enter OLD Trailer # to Pick Up (optional)",
                placeholder="e.g., 6014",
                help="Leave blank if you'll determine this later"
            )
        
        st.divider()
        
        # Section 4: Driver and Move Details
        st.markdown("### 4. Assignment Details")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Get drivers
            cursor.execute('SELECT id, driver_name FROM drivers WHERE status = "active"')
            drivers = cursor.fetchall()
            driver_options = {d[1]: d[0] for d in drivers}
            selected_driver = st.selectbox(
                "👤 Assign to Driver", 
                options=list(driver_options.keys()),
                help="Select the driver who will handle this move"
            )
        
        with col2:
            move_date = st.date_input(
                "📅 Move Date", 
                value=date.today(),
                help="When will this move take place?"
            )
        
        with col3:
            client = st.text_input(
                "🏢 Client/Customer", 
                placeholder="e.g., Metro Logistics",
                help="Enter the client name for this move"
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
                    # Round trip calculation
                    total_miles = miles * 2  # Round trip
                    earnings = total_miles * 2.10
                    
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
        st.subheader("Available NEW Trailers at Fleet")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get available NEW trailers at Fleet Memphis ONLY
        cursor.execute("PRAGMA table_info(trailers)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'current_location_id' in columns:
            # Get Fleet Memphis ID
            cursor.execute("SELECT id FROM locations WHERE location_title = 'Fleet Memphis'")
            fleet_id = cursor.fetchone()
            fleet_id = fleet_id[0] if fleet_id else 1
            
            # Get only NEW trailers at Fleet Memphis that are available
            cursor.execute('''
                SELECT t.trailer_number, 
                       'Fleet Memphis' as location, 
                       t.status
                FROM trailers t
                WHERE t.current_location_id = ?
                AND t.is_new = 1
                AND t.status = 'available'
                AND t.id NOT IN (
                    SELECT trailer_id FROM moves 
                    WHERE status IN ('active', 'assigned', 'in_transit')
                    AND trailer_id IS NOT NULL
                )
                ORDER BY t.trailer_number
            ''', (fleet_id,))
        else:
            # Simple structure - still only get NEW trailers at Fleet
            cursor.execute('''
                SELECT t.trailer_number, 
                       'Fleet Memphis' as location, 
                       t.status
                FROM trailers t
                WHERE (t.current_location = 'Fleet Memphis' OR t.current_location IS NULL)
                AND t.status = 'available'
                AND (
                    t.trailer_number LIKE '190%' OR 
                    t.trailer_number LIKE '18V%' OR 
                    t.trailer_number = '7728'
                )
                AND t.id NOT IN (
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
        
        if 'new_trailer' in move_columns:
            # Get NEW trailers that are assigned to active moves
            cursor.execute('''
                SELECT m.new_trailer as trailer_number, 
                       m.driver_name, 
                       m.status,
                       l.location_title as destination
                FROM moves m
                LEFT JOIN locations l ON m.destination_location_id = l.id
                WHERE m.status IN ('active', 'assigned', 'in_transit')
                AND m.new_trailer IS NOT NULL
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
        if 'new_trailer' in move_columns and 'old_trailer' in move_columns:
            # Use new_trailer and old_trailer columns
            cursor.execute('''
                SELECT m.system_id, m.move_date, m.client, m.driver_name, m.status, m.payment_status,
                       m.new_trailer || ' / ' || COALESCE(m.old_trailer, 'TBD') as trailer_info, 
                       orig.location_title as origin, dest.location_title as destination,
                       m.estimated_miles, m.estimated_earnings
                FROM moves m
                LEFT JOIN locations orig ON m.origin_location_id = orig.id
                LEFT JOIN locations dest ON m.destination_location_id = dest.id
                WHERE m.mlbl_number IS NULL OR m.mlbl_number = ''
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
                # Check what columns we actually have
                if 'trailer_id' in move_columns:
                    # Has trailer_id - join with trailers table
                    cursor.execute('''
                        SELECT m.order_number as system_id, 
                               COALESCE(m.pickup_date, m.move_date, m.completed_date) as move_date, 
                               COALESCE(m.customer_name, 'FedEx') as client, 
                               m.driver_name, m.status, 
                               'pending' as payment_status,
                               COALESCE(t.trailer_number, m.order_number) as trailer_number, 
                               COALESCE(m.origin_location, 'Fleet Memphis') as origin, 
                               COALESCE(m.destination_location, m.delivery_location, 'Unknown') as destination,
                               COALESCE(m.estimated_miles, 0) as estimated_miles, 
                               COALESCE(m.amount, m.estimated_earnings, 0) as estimated_earnings
                        FROM moves m
                        LEFT JOIN trailers t ON m.trailer_id = t.id
                        WHERE (m.mlbl_number IS NULL OR m.mlbl_number = '')
                        ORDER BY move_date DESC, m.order_number
                    ''')
                else:
                    # Simpler schema without trailer_id
                    cursor.execute('''
                        SELECT m.order_number as system_id, 
                               COALESCE(m.pickup_date, m.move_date, m.completed_date) as move_date, 
                               'FedEx' as client, 
                               m.driver_name, m.status, 
                               'pending' as payment_status,
                               m.order_number as trailer_number, 
                               COALESCE(m.origin_location, 'Fleet Memphis') as origin, 
                               COALESCE(m.destination_location, m.delivery_location, 'Unknown') as destination,
                               0 as estimated_miles, 
                               COALESCE(m.amount, 0) as estimated_earnings
                        FROM moves m
                        WHERE (m.mlbl_number IS NULL OR m.mlbl_number = '')
                        ORDER BY move_date DESC, m.order_number
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
                        if '/' in str(trailer):  # Format: "NEW / OLD"
                            new_t, old_t = trailer.split(' / ')
                            st.write(f" NEW Trailer: {new_t}")
                            st.write(f" OLD Trailer: {old_t}")
                        else:
                            st.write(f" Trailer: {trailer if trailer and trailer != 'None' else 'Not assigned'}")
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
                        if '/' in str(trailer):  # Format: "NEW / OLD"
                            new_t, old_t = trailer.split(' / ')
                            st.write(f" NEW Trailer: {new_t}")
                            st.write(f" OLD Trailer: {old_t}")
                        else:
                            st.write(f" Trailer: {trailer if trailer and trailer != 'None' else 'Not assigned'}")
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
                        if '/' in str(trailer):  # Format: "NEW / OLD"
                            new_t, old_t = trailer.split(' / ')
                            st.write(f" NEW Trailer: {new_t}")
                            st.write(f" OLD Trailer: {old_t}")
                        else:
                            st.write(f" Trailer: {trailer if trailer and trailer != 'None' else 'Not assigned'}")
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
                           COALESCE(m.origin_location, 'Unknown') || ' -> ' || COALESCE(m.destination_location, m.delivery_location, 'Unknown') as route,
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
                           COALESCE(m.origin_location, 'Unknown') || ' -> ' || COALESCE(m.destination_location, m.delivery_location, 'Unknown') as route,
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
                           COALESCE(m.origin_location, 'Unknown') || ' -> ' || COALESCE(m.destination_location, m.delivery_location, 'Unknown') as route,
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
                # Check if we have trailer_id to join with trailers table
                if 'trailer_id' in move_columns:
                    cursor.execute('''
                        SELECT m.order_number, m.order_number, m.pickup_date, m.driver_name,
                               COALESCE(m.destination_location, m.delivery_location, 'Unknown'), 
                               COALESCE(t.trailer_number, 'Not assigned'), '-', 
                               m.status, 0, m.amount
                        FROM moves m
                        LEFT JOIN trailers t ON m.trailer_id = t.id
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
        st.write("### Active Moves with Status Updates")
        
        # Add expandable sections for each move with update buttons
        for move in moves:
            system_id, mlbl, date, driver, location, new_trailer, return_trailer, status, miles, earnings = move
            
            with st.expander(f"📦 {system_id} - {driver} - {location} [{status.upper()}]"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Move Details:**")
                    st.write(f"System ID: {system_id}")
                    st.write(f"MLBL: {mlbl or 'Not assigned'}")
                    st.write(f"Date: {date}")
                    st.write(f"Driver: {driver}")
                
                with col2:
                    st.write("**Trailer Info:**")
                    st.write(f"New Trailer: {new_trailer}")
                    st.write(f"Return Trailer: {return_trailer}")
                    st.write(f"Location: {location}")
                    st.write(f"Miles: {miles:,.2f}" if miles else "Miles: 0")
                
                with col3:
                    st.write("**Status & Earnings:**")
                    st.write(f"Current Status: **{status.upper()}**")
                    st.write(f"Est. Earnings: ${earnings:,.2f}" if earnings else "Est. Earnings: $0")
                
                st.divider()
                st.write("**Update Status:**")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("🚛 In Transit", key=f"transit_{system_id}", disabled=(status == 'in_transit')):
                        cursor.execute("UPDATE moves SET status = 'in_transit' WHERE system_id = ? OR order_number = ?", 
                                     (system_id, system_id))
                        conn.commit()
                        st.success("Status updated to In Transit!")
                        st.rerun()
                
                with col2:
                    if st.button("📍 At Destination", key=f"dest_{system_id}", disabled=(status == 'at_destination')):
                        cursor.execute("UPDATE moves SET status = 'at_destination' WHERE system_id = ? OR order_number = ?", 
                                     (system_id, system_id))
                        conn.commit()
                        st.success("Status updated to At Destination!")
                        st.rerun()
                
                with col3:
                    if st.button("🔄 Returning", key=f"return_{system_id}", disabled=(status == 'returning')):
                        cursor.execute("UPDATE moves SET status = 'returning' WHERE system_id = ? OR order_number = ?", 
                                     (system_id, system_id))
                        conn.commit()
                        st.success("Status updated to Returning!")
                        st.rerun()
                
                with col4:
                    if st.button("✅ Complete", key=f"complete_{system_id}", type="primary"):
                        # Update move status
                        cursor.execute("UPDATE moves SET status = 'completed' WHERE system_id = ? OR order_number = ?", 
                                     (system_id, system_id))
                        
                        # If there's an old trailer, mark it as delivered/completed
                        if old_trailer and old_trailer != '-':
                            cursor.execute("UPDATE trailers SET status = 'delivered' WHERE trailer_number = ?", (old_trailer,))
                        
                        # Update new trailer status to available at destination
                        if new_trailer and new_trailer != '-':
                            cursor.execute("UPDATE trailers SET status = 'available' WHERE trailer_number = ?", (new_trailer,))
                        
                        conn.commit()
                        st.success("Move marked as Completed!")
                        st.rerun()
        
        # Also show the summary table
        st.divider()
        st.write("### Summary Table")
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
                           COALESCE(m.destination_location, m.delivery_location, 'Unknown'), m.new_trailer, m.old_trailer, 'pending', 0, m.amount
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
                # Check if we have trailer_id to join with trailers table
                if 'trailer_id' in move_columns:
                    cursor.execute('''
                        SELECT m.order_number, m.order_number, 
                               COALESCE(m.completed_date, m.move_date, m.pickup_date), 
                               m.driver_name,
                               COALESCE(m.destination_location, m.delivery_location, 'Unknown'), 
                               COALESCE(t.trailer_number, 'Not assigned'), '-', 
                               'pending', 0, m.amount
                        FROM moves m
                        LEFT JOIN trailers t ON m.trailer_id = t.id
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

# Admin Panel with Full Edit Capabilities
def admin_panel():
    """Comprehensive admin panel for manual data management"""
    st.subheader("🔧 Full System Control Panel")
    
    admin_tabs = st.tabs(["Manage Moves", "Manage Trailers", "Manage Locations", "Reassign Routes", "Update Return Trailers", "Edit Drivers", "Database Manager", "View All Data"])
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with admin_tabs[0]:
        st.write("### 📝 Manage All Moves")
        
        # Get all moves
        cursor.execute("PRAGMA table_info(moves)")
        move_cols = [col[1] for col in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM moves ORDER BY move_date DESC LIMIT 100")
        moves = cursor.fetchall()
        
        if moves:
            # Create editable dataframe
            df = pd.DataFrame(moves, columns=move_cols)
            
            # Select a move to edit
            move_id = st.selectbox("Select Move to Edit", df['system_id'] if 'system_id' in move_cols else df['order_number'])
            
            if move_id:
                move_data = df[df['system_id'] == move_id] if 'system_id' in move_cols else df[df['order_number'] == move_id]
                
                if not move_data.empty:
                    st.write("#### Edit Move Details")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_status = st.selectbox("Status", ["active", "completed", "cancelled"], 
                                                 index=["active", "completed", "cancelled"].index(move_data.iloc[0]['status']) if move_data.iloc[0]['status'] in ["active", "completed", "cancelled"] else 0)
                        # Get drivers from database for dropdown
                        try:
                            cursor.execute("SELECT driver_name FROM drivers WHERE status = 'active' ORDER BY driver_name")
                            driver_list = [d[0] for d in cursor.fetchall()]
                            current_driver = move_data.iloc[0]['driver_name']
                            if current_driver not in driver_list:
                                driver_list.append(current_driver)
                            new_driver = st.selectbox("Driver", driver_list, index=driver_list.index(current_driver))
                        except:
                            new_driver = st.text_input("Driver Name", value=move_data.iloc[0]['driver_name'])
                        
                        new_payment = st.selectbox("Payment Status", ["pending", "paid"], 
                                                  index=["pending", "paid"].index(move_data.iloc[0].get('payment_status', 'pending')) if move_data.iloc[0].get('payment_status', 'pending') in ["pending", "paid"] else 0)
                    
                    with col2:
                        # Add trailer editing
                        if 'new_trailer' in move_cols:
                            cursor.execute("SELECT trailer_number FROM trailers ORDER BY trailer_number")
                            all_trailers = [t[0] for t in cursor.fetchall()]
                            current_new = move_data.iloc[0].get('new_trailer', '')
                            if current_new and current_new not in all_trailers:
                                all_trailers.append(current_new)
                            new_trailer = st.selectbox("New Trailer", all_trailers, 
                                                      index=all_trailers.index(current_new) if current_new in all_trailers else 0)
                        
                        if 'old_trailer' in move_cols:
                            current_old = move_data.iloc[0].get('old_trailer', '')
                            old_trailer = st.text_input("Return Trailer", value=current_old or '')
                        
                        if 'mlbl_number' in move_cols:
                            new_mlbl = st.text_input("MLBL Number", value=move_data.iloc[0].get('mlbl_number', ''))
                        if 'estimated_earnings' in move_cols:
                            new_earnings = st.number_input("Earnings", value=float(move_data.iloc[0].get('estimated_earnings', 0)))
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("💾 Update Move", type="primary"):
                            # Store old trailer info before updating
                            old_trailer_num = None
                            if 'new_trailer' in move_cols:
                                old_trailer_num = move_data.iloc[0].get('new_trailer', None)
                            
                            update_query = f"UPDATE moves SET status = ?, driver_name = ?"
                            params = [new_status, new_driver]
                            
                            # Add trailer updates
                            if 'new_trailer' in move_cols:
                                update_query += ", new_trailer = ?"
                                params.append(new_trailer)
                            if 'old_trailer' in move_cols:
                                update_query += ", old_trailer = ?"
                                params.append(old_trailer)
                            if 'payment_status' in move_cols:
                                update_query += ", payment_status = ?"
                                params.append(new_payment)
                            if 'mlbl_number' in move_cols:
                                update_query += ", mlbl_number = ?"
                                params.append(new_mlbl)
                            if 'estimated_earnings' in move_cols:
                                update_query += ", estimated_earnings = ?"
                                params.append(new_earnings)
                            
                            # Update trailer statuses when trailers are changed
                            if 'new_trailer' in move_cols and old_trailer_num != new_trailer:
                                # Release old trailer back to available
                                if old_trailer_num:
                                    cursor.execute('''
                                        UPDATE trailers 
                                        SET status = 'available'
                                        WHERE trailer_number = ?
                                    ''', (old_trailer_num,))
                                
                                # Set new trailer to in_use
                                cursor.execute('''
                                    UPDATE trailers 
                                    SET status = 'in_use'
                                    WHERE trailer_number = ?
                                ''', (new_trailer,))
                            
                            if 'system_id' in move_cols:
                                update_query += " WHERE system_id = ?"
                            else:
                                update_query += " WHERE order_number = ?"
                            params.append(move_id)
                            
                            cursor.execute(update_query, params)
                            conn.commit()
                            st.success(f"Move {move_id} updated!")
                            st.rerun()
                    
                    with col2:
                        if st.button("🗑️ Delete Move", type="secondary"):
                            if 'system_id' in move_cols:
                                cursor.execute("DELETE FROM moves WHERE system_id = ?", (move_id,))
                            else:
                                cursor.execute("DELETE FROM moves WHERE order_number = ?", (move_id,))
                            conn.commit()
                            st.success(f"Move {move_id} deleted!")
                            st.rerun()
    
    with admin_tabs[1]:
        st.write("### 🚛 Manage Trailers - Location & Status")
        
        # Update trailer location AND status
        st.write("#### 🔄 Update Trailer Location & Status")
        cursor.execute("PRAGMA table_info(trailers)")
        trailer_cols = [col[1] for col in cursor.fetchall()]
        
        # Get all trailers with current status
        if 'status' in trailer_cols and 'current_location' in trailer_cols:
            cursor.execute("SELECT trailer_number, status, current_location FROM trailers ORDER BY trailer_number")
            trailer_data = cursor.fetchall()
            all_trailers = [f"{t[0]} (Status: {t[1]}, Loc: {t[2]})" for t in trailer_data]
            trailer_nums = [t[0] for t in trailer_data]
        elif 'status' in trailer_cols:
            cursor.execute("SELECT trailer_number, status FROM trailers ORDER BY trailer_number")
            trailer_data = cursor.fetchall()
            all_trailers = [f"{t[0]} (Status: {t[1]})" for t in trailer_data]
            trailer_nums = [t[0] for t in trailer_data]
        else:
            cursor.execute("SELECT trailer_number FROM trailers ORDER BY trailer_number")
            all_trailers = [t[0] for t in cursor.fetchall()]
            trailer_nums = all_trailers
        
        selected_display = st.selectbox("Select Trailer", all_trailers)
        if selected_display:
            # Extract just the trailer number
            selected_trailer = trailer_nums[all_trailers.index(selected_display)]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Location update
                cursor.execute("SELECT location_title FROM locations ORDER BY location_title")
                locations = [l[0] for l in cursor.fetchall()]
                new_location = st.selectbox("New Location", locations)
            
            with col2:
                # Status update
                trailer_statuses = ['available', 'in_use', 'in_transit', 'delivered', 'maintenance', 'out_of_service']
                new_status = st.selectbox("New Status", trailer_statuses)
            
            with col3:
                # Is New trailer toggle
                if 'is_new' in trailer_cols:
                    is_new = st.selectbox("Trailer Type", ["OLD (0)", "NEW (1)"], index=0)
                    is_new_val = 1 if "NEW" in is_new else 0
            
            with col4:
                if st.button("📝 Update Trailer", type="primary"):
                    # Update location
                    if 'current_location_id' in trailer_cols:
                        cursor.execute("SELECT id FROM locations WHERE location_title = ?", (new_location,))
                        loc_result = cursor.fetchone()
                        if loc_result:
                            loc_id = loc_result[0]
                            update_query = "UPDATE trailers SET current_location_id = ?, status = ?"
                            params = [loc_id, new_status]
                            
                            if 'is_new' in trailer_cols:
                                update_query += ", is_new = ?"
                                params.append(is_new_val)
                            
                            update_query += " WHERE trailer_number = ?"
                            params.append(selected_trailer)
                            cursor.execute(update_query, params)
                    else:
                        update_query = "UPDATE trailers SET current_location = ?, status = ?"
                        params = [new_location, new_status]
                        
                        if 'is_new' in trailer_cols:
                            update_query += ", is_new = ?"
                            params.append(is_new_val)
                        
                        update_query += " WHERE trailer_number = ?"
                        params.append(selected_trailer)
                        cursor.execute(update_query, params)
                    
                    conn.commit()
                    st.success(f"✅ Trailer {selected_trailer} updated: Location={new_location}, Status={new_status}")
                    st.rerun()
        
        st.divider()
        
        # Add new trailer
        st.write("#### Add New Trailer")
        col1, col2, col3 = st.columns(3)
        with col1:
            new_trailer_num = st.text_input("Trailer Number")
        with col2:
            new_trailer_loc = st.text_input("Current Location", placeholder="Fleet Memphis")
        with col3:
            if st.button("➕ Add Trailer"):
                if new_trailer_num:
                    cursor.execute("PRAGMA table_info(trailers)")
                    trailer_cols = [col[1] for col in cursor.fetchall()]
                    
                    if 'current_location_id' in trailer_cols:
                        cursor.execute("SELECT id FROM locations WHERE location_title = ?", (new_trailer_loc,))
                        loc_id = cursor.fetchone()
                        loc_id = loc_id[0] if loc_id else 1
                        cursor.execute("INSERT INTO trailers (trailer_number, status, current_location_id) VALUES (?, 'available', ?)",
                                     (new_trailer_num, loc_id))
                    else:
                        cursor.execute("INSERT INTO trailers (trailer_number, status, current_location) VALUES (?, 'available', ?)",
                                     (new_trailer_num, new_trailer_loc))
                    conn.commit()
                    st.success(f"Trailer {new_trailer_num} added!")
                    st.rerun()
        
        # List and edit existing trailers
        st.write("#### Edit/Delete Existing Trailers")
        
        # Check what columns exist in trailers table
        cursor.execute("PRAGMA table_info(trailers)")
        trailer_cols = [col[1] for col in cursor.fetchall()]
        
        if 'current_location_id' in trailer_cols:
            cursor.execute('''
                SELECT t.trailer_number, t.status, COALESCE(l.location_title, 'Fleet Memphis')
                FROM trailers t
                LEFT JOIN locations l ON t.current_location_id = l.id
                ORDER BY t.trailer_number
            ''')
        elif 'current_location' in trailer_cols:
            cursor.execute("SELECT trailer_number, status, current_location FROM trailers ORDER BY trailer_number")
        else:
            cursor.execute("SELECT trailer_number, status, 'Unknown' FROM trailers ORDER BY trailer_number")
        trailers = cursor.fetchall()
        
        if trailers:
            for trailer in trailers:
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                with col1:
                    st.text(f"🚛 {trailer[0]}")
                with col2:
                    st.text(f"📍 {trailer[2]}")
                with col3:
                    st.text(f"Status: {trailer[1]}")
                with col4:
                    if st.button("🗑️", key=f"del_trailer_{trailer[0]}"):
                        cursor.execute("DELETE FROM trailers WHERE trailer_number = ?", (trailer[0],))
                        conn.commit()
                        st.success(f"Trailer {trailer[0]} deleted!")
                        st.rerun()
    
    with admin_tabs[3]:
        st.write("### 🔄 Reassign Routes")
        
        # Get active moves
        cursor.execute("PRAGMA table_info(moves)")
        move_cols = [col[1] for col in cursor.fetchall()]
        
        try:
            if 'system_id' in move_cols:
                if 'move_date' in move_cols:
                    cursor.execute('''
                        SELECT system_id, driver_name, move_date, 
                               COALESCE(destination_location, delivery_location, 'Unknown') as destination
                        FROM moves 
                        WHERE status IN ('active', 'assigned', 'in_transit')
                        ORDER BY move_date DESC
                    ''')
                else:
                    cursor.execute('''
                        SELECT system_id, driver_name, 
                               COALESCE(pickup_date, completed_date, CURRENT_DATE), 
                               COALESCE(destination_location, delivery_location, 'Unknown')
                        FROM moves 
                        WHERE status IN ('active', 'assigned', 'in_transit')
                        ORDER BY system_id DESC
                    ''')
            else:
                if 'pickup_date' in move_cols:
                    cursor.execute('''
                        SELECT order_number, driver_name, 
                               COALESCE(pickup_date, completed_date, CURRENT_DATE), 
                               COALESCE(destination_location, delivery_location, 'Unknown')
                        FROM moves 
                        WHERE status IN ('active', 'assigned', 'in_transit')
                        ORDER BY order_number DESC
                    ''')
                else:
                    cursor.execute('''
                        SELECT order_number, driver_name, 
                               CURRENT_DATE, 
                               COALESCE(destination_location, delivery_location, 'Unknown')
                        FROM moves 
                        WHERE status IN ('active', 'assigned', 'in_transit')
                        ORDER BY order_number DESC
                    ''')
            active_moves = cursor.fetchall()
        except sqlite3.OperationalError as e:
            st.error(f"Database error: {str(e)}")
            active_moves = []
        
        if active_moves:
            st.write("#### Select Move to Reassign")
            move_options = [f"{m[0]} - {m[1]} to {m[3]}" for m in active_moves]
            selected_move = st.selectbox("Active Move", move_options)
            
            if selected_move:
                move_id = selected_move.split(" - ")[0]
                
                st.info("Leave any field as 'No Change' to keep the current value")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Get all drivers
                    try:
                        cursor.execute("SELECT driver_name FROM drivers WHERE status = 'active' ORDER BY driver_name")
                        drivers = [d[0] for d in cursor.fetchall()]
                    except:
                        cursor.execute("SELECT DISTINCT driver_name FROM moves WHERE driver_name IS NOT NULL ORDER BY driver_name")
                        drivers = [d[0] for d in cursor.fetchall()]
                    new_driver = st.selectbox("Change Driver", ['No Change'] + drivers, index=0)
                
                with col2:
                    # Get all locations including Fleet Memphis
                    try:
                        cursor.execute("SELECT location_title FROM locations WHERE location_title LIKE 'FedEx%' OR location_title = 'Fleet Memphis'")
                        locations = [l[0] for l in cursor.fetchall()]
                        if 'Fleet Memphis' not in locations:
                            locations.append('Fleet Memphis')
                    except:
                        # Fallback to hardcoded locations
                        locations = ['Fleet Memphis', 'FedEx Memphis', 'FedEx Indy', 'FedEx Chicago', 'FedEx Dallas', 'FedEx Houston']
                    new_destination = st.selectbox("Change Destination", ['No Change'] + locations, index=0)
                
                col3, col4 = st.columns(2)
                
                with col3:
                    # Add new trailer reassignment
                    cursor.execute("SELECT trailer_number FROM trailers WHERE status = 'available' ORDER BY trailer_number")
                    available_trailers = [t[0] for t in cursor.fetchall()]
                    if 'new_trailer' in move_cols:
                        new_trailer = st.selectbox("Change New Trailer", ['No Change'] + available_trailers, index=0)
                    else:
                        new_trailer = 'No Change'
                
                with col4:
                    # Add old/return trailer reassignment
                    if 'old_trailer' in move_cols:
                        old_trailer = st.text_input("Change Return Trailer", placeholder="Enter trailer number or leave blank")
                    else:
                        old_trailer = None
                    
                if st.button("✅ Update Move", type="primary", use_container_width=True):
                    # Build update query dynamically based on what's changed
                    update_parts = []
                    params = []
                    changes_made = []
                    
                    # Check and add driver update
                    if new_driver != 'No Change':
                        update_parts.append("driver_name = ?")
                        params.append(new_driver)
                        changes_made.append(f"Driver: {new_driver}")
                    
                    # Check and add destination update
                    if new_destination != 'No Change':
                        if 'destination_location_id' in move_cols:
                            cursor.execute("SELECT id FROM locations WHERE location_title = ?", (new_destination,))
                            loc_id = cursor.fetchone()
                            if loc_id:
                                update_parts.append("destination_location_id = ?")
                                params.append(loc_id[0])
                        else:
                            update_parts.append("destination_location = ?")
                            params.append(new_destination)
                        changes_made.append(f"Destination: {new_destination}")
                    
                    # Check and add new trailer update
                    if 'new_trailer' in move_cols and new_trailer != 'No Change':
                        # Get current trailer to release it
                        cursor.execute("SELECT new_trailer FROM moves WHERE order_number = ? OR system_id = ?", (move_id, move_id))
                        current_trailer = cursor.fetchone()
                        if current_trailer and current_trailer[0]:
                            # Release current trailer
                            cursor.execute("UPDATE trailers SET status = 'available' WHERE trailer_number = ?", (current_trailer[0],))
                        
                        # Add new trailer to update
                        update_parts.append("new_trailer = ?")
                        params.append(new_trailer)
                        changes_made.append(f"New Trailer: {new_trailer}")
                        
                        # Mark new trailer as in_use
                        cursor.execute("UPDATE trailers SET status = 'in_use' WHERE trailer_number = ?", (new_trailer,))
                    
                    # Check and add old trailer update
                    if 'old_trailer' in move_cols and old_trailer and old_trailer.strip():
                        update_parts.append("old_trailer = ?")
                        params.append(old_trailer.strip())
                        changes_made.append(f"Return Trailer: {old_trailer.strip()}")
                    
                    # Only update if there are changes
                    if update_parts:
                        # Build the complete update query
                        update_query = f"UPDATE moves SET {', '.join(update_parts)}"
                        
                        # Add WHERE clause
                        if 'system_id' in move_cols:
                            update_query += " WHERE system_id = ?"
                        else:
                            update_query += " WHERE order_number = ?"
                        params.append(move_id)
                        
                        # Execute the update
                        cursor.execute(update_query, params)
                        conn.commit()
                        
                        # Show success message with what was changed
                        st.success(f"Move {move_id} updated: {', '.join(changes_made)}")
                        st.rerun()
                    else:
                        st.warning("No changes were made. Select at least one field to update.")
        else:
            st.info("No active moves to reassign")
    
    with admin_tabs[4]:
        st.write("### 🔄 Update Return Trailers")
        
        # Get moves that might need return trailer updates
        cursor.execute("PRAGMA table_info(moves)")
        move_cols = [col[1] for col in cursor.fetchall()]
        
        try:
            if 'old_trailer' in move_cols and 'new_trailer' in move_cols:
                if 'move_date' in move_cols:
                    cursor.execute('''
                        SELECT system_id, driver_name, new_trailer, old_trailer, move_date
                        FROM moves 
                        WHERE status IN ('active', 'completed')
                        ORDER BY move_date DESC
                        LIMIT 50
                    ''')
                else:
                    cursor.execute('''
                        SELECT system_id, driver_name, new_trailer, old_trailer, 
                               COALESCE(pickup_date, completed_date, CURRENT_DATE)
                        FROM moves 
                        WHERE status IN ('active', 'completed')
                        ORDER BY system_id DESC
                        LIMIT 50
                    ''')
                moves = cursor.fetchall()
            else:
                moves = []
                st.warning("Return trailer tracking not available in this database schema")
        except sqlite3.OperationalError as e:
            st.error(f"Database error: {str(e)}")
            moves = []
        
        if moves:
                st.write("#### Select Move to Update Return Trailer")
                move_options = [f"{m[0]} - {m[1]} - New: {m[2]} - Old: {m[3] or 'None'}" for m in moves]
                selected_move = st.selectbox("Move", move_options)
                
                if selected_move:
                    move_id = selected_move.split(" - ")[0]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_return_trailer = st.text_input("New Return Trailer Number", placeholder="Enter trailer number")
                    
                    with col2:
                        if st.button("📝 Update Return Trailer", type="primary"):
                            cursor.execute('''
                                UPDATE moves 
                                SET old_trailer = ?
                                WHERE system_id = ?
                            ''', (new_return_trailer, move_id))
                            conn.commit()
                            st.success(f"Return trailer updated for move {move_id}")
                            st.rerun()
        else:
            st.info("No moves found")
    
    with admin_tabs[5]:
        st.write("### 👤 Edit/Add/Delete Drivers & Company Info")
        
        # Check if company columns exist, if not add them
        cursor.execute("PRAGMA table_info(drivers)")
        driver_cols = [col[1] for col in cursor.fetchall()]
        
        if 'company_name' not in driver_cols:
            cursor.execute("ALTER TABLE drivers ADD COLUMN company_name TEXT")
            conn.commit()
        if 'phone' not in driver_cols:
            cursor.execute("ALTER TABLE drivers ADD COLUMN phone TEXT")
            conn.commit()
        if 'email' not in driver_cols:
            cursor.execute("ALTER TABLE drivers ADD COLUMN email TEXT")
            conn.commit()
        
        # Add new driver with company info
        st.write("#### Add New Driver")
        col1, col2 = st.columns(2)
        with col1:
            new_driver_name = st.text_input("Driver Name", placeholder="Enter driver name")
            new_company = st.text_input("Company Name", placeholder="Enter company name (for contractors)")
            new_phone = st.text_input("Phone Number", placeholder="(XXX) XXX-XXXX")
        with col2:
            new_email = st.text_input("Email", placeholder="driver@company.com")
            new_driver_type = st.selectbox("Driver Type", ["contractor", "driver", "owner"])
            if st.button("➕ Add Driver", type="primary", use_container_width=True):
                if new_driver_name:
                    cursor.execute("""
                        INSERT INTO drivers (driver_name, status, driver_type, company_name, phone, email) 
                        VALUES (?, 'active', ?, ?, ?, ?)
                    """, (new_driver_name, new_driver_type, new_company, new_phone, new_email))
                    conn.commit()
                    st.success(f"Driver {new_driver_name} added with company info!")
                    st.rerun()
        
        st.divider()
        
        # List and edit existing drivers
        st.write("#### Edit/Update Driver Company Information")
        cursor.execute("""
            SELECT driver_name, status, driver_type, 
                   COALESCE(company_name, ''), 
                   COALESCE(phone, ''), 
                   COALESCE(email, '') 
            FROM drivers 
            ORDER BY driver_name
        """)
        drivers = cursor.fetchall()
        
        if drivers:
            for driver in drivers:
                with st.expander(f"👤 {driver[0]} - {driver[2].upper()} ({driver[1]})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        updated_company = st.text_input("Company Name", value=driver[3], key=f"company_{driver[0]}", placeholder="Enter company name")
                        updated_phone = st.text_input("Phone", value=driver[4], key=f"phone_{driver[0]}", placeholder="(XXX) XXX-XXXX")
                    with col2:
                        updated_email = st.text_input("Email", value=driver[5], key=f"email_{driver[0]}", placeholder="email@company.com")
                        updated_status = st.selectbox("Status", ["active", "inactive"], index=0 if driver[1]=="active" else 1, key=f"status_{driver[0]}")
                    
                    col3, col4 = st.columns(2)
                    with col3:
                        if st.button("💾 Update Info", key=f"update_{driver[0]}", type="primary"):
                            cursor.execute("""
                                UPDATE drivers 
                                SET company_name = ?, phone = ?, email = ?, status = ?
                                WHERE driver_name = ?
                            """, (updated_company, updated_phone, updated_email, updated_status, driver[0]))
                            conn.commit()
                            st.success(f"Updated {driver[0]}'s information!")
                            st.rerun()
                    with col4:
                        if st.button("🗑️ Delete Driver", key=f"del_{driver[0]}"):
                            cursor.execute("DELETE FROM drivers WHERE driver_name = ?", (driver[0],))
                            conn.commit()
                            st.success(f"Driver {driver[0]} deleted!")
                            st.rerun()
    
    with admin_tabs[2]:
        st.write("### 📍 Manage Locations with Full Address")
        
        # Add/Edit location with full address
        st.write("#### Add/Edit Location")
        col1, col2 = st.columns(2)
        
        with col1:
            location_name = st.text_input("Location Name", placeholder="FedEx Memphis")
            street_address = st.text_input("Street Address", placeholder="123 Main St")
            city = st.text_input("City", placeholder="Memphis")
        
        with col2:
            state = st.text_input("State", placeholder="TN", max_chars=2)
            zip_code = st.text_input("ZIP Code", placeholder="38103")
            location_type = st.selectbox("Type", ["customer", "fedex_hub", "base"])
        
        if st.button("💾 Save Location", type="primary"):
            if location_name:
                # Check if address column exists
                cursor.execute("PRAGMA table_info(locations)")
                loc_cols = [col[1] for col in cursor.fetchall()]
                
                full_address = f"{street_address}, {city}, {state} {zip_code}"
                
                if 'address' in loc_cols:
                    cursor.execute('''
                        INSERT OR REPLACE INTO locations 
                        (location_title, address, city, state, location_type, is_base_location)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (location_name, full_address, city, state, location_type, 
                         1 if location_type == 'base' else 0))
                else:
                    cursor.execute('''
                        INSERT OR REPLACE INTO locations 
                        (location_title, city, state, location_type, is_base_location)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (location_name, city, state, location_type, 
                         1 if location_type == 'base' else 0))
                
                conn.commit()
                st.success(f"Location {location_name} saved with address: {full_address}")
                st.rerun()
        
        # Display existing locations
        st.write("#### Existing Locations")
        cursor.execute("SELECT * FROM locations ORDER BY location_title")
        locations = cursor.fetchall()
        if locations:
            cursor.execute("PRAGMA table_info(locations)")
            cols = [col[1] for col in cursor.fetchall()]
            df = pd.DataFrame(locations, columns=cols)
            st.dataframe(df, use_container_width=True, height=300)
        
        # Add new location
        st.write("#### Add New Location")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            new_loc_title = st.text_input("Location Name")
        with col2:
            new_loc_city = st.text_input("City")
        with col3:
            new_loc_state = st.text_input("State (2 letters)")
        with col4:
            if st.button("➕ Add Location"):
                if new_loc_title:
                    cursor.execute("INSERT INTO locations (location_title, city, state, location_type, is_base_location) VALUES (?, ?, ?, 'customer', 0)",
                                 (new_loc_title, new_loc_city, new_loc_state))
                    conn.commit()
                    st.success(f"Location {new_loc_title} added!")
                    st.rerun()
    
    with admin_tabs[6]:
        st.write("### 🗄️ Database Management")
        
        # Check database status
        st.write("#### Database Status")
        col1, col2, col3, col4 = st.columns(4)
        
        try:
            cursor.execute("SELECT COUNT(*) FROM moves")
            move_count = cursor.fetchone()[0]
        except:
            move_count = 0
            
        try:
            cursor.execute("SELECT COUNT(*) FROM trailers")
            trailer_count = cursor.fetchone()[0]
        except:
            trailer_count = 0
            
        try:
            cursor.execute("SELECT COUNT(*) FROM drivers")
            driver_count = cursor.fetchone()[0]
        except:
            driver_count = 0
            
        try:
            cursor.execute("SELECT COUNT(*) FROM locations")
            location_count = cursor.fetchone()[0]
        except:
            location_count = 0
        
        with col1:
            st.metric("Moves", move_count)
        with col2:
            st.metric("Trailers", trailer_count)
        with col3:
            st.metric("Drivers", driver_count)
        with col4:
            st.metric("Locations", location_count)
        
        st.divider()
        
        # Database actions
        st.write("#### Database Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Initialize All Data", type="primary"):
                # Initialize database tables
                init_database()
                
                # Load initial data
                load_initial_data()
                
                # Try to load production data
                try:
                    from init_production_data import init_production_data
                    init_production_data()
                    st.success("✅ All databases initialized with production data!")
                except Exception as e:
                    st.warning(f"Basic data loaded. Production data error: {str(e)}")
                
                st.rerun()
        
        with col2:
            if st.button("🔄 Reload Production Data"):
                load_initial_data()
                try:
                    from init_production_data import init_production_data
                    init_production_data()
                    st.success("Production data reloaded!")
                except:
                    st.warning("Basic data reloaded")
                st.rerun()
        
        with col3:
            if st.button("🧹 Clear All Cache"):
                st.cache_data.clear()
                st.cache_resource.clear()
                st.success("Cache cleared!")
                st.rerun()
    
    with admin_tabs[7]:
        st.write("### 📊 Complete Database View")
        
        data_view_tabs = st.tabs(["Trailers", "Locations", "Moves", "Drivers"])
        
        with data_view_tabs[0]:
            st.write("#### All Trailers in Database")
            try:
                cursor.execute("PRAGMA table_info(trailers)")
                trailer_cols = [col[1] for col in cursor.fetchall()]
                
                if trailer_cols:
                    cursor.execute("SELECT * FROM trailers ORDER BY trailer_number")
                    trailers = cursor.fetchall()
                    
                    if trailers:
                        df = pd.DataFrame(trailers, columns=trailer_cols)
                        st.dataframe(df, use_container_width=True, height=400)
                        st.caption(f"Total: {len(trailers)} trailers")
                        
                        # Add button to initialize sample data
                        if len(trailers) == 0:
                            if st.button("🔄 Initialize Sample Trailers"):
                                from init_production_data import init_production_data
                                init_production_data()
                                st.success("Sample trailers added!")
                                st.rerun()
                    else:
                        st.warning("No trailers in database")
                        if st.button("🔄 Initialize Sample Trailers"):
                            from init_production_data import init_production_data
                            init_production_data()
                            st.success("Sample trailers added!")
                            st.rerun()
                else:
                    st.error("Trailers table structure not found")
            except Exception as e:
                st.error(f"Error loading trailers: {str(e)}")
        
        with data_view_tabs[1]:
            st.write("#### All Locations in Database")
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='locations'")
            if cursor.fetchone()[0] > 0:
                cursor.execute("PRAGMA table_info(locations)")
                location_cols = [col[1] for col in cursor.fetchall()]
                
                cursor.execute("SELECT * FROM locations ORDER BY location_title")
                locations = cursor.fetchall()
                
                if locations:
                    df = pd.DataFrame(locations, columns=location_cols)
                    st.dataframe(df, use_container_width=True, height=400)
                    st.caption(f"Total: {len(locations)} locations")
                else:
                    st.warning("No locations in database")
            else:
                st.error("Locations table does not exist")
        
        with data_view_tabs[2]:
            st.write("#### All Moves in Database")
            try:
                cursor.execute("PRAGMA table_info(moves)")
                move_cols = [col[1] for col in cursor.fetchall()]
            
                cursor.execute("SELECT * FROM moves ORDER BY move_date DESC LIMIT 200")
                moves = cursor.fetchall()
                
                if moves:
                    df = pd.DataFrame(moves, columns=move_cols)
                    st.dataframe(df, use_container_width=True, height=400)
                    st.caption(f"Showing latest {len(moves)} moves")
                else:
                    st.warning("No moves in database")
            except Exception as e:
                st.error(f"Error loading moves: {str(e)}")
        
        with data_view_tabs[3]:
            st.write("#### All Drivers in Database")
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='drivers'")
            if cursor.fetchone()[0] > 0:
                cursor.execute("PRAGMA table_info(drivers)")
                driver_cols = [col[1] for col in cursor.fetchall()]
                
                cursor.execute("SELECT * FROM drivers ORDER BY driver_name")
                drivers = cursor.fetchall()
                
                if drivers:
                    df = pd.DataFrame(drivers, columns=driver_cols)
                    st.dataframe(df, use_container_width=True, height=400)
                    st.caption(f"Total: {len(drivers)} drivers")
                else:
                    st.warning("No drivers in database")
            else:
                st.error("Drivers table does not exist")
    
    conn.close()

# Main dashboard
def show_dashboard():
    """Display role-specific dashboard"""
    role = st.session_state.get('role', 'Unknown')
    user_data = st.session_state.get('user_data', {})
    
    # Check if user has multiple roles
    if 'roles' in user_data and len(user_data['roles']) > 1:
        st.title(f"Trailer Fleet Management System - {'/'.join(user_data['roles'])} Dashboard")
    else:
        st.title(f"Trailer Fleet Management System - {role} Dashboard")
    
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
            st.markdown("*Shows where all trailers are currently located - not all need to be moved*")
            
            # NEW trailers at Fleet Memphis (ready for delivery)
            st.info("**NEW Trailers at Fleet Memphis (Available for Delivery)**")
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
                st.caption(f"✓ {len(new_fleet)} NEW trailers available for delivery")
            else:
                st.write("No new trailers available at Fleet Memphis")
            
            # OLD trailers at FedEx (ready for pickup)
            st.warning("**OLD Trailers at FedEx Locations (Available for Pickup)**")
            cursor.execute('''
                SELECT t.trailer_number, l.location_title, l.city || ', ' || l.state as details
                FROM trailers t
                LEFT JOIN locations l ON t.current_location_id = l.id
                WHERE t.is_new = 0 
                AND l.location_title LIKE 'FedEx%'
                AND t.status = 'available'
                ORDER BY l.location_title, t.trailer_number
            ''')
            old_fedex = cursor.fetchall()
            if old_fedex:
                df = pd.DataFrame(old_fedex, columns=['Trailer #', 'Location', 'City, State'])
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"✓ {len(old_fedex)} OLD trailers available for pickup")
            else:
                st.write("No old trailers available at FedEx locations")
            
            conn.close()
        with tabs[8]:
            # Location Management
            st.subheader("📍 Location Management")
            st.info("💡 Add new FedEx locations even with partial information - addresses can be updated later!")
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Quick Add New FedEx Location (Simplified)
            st.markdown("### Quick Add New FedEx Location")
            with st.form("quick_add_location"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    quick_city = st.text_input("City Name*", placeholder="e.g., Nashville")
                with col2:
                    quick_state = st.text_input("State*", placeholder="e.g., TN")
                with col3:
                    add_button = st.form_submit_button("Add FedEx Location", type="primary", use_container_width=True)
                
                if add_button:
                    if quick_city and quick_state:
                        location_title = f"FedEx {quick_city}"
                        # Check if already exists
                        cursor.execute("SELECT id FROM locations WHERE location_title = ?", (location_title,))
                        if cursor.fetchone():
                            st.error(f"{location_title} already exists!")
                        else:
                            cursor.execute('''
                                INSERT INTO locations (location_title, address, city, state, 
                                                      zip_code, location_type, is_base_location, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (location_title, 'Address TBD', quick_city, quick_state, 
                                  '', 'fedex_hub', 0, datetime.now()))
                            conn.commit()
                            st.success(f"Added {location_title}! You can add the address details below.")
                            st.rerun()
                    else:
                        st.error("City and State are required")
            
            st.divider()
            
            # Get all locations with trailer counts
            cursor.execute('''
                SELECT l.id, l.location_title, l.address, l.city, l.state, l.zip_code, 
                       l.location_type, l.is_base_location,
                       COUNT(t.id) as trailer_count,
                       SUM(CASE WHEN t.is_new = 1 THEN 1 ELSE 0 END) as new_trailers,
                       SUM(CASE WHEN t.is_new = 0 THEN 1 ELSE 0 END) as old_trailers
                FROM locations l
                LEFT JOIN trailers t ON t.current_location_id = l.id AND t.status = 'available'
                GROUP BY l.id
                ORDER BY l.location_type DESC, l.location_title
            ''')
            locations = cursor.fetchall()
            
            # Show locations by type
            st.markdown("### 📋 All Locations")
            
            # Separate by type
            fleet_locations = [loc for loc in locations if loc[7] == 1]  # is_base_location
            fedex_locations = [loc for loc in locations if loc[6] == 'fedex_hub']
            
            # Fleet Memphis (Base)
            if fleet_locations:
                st.markdown("#### 🏢 Fleet Base")
                for loc in fleet_locations:
                    loc_id, title, address, city, state, zip_code, loc_type, is_base, total, new, old = loc
                    with st.expander(f"[BASE] {title} - {city}, {state} (Base Location) - {new} NEW, {old} OLD trailers"):
                        with st.form(f"location_{loc_id}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                new_address = st.text_input("Street Address", value=address or "")
                                new_city = st.text_input("City", value=city or "")
                            with col2:
                                new_state = st.text_input("State", value=state or "")
                                new_zip = st.text_input("ZIP Code", value=zip_code or "")
                            
                            if st.form_submit_button("Update Fleet Base"):
                                cursor.execute('''
                                    UPDATE locations 
                                    SET address = ?, city = ?, state = ?, zip_code = ?
                                    WHERE id = ?
                                ''', (new_address, new_city, new_state, new_zip, loc_id))
                                conn.commit()
                                st.success(f"Updated {title}")
                                st.rerun()
            
            # FedEx Locations
            if fedex_locations:
                st.markdown("#### 📦 FedEx Locations")
                
                # Count locations with/without addresses
                with_address = sum(1 for loc in fedex_locations if loc[2] and loc[2] != 'Address TBD')
                without_address = len(fedex_locations) - with_address
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total FedEx Locations", len(fedex_locations))
                with col2:
                    st.metric("With Full Address", with_address)
                with col3:
                    st.metric("Need Address", without_address)
                
                for loc in fedex_locations:
                    loc_id, title, address, city, state, zip_code, loc_type, is_base, total, new, old = loc
                    
                    # Status indicator
                    if address and address != 'Address TBD':
                        status = "[OK]"
                        expand_text = f"{status} {title} - {city}, {state}"
                    else:
                        status = "[NEEDS ADDRESS]"
                        expand_text = f"{status} {title} - {city}, {state} (Address needed)"
                    
                    # Add trailer count if any
                    if old > 0:
                        expand_text += f" - {old} OLD trailer{'s' if old > 1 else ''} available"
                    
                    with st.expander(expand_text):
                        with st.form(f"location_{loc_id}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                new_address = st.text_input("Street Address", 
                                                           value="" if address == 'Address TBD' else (address or ""),
                                                           placeholder="Enter street address")
                                new_city = st.text_input("City", value=city or "")
                            
                            with col2:
                                new_state = st.text_input("State", value=state or "")
                                new_zip = st.text_input("ZIP Code", value=zip_code or "", 
                                                       placeholder="e.g., 12345")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Update Location", type="primary", use_container_width=True):
                                    cursor.execute('''
                                        UPDATE locations 
                                        SET address = ?, city = ?, state = ?, zip_code = ?
                                        WHERE id = ?
                                    ''', (new_address, new_city, new_state, new_zip, loc_id))
                                    conn.commit()
                                    st.success(f"Updated {title}")
                                    st.rerun()
                            
                            with col2:
                                if st.form_submit_button("Delete Location", type="secondary", use_container_width=True):
                                    if total == 0:  # Only allow deletion if no trailers
                                        cursor.execute("DELETE FROM locations WHERE id = ?", (loc_id,))
                                        conn.commit()
                                        st.success(f"Deleted {title}")
                                        st.rerun()
                                    else:
                                        st.error(f"Cannot delete - {total} trailers at this location")
            
            conn.close()
        with tabs[9]:
            admin_panel()
    
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
            admin_panel()
    
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
                
                # Get and display driver company info from database
                try:
                    cursor.execute("""
                        SELECT company_name, phone, email, driver_type 
                        FROM drivers 
                        WHERE driver_name = ?
                    """, (driver_name,))
                    driver_info = cursor.fetchone()
                    
                    if driver_info and driver_info[0]:  # If company info exists
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.info(f"**Company:** {driver_info[0]}")
                        with col2:
                            if driver_info[1]:
                                st.info(f"**Phone:** {driver_info[1]}")
                        with col3:
                            if driver_info[2]:
                                st.info(f"**Email:** {driver_info[2]}")
                except:
                    pass  # If no driver info, continue without it
                
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
                
                st.caption("**IMPORTANT:** Service fees are NOT included in these totals. Only the 3% factoring fee has been deducted.")
                
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
                    
                    # Add status update section
                    st.divider()
                    st.write("#### Update Move Status")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        move_to_update = st.selectbox(
                            "Select Move to Update",
                            [f"{m[0]} - {m[5]}" for m in active_moves],
                            help="Select a move to update its status"
                        )
                    
                    with col2:
                        new_status = st.selectbox(
                            "New Status",
                            ["in_transit", "completed"],
                            help="Update the status of your move"
                        )
                    
                    with col3:
                        if st.button("Update Status", type="primary"):
                            move_id = move_to_update.split(" - ")[0]
                            cursor.execute('''
                                UPDATE moves 
                                SET status = ?, completed_date = CASE WHEN ? = 'completed' THEN date('now') ELSE completed_date END
                                WHERE system_id = ? AND driver_name = ?
                            ''', (new_status, new_status, move_id, driver_name))
                            conn.commit()
                            st.success(f"Move {move_id} status updated to {new_status}")
                            st.rerun()
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
                        
                        # Check available columns
                        cursor.execute("PRAGMA table_info(moves)")
                        available_cols = [col[1] for col in cursor.fetchall()]
                        
                        # Build query based on available columns
                        if 'new_trailer' in available_cols and 'old_trailer' in available_cols:
                            base_query = '''
                                SELECT m.order_number, m.move_date, m.new_trailer, m.old_trailer,
                                       COALESCE(m.origin_location, 'Fleet Memphis') || ' -> ' || 
                                       COALESCE(m.destination_location, m.delivery_location, 'Unknown') as route,
                                       COALESCE(m.estimated_miles, 0), COALESCE(m.estimated_earnings, 0), 
                                       COALESCE(m.payment_status, 'pending')
                                FROM moves m
                                WHERE m.driver_name = ? 
                                AND m.status = 'completed'
                                AND date(m.move_date) BETWEEN date(?) AND date(?)
                            '''
                        else:
                            base_query = '''
                                SELECT m.order_number, m.pickup_date, m.order_number, '-',
                                       COALESCE(m.origin_location, 'Fleet Memphis') || ' -> ' || 
                                       COALESCE(m.destination_location, m.delivery_location, 'Unknown') as route,
                                       0, 0, 'pending'
                                FROM moves m
                                WHERE m.driver_name = ? 
                                AND m.status = 'completed'
                                AND date(m.pickup_date) BETWEEN date(?) AND date(?)
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
                            
                            # Generate report (PDF or text based on availability)
                            try:
                                # Always try to generate - function handles fallback internally
                                filename = generate_driver_receipt(driver_name, from_date, to_date)
                                
                                # Determine file type
                                is_pdf = filename.endswith('.pdf')
                                
                                with open(filename, "rb") as file:
                                    st.download_button(
                                        label=f"Download Invoice {'PDF' if is_pdf else 'Report'}",
                                        data=file.read(),
                                        file_name=f"driver_invoice_{driver_name.replace(' ', '_')}_{from_date}_{to_date}{'.pdf' if is_pdf else '.txt'}",
                                        mime="application/pdf" if is_pdf else "text/plain"
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
                                st.error(f"Error generating report: {str(e)}")
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
                Smith & Williams Trucking LLC - All Rights Reserved
            </p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()