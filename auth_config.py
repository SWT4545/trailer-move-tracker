"""
Authentication and Access Control Configuration
"""

# User roles and their permissions
USER_ROLES = {
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
    'manager': {
        'description': 'Can view and edit most features, limited financial access',
        'access': [
            'dashboard', 'trailer_management', 'add_move', 'progress_dashboard',
            'locations', 'drivers', 'mileage', 'import_export'
        ],
        'can_edit': True,
        'can_delete': False,
        'can_export': True,
        'view_financial': False
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

# User accounts (in production, store hashed passwords in database)
USERS = {
    'brandon_smith': {
        'password': 'executive123',  # CHANGE THIS IMMEDIATELY!
        'role': 'executive',
        'name': 'Brandon Smith',
        'title': 'CEO',
        'email': 'swtruckingceo@gmail.com'
    },
    'admin': {
        'password': 'admin123',  # Change this!
        'role': 'admin',
        'name': 'System Administrator'
    },
    'manager': {
        'password': 'manager123',  # Change this!
        'role': 'manager',
        'name': 'Operations Manager'
    },
    'viewer': {
        'password': 'view123',  # Change this!
        'role': 'viewer',
        'name': 'Read-Only User'
    },
    'client': {
        'password': 'client123',  # Change this!
        'role': 'client',
        'name': 'Client Access'
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
    """Validate user credentials"""
    # Strip any whitespace from inputs
    username = username.strip() if username else ""
    password = password.strip() if password else ""
    
    if username in USERS:
        stored_password = USERS[username]['password']
        if stored_password == password:
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