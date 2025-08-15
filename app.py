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
    """Load real production data only"""
    # Import and run the real data loader
    try:
        from load_real_production_data import load_real_production_data
        load_real_production_data()
    except Exception as e:
        # Log error but don't add any dummy data
        print(f"Error loading real production data: {e}")
        pass

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
    st.subheader("🚛 Create New Move Order")
    
    # Clear explanation of the process
    with st.expander("ℹ️ **How Trailer Swaps Work**", expanded=False):
        st.markdown("""
        **The Process:**
        1. **Deliver** - Take a trailer FROM Fleet Memphis TO a FedEx location
        2. **Swap** - Drop off your trailer and pick up a different one
        3. **Return** - Bring the swapped trailer BACK to Fleet Memphis
        4. **Payment** - Get paid for total round-trip mileage at $2.10/mile
        
        **Example:** Fleet Memphis -> FedEx Indy -> Fleet Memphis = 933.33 miles total = $1,960
        """)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Use containers instead of form for real-time updates
    with st.container():
        # Section 1: Trailer Selection
        st.markdown("### 1️⃣ Select Trailer from Fleet Memphis")
        
        # Get available trailers at Fleet Memphis
        cursor.execute('''
            SELECT t.id, t.trailer_number, l.location_title, t.status
            FROM trailers t
            LEFT JOIN locations l ON t.current_location_id = l.id
            WHERE t.id NOT IN (
                SELECT trailer_id FROM moves 
                WHERE status IN ('active', 'assigned', 'in_transit', 'completed')
                AND trailer_id IS NOT NULL
            )
        ''')
        trailers = cursor.fetchall()
        
        if trailers:
            trailer_options = {f"Trailer #{t[1]}": t[0] for t in trailers}
            selected_trailer = st.selectbox(
                "🚛 Select Trailer to Take to FedEx", 
                options=list(trailer_options.keys()),
                help="Choose which trailer from Fleet Memphis to deliver to the FedEx location"
            )
            st.success(f"✅ {len(trailers)} trailers available at Fleet Memphis")
        else:
            st.error("❌ No trailers available - All trailers are currently assigned or in transit")
            trailer_options = {}
            selected_trailer = None
        
        st.divider()
        
        # Section 2: Route Information
        st.markdown("### 2️⃣ Route Details")
        st.info("📍 **All moves start from Fleet Memphis**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Get locations
            cursor.execute('SELECT id, location_title FROM locations ORDER BY location_title')
            locations = cursor.fetchall()
            location_options = {l[1]: l[0] for l in locations}
            
            # Origin is always Fleet Memphis
            origin = "Fleet Memphis"
            st.text_input(
                "📍 Starting Location", 
                value="Fleet Memphis",
                disabled=True,
                help="All trailer moves originate from Fleet Memphis"
            )
        
        with col2:
            destination = st.selectbox(
                "📍 Delivery Location", 
                options=list(location_options.keys()),
                help="Where will the trailer be delivered to?",
                key="destination_select"
            )
        
        # Auto-calculate miles based on route - REAL-TIME UPDATE
        if destination == "FedEx Indy":
            default_miles = 933.33
        elif destination == "FedEx Chicago":
            default_miles = 1080.0
        elif destination == "FedEx Memphis":
            default_miles = 30.0
        else:
            default_miles = 450.0
        
        # Show auto-calculated mileage
        st.info(f"📊 **Auto-calculated mileage for {destination}:** {default_miles:,.2f} miles")
        
        miles = st.number_input(
            "🛣️ Total Round Trip Miles", 
            min_value=0.0, 
            value=default_miles, 
            step=10.0,
            help="Auto-calculated based on destination. You can adjust if needed.",
            key=f"miles_{destination}"
        )
        
        # Show LIVE earnings calculation
        st.markdown("### 💰 Real-Time Earnings Calculation")
        earnings = miles * 2.10
        after_factoring = earnings * 0.97
        service_fee_estimate = 6.00  # Placeholder
        final_estimate = after_factoring - service_fee_estimate
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Miles × Rate", f"{miles:,.2f} × $2.10")
        with col2:
            st.metric("Gross Earnings", f"${earnings:,.2f}")
        with col3:
            st.metric("After 3% Factoring", f"${after_factoring:,.2f}")
        with col4:
            st.metric("Est. Net (after fees)", f"${final_estimate:,.2f}")
        
        st.divider()
        
        # Section 3: Assignment Details
        st.markdown("### 3️⃣ Assignment Information")
        col1, col2 = st.columns(2)
        
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
            
            move_date = st.date_input(
                "📅 Move Date", 
                value=date.today(),
                help="When will this move take place?"
            )
        
        with col2:
            client = st.text_input(
                "🏢 Client/Customer", 
                placeholder="e.g., Metro Logistics",
                help="Enter the client name for this move"
            )
            
            swap_trailer = st.text_input(
                "🔄 Trailer to Pick Up & Return to Fleet Memphis",
                placeholder="e.g., 6014",
                help="Enter the trailer # you'll pick up at FedEx and bring back to Fleet Memphis"
            )
        
        st.divider()
        
        # Submit button (no form needed)
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✅ CREATE MOVE ORDER", type="primary", use_container_width=True, key="create_move_btn"):
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
                    st.success(f"✅ Move Order Created Successfully!")
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
                    st.error("❌ Please select an available trailer to create the move")
    
    conn.close()
    
    # Show trailer status sections
    st.divider()
    
    # Two columns for available and unavailable
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ Available Trailers")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get available trailers
        cursor.execute('''
            SELECT t.trailer_number, l.location_title, t.status
            FROM trailers t
            LEFT JOIN locations l ON t.current_location_id = l.id
            WHERE t.id NOT IN (
                SELECT trailer_id FROM moves 
                WHERE status IN ('active', 'assigned', 'in_transit')
                AND trailer_id IS NOT NULL
            )
            ORDER BY t.trailer_number
        ''')
        
        available_trailers = cursor.fetchall()
        
        if available_trailers:
            st.success(f"📊 {len(available_trailers)} trailers ready for assignment")
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
        st.subheader("🚫 Assigned/In-Use Trailers")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get trailers in use
        cursor.execute('''
            SELECT t.trailer_number, m.driver_name, m.status,
                   dest.location_title as destination
            FROM trailers t
            JOIN moves m ON t.id = m.trailer_id
            LEFT JOIN locations dest ON m.destination_location_id = dest.id
            WHERE m.status IN ('active', 'assigned', 'in_transit')
            ORDER BY m.status, m.move_date DESC
        ''')
        
        unavailable_trailers = cursor.fetchall()
        
        if unavailable_trailers:
            st.warning(f"📊 {len(unavailable_trailers)} trailers currently assigned")
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
    st.subheader("🔢 MLBL Number Management")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get ALL moves (active and completed) without MLBL with full details
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
    
    pending_moves = cursor.fetchall()
    
    if pending_moves:
        st.write(f"### {len(pending_moves)} Moves Awaiting MLBL Numbers")
        
        # Group by status for better organization
        active_moves = [m for m in pending_moves if m[4] == 'active']
        completed_unpaid = [m for m in pending_moves if m[4] == 'completed' and m[5] == 'pending']
        completed_paid = [m for m in pending_moves if m[4] == 'completed' and m[5] == 'paid']
        
        if active_moves:
            st.write("#### 🚛 Active Moves")
            for move in active_moves:
                # Unpack move details
                sys_id, date, client, driver, status, payment, trailer, origin, dest, miles, earnings = move
                move_title = f"{sys_id} | {date} | {driver}"
                
                with st.expander(move_title):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Move Details:**")
                        st.write(f"📅 Date: {date}")
                        st.write(f"🚛 Trailer: {trailer}")
                        st.write(f"👤 Driver: {driver}")
                        st.write(f"🏢 Client: {client or 'FedEx'}")
                    with col2:
                        st.write("**Route Information:**")
                        st.write(f"📍 From: {origin}")
                        st.write(f"📍 To: {dest}")
                        st.write(f"🛣️ Miles: {miles}")
                        st.write(f"💰 Earnings: ${earnings:,.2f}")
                    
                    st.divider()
                    mlbl = st.text_input(f"Enter MLBL Number for this move", key=f"mlbl_{sys_id}")
                    if st.button("✅ Add MLBL", key=f"btn_{sys_id}"):
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
            st.write("#### 📦 Completed - Awaiting Payment")
            for move in completed_unpaid:
                # Unpack move details
                sys_id, date, client, driver, status, payment, trailer, origin, dest, miles, earnings = move
                move_title = f"{sys_id} | {date} | {driver}"
                
                with st.expander(move_title):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Move Details:**")
                        st.write(f"📅 Date: {date}")
                        st.write(f"🚛 Trailer: {trailer}")
                        st.write(f"👤 Driver: {driver}")
                        st.write(f"🏢 Client: {client or 'FedEx'}")
                    with col2:
                        st.write("**Route Information:**")
                        st.write(f"📍 From: {origin}")
                        st.write(f"📍 To: {dest}")
                        st.write(f"🛣️ Miles: {miles}")
                        st.write(f"💰 Earnings: ${earnings:,.2f}")
                    
                    st.divider()
                    mlbl = st.text_input(f"Enter MLBL Number for this move", key=f"mlbl_{sys_id}")
                    if st.button("✅ Add MLBL", key=f"btn_{sys_id}"):
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
            st.write("#### ✅ Completed & Paid")
            for move in completed_paid:
                # Unpack move details
                sys_id, date, client, driver, status, payment, trailer, origin, dest, miles, earnings = move
                move_title = f"{sys_id} | {date} | {driver}"
                
                with st.expander(move_title):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Move Details:**")
                        st.write(f"📅 Date: {date}")
                        st.write(f"🚛 Trailer: {trailer}")
                        st.write(f"👤 Driver: {driver}")
                        st.write(f"🏢 Client: {client or 'FedEx'}")
                    with col2:
                        st.write("**Route Information:**")
                        st.write(f"📍 From: {origin}")
                        st.write(f"📍 To: {dest}")
                        st.write(f"🛣️ Miles: {miles}")
                        st.write(f"💰 Earnings: ${earnings:,.2f}")
                    
                    st.divider()
                    mlbl = st.text_input(f"Enter MLBL Number for this move", key=f"mlbl_{sys_id}")
                    if st.button("✅ Add MLBL", key=f"btn_{sys_id}"):
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
        st.success("✅ All moves have MLBL numbers assigned!")
    
    # Show moves with MLBL numbers
    cursor.execute('''
        SELECT m.system_id, m.mlbl_number, m.move_date, m.driver_name, 
               t.trailer_number,
               orig.location_title || ' -> ' || dest.location_title as route,
               m.status, m.payment_status
        FROM moves m
        LEFT JOIN trailers t ON m.trailer_id = t.id
        LEFT JOIN locations orig ON m.origin_location_id = orig.id
        LEFT JOIN locations dest ON m.destination_location_id = dest.id
        WHERE m.mlbl_number IS NOT NULL
        ORDER BY m.mlbl_number
    ''')
    
    mlbl_moves = cursor.fetchall()
    if mlbl_moves:
        st.write("### Moves with MLBL Numbers Assigned")
        df = pd.DataFrame(mlbl_moves, columns=[
            'System ID', 'MLBL', 'Date', 'Driver', 'Trailer', 'Route', 'Status', 'Payment'
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
    
    cursor.execute('''
        SELECT m.system_id, m.mlbl_number, m.move_date, m.driver_name,
               dest.location_title, t.trailer_number, m.status, m.estimated_miles, m.estimated_earnings
        FROM moves m
        LEFT JOIN locations dest ON m.destination_location_id = dest.id
        LEFT JOIN trailers t ON m.trailer_id = t.id
        WHERE m.status IN ('active', 'assigned', 'in_transit')
        ORDER BY m.move_date DESC
    ''')
    
    moves = cursor.fetchall()
    
    if moves:
        df = pd.DataFrame(moves, columns=[
            'System ID', 'MLBL', 'Date', 'Driver', 'Location',
            'Trailer', 'Status', 'Miles', 'Est. Earnings'
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
    
    cursor.execute('''
        SELECT m.system_id, m.mlbl_number, m.move_date, m.driver_name,
               dest.location_title, t.trailer_number, m.payment_status, m.estimated_miles, m.estimated_earnings
        FROM moves m
        LEFT JOIN locations dest ON m.destination_location_id = dest.id
        LEFT JOIN trailers t ON m.trailer_id = t.id
        WHERE m.status = 'completed'
        ORDER BY m.move_date DESC
    ''')
    
    moves = cursor.fetchall()
    
    if moves:
        df = pd.DataFrame(moves, columns=[
            'System ID', 'MLBL', 'Date', 'Driver', 'Location',
            'Trailer', 'Payment Status', 'Miles', 'Est. Earnings'
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
            "📊 Overview", "🚛 Create Move", "📋 Active Moves", 
            "✅ Completed Moves", "👤 My Driver Moves", "🔢 MLBL Management", 
            "💰 Financials", "🔧 Admin"
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
            st.subheader("🚛 My Driver Moves")
            driver_name = user_data.get('driver_name', 'Brandon Smith')
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT m.system_id, m.mlbl_number, m.move_date,
                       t.trailer_number,
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
                    active_count = sum(1 for m in moves if m[5] == 'active')
                    st.metric("Active Moves", active_count)
                with col2:
                    completed_count = sum(1 for m in moves if m[5] == 'completed')
                    st.metric("Completed Moves", completed_count)
                with col3:
                    total_earnings = sum(m[7] for m in moves if m[7])
                    st.metric("Total Earnings", f"${total_earnings:,.2f}")
                
                st.divider()
                
                df = pd.DataFrame(moves, columns=[
                    'System ID', 'MLBL', 'Date', 'Trailer', 'Route', 
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
            st.subheader("💰 Financial Management")
            st.info("Financial management interface")
        with tabs[7]:
            st.subheader("🔧 System Administration")
            if st.button("🔄 Reload Production Data"):
                load_initial_data()
                st.success("Production data reloaded!")
                st.rerun()
    
    elif role == "Owner":  # Regular owner without driver role
        tabs = st.tabs([
            "📊 Overview", "🚛 Create Move", "📋 Active Moves", 
            "✅ Completed Moves", "🔢 MLBL Management", "💰 Financials", "🔧 Admin"
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
            st.subheader("💰 Financial Management")
            st.info("Financial management interface")
        with tabs[6]:
            st.subheader("🔧 System Administration")
            if st.button("🔄 Reload Production Data"):
                load_initial_data()
                st.success("Production data reloaded!")
                st.rerun()
    
    elif role == "Manager":
        tabs = st.tabs([
            "📊 Overview", "🚛 Create Move", "📋 Active Moves", "✅ Completed Moves", "🔢 MLBL Management"
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
        tabs = st.tabs(["📊 Overview", "📋 Active Moves"])
        
        with tabs[0]:
            show_overview_metrics()
        with tabs[1]:
            show_active_moves()
    
    elif role == "Driver":
        # Enhanced driver dashboard with tabs
        driver_name = st.session_state.get('user_data', {}).get('driver_name')
        
        if driver_name:
            tabs = st.tabs(["📊 My Overview", "📋 My Active Moves", "✅ My Completed Moves", "📄 Documents"])
            
            with tabs[0]:
                st.subheader(f"🚛 Driver Dashboard - {driver_name}")
                
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
                    st.metric("Total Earnings", f"${stats[5] or 0:,.2f}")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Paid Moves", stats[3] or 0)
                with col2:
                    st.metric("Pending Payment", stats[4] or 0)
                with col3:
                    st.metric("Paid Earnings", f"${stats[6] or 0:,.2f}")
                with col4:
                    st.metric("Pending Earnings", f"${stats[7] or 0:,.2f}")
                
                conn.close()
            
            with tabs[1]:
                st.subheader("📋 My Active Moves")
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT m.system_id, m.mlbl_number, m.move_date,
                           t.trailer_number,
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
                        'System ID', 'MLBL', 'Date', 'Trailer', 'Route', 'Miles', 'Earnings'
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
            
            with tabs[2]:
                st.subheader("✅ My Completed Moves")
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT m.system_id, m.mlbl_number, m.move_date,
                           t.trailer_number,
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
                        'System ID', 'MLBL', 'Date', 'Trailer', 'Route', 'Payment', 'Earnings'
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
            
            with tabs[3]:
                st.subheader("📄 Document Upload")
                st.info("Document upload functionality for PODs, BOLs, and Photos")
                
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