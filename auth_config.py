"""
Authentication and Access Control Configuration
"""

# User roles and their permissions
USER_ROLES = {
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
    'admin': {
        'password': 'admin123',
        'role': 'business_administrator', 
        'name': 'Administrator',
        'title': 'Administrator'
    },
    'setup': {
        'password': 'setup123',
        'role': 'business_administrator',
        'name': 'Setup Admin',
        'title': 'Initial Setup'
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
            WHERE username = ? AND password = ? AND active = 1
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
        if username == 'setup' and password == 'setup':
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
            if row['username'] in USERS:
                df.loc[df['username'] == row['username'], 'name'] = USERS[row['username']].get('name', 'N/A')
        
        return df
    except:
        # Return static users if database not available
        users_list = []
        for username, info in USERS.items():
            users_list.append({
                'username': username,
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
            WHERE username = ?
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
            WHERE username = ?
        """, (new_role, username))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except:
        return False

def create_user(username, password, role='viewer', name=None, email=None, phone=None):
    """Create a new user"""
    try:
        # Add to static users
        USERS[username] = {
            'password': password,
            'role': role,
            'name': name or username,
            'email': email or '',
            'phone': phone or ''
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            hashed_pw = hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password, role, name, email, phone)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, hashed_pw, role, name, email, phone))
            
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
            WHERE username = ?
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
            WHERE username = ?
        """, (username,))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except:
        return False