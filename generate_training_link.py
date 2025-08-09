"""
Generate assignable training links for users
"""

import secrets
import string
from datetime import datetime, timedelta
import json
import os

def generate_training_token(length=16):
    """Generate a secure random token for training access"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_training_link(role, base_url="http://localhost:8503", user_name=""):
    """
    Create an assignable training link
    
    Args:
        role: User role (admin, manager, viewer, client)
        base_url: The base URL where training_system.py is hosted
        user_name: Optional name of the person being trained
    
    Returns:
        tuple: (token, training_link, role, user_name)
    """
    token = generate_training_token()
    training_link = f"{base_url}?role={role}&token={token}"
    
    return token, training_link, role, user_name

def save_training_assignment(token, role, user_name, expiry_days=30):
    """
    Save training assignment record
    In production, this should save to a database
    """
    assignment = {
        'token': token,
        'role': role,
        'user_name': user_name,
        'assigned_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'expiry_date': (datetime.now() + timedelta(days=expiry_days)).strftime('%Y-%m-%d'),
        'status': 'assigned'
    }
    
    # Save to JSON file (in production, use database)
    filename = 'training_assignments.json'
    
    # Load existing assignments
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            assignments = json.load(f)
    else:
        assignments = []
    
    # Add new assignment
    assignments.append(assignment)
    
    # Save back to file
    with open(filename, 'w') as f:
        json.dump(assignments, f, indent=2)
    
    return assignment

def generate_welcome_email(user_name, role, training_link):
    """Generate a welcome email template with training link"""
    
    role_descriptions = {
        'admin': 'Administrator with full system access',
        'manager': 'Operations Manager with editing capabilities',
        'viewer': 'Read-only access to dashboards',
        'client': 'Client with progress dashboard access'
    }
    
    email_template = f"""
Subject: Welcome to Smith and Williams Trucking - Training Access

Dear {user_name or 'Team Member'},

Welcome to the Smith and Williams Trucking Trailer Move Tracker system!

You have been assigned the role of: {role_descriptions.get(role, role)}

Please complete your training by following this link:
{training_link}

Your Initial Login Credentials:
- Username: {role}
- Temporary Password: {role}123

IMPORTANT SECURITY STEPS:
1. Complete the training modules
2. Change your password immediately after first login
3. Never share your credentials with anyone
4. Contact admin if you have any issues

The training will cover:
- How to login and navigate the system
- Your specific role permissions and features
- Security best practices
- How to change your password

This training link expires in 30 days. Please complete your training as soon as possible.

If you have any questions, please contact your system administrator.

Best regards,
Smith and Williams Trucking
Operations Team
"""
    
    return email_template

def main():
    """Interactive training link generator"""
    print("\n" + "="*60)
    print("🎓 TRAINING LINK GENERATOR")
    print("Smith and Williams Trucking - Trailer Move Tracker")
    print("="*60 + "\n")
    
    # Get user details
    print("Enter details for the new user:\n")
    
    user_name = input("User's Full Name: ").strip()
    if not user_name:
        user_name = "New User"
    
    print("\nSelect Role:")
    print("1. Administrator (admin)")
    print("2. Manager (manager)")
    print("3. Viewer (viewer)")
    print("4. Client (client)")
    
    role_choice = input("\nEnter choice (1-4): ").strip()
    
    role_map = {
        '1': 'admin',
        '2': 'manager',
        '3': 'viewer',
        '4': 'client'
    }
    
    role = role_map.get(role_choice, 'viewer')
    
    # Get base URL
    use_default = input("\nUse default URL (http://localhost:8503)? (y/n): ").lower()
    if use_default != 'y':
        base_url = input("Enter training system URL: ").strip()
    else:
        base_url = "http://localhost:8503"
    
    # Generate the training link
    token, training_link, role, user_name = create_training_link(role, base_url, user_name)
    
    # Save assignment
    assignment = save_training_assignment(token, role, user_name)
    
    # Generate email template
    email = generate_welcome_email(user_name, role, training_link)
    
    # Display results
    print("\n" + "="*60)
    print("✅ TRAINING LINK GENERATED SUCCESSFULLY!")
    print("="*60 + "\n")
    
    print(f"User: {user_name}")
    print(f"Role: {role}")
    print(f"Token: {token}")
    print(f"\n📧 Training Link:\n{training_link}\n")
    
    print("="*60)
    print("📋 WELCOME EMAIL TEMPLATE (Copy and send):")
    print("="*60)
    print(email)
    
    print("="*60)
    print("📝 ASSIGNMENT DETAILS SAVED")
    print("="*60)
    print(f"Assignment saved to: training_assignments.json")
    print(f"Expires: {assignment['expiry_date']}")
    print(f"Status: {assignment['status']}")
    
    print("\n" + "="*60)
    print("📌 NEXT STEPS:")
    print("="*60)
    print("1. Send the welcome email to the user")
    print("2. Have them complete the training")
    print("3. Ensure they change their password after first login")
    print("4. Monitor their training progress")
    print("5. Follow up if training not completed within 7 days")
    print("\n")

if __name__ == "__main__":
    main()