# 📚 Complete User Guide & Training System
## Smith and Williams Trucking - Trailer Move Tracker

---

## 🚀 Quick Start Guide

### Default Login Credentials (MUST BE CHANGED!)

| Role | Username | Password | Access Level |
|------|----------|----------|--------------|
| **Administrator** | `admin` | `admin123` | Full system access |
| **Manager** | `manager` | `manager123` | Operations (no financials) |
| **Viewer** | `viewer` | `view123` | Read-only dashboards |
| **Client** | `client` | `client123` | Progress dashboard only |

### System URLs

| Component | URL | Purpose |
|-----------|-----|---------|
| **Main System** | http://localhost:8501 | Full application |
| **Progress Viewer** | http://localhost:8502 | Client read-only view |
| **Training Center** | http://localhost:8503 | Interactive training |

---

## 🎓 Training System Access

### Method 1: Direct Role Access
```
http://localhost:8503?role=admin
http://localhost:8503?role=manager
http://localhost:8503?role=viewer
http://localhost:8503?role=client
```

### Method 2: Generate Training Links
```python
# Run this to create assignable training links
python generate_training_link.py
```

### Method 3: Launch Training System
```bash
streamlit run training_system.py --server.port 8503
```

---

## 🔐 SECURITY: How to Change Passwords

### Step 1: Locate the Configuration File
```
C:\trailer-move-tracker\auth_config.py
```

### Step 2: Edit User Passwords
Open `auth_config.py` in any text editor and find:

```python
USERS = {
    'admin': {
        'password': 'admin123',  # CHANGE THIS LINE!
        'role': 'admin',
        'name': 'Administrator'
    },
    'manager': {
        'password': 'manager123',  # CHANGE THIS LINE!
        'role': 'manager',
        'name': 'Operations Manager'
    },
    'viewer': {
        'password': 'view123',  # CHANGE THIS LINE!
        'role': 'viewer',
        'name': 'Read-Only User'
    },
    'client': {
        'password': 'client123',  # CHANGE THIS LINE!
        'role': 'client',
        'name': 'Client Access'
    }
}
```

### Step 3: Replace with Secure Passwords

**Example of Good Passwords:**
```python
USERS = {
    'admin': {
        'password': 'Truck#Admin2024$Secure!',  # Strong password
        'role': 'admin',
        'name': 'Administrator'
    },
    'manager': {
        'password': 'Manage*Fleet2024@Safe',  # Strong password
        'role': 'manager',
        'name': 'Operations Manager'
    },
    'viewer': {
        'password': 'View#Only2024$Read',  # Strong password
        'role': 'viewer',
        'name': 'Read-Only User'
    },
    'client': {
        'password': 'Client$Access2024!',  # Strong password
        'role': 'client',
        'name': 'Client Access'
    }
}
```

### Step 4: Save and Restart
1. Save the file (Ctrl+S)
2. Close any running Streamlit apps (Ctrl+C in terminal)
3. Restart the application
4. Test login with new password

---

## 👥 User Management

### Adding a New User

Add to the `USERS` dictionary in `auth_config.py`:

```python
USERS = {
    # ... existing users ...
    'john_smith': {  # New user
        'password': 'TempPass2024!',  # They should change this
        'role': 'manager',  # Assign appropriate role
        'name': 'John Smith'
    }
}
```

### Creating Custom Roles

Add to the `USER_ROLES` dictionary:

```python
USER_ROLES = {
    # ... existing roles ...
    'dispatcher': {  # New custom role
        'description': 'Can manage routes and drivers',
        'access': [
            'dashboard',
            'trailer_management', 
            'add_move',
            'drivers',
            'locations'
        ],
        'can_edit': True,
        'can_delete': False,
        'can_export': True,
        'view_financial': False
    }
}
```

---

## 📊 Role-Based Features Access

### Administrator Can:
✅ Everything! Including:
- View/Edit all data
- Manage users
- Generate invoices
- View financial reports
- Delete records
- System settings
- Export all data

### Manager Can:
✅ Operational tasks:
- Add/Edit moves
- Manage trailers
- Manage drivers
- View dashboards
- Export reports

❌ Cannot:
- View financial data
- Delete records
- Change system settings

### Viewer Can:
✅ View only:
- Main dashboard
- Progress dashboard

❌ Cannot:
- Edit anything
- Export data
- Access management sections

### Client Can:
✅ View only:
- Progress dashboard

❌ Cannot:
- Access any other features
- See financial information
- View driver details

---

## 🔗 Sharing Dashboard with Clients

### Option 1: Client Account
1. Give them username: `client`
2. Give them password: `client123` (or changed password)
3. They login to main app but only see progress dashboard

### Option 2: Standalone Progress Viewer
1. Run: `streamlit run progress_viewer.py --server.port 8502`
2. Share URL: `http://yourserver:8502`
3. Give access code: `client123`

### Option 3: Generate Time-Limited Link
```bash
python generate_share_link.py
```
Follow prompts to create a link like:
```
http://yourserver:8502?token=abc123xyz
```

---

## 📱 Step-by-Step Workflows

### For New Employees

1. **Create Account**
   - Add user to `auth_config.py`
   - Assign appropriate role
   - Set temporary password

2. **Send Training Link**
   ```
   http://localhost:8503?role=manager
   ```

3. **First Login Instructions**
   - Username: [their_username]
   - Password: [temp_password]
   - Must change password immediately

4. **Monitor Progress**
   - Check training completion
   - Answer questions
   - Verify understanding

### For Clients

1. **Decide Access Level**
   - View-only progress dashboard
   - No financial data visible
   - Time-limited or permanent

2. **Create Access**
   ```bash
   # Generate 30-day link
   python generate_share_link.py
   ```

3. **Send Instructions**
   ```
   Dear Client,
   
   Access your progress dashboard at:
   http://tracker.smithwilliams.com:8502
   
   Access Code: client123
   
   This shows real-time progress of your shipments.
   ```

---

## 🛠️ System Administration

### Daily Tasks
1. Check unpaid moves
2. Review in-progress shipments
3. Update trailer statuses
4. Monitor driver assignments

### Weekly Tasks
1. Generate invoices
2. Archive completed moves
3. Review user access
4. Backup database

### Monthly Tasks
1. Change passwords
2. Review security logs
3. Update mileage cache
4. Clean old data

---

## 🚨 Troubleshooting

### Can't Login?
1. Check username spelling
2. Check password (case-sensitive)
3. Check Caps Lock
4. Try incognito/private browser mode
5. Clear browser cache

### Forgot Password?
1. Admin must edit `auth_config.py`
2. Set new password
3. Restart application
4. Login with new password

### Training Not Loading?
1. Check URL includes role parameter
2. Try: `http://localhost:8503?role=admin`
3. Clear browser cache
4. Check training_system.py is running

### Dashboard Not Updating?
1. Refresh browser (F5)
2. Check database connection
3. Verify data was saved
4. Check filters aren't hiding data

---

## 📞 Support Contacts

### Technical Issues
- Check this guide first
- Review error messages
- Contact system administrator

### Training Questions
- Use interactive training system
- Review specific module
- Ask supervisor for help

### Emergency Access
- Administrator can reset any password
- Keep backup admin account
- Document all access changes

---

## ✅ Security Checklist

### Immediate Actions (Day 1)
- [ ] Change ALL default passwords
- [ ] Test new passwords work
- [ ] Document passwords securely
- [ ] Remove test accounts

### Weekly Security
- [ ] Review active users
- [ ] Check for unusual activity
- [ ] Verify backups working
- [ ] Update expired share links

### Monthly Security
- [ ] Rotate passwords
- [ ] Audit user permissions  
- [ ] Review access logs
- [ ] Update training materials

---

## 📝 Notes Section

### Your Custom Settings:
```
Main App URL: _______________________
Progress URL: _______________________
Admin Password: [Store Securely!]
Backup Location: ____________________
```

### Important Dates:
- System Installed: ___________
- Last Password Change: ___________
- Next Security Review: ___________
- Training Completed: ___________

---

## 🎯 Quick Reference Card

### Login URLs
- Main: http://localhost:8501
- Progress: http://localhost:8502  
- Training: http://localhost:8503

### Default Passwords (CHANGE!)
- Admin: admin/admin123
- Manager: manager/manager123
- Viewer: viewer/view123
- Client: client/client123

### Key Commands
```bash
# Start main app
streamlit run app.py

# Start progress viewer
streamlit run progress_viewer.py --server.port 8502

# Start training
streamlit run training_system.py --server.port 8503

# Generate share link
python generate_share_link.py
```

### File Locations
- User Config: `auth_config.py`
- Database: `data/trailer_moves.db`
- Training: `training_system.py`

---

**Remember:** Security is everyone's responsibility. Change passwords, limit access, and keep data safe!