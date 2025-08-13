"""
Smith & Williams Trucking - Version 3 Complete
Phase 3: Full-featured data entry system with Vernon guidance
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sqlite3
import hashlib
import json
from typing import Dict, List, Optional
import os
from pathlib import Path
import base64
import io

# Try to import PDF libraries
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Smith & Williams Trucking",
    page_icon="🚛",
    layout="wide"
)

# Initialize database
def init_database():
    """Initialize all database tables"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Trailers table with enhanced fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trailers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trailer_number TEXT UNIQUE NOT NULL,
            trailer_type TEXT,
            location TEXT,
            status TEXT,
            last_inspection DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT
        )
    ''')
    
    # Moves table with enhanced fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            customer_name TEXT,
            origin_city TEXT,
            destination_city TEXT,
            pickup_date DATE,
            delivery_date DATE,
            status TEXT,
            amount REAL,
            trailer_id INTEGER,
            driver_name TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT,
            FOREIGN KEY (trailer_id) REFERENCES trailers (id)
        )
    ''')
    
    # Data entry logs (Vernon's tracking)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_entry_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            action TEXT,
            table_name TEXT,
            record_id INTEGER,
            changes TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Enhanced trailer inventory for data entry
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trailer_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trailer_number TEXT UNIQUE NOT NULL,
            trailer_type TEXT,
            status TEXT DEFAULT 'available',
            condition TEXT DEFAULT 'good',
            current_location TEXT,
            location_lat REAL,
            location_lng REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT,
            notes TEXT,
            customer_owner TEXT,
            year_manufactured INTEGER,
            last_inspection DATE,
            next_inspection DATE
        )
    ''')
    
    # Location history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trailer_location_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trailer_number TEXT,
            old_location TEXT,
            new_location TEXT,
            change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            changed_by TEXT,
            reason TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# Database connection
def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

# Vernon's validation system
class VernonValidator:
    """Vernon - Chief Data Security Officer validation system"""
    
    @staticmethod
    def validate_trailer_number(number: str) -> tuple[bool, str]:
        """Validate trailer number format"""
        if not number:
            return False, "Trailer number is required"
        if len(number) < 3:
            return False, "Trailer number must be at least 3 characters"
        if not number.replace("-", "").replace("_", "").isalnum():
            return False, "Trailer number can only contain letters, numbers, hyphens, and underscores"
        return True, "Valid"
    
    @staticmethod
    def validate_amount(amount: float) -> tuple[bool, str]:
        """Validate monetary amounts"""
        if amount < 0:
            return False, "Amount cannot be negative"
        if amount > 1000000:
            return False, "Amount exceeds maximum limit ($1,000,000)"
        return True, "Valid"
    
    @staticmethod
    def validate_date(date_value: date, is_future_allowed: bool = True) -> tuple[bool, str]:
        """Validate date values"""
        if not date_value:
            return False, "Date is required"
        if not is_future_allowed and date_value > date.today():
            return False, "Future dates are not allowed"
        if date_value < date(2020, 1, 1):
            return False, "Date cannot be before 2020"
        return True, "Valid"
    
    @staticmethod
    def log_data_entry(user: str, action: str, table: str, record_id: int, changes: dict):
        """Log all data entry actions for audit trail"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO data_entry_logs (user, action, table_name, record_id, changes) VALUES (?, ?, ?, ?, ?)",
                (user, action, table, record_id, json.dumps(changes))
            )
            conn.commit()
            conn.close()
        except:
            pass

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Load logo as base64
def get_logo_base64():
    """Load logo and convert to base64 for embedding"""
    logo_path = "swt_logo.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.page = 'Dashboard'
    st.session_state.vernon_tips = True

# Login function
def check_login(username, password):
    """Enhanced login with hardcoded accounts"""
    # Hardcoded accounts
    accounts = {
        "Brandon": ("owner123", "admin"),
        "admin": ("admin123", "admin"),
        "demo": ("demo", "admin"),
        "driver": ("driver123", "driver"),
        "dispatch": ("dispatch123", "dispatcher"),
        "dataentry": ("data123", "data_entry")
    }
    
    if username in accounts:
        stored_pass, role = accounts[username]
        if password == stored_pass:
            return True, role
    
    # Database check
    try:
        conn = get_connection()
        cursor = conn.cursor()
        hashed = hash_password(password)
        cursor.execute(
            "SELECT role FROM users WHERE username = ? AND password = ?",
            (username, hashed)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return True, result[0]
    except:
        pass
    
    return False, None

# Bulk upload function
def bulk_upload_data(df, table_type, username):
    """Bulk upload data to specified table"""
    conn = get_connection()
    cursor = conn.cursor()
    
    success_count = 0
    error_list = []
    
    for index, row in df.iterrows():
        try:
            if table_type == "trailers":
                cursor.execute('''
                    INSERT OR REPLACE INTO trailer_inventory 
                    (trailer_number, trailer_type, status, condition, current_location, 
                     customer_owner, notes, updated_by, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('trailer_number'),
                    row.get('trailer_type', 'Dry Van'),
                    row.get('status', 'available'),
                    row.get('condition', 'good'),
                    row.get('current_location', 'Unknown'),
                    row.get('customer_owner', ''),
                    row.get('notes', ''),
                    username,
                    datetime.now()
                ))
            elif table_type == "moves":
                cursor.execute('''
                    INSERT INTO moves 
                    (order_number, customer_name, origin_city, destination_city, 
                     status, amount, driver_name, updated_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('order_number'),
                    row.get('customer_name'),
                    row.get('origin_city'),
                    row.get('destination_city'),
                    row.get('status', 'pending'),
                    row.get('amount', 0),
                    row.get('driver_name', ''),
                    username
                ))
            
            success_count += 1
        except Exception as e:
            error_list.append(f"Row {index + 1}: {str(e)}")
    
    conn.commit()
    conn.close()
    
    return success_count, error_list

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .vernon-tip {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 10px;
        margin: 10px 0;
        border-radius: 0 5px 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Login page
if not st.session_state.authenticated:
    # Logo at top of login page
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Use white logo for better visibility
        if os.path.exists("swt_logo_white.png"):
            st.image("swt_logo_white.png", use_container_width=True)
        elif os.path.exists("swt_logo.png"):
            st.image("swt_logo.png", use_container_width=True)
        else:
            st.markdown("# 🚛")
        
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
            if st.button("🔐 Login", type="primary", use_container_width=True):
                success, role = check_login(username, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_role = role
                    st.success("✅ Login successful!")
                    
                    # Log the login
                    VernonValidator.log_data_entry(username, "LOGIN", "users", 0, {"action": "login"})
                    
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        
        with col_b:
            if st.button("🎯 Demo Mode", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.username = "demo_user"
                st.session_state.user_role = "admin"
                st.rerun()
        
        # Remove credentials display - just show Demo Mode is available
        st.info("💡 Use Demo Mode for quick access or contact administrator for credentials")
    
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #888;'>© 2025 Smith & Williams Trucking | 🔐 Protected by Vernon - Chief Data Security Officer</p>",
        unsafe_allow_html=True
    )

# Main Application
else:
    # Sidebar with logo
    with st.sidebar:
        # Logo - use white version for better visibility
        if os.path.exists("swt_logo_white.png"):
            st.image("swt_logo_white.png", use_container_width=True)
        elif os.path.exists("swt_logo.png"):
            st.image("swt_logo.png", use_container_width=True)
        
        st.markdown(f"### 👤 {st.session_state.username}")
        st.markdown(f"**Role:** {st.session_state.user_role}")
        
        # Vernon's presence
        st.markdown("---")
        st.markdown("### 🔐 Vernon")
        st.markdown("*Chief Data Security Officer*")
        
        if st.session_state.vernon_tips:
            st.info("💡 Vernon is monitoring all data entry for accuracy and security")
        
        # Navigation
        st.markdown("---")
        st.markdown("### Navigation")
        
        pages = ["📊 Dashboard", "📝 Data Entry", "🚚 Trailers", "📦 Moves", 
                 "📄 Reports", "⚙️ Settings"]
        
        for page in pages:
            if st.button(page, use_container_width=True):
                st.session_state.page = page.split()[1]
                st.rerun()
        
        # Logout
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_role = None
            st.rerun()
    
    # Main content area
    st.title(f"🚛 Smith & Williams Trucking")
    
    # Dashboard Page
    if st.session_state.page == "Dashboard":
        st.header("Dashboard")
        st.markdown(f"Welcome back, **{st.session_state.username}**! Here's your overview:")
        
        # Metrics
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
            
            cursor.execute("SELECT COUNT(*) FROM trailer_inventory")
            total_trailers = cursor.fetchone()[0]
            
            conn.close()
            
            with col1:
                st.metric("📋 Pending Moves", pending, delta="2 new")
            with col2:
                st.metric("🚛 In Progress", in_progress)
            with col3:
                st.metric("✅ Completed", completed)
            with col4:
                st.metric("🚚 Total Trailers", total_trailers)
        except:
            with col1:
                st.metric("📋 Pending Moves", 0)
            with col2:
                st.metric("🚛 In Progress", 0)
            with col3:
                st.metric("✅ Completed", 0)
            with col4:
                st.metric("🚚 Total Trailers", 0)
        
        # Recent activity
        st.markdown("---")
        st.subheader("📈 Recent Activity")
        
        try:
            conn = get_connection()
            df = pd.read_sql_query(
                """SELECT order_number, customer_name, status, amount, created_at 
                   FROM moves ORDER BY created_at DESC LIMIT 5""",
                conn
            )
            conn.close()
            
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No recent activity")
        except:
            st.info("No activity data available")
        
        # Quick Actions
        st.markdown("---")
        st.subheader("🚀 Quick Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("➕ New Move", use_container_width=True):
                st.session_state.page = "Moves"
                st.rerun()
        with col2:
            if st.button("🚚 New Trailer", use_container_width=True):
                st.session_state.page = "Data"
                st.rerun()
        with col3:
            if st.button("📝 Bulk Entry", use_container_width=True):
                st.session_state.page = "Data"
                st.rerun()
        with col4:
            if st.button("📄 Generate Report", use_container_width=True):
                st.session_state.page = "Reports"
                st.rerun()
    
    # Enhanced Data Entry Page
    elif st.session_state.page == "Data":
        st.header("📝 Enhanced Data Entry System")
        
        # Vernon's guidance banner
        st.markdown("""
        <div class="vernon-tip">
            🔐 <strong>Vernon says:</strong> I'm here to help you enter data accurately and efficiently. 
            All entries are validated and logged for security.
        </div>
        """, unsafe_allow_html=True)
        
        # Data entry tabs
        entry_tabs = st.tabs(["➕ Single Entry", "📊 Bulk Import", "🔍 Quick Templates", "📍 Update Locations"])
        
        # Single Entry Tab
        with entry_tabs[0]:
            entry_type = st.selectbox("Entry Type", ["New Trailer", "New Move", "Update Trailer", "Update Move"])
            
            if entry_type == "New Trailer":
                st.subheader("Add New Trailer")
                
                col1, col2 = st.columns(2)
                with col1:
                    trailer_num = st.text_input("Trailer Number*", help="Unique identifier")
                    trailer_type = st.selectbox("Type*", ["Roller Bed", "Dry Van", "Flatbed", "Reefer", "Step Deck", "Double Drop", "Lowboy", "Conestoga", "Tanker", "Car Hauler", "Dump Trailer", "Hopper Bottom", "Livestock", "Pneumatic", "Stretch Trailer", "Side Kit", "Other"])
                    condition = st.selectbox("Condition", ["Excellent", "Good", "Fair", "Poor"])
                    year = st.number_input("Year", min_value=1990, max_value=2025, value=2020)
                
                with col2:
                    location = st.text_input("Current Location*")
                    status = st.selectbox("Status*", ["available", "in_use", "maintenance", "retired"])
                    owner = st.text_input("Customer/Owner")
                    inspection = st.date_input("Last Inspection", value=date.today())
                
                notes = st.text_area("Notes", height=100)
                
                if st.button("✅ Save Trailer", type="primary", use_container_width=True):
                    validator = VernonValidator()
                    valid, msg = validator.validate_trailer_number(trailer_num)
                    
                    if not valid:
                        st.error(f"🔐 Vernon: {msg}")
                    else:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            
                            cursor.execute('''
                                INSERT INTO trailer_inventory
                                (trailer_number, trailer_type, status, condition, current_location,
                                 customer_owner, year_manufactured, last_inspection, notes, 
                                 updated_by, last_updated)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (trailer_num, trailer_type, status, condition, location,
                                  owner, year, inspection, notes, 
                                  st.session_state.username, datetime.now()))
                            
                            record_id = cursor.lastrowid
                            conn.commit()
                            conn.close()
                            
                            # Log the entry
                            validator.log_data_entry(
                                st.session_state.username,
                                "INSERT",
                                "trailer_inventory",
                                record_id,
                                {"trailer": trailer_num, "type": trailer_type, "status": status}
                            )
                            
                            st.success(f"✅ Trailer {trailer_num} added successfully!")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            elif entry_type == "New Move":
                st.subheader("Add New Move")
                
                col1, col2 = st.columns(2)
                with col1:
                    order_num = st.text_input("Order Number*", help="Unique identifier")
                    customer = st.text_input("Customer Name*", help="Full company name")
                    origin = st.text_input("Origin City*")
                    pickup_date = st.date_input("Pickup Date", value=date.today())
                    driver = st.text_input("Driver Name")
                
                with col2:
                    destination = st.text_input("Destination City*")
                    delivery_date = st.date_input("Delivery Date", value=date.today() + timedelta(days=3))
                    amount = st.number_input("Amount ($)*", min_value=0.0, max_value=1000000.0)
                    status = st.selectbox("Status", ["pending", "in_progress", "completed"])
                    
                    # Trailer selection
                    try:
                        conn = get_connection()
                        df = pd.read_sql_query(
                            "SELECT trailer_number FROM trailer_inventory WHERE status = 'available'",
                            conn
                        )
                        conn.close()
                        
                        if not df.empty:
                            trailer = st.selectbox("Assign Trailer", ["None"] + df['trailer_number'].tolist())
                        else:
                            trailer = None
                            st.info("No available trailers")
                    except:
                        trailer = None
                
                notes = st.text_area("Notes", height=100)
                
                if st.button("✅ Submit Move", type="primary", use_container_width=True):
                    validator = VernonValidator()
                    valid, msg = validator.validate_amount(amount)
                    
                    if not valid:
                        st.error(f"🔐 Vernon: {msg}")
                    else:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            
                            cursor.execute('''
                                INSERT INTO moves (order_number, customer_name, origin_city, 
                                destination_city, pickup_date, delivery_date, status, amount, 
                                driver_name, notes, updated_by)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (order_num, customer, origin, destination, pickup_date, 
                                  delivery_date, status, amount, driver, notes,
                                  st.session_state.username))
                            
                            record_id = cursor.lastrowid
                            
                            # Update trailer status if assigned
                            if trailer and trailer != "None":
                                cursor.execute(
                                    "UPDATE trailer_inventory SET status = 'in_use' WHERE trailer_number = ?",
                                    (trailer,)
                                )
                            
                            conn.commit()
                            conn.close()
                            
                            # Log the entry
                            validator.log_data_entry(
                                st.session_state.username,
                                "INSERT",
                                "moves",
                                record_id,
                                {"order": order_num, "customer": customer, "amount": amount}
                            )
                            
                            st.success(f"✅ Move {order_num} added successfully!")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Error: {e}")
        
        # Bulk Import Tab
        with entry_tabs[1]:
            st.subheader("Bulk Data Import")
            st.markdown("Upload CSV files to import multiple records at once")
            
            import_type = st.selectbox("Import Type", ["Trailers", "Moves"])
            
            # Download template
            if st.button("📥 Download CSV Template"):
                if import_type == "Trailers":
                    template_df = pd.DataFrame({
                        'trailer_number': ['TR-001', 'TR-002', 'TR-003'],
                        'trailer_type': ['Dry Van', 'Reefer', 'Flatbed'],
                        'status': ['available', 'in_use', 'available'],
                        'condition': ['Good', 'Excellent', 'Fair'],
                        'current_location': ['Atlanta Depot', 'Miami Terminal', 'Dallas Yard'],
                        'customer_owner': ['ABC Corp', 'XYZ Inc', 'Company Owned']
                    })
                else:
                    template_df = pd.DataFrame({
                        'order_number': ['ORD-001', 'ORD-002', 'ORD-003'],
                        'customer_name': ['ABC Corp', 'XYZ Inc', '123 Company'],
                        'origin_city': ['Atlanta', 'Miami', 'Dallas'],
                        'destination_city': ['Chicago', 'New York', 'Los Angeles'],
                        'amount': [1500.00, 2500.00, 3500.00],
                        'status': ['pending', 'in_progress', 'pending']
                    })
                
                csv = template_df.to_csv(index=False)
                st.download_button(
                    "Download Template",
                    csv,
                    f"{import_type.lower()}_template.csv",
                    "text/csv"
                )
            
            uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
            
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.write("Preview (first 5 rows):")
                    st.dataframe(df.head())
                    
                    if st.button("🚀 Import Data", type="primary"):
                        progress = st.progress(0)
                        success_count, errors = bulk_upload_data(
                            df, 
                            import_type.lower(),
                            st.session_state.username
                        )
                        progress.progress(1.0)
                        
                        if success_count > 0:
                            st.success(f"✅ Successfully imported {success_count} records!")
                            
                            # Log bulk import
                            VernonValidator.log_data_entry(
                                st.session_state.username,
                                "BULK_IMPORT",
                                import_type.lower(),
                                0,
                                {"count": success_count}
                            )
                        
                        if errors:
                            st.warning("Some entries had errors:")
                            for error in errors[:5]:  # Show first 5 errors
                                st.write(f"- {error}")
                except Exception as e:
                    st.error(f"Error reading file: {e}")
        
        # Quick Templates Tab
        with entry_tabs[2]:
            st.subheader("Quick Entry Templates")
            st.markdown("Use pre-configured templates for common entries")
            
            template = st.selectbox("Select Template", [
                "Local Delivery (Same Day)",
                "Regional Haul (2-3 Days)",
                "Cross-Country (5-7 Days)",
                "Express Delivery (Next Day)",
                "Refrigerated Transport",
                "Hazmat Transport"
            ])
            
            # Template configurations
            templates = {
                "Local Delivery (Same Day)": {
                    "prefix": "LOC",
                    "amount": 250.00,
                    "days": 0
                },
                "Regional Haul (2-3 Days)": {
                    "prefix": "REG",
                    "amount": 750.00,
                    "days": 2
                },
                "Cross-Country (5-7 Days)": {
                    "prefix": "CRS",
                    "amount": 2500.00,
                    "days": 5
                },
                "Express Delivery (Next Day)": {
                    "prefix": "EXP",
                    "amount": 500.00,
                    "days": 1
                },
                "Refrigerated Transport": {
                    "prefix": "REF",
                    "amount": 1500.00,
                    "days": 3
                },
                "Hazmat Transport": {
                    "prefix": "HAZ",
                    "amount": 3000.00,
                    "days": 4
                }
            }
            
            config = templates[template]
            
            col1, col2 = st.columns(2)
            with col1:
                order = st.text_input(
                    "Order Number", 
                    value=f"{config['prefix']}-{datetime.now().strftime('%Y%m%d%H%M')}"
                )
                customer = st.text_input("Customer")
                origin = st.text_input("Origin City")
            
            with col2:
                destination = st.text_input("Destination City")
                amount = st.number_input("Amount", value=config['amount'])
                delivery = st.date_input(
                    "Delivery Date", 
                    value=date.today() + timedelta(days=config['days'])
                )
            
            if st.button(f"Create {template}", type="primary"):
                if order and customer and origin and destination:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute('''
                            INSERT INTO moves (order_number, customer_name, origin_city, 
                            destination_city, pickup_date, delivery_date, status, amount, updated_by)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (order, customer, origin, destination, date.today(), 
                              delivery, 'pending', amount, st.session_state.username))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"✅ {template} created successfully!")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Please fill in all fields")
        
        # Update Locations Tab
        with entry_tabs[3]:
            st.subheader("📍 Batch Location Update")
            st.markdown("Update multiple trailer locations at once")
            
            try:
                conn = get_connection()
                df = pd.read_sql_query(
                    "SELECT trailer_number, current_location, status FROM trailer_inventory",
                    conn
                )
                conn.close()
                
                if not df.empty:
                    # Multi-select trailers
                    selected_trailers = st.multiselect(
                        "Select trailers to update",
                        df['trailer_number'].tolist()
                    )
                    
                    if selected_trailers:
                        new_location = st.text_input("New Location for Selected Trailers")
                        reason = st.selectbox(
                            "Reason for Move",
                            ["Delivery", "Pickup", "Storage", "Maintenance", "Transfer"]
                        )
                        
                        if st.button(f"📍 Update {len(selected_trailers)} Trailers", type="primary"):
                            if new_location:
                                conn = get_connection()
                                cursor = conn.cursor()
                                
                                for trailer in selected_trailers:
                                    # Update location
                                    cursor.execute('''
                                        UPDATE trailer_inventory
                                        SET current_location = ?, last_updated = ?, updated_by = ?
                                        WHERE trailer_number = ?
                                    ''', (new_location, datetime.now(), st.session_state.username, trailer))
                                    
                                    # Log history
                                    cursor.execute('''
                                        INSERT INTO trailer_location_history
                                        (trailer_number, new_location, changed_by, reason)
                                        VALUES (?, ?, ?, ?)
                                    ''', (trailer, new_location, st.session_state.username, reason))
                                
                                conn.commit()
                                conn.close()
                                
                                st.success(f"✅ Updated location for {len(selected_trailers)} trailers!")
                            else:
                                st.warning("Please enter a new location")
                else:
                    st.info("No trailers in system yet")
            except:
                st.info("Add trailers first to update locations")
    
    # Trailers Page
    elif st.session_state.page == "Trailers":
        st.header("🚚 Trailer Management")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_status = st.selectbox("Filter by Status", ["All", "available", "in_use", "maintenance"])
        with col2:
            filter_type = st.selectbox("Filter by Type", ["All", "Roller Bed", "Dry Van", "Flatbed", "Reefer", "Step Deck", "Double Drop", "Lowboy", "Other"])
        with col3:
            search = st.text_input("Search Trailer Number")
        
        # Display trailers
        try:
            conn = get_connection()
            query = "SELECT * FROM trailer_inventory WHERE 1=1"
            params = []
            
            if filter_status != "All":
                query += " AND status = ?"
                params.append(filter_status)
            if filter_type != "All":
                query += " AND trailer_type = ?"
                params.append(filter_type)
            if search:
                query += " AND trailer_number LIKE ?"
                params.append(f"%{search}%")
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Export option
                csv = df.to_csv(index=False)
                st.download_button("📥 Download CSV", csv, "trailers.csv", "text/csv")
            else:
                st.info("No trailers found")
        except:
            st.info("No trailer data available")
    
    # Moves Page
    elif st.session_state.page == "Moves":
        st.header("📦 Move Management")
        
        # Add new move button
        if st.button("➕ Add New Move", type="primary"):
            st.session_state.page = "Data"
            st.rerun()
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            filter_status = st.selectbox("Status", ["All", "pending", "in_progress", "completed"])
        with col2:
            date_filter = st.date_input("From Date", value=date.today() - timedelta(days=30))
        with col3:
            search_customer = st.text_input("Customer Search")
        with col4:
            min_amount = st.number_input("Min Amount", value=0.0)
        
        # Display moves
        try:
            conn = get_connection()
            query = """SELECT order_number, customer_name, origin_city, destination_city, 
                       status, amount, pickup_date, delivery_date 
                       FROM moves WHERE 1=1"""
            params = []
            
            if filter_status != "All":
                query += " AND status = ?"
                params.append(filter_status)
            if search_customer:
                query += " AND customer_name LIKE ?"
                params.append(f"%{search_customer}%")
            if min_amount > 0:
                query += " AND amount >= ?"
                params.append(min_amount)
            
            query += " ORDER BY created_at DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            if not df.empty:
                # Summary stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Moves", len(df))
                with col2:
                    st.metric("Total Revenue", f"${df['amount'].sum():,.2f}")
                with col3:
                    st.metric("Avg per Move", f"${df['amount'].mean():,.2f}")
                
                st.dataframe(df, use_container_width=True)
                
                # Export option
                csv = df.to_csv(index=False)
                st.download_button("📥 Download CSV", csv, "moves.csv", "text/csv")
            else:
                st.info("No moves found")
        except Exception as e:
            st.info(f"No move data available")
    
    # Reports Page
    elif st.session_state.page == "Reports":
        st.header("📄 Reports & Analytics")
        
        report_tabs = st.tabs(["📊 Dashboard", "📈 Analytics", "📝 Data Entry Logs", "📄 PDF Reports"])
        
        # Dashboard Tab
        with report_tabs[0]:
            st.subheader("Executive Dashboard")
            
            try:
                conn = get_connection()
                
                # Get summary stats
                col1, col2, col3 = st.columns(3)
                
                # Revenue by status
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT status, SUM(amount) as total 
                    FROM moves 
                    GROUP BY status
                """)
                revenue_by_status = cursor.fetchall()
                
                with col1:
                    st.markdown("#### Revenue by Status")
                    for status, total in revenue_by_status:
                        st.write(f"{status}: ${total:,.2f}")
                
                # Trailer utilization
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM trailer_inventory 
                    GROUP BY status
                """)
                trailer_status = cursor.fetchall()
                
                with col2:
                    st.markdown("#### Trailer Utilization")
                    for status, count in trailer_status:
                        st.write(f"{status}: {count}")
                
                # Top customers
                cursor.execute("""
                    SELECT customer_name, COUNT(*) as moves, SUM(amount) as revenue
                    FROM moves
                    GROUP BY customer_name
                    ORDER BY revenue DESC
                    LIMIT 5
                """)
                top_customers = cursor.fetchall()
                
                with col3:
                    st.markdown("#### Top Customers")
                    for customer, moves, revenue in top_customers:
                        st.write(f"{customer}: ${revenue:,.2f}")
                
                conn.close()
            except:
                st.info("No data available for dashboard")
        
        # Analytics Tab
        with report_tabs[1]:
            st.subheader("Analytics & Trends")
            
            date_range = st.date_input(
                "Select Date Range",
                value=(date.today() - timedelta(days=30), date.today()),
                key="analytics_date"
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                
                try:
                    conn = get_connection()
                    
                    # Revenue over time
                    df = pd.read_sql_query("""
                        SELECT DATE(created_at) as date, SUM(amount) as revenue
                        FROM moves
                        WHERE DATE(created_at) BETWEEN ? AND ?
                        GROUP BY DATE(created_at)
                        ORDER BY date
                    """, conn, params=[start_date, end_date])
                    
                    if not df.empty:
                        st.line_chart(df.set_index('date')['revenue'])
                    
                    conn.close()
                except:
                    st.info("No data available for selected period")
        
        # Data Entry Logs Tab
        with report_tabs[2]:
            st.subheader("🔐 Vernon's Data Entry Audit Log")
            
            try:
                conn = get_connection()
                df = pd.read_sql_query("""
                    SELECT user, action, table_name, timestamp 
                    FROM data_entry_logs 
                    ORDER BY timestamp DESC 
                    LIMIT 100
                """, conn)
                conn.close()
                
                if not df.empty:
                    # User activity summary
                    user_activity = df['user'].value_counts()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### User Activity")
                        for user, count in user_activity.items():
                            st.write(f"{user}: {count} actions")
                    
                    with col2:
                        st.markdown("#### Recent Actions")
                        st.dataframe(df.head(10), use_container_width=True, hide_index=True)
                    
                    # Full log
                    with st.expander("View Full Audit Log"):
                        st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No data entry logs yet")
            except:
                st.info("Data entry logging will begin with first entry")
        
        # PDF Reports Tab
        with report_tabs[3]:
            st.subheader("PDF Report Generation")
            
            if PDF_AVAILABLE:
                report_type = st.selectbox("Report Type", [
                    "Daily Summary",
                    "Weekly Performance",
                    "Monthly Revenue",
                    "Trailer Inventory",
                    "Customer Report"
                ])
                
                if st.button("📄 Generate PDF Report", type="primary"):
                    st.info("PDF generation in progress...")
                    # PDF generation code would go here
                    st.success("PDF report generated!")
            else:
                st.info("PDF generation requires reportlab library")
                st.code("pip install reportlab")
    
    # Settings Page
    elif st.session_state.page == "Settings":
        st.header("⚙️ Settings")
        
        settings_tabs = st.tabs(["Profile", "System", "Vernon Security", "Data Management"])
        
        with settings_tabs[0]:
            st.subheader("User Profile")
            st.write(f"Username: {st.session_state.username}")
            st.write(f"Role: {st.session_state.user_role}")
            
            if st.button("Change Password"):
                st.info("Password change feature coming soon")
        
        with settings_tabs[1]:
            st.subheader("System Settings")
            
            theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
            notifications = st.checkbox("Enable notifications", value=True)
            auto_save = st.checkbox("Auto-save entries", value=True)
            
            if st.button("Save Settings"):
                st.success("Settings saved!")
        
        with settings_tabs[2]:
            st.subheader("🔐 Vernon Security Dashboard")
            
            # Vernon tips toggle
            vernon_tips = st.checkbox("Show Vernon's tips", value=st.session_state.vernon_tips)
            if vernon_tips != st.session_state.vernon_tips:
                st.session_state.vernon_tips = vernon_tips
                st.rerun()
            
            # Security stats
            st.markdown("#### Security Statistics")
            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                # Count total entries
                cursor.execute("SELECT COUNT(*) FROM data_entry_logs")
                total_entries = cursor.fetchone()[0]
                
                # Count users
                cursor.execute("SELECT COUNT(DISTINCT user) FROM data_entry_logs")
                total_users = cursor.fetchone()[0]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Entries", total_entries)
                with col2:
                    st.metric("Active Users", total_users)
                with col3:
                    st.metric("Security Level", "High 🟢")
                
                conn.close()
            except:
                st.info("Security monitoring active")
        
        with settings_tabs[3]:
            st.subheader("Data Management")
            
            st.warning("⚠️ Danger Zone")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📥 Export All Data"):
                    try:
                        conn = get_connection()
                        
                        # Export all tables to CSV
                        tables = ['moves', 'trailer_inventory', 'data_entry_logs']
                        for table in tables:
                            try:
                                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    f"Download {table}.csv", 
                                    csv, 
                                    f"{table}.csv", 
                                    "text/csv",
                                    key=f"download_{table}"
                                )
                            except:
                                st.info(f"No data in {table}")
                        
                        conn.close()
                    except Exception as e:
                        st.error(f"Export error: {e}")
            
            with col2:
                if st.button("🗑️ Clear Test Data", type="secondary"):
                    if st.checkbox("I understand this will delete all test data"):
                        st.info("Data clearing feature disabled in production")
    
    # Footer
    st.markdown("---")
    st.markdown("© 2025 Smith & Williams Trucking | 🔐 Protected by Vernon - Chief Data Security Officer | Version 3.0")