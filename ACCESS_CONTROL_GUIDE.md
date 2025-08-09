# Access Control & Sharing Guide

## Overview
The Trailer Move Tracker now includes a comprehensive role-based access control system with the ability to share read-only progress dashboards with clients and stakeholders.

## User Roles

### 1. **Admin** (Full Access)
- Username: `admin`
- Password: `admin123` (CHANGE THIS!)
- Access: All features including financial data, settings, and user management
- Can: Edit, delete, export, view financials

### 2. **Manager** (Operations Access)
- Username: `manager` 
- Password: `manager123` (CHANGE THIS!)
- Access: Most features except financial data and critical settings
- Can: Edit, export data
- Cannot: Delete records, view invoices/financial data

### 3. **Viewer** (Read-Only Dashboard)
- Username: `viewer`
- Password: `view123` (CHANGE THIS!)
- Access: Dashboard and progress dashboard only
- Can: View data only
- Cannot: Edit, delete, or export

### 4. **Client** (Progress Only)
- Username: `client`
- Password: `client123` (CHANGE THIS!)
- Access: Progress dashboard only
- Can: View progress metrics only
- Cannot: Access any other features

## Running the Applications

### Main Application (Full System)
```bash
streamlit run app.py
```
Access at: http://localhost:8501

### Progress Viewer (Standalone Read-Only)
```bash
streamlit run progress_viewer.py --server.port 8502
```
Access at: http://localhost:8502

## Sharing Progress Dashboard

### Method 1: Direct Access Code
Share the progress viewer URL with clients along with an access code:
- URL: `http://your-domain.com:8502`
- Access Code: `client123` or `progress2024`

### Method 2: Shareable Links (Recommended)

1. **Generate a shareable link:**
```bash
python generate_share_link.py
```

2. **Follow the prompts:**
   - Enter your domain URL
   - Set expiration period (default 30 days)
   - Add description

3. **Add token to auth_config.py:**
   - Copy the generated token configuration
   - Add it to the `SHARE_TOKENS` dictionary in `auth_config.py`

4. **Share the link:**
   - Send the generated URL to clients
   - Link format: `http://your-domain.com:8502?token=GENERATED_TOKEN`
   - Link expires automatically after set period

## Security Best Practices

### 1. Change Default Passwords
**IMPORTANT:** Change all default passwords in `auth_config.py`:
```python
USERS = {
    'admin': {
        'password': 'YOUR_SECURE_PASSWORD_HERE',  # CHANGE THIS!
        ...
    }
}
```

### 2. Use Environment Variables
For production, store passwords in environment variables:
```python
import os
password = os.environ.get('ADMIN_PASSWORD', 'default_password')
```

### 3. Implement Password Hashing
For production, use password hashing:
```python
import hashlib
hashed = hashlib.sha256(password.encode()).hexdigest()
```

### 4. HTTPS in Production
Always use HTTPS in production:
- Use a reverse proxy (nginx/Apache)
- Configure SSL certificates
- Update share links to use https://

## Deployment Options

### Option 1: Single Server
Run both apps on different ports:
```bash
# Main app on port 8501
streamlit run app.py &

# Progress viewer on port 8502
streamlit run progress_viewer.py --server.port 8502 &
```

### Option 2: Separate Deployments
- Deploy main app on internal network
- Deploy progress viewer on DMZ or public server
- Use database replication for data sync

### Option 3: Cloud Deployment
**Streamlit Cloud:**
1. Create two separate GitHub repos
2. Deploy each app separately
3. Use Streamlit secrets for authentication

**Other Platforms:**
- Heroku: Use Procfile for multi-app deployment
- AWS/Azure: Use container services
- Docker: Create separate containers

## Customization

### Adding New Roles
Edit `auth_config.py`:
```python
USER_ROLES = {
    'custom_role': {
        'description': 'Custom role description',
        'access': ['dashboard', 'progress_dashboard'],
        'can_edit': False,
        'can_delete': False,
        'can_export': True,
        'view_financial': False
    }
}
```

### Modifying Permissions
Update the `access` list for each role to control page visibility:
```python
'access': [
    'dashboard',           # Main dashboard
    'trailer_management',  # Trailer management
    'add_move',           # Add new moves
    'progress_dashboard',  # Progress dashboard
    'invoices',           # Financial/invoices
    'email_center',       # Email functionality
    'locations',          # Location management
    'drivers',            # Driver management
    'mileage',           # Mileage management
    'import_export',      # Data import/export
    'settings'           # System settings
]
```

### Customizing Progress Viewer
Edit `progress_viewer.py` to:
- Change branding
- Modify access codes
- Add/remove dashboard sections
- Customize refresh intervals

## Troubleshooting

### Issue: Users see wrong pages
**Solution:** Clear browser cache and session state:
```python
st.session_state.clear()
```

### Issue: Token not working
**Solution:** Check token expiration and format in `auth_config.py`

### Issue: Can't run both apps
**Solution:** Use different ports:
```bash
streamlit run app.py --server.port 8501
streamlit run progress_viewer.py --server.port 8502
```

## Support
For issues or questions:
1. Check this guide
2. Review code comments
3. Test with different user roles
4. Verify token expiration dates