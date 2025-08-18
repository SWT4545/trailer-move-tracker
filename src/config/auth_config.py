"""
Authentication and Access Control Configuration
"""

# User roles and their permissions
USER_ROLES = {
    'Owner': {
        'description': 'Owner - Complete system control with all permissions',
        'access': [
            'dashboard', 'trailer_management', 'add_move', 'progress_dashboard',
            'invoices', 'email_center', 'locations', 'drivers', 'mileage',
            'import_export', 'settings', 'user_management', 'financial_reports',
            'system_config', 'audit_logs', 'driver_management', 'payments',
            'reports', 'data_entry', 'vernon_cdso'
        ],
        'can_edit': True,
        'can_delete': True,
        'can_export': True,
        'view_financial': True,
        'manage_users': True,
        'override_all': True,
        'is_owner': True
    },
    'owner_driver': {
        'description': 'Owner acting as Driver - Driver interface with owner permissions',
        'access': [
            'dashboard', 'self_assign', 'my_moves', 'my_earnings', 'documents',
            'profile', 'settings', 'mobile_driver'
        ],
        'can_edit': True,
        'can_delete': True,
        'can_export': True,
        'view_financial': True,
        'is_owner': True,
        'driver_mode': True
    },
    'business_administrator': {
        'description': 'Business Administrator - Complete system control',
        'access': [
            'dashboard', 'trailer_management', 'add_move', 'progress_dashboard',
            'invoices', 'email_center', 'locations', 'drivers', 'mileage',
            'import_export', 'settings', 'user_management', 'financial_reports',
            'system_config', 'audit_logs'
        ],
        'can_edit': True,
        'can_delete': True,
        'can_export': True,
        'view_financial': True,
        'manage_users': True,
        'override_all': True
    },
    'executive': {
        'description': 'CEO/Executive - Complete system control',
        'access': [
            'dashboard', 'trailer_management', 'add_move', 'progress_dashboard',
            'invoices', 'email_center', 'locations', 'drivers', 'mileage',
            'import_export', 'settings', 'user_management', 'financial_reports',
            'system_config', 'audit_logs'
        ],
        'can_edit': True,
        'can_delete': True,
        'can_export': True,
        'view_financial': True,
        'manage_users': True,
        'override_all': True
    },
    'admin': {
        'description': 'Administrator - System management',
        'access': [
            'dashboard', 'trailer_management', 'add_move', 'progress_dashboard',
            'invoices', 'email_center', 'locations', 'drivers', 'mileage',
            'import_export', 'settings'
        ],
        'can_edit': True,
        'can_delete': True,
        'can_export': True,
        'view_financial': True
    },
    'operations_coordinator': {
        'description': 'Operations Coordinator - Strategic route planning and full operational control',
        'access': [
            'dashboard', 'trailer_management', 'add_move', 'progress_dashboard',
            'locations', 'drivers', 'mileage', 'import_export', 'email_center',
            'driver_management', 'route_optimization', 'customer_communications',
            'document_processing', 'reports_analytics'
        ],
        'can_edit': True,
        'can_delete': True,
        'can_export': True,
        'view_financial': False,
        'can_assign_drivers': True,
        'can_send_emails': True,
        'can_generate_reports': True
    },
    'operations_specialist': {
        'description': 'Operations Specialist - Data entry and viewing, supports Operations Coordinator',
        'access': [
            'dashboard', 'trailer_management', 'progress_dashboard',
            'locations', 'import_export'
        ],
        'can_edit': True,  # Limited to trailer and location data
        'can_delete': False,
        'can_export': False,
        'view_financial': False,
        'can_assign_drivers': False,
        'can_send_emails': False,
        'can_generate_reports': False,
        'data_entry_only': True
    },
    'data_entry': {
        'description': 'Data Entry Specialist - Full trailer location and data management',
        'access': [
            'trailer_data_entry', 'trailer_management', 'locations',
            'import_export', 'dashboard', 'progress_dashboard'
        ],
        'can_edit': True,
        'can_delete': False,
        'can_export': True,
        'view_financial': False,
        'can_update_trailer_status': True,
        'can_bulk_operations': True,
        'vernon_guidance': True,
        'pdf_reports': True
    },
    'driver': {
        'description': 'Driver - View assignments and upload PODs',
        'access': [
            'dashboard', 'pod_upload', 'view_assignments'
        ],
        'can_edit': False,
        'can_delete': False,
        'can_export': False,
        'view_financial': False,
        'can_upload_pod': True
    },
    'viewer': {
        'description': 'Read-only access to progress and basic info',
        'access': [
            'progress_dashboard', 'dashboard'
        ],
        'can_edit': False,
        'can_delete': False,
        'can_export': False,
        'view_financial': False
    },
    'client': {
        'description': 'Client view - progress dashboard only',
        'access': [
            'progress_dashboard'
        ],
        'can_edit': False,
        'can_delete': False,
        'can_export': False,
        'view_financial': False
    }
}

# User accounts are now stored in database
# Temporary accounts for Streamlit Cloud until database is created
USERS = {
    'brandon': {
        'password': 'owner2024',
        'role': 'Owner',
        'name': 'Brandon Smith',
        'title': 'Owner',
        'is_owner': True,
        'can_act_as_driver': True
    },
    'brandon_driver': {
        'password': 'owner2024',
        'role': 'owner_driver',
        'name': 'Brandon Smith (Driver Mode)',
        'title': 'Owner/Driver',
        'is_owner': True,
        'driver_mode': True
    },
    'j_duckett': {
        'password': 'duck123',
        'role': 'driver',
        'name': 'Justin Duckett',
        'title': 'Contract Driver',
        'company': 'L&P Solutions'
    },
    'c_strickland': {
        'password': 'strik123',
        'role': 'driver',
        'name': 'Carl Strickland',
        'title': 'Contract Driver',
        'company': 'Cross State Logistics Inc.'
    },
    'admin': {
        'password': 'admin123',
        'role': 'business_administrator', 
        'name': 'Administrator',
        'title': 'Administrator'
    }
}

# Shareable link tokens (in production, generate and store in database)
SHARE_TOKENS = {
    'progress_readonly_2024': {
        'type': 'progress_dashboard',
        'expires': '2024-12-31',
        'description': 'Read-only progress dashboard link'
    }
}

def get_user_permissions(username):
    """Get permissions for a specific user"""
    if username in USERS:
        user = USERS[username]
        role = user['role']
        if role in USER_ROLES:
            return USER_ROLES[role]
    return None

def validate_user(username, password):
    """Validate user credentials from database or fallback"""
    # Strip any whitespace from inputs
    username = username.strip() if username else ""
    password = password.strip() if password else ""
    
    # Special case for Brandon - direct check
    if username == "Brandon" and password == "owner123":
        return True
    
    # First check static USERS dictionary (for initial access)
    if username in USERS:
        if USERS[username]['password'] == password:
            return True
    
    # Check if database exists
    import os
    if not os.path.exists('trailer_tracker_streamlined.db'):
        # No database yet, use static users
        return username in USERS and USERS[username]['password'] == password
    
    # Check database for user
    try:
        import sqlite3
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        
        # Hash the provided password
        hashed_pw = hash_password(password)
        
        # Check credentials
        cursor.execute("""
            SELECT username, role, name 
            FROM users 
            WHERE user = ? AND password = ? AND active = 1
        """, (username, hashed_pw))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            # Store user info in USERS dict for session
            USERS[username] = {
                'role': user[1],
                'name': user[2],
                'password': hashed_pw  # Store hashed version
            }
            return True
        
        return False
    except Exception as e:
        print(f"Auth error: {e}")
        # Fallback to setup user if database error
        if username == 'setup' and password == 'setup123':
            return True
        return False

def validate_share_token(token):
    """Validate a shareable link token"""
    if token in SHARE_TOKENS:
        from datetime import datetime
        token_data = SHARE_TOKENS[token]
        # Check expiration
        if 'expires' in token_data:
            expires = datetime.strptime(token_data['expires'], '%Y-%m-%d')
            if datetime.now() > expires:
                return False, "Token has expired"
        return True, token_data
    return False, "Invalid token"

def can_access_page(username, page):
    """Check if user can access a specific page"""
    permissions = get_user_permissions(username)
    if permissions:
        # Map page names to permission keys
        page_mapping = {
            "📊 Dashboard": "dashboard",
            "🚛 Trailer Management": "trailer_management",
            "➕ Add New Move": "add_move",
            "📈 Progress Dashboard": "progress_dashboard",
            "💰 Updates & Invoices": "invoices",
            "✉️ Email Center": "email_center",
            "📍 Manage Locations": "locations",
            "👥 Manage Drivers": "drivers",
            "🛣️ Manage Mileage": "mileage",
            "📁 Import/Export": "import_export",
            "⚙️ Settings": "settings"
        }
        
        page_key = page_mapping.get(page, '')
        return page_key in permissions.get('access', [])
    return False

# Database-based user management functions
import sqlite3
import hashlib
import pandas as pd

def hash_password(password):
    """Hash a password for secure storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_all_users():
    """Get all users from database"""
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        query = "SELECT username, role, created_at FROM users"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Add name field if available
        for _, row in df.iterrows():
            if row['user'] in USERS:
                df.loc[df['user'] == row['user'], 'name'] = USERS[row['user']].get('name', 'N/A')
        
        return df
    except:
        # Return static users if database not available
        users_list = []
        for username, info in USERS.items():
            users_list.append({
                'user': username,
                'role': info['role'],
                'name': info.get('name', 'N/A'),
                'created_at': 'Static User'
            })
        return pd.DataFrame(users_list)

def reset_user_password(username, new_password):
    """Reset a user's password"""
    try:
        # For static users, update the dictionary
        if username in USERS:
            USERS[username]['password'] = new_password
            return True
        
        # For database users
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        
        hashed_pw = hash_password(new_password)
        cursor.execute("""
            UPDATE users 
            SET password = ? 
            WHERE user = ?
        """, (hashed_pw, username))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except:
        return False

def update_user_role(username, new_role):
    """Update a user's role"""
    try:
        # For static users
        if username in USERS:
            USERS[username]['role'] = new_role
            return True
        
        # For database users
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users 
            SET role = ? 
            WHERE user = ?
        """, (new_role, username))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except:
        return False

def create_user(username, password, role='viewer', name=None, email=None, phone=None, is_owner=False):
    """Create a new user with optional owner flag"""
    try:
        # Add to static users
        USERS[username] = {
            'password': password,
            'role': role,
            'name': name or username,
            'email': email or '',
            'phone': phone or '',
            'is_owner': is_owner
        }
        
        # Try to add to database as well
        try:
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            cursor = conn.cursor()
            
            # Create users table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    active BOOLEAN DEFAULT 1,
                    is_owner BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            hashed_pw = hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password, role, name, email, phone, is_owner)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, hashed_pw, role, name, email, phone, 1 if is_owner else 0))
            
            conn.commit()
            conn.close()
        except:
            pass  # Database might not be available, but user is added to static dict
        
        return True
    except:
        return False

def deactivate_user(username):
    """Deactivate a user"""
    try:
        # Remove from static users or mark as inactive
        if username in USERS:
            USERS[username]['active'] = False
            return True
        
        # Update database
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users 
            SET active = 0 
            WHERE user = ?
        """, (username,))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except:
        return False

def activate_user(username):
    """Activate a user"""
    try:
        # Reactivate in static users
        if username in USERS:
            USERS[username]['active'] = True
            return True
        
        # Update database
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users 
            SET active = 1 
            WHERE user = ?
        """, (username,))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except:
        return False

def check_owner_exists():
    """Check if an owner account already exists"""
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        
        # Check for owner in database
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_owner = 1")
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    except:
        # Check static users for owner flag
        for user_data in USERS.values():
            if user_data.get('is_owner', False):
                return True
        return False

def is_user_owner(username):
    """Check if a specific user is the owner"""
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT is_owner FROM users WHERE user = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0] == 1
    except:
        pass
    
    # Check static users
    if username in USERS:
        return USERS[username].get('is_owner', False)
    return False

def create_demo_environment():
    """Create demo environment with test data"""
    import sqlite3
    from datetime import datetime, timedelta
    import random
    
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    # Check if demo data already exists
    cursor.execute("SELECT COUNT(*) FROM moves WHERE customer_name LIKE '%DEMO%'")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return  # Demo data already exists
    
    # Create demo moves
    demo_moves = [
        ('DEMO-001', 'DEMO Customer A', 'Atlanta', 'GA', 'Miami', 'FL', 'pending', 1500),
        ('DEMO-002', 'DEMO Customer B', 'Dallas', 'TX', 'Houston', 'TX', 'in_progress', 1200),
        ('DEMO-003', 'DEMO Customer C', 'Chicago', 'IL', 'Detroit', 'MI', 'completed', 1800),
        ('DEMO-004', 'DEMO Customer A', 'Phoenix', 'AZ', 'Las Vegas', 'NV', 'in_progress', 1350),
        ('DEMO-005', 'DEMO Customer D', 'Denver', 'CO', 'Salt Lake City', 'UT', 'pending', 1650),
    ]
    
    for order, customer, orig_city, orig_state, dest_city, dest_state, status, amount in demo_moves:
        pickup = datetime.now() + timedelta(days=random.randint(1, 7))
        delivery = pickup + timedelta(days=random.randint(2, 5))
        
        cursor.execute('''
            INSERT INTO moves (order_number, customer_name, origin_city, origin_state,
                             destination_city, destination_state, status, amount,
                             pickup_date, delivery_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order, customer, orig_city, orig_state, dest_city, dest_state,
              status, amount, pickup, delivery, datetime.now()))
    
    # Create demo trailers
    demo_trailers = [
        ('DEMO-TR-001', 'Dry Van', 'available', 'Good', 'Atlanta Depot'),
        ('DEMO-TR-002', 'Reefer', 'in_use', 'Excellent', 'Miami Terminal'),
        ('DEMO-TR-003', 'Flatbed', 'maintenance', 'Fair', 'Service Center'),
        ('DEMO-TR-004', 'Step Deck', 'available', 'Good', 'Dallas Yard'),
        ('DEMO-TR-005', 'Double Drop', 'available', 'Excellent', 'Phoenix Hub'),
    ]
    
    # Create trailer inventory table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trailer_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trailer_number TEXT UNIQUE NOT NULL,
            trailer_type TEXT,
            status TEXT DEFAULT 'available',
            condition TEXT DEFAULT 'good',
            current_location TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT DEFAULT 'demo_user'
        )
    ''')
    
    for trailer_num, trailer_type, status, condition, location in demo_trailers:
        cursor.execute('''
            INSERT OR IGNORE INTO trailer_inventory
            (trailer_number, trailer_type, status, condition, current_location)
            VALUES (?, ?, ?, ?, ?)
        ''', (trailer_num, trailer_type, status, condition, location))
    
    # Create demo drivers
    demo_drivers = [
        ('DEMO Driver 1', 'demo1@test.com', '555-0001', 'Active'),
        ('DEMO Driver 2', 'demo2@test.com', '555-0002', 'Active'),
        ('DEMO Driver 3', 'demo3@test.com', '555-0003', 'On Leave'),
    ]
    
    for name, email, phone, status in demo_drivers:
        cursor.execute('''
            INSERT OR IGNORE INTO drivers (name, email, phone, status)
            VALUES (?, ?, ?, ?)
        ''', (name, email, phone, status))
    
    conn.commit()
    conn.close()

def show_login():
    """Show login page"""
    import streamlit as st
    
    st.markdown("""
    <div style='text-align: center; padding: 2rem;'>
        <h1 style='color: #FFFFFF; font-size: 3rem;'>🚛</h1>
        <h1 style='color: #FFFFFF;'>Smith & Williams Trucking</h1>
        <p style='color: #888;'>Trailer Move Management System</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                login_button = st.form_submit_button("🔓 Login", use_container_width=True, type="primary")
            with col_b:
                demo_button = st.form_submit_button("📱 Demo Mode", use_container_width=True)
            
            if login_button:
                if validate_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    
                    # Get user role
                    conn = sqlite3.connect('trailer_tracker_streamlined.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT role FROM users WHERE user = ?", (username,))
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result:
                        st.session_state.user_role = result[0]
                    else:
                        # Check auth_config USERS dict for legacy support
                        if username in USERS:
                            st.session_state.user_role = USERS[username]['role']
                        else:
                            st.session_state.user_role = 'viewer'
                    
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
            
            if demo_button:
                # Enhanced demo mode with test environment
                st.session_state.authenticated = True
                st.session_state.username = "demo_user"
                st.session_state.user_role = "business_administrator"
                st.session_state.demo_mode = True
                
                # Create test data if not exists
                try:
                    create_demo_environment()
                except:
                    pass
                
                st.success("✅ Demo mode activated with full test environment!")
                st.info("You have full administrator access to test all features")
                st.rerun()