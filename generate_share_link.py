"""
Generate shareable links for the progress dashboard
"""

import secrets
import string
from datetime import datetime, timedelta
import json

def generate_token(length=32):
    """Generate a secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_share_link(base_url="http://localhost:8502", days_valid=30):
    """
    Create a shareable link for the progress dashboard
    
    Args:
        base_url: The base URL where progress_viewer.py is hosted
        days_valid: Number of days the link should be valid
    
    Returns:
        tuple: (token, share_link, expiry_date)
    """
    token = generate_token()
    expiry_date = (datetime.now() + timedelta(days=days_valid)).strftime('%Y-%m-%d')
    share_link = f"{base_url}?token={token}"
    
    return token, share_link, expiry_date

def save_token(token, expiry_date, description="Progress Dashboard Access"):
    """
    Save token to auth_config.py
    In production, this should save to a database
    """
    token_data = {
        'type': 'progress_dashboard',
        'expires': expiry_date,
        'description': description,
        'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # In production, save to database
    # For now, print the token info
    print(f"""
    ============================================
    NEW SHAREABLE LINK GENERATED
    ============================================
    
    Token: {token}
    Expires: {expiry_date}
    Description: {description}
    
    Add this to auth_config.py SHARE_TOKENS:
    
    '{token}': {{
        'type': 'progress_dashboard',
        'expires': '{expiry_date}',
        'description': '{description}'
    }}
    
    ============================================
    """)
    
    return token_data

def main():
    """Generate a new shareable link"""
    print("\n🔗 Generate Shareable Progress Dashboard Link\n")
    
    # Get configuration
    base_url = input("Enter base URL (default: http://localhost:8502): ").strip()
    if not base_url:
        base_url = "http://localhost:8502"
    
    days_valid = input("Valid for how many days? (default: 30): ").strip()
    try:
        days_valid = int(days_valid) if days_valid else 30
    except:
        days_valid = 30
    
    description = input("Description (default: Progress Dashboard Access): ").strip()
    if not description:
        description = "Progress Dashboard Access"
    
    # Generate the link
    token, share_link, expiry_date = create_share_link(base_url, days_valid)
    
    # Save token info
    save_token(token, expiry_date, description)
    
    print(f"""
    ============================================
    SHAREABLE LINK
    ============================================
    
    {share_link}
    
    This link will expire on: {expiry_date}
    
    Share this link with clients or stakeholders
    who need read-only access to the progress
    dashboard.
    
    ============================================
    """)

if __name__ == "__main__":
    main()