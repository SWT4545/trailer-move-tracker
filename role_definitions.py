"""
Role Definitions for Smith & Williams Trucking
Clearly defined roles with specific access levels
"""

SYSTEM_ROLES = {
    "Owner-CEO-Driver": {
        "description": "Brandon Smith - Full system control + driving capability",
        "access_level": "FULL",
        "capabilities": [
            "All financial visibility and control",
            "User management",
            "System administration", 
            "Process payments and factoring",
            "Self-assign and complete moves as driver",
            "View money bag earnings",
            "Access all dashboards",
            "Generate all reports"
        ],
        "restrictions": [],
        "dashboard": "Executive Dashboard",
        "users": ["Brandon"]
    },
    
    "Business Admin": {
        "description": "Business Administrator - Operations and admin without financials",
        "access_level": "HIGH",
        "capabilities": [
            "User account management",
            "System configuration",
            "Operational oversight",
            "Document management",
            "Move creation and assignment",
            "Generate operational reports",
            "View operational metrics"
        ],
        "restrictions": [
            "Cannot see payment amounts",
            "Cannot see revenue figures",
            "Cannot process payments",
            "Cannot access factoring"
        ],
        "dashboard": "Admin Dashboard"
    },
    
    "Ops Coordinator": {
        "description": "Operations Coordinator - Document and move coordination",
        "access_level": "MEDIUM",
        "capabilities": [
            "Collect and upload documents",
            "Assign moves to drivers",
            "Track move status",
            "Update operational data",
            "Coordinate deliveries",
            "Communicate with drivers"
        ],
        "restrictions": [
            "No financial visibility",
            "Cannot see payment information",
            "Cannot access user management",
            "Cannot modify system settings"
        ],
        "dashboard": "Coordinator Dashboard"
    },
    
    "Data Entry": {
        "description": "Data Entry Clerk - Input and update operational data",
        "access_level": "LIMITED",
        "capabilities": [
            "Enter new moves",
            "Update move information",
            "Input trailer data",
            "Upload documents",
            "Update statuses"
        ],
        "restrictions": [
            "No financial visibility",
            "Cannot assign moves",
            "Cannot access reports",
            "Cannot manage users",
            "Limited to data input only"
        ],
        "dashboard": "Data Entry Dashboard"
    },
    
    "Driver": {
        "description": "Contract Drivers - Field operations and deliveries",
        "access_level": "DRIVER",
        "capabilities": [
            "View available moves",
            "Self-assign moves",
            "Update move status",
            "Upload PODs",
            "View own earnings (money bag)",
            "Track own performance",
            "View own payment history"
        ],
        "restrictions": [
            "Can only see own data",
            "No access to other drivers' info",
            "No financial visibility except own earnings",
            "Cannot see customer details"
        ],
        "dashboard": "Driver Portal",
        "users": ["Justin Duckett", "Carl Strickland"]  # Only 2 contractor drivers
    },
    
    "Client": {
        "description": "Client Portal - Customer tracking their shipments",
        "access_level": "EXTERNAL",
        "capabilities": [
            "Track their company's moves",
            "View move progress in real-time",
            "See pickup/delivery locations",
            "View completion status",
            "Access POD documents",
            "See trailer locations",
            "View detailed move timeline"
        ],
        "restrictions": [
            "Cannot see driver names",
            "Cannot see payment information",
            "Cannot see internal notes",
            "Only see their company's moves",
            "No system access beyond tracking"
        ],
        "dashboard": "Client Tracking Portal"
    },
    
    "Viewer": {
        "description": "Observer - Birds eye view of the system",
        "access_level": "READ_ONLY",
        "capabilities": [
            "View system dashboard",
            "See operational metrics",
            "Monitor move progress",
            "View system architecture",
            "Access demonstration features",
            "See workflow visualizations"
        ],
        "restrictions": [
            "Cannot modify any data",
            "No financial visibility",
            "Cannot access user details",
            "Read-only access to all features",
            "Perfect for demonstrations"
        ],
        "dashboard": "System Overview Dashboard"
    }
}

def get_role_capabilities(role):
    """Get capabilities for a specific role"""
    return SYSTEM_ROLES.get(role, {}).get("capabilities", [])

def get_role_restrictions(role):
    """Get restrictions for a specific role"""
    return SYSTEM_ROLES.get(role, {}).get("restrictions", [])

def get_dashboard_name(role, username=None):
    """Get appropriate dashboard name for role"""
    if username == "Brandon" and role == "Owner-CEO-Driver":
        return "Executive Dashboard"
    return SYSTEM_ROLES.get(role, {}).get("dashboard", "Dashboard")

def can_see_financials(role):
    """Check if role can see financial information"""
    return role == "Owner-CEO-Driver"

def can_manage_users(role):
    """Check if role can manage users"""
    return role in ["Owner-CEO-Driver", "Business Admin"]

def can_assign_moves(role):
    """Check if role can assign moves"""
    return role in ["Owner-CEO-Driver", "Business Admin", "Ops Coordinator"]

def can_upload_documents(role):
    """Check if role can upload documents"""
    return role in ["Owner-CEO-Driver", "Business Admin", "Ops Coordinator", "Data Entry", "Driver"]

def is_driver(username):
    """Check if user is a driver"""
    drivers = ["Justin Duckett", "Carl Strickland", "Brandon Smith"]
    return username in drivers

def get_client_company(username):
    """Get client company name for filtering"""
    # This would be stored in the database
    # For now, return a placeholder
    client_companies = {
        "walmart_viewer": "Walmart",
        "fedex_tracker": "FedEx",
        "ups_monitor": "UPS"
    }
    return client_companies.get(username, None)