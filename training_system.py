"""
Interactive Training System for Trailer Move Tracker
Complete user guide with role-based tutorials
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from PIL import Image
import auth_config
import branding

# Page configuration
page_icon = "📚"
if os.path.exists("swt_logo.png"):
    try:
        page_icon = Image.open("swt_logo.png")
    except:
        pass

st.set_page_config(
    page_title="Training Center - Smith and Williams Trucking",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Training modules for each role
TRAINING_MODULES = {
    'admin': {
        'title': 'Administrator Complete Training',
        'modules': [
            'login_basics',
            'dashboard_overview',
            'trailer_management',
            'add_moves',
            'financial_management',
            'user_management',
            'password_management',
            'reports_exports',
            'security_best_practices'
        ]
    },
    'manager': {
        'title': 'Manager Training Guide',
        'modules': [
            'login_basics',
            'dashboard_overview',
            'trailer_management',
            'add_moves',
            'driver_management',
            'location_management',
            'reports_exports',
            'password_management'
        ]
    },
    'viewer': {
        'title': 'Viewer Training Guide',
        'modules': [
            'login_basics',
            'dashboard_overview',
            'progress_monitoring',
            'password_management'
        ]
    },
    'client': {
        'title': 'Client Access Guide',
        'modules': [
            'access_instructions',
            'progress_dashboard',
            'understanding_metrics'
        ]
    }
}

# Detailed content for each module
MODULE_CONTENT = {
    'login_basics': {
        'title': '🔐 Login & Access',
        'duration': '5 minutes',
        'content': """
        ### Getting Started with the System
        
        #### Step 1: Access the Application
        1. Open your web browser (Chrome, Firefox, Edge recommended)
        2. Navigate to: **http://localhost:8501** (or your company URL)
        3. You'll see the login screen
        
        #### Step 2: Enter Your Credentials
        
        **Your Login Information:**
        - **Username:** `{username}`
        - **Password:** `{password}`
        
        > ⚠️ **IMPORTANT:** You must change your password on first login!
        
        #### Step 3: Login Process
        1. Enter your username in the first field
        2. Enter your password in the second field
        3. Click the **🔓 Login** button
        4. Wait for the system to verify your credentials
        
        #### Common Issues:
        - **"Invalid username or password"**: Check for typos, caps lock
        - **Page not loading**: Check your internet connection
        - **Forgot password**: Contact your administrator
        
        #### Security Tips:
        - Never share your login credentials
        - Always logout when finished
        - Use a strong password (we'll show you how next)
        """
    },
    'password_management': {
        'title': '🔑 Password Management',
        'duration': '10 minutes',
        'content': """
        ### How to Change Your Password
        
        #### Why Change Your Password?
        - Default passwords are not secure
        - Regular changes prevent unauthorized access
        - Protects company and client data
        
        #### Step-by-Step Password Change:
        
        1. **Access Password Settings**
           - Login with your current credentials
           - Navigate to **⚙️ Settings** in the sidebar
           - Click on **🔐 Access Control** tab
        
        2. **Current Default Passwords** (MUST BE CHANGED):
           ```
           Admin:    admin / admin123
           Manager:  manager / manager123
           Viewer:   viewer / view123
           Client:   client / client123
           ```
        
        3. **Creating a Strong Password:**
           
           ✅ **Good Password Example:** `Truck#2024$Secure!`
           - At least 12 characters
           - Mix of uppercase and lowercase
           - Include numbers
           - Include special characters
           - Not related to personal info
           
           ❌ **Bad Password Examples:**
           - `password123` (too common)
           - `john2024` (personal info)
           - `12345678` (too simple)
        
        4. **Changing Your Password:**
           ```python
           # For Administrators: Edit auth_config.py
           
           USERS = {
               'admin': {
                   'password': 'YourNewSecurePassword#2024!',  # Change this line
                   'role': 'admin',
                   'name': 'Administrator'
               }
           }
           ```
        
        5. **After Changing:**
           - Save the file
           - Restart the application
           - Test login with new password
           - Store password securely (use password manager)
        
        #### Password Security Checklist:
        - [ ] Changed default password
        - [ ] Password is at least 12 characters
        - [ ] Includes uppercase and lowercase
        - [ ] Includes numbers and symbols
        - [ ] Not used elsewhere
        - [ ] Stored securely
        - [ ] Not written on sticky notes!
        """
    },
    'dashboard_overview': {
        'title': '📊 Dashboard Overview',
        'duration': '15 minutes',
        'content': """
        ### Understanding the Main Dashboard
        
        #### Key Metrics Section
        At the top of your dashboard, you'll see 5 key metrics:
        
        1. **Total Moves** - All trailer moves in the system
        2. **Unpaid Moves** - Moves pending payment
        3. **Total Unpaid** - Dollar amount outstanding
        4. **In Progress** - Currently active moves
        5. **Total Miles** - Cumulative distance
        
        #### Using Filters
        
        **Step 1: Status Filter**
        - Click the dropdown under "Status Filter"
        - Options: All, Unpaid, Paid, In Progress, Completed
        - Select to filter the data table
        
        **Step 2: Driver Filter**
        - Select specific driver or "All"
        - Updates table immediately
        
        **Step 3: Date Range**
        - Click calendar icons
        - Select From and To dates
        - Data updates automatically
        
        #### Working with the Data Table
        
        **Viewing Moves:**
        - Scroll horizontally to see all columns
        - Click column headers to sort
        - Use search box to find specific entries
        
        **Editing Moves:**
        1. Find the move ID you want to edit
        2. Enter the ID in "Enter Move ID" field
        3. Click **📝 Edit Details**
        4. Update information in the form
        5. Click **💾 Save Changes**
        
        **Deleting Moves** (Admin only):
        1. Enter the Move ID
        2. Click **🗑️ Delete**
        3. Confirm the deletion
        
        #### Pro Tips:
        - Export data regularly for backups
        - Use filters to find information quickly
        - Check "Unpaid Moves" daily
        """
    },
    'trailer_management': {
        'title': '🚛 Trailer Management',
        'duration': '20 minutes',
        'content': """
        ### Complete Trailer Management Guide
        
        #### Understanding Trailer Types
        
        **New Trailers:** Empty trailers going to destination
        **Old Trailers:** Loaded trailers being picked up
        
        #### Adding a New Trailer
        
        1. **Navigate to Trailer Management**
           - Click **🚛 Trailer Management** in sidebar
        
        2. **Click "Add New Trailer" Tab**
        
        3. **Fill in Required Information:**
           - **Trailer Number:** Enter unique identifier (e.g., "TR2024-001")
           - **Trailer Type:** Select "New" or "Old"
           - **Current Location:** Choose from dropdown or add new
           - **Status:** Select current status
           - **VIN (optional):** Vehicle identification number
           - **Year/Make/Model:** Equipment details
        
        4. **Click "➕ Add Trailer"**
        
        #### Managing Existing Trailers
        
        **View All Trailers:**
        - Default view shows all trailers
        - Color coding:
          - 🟢 Green border = Available
          - 🟡 Yellow = Assigned/In Transit
          - ⚫ Gray = Completed/Archived
        
        **Update Trailer Status:**
        1. Find trailer in list
        2. Click **Update Status** button
        3. Select new status:
           - Available
           - Assigned
           - In Transit
           - Maintenance
           - Completed
        4. Add notes if needed
        5. Save changes
        
        **Archive Old Trailers:**
        - Completed moves older than 7 days
        - Click **Archive Completed** button
        - Trailers move to archive tab
        
        #### Best Practices:
        - Update status immediately when assigned
        - Add notes for maintenance issues
        - Review available trailers daily
        - Archive completed moves weekly
        """
    },
    'add_moves': {
        'title': '➕ Adding New Moves',
        'duration': '15 minutes',
        'content': """
        ### How to Add a New Trailer Move
        
        #### Step-by-Step Process
        
        **1. Navigate to Add New Move**
        - Click **➕ Add New Move** in sidebar
        
        **2. Trailer Information Section**
        
        📦 **New Trailer Details:**
        - Check "Select from Available Trailers" if using existing
        - Or enter new trailer number manually
        - Select pickup location from dropdown
        - Select destination
        
        🔄 **Old Trailer (Optional):**
        - Enter if swapping trailers
        - Include old pickup and destination
        
        **3. Driver Assignment**
        
        👤 **Assign Driver:**
        - Select from dropdown list
        - Or click "➕ Add New Driver" if not listed
        - Enter assignment date (defaults to today)
        
        **4. Mileage & Payment**
        
        📏 **Calculate Miles:**
        - System auto-calculates if locations are cached
        - Or enter manually
        - Check "💾 Save mileage" for future use
        
        💰 **Payment Calculation:**
        - **Rate per Mile:** Default $2.10 (editable)
        - **Factor Fee:** Default 3% (0.03)
        - **Load Pay:** Auto-calculated
        
        **Example Calculation:**
        ```
        Miles: 250
        Rate: $2.10
        Gross: 250 × $2.10 = $525.00
        Factor Fee: $525.00 × 0.03 = $15.75
        Net Pay: $525.00 - $15.75 = $509.25
        ```
        
        **5. Status & Notes**
        
        ☑️ **Check applicable boxes:**
        - [ ] Received PPW (Proof of Pickup/Weight)
        - [ ] Processed
        - [ ] Paid
        
        📝 **Add Comments:**
        - Special instructions
        - Delivery requirements
        - Contact information
        
        **6. Save the Move**
        - Click **💾 Save Trailer Move**
        - System assigns unique ID
        - Confirmation message appears
        
        #### Common Scenarios
        
        **Scenario 1: Simple Delivery**
        - New trailer from Dallas to Houston
        - No old trailer
        - Single driver assigned
        
        **Scenario 2: Trailer Swap**
        - Pick up old trailer in Austin
        - Deliver to San Antonio
        - Pick up new trailer in San Antonio
        - Deliver to Dallas
        
        **Scenario 3: Multi-Stop Route**
        - Use comments to note all stops
        - Calculate total miles
        - Assign primary driver
        
        #### Troubleshooting:
        - **"Location not found"**: Add location first in Manage Locations
        - **"Driver not available"**: Check driver isn't already assigned
        - **"Invalid miles"**: Must be greater than 0
        """
    },
    'progress_monitoring': {
        'title': '📈 Progress Dashboard',
        'duration': '10 minutes',
        'content': """
        ### Understanding the Progress Dashboard
        
        #### Key Sections
        
        **1. Active Routes (Top Metrics)**
        - Routes in Progress: Currently moving
        - Completed Today: Finished today
        - Completed This Week: 7-day total
        - Avg Completion: Average days per route
        
        **2. Driver Performance Charts**
        
        **Active Drivers (Left Chart):**
        - Shows drivers with active routes
        - Bar length = number of active routes
        - Sorted by most active
        
        **Completion Rates (Right Chart):**
        - Percentage of completed assignments
        - Color coding:
          - 🟢 Green = 90%+ (Excellent)
          - 🟡 Yellow = 70-89% (Good)
          - 🔴 Red = Below 70% (Needs Improvement)
        
        **3. Interactive Charts Toggle**
        - Check "📊 Interactive Charts" for hover details
        - Uncheck for static view (better for printing)
        
        **4. Trend Analysis**
        
        **Daily Completions:**
        - Line graph showing 30-day trend
        - Dotted line = 7-day average
        - Look for patterns (busy days, slow periods)
        
        **Top Routes:**
        - Most frequently used routes
        - Helps identify main corridors
        - Plan resources accordingly
        
        **5. Trailer Status**
        - Pie chart showing fleet distribution
        - Available vs In Transit
        - Quick visual of utilization rate
        
        #### Using Filters
        - Date range selection
        - Driver specific views
        - Status filters
        
        #### Interpreting Metrics
        
        **Good Performance Indicators:**
        - Completion rate above 85%
        - Avg completion under 3 days
        - Utilization above 60%
        
        **Warning Signs:**
        - Completion rate below 70%
        - Increasing in-progress count
        - Low utilization (under 40%)
        """
    },
    'financial_management': {
        'title': '💰 Financial Management',
        'duration': '25 minutes',
        'content': """
        ### Managing Invoices & Payments (Admin Only)
        
        #### Invoice Generation
        
        **Step 1: Navigate to Updates & Invoices**
        - Click **💰 Updates & Invoices** in sidebar
        
        **Step 2: Select Moves for Invoice**
        1. Filter by date range
        2. Filter by driver/contractor
        3. Check unpaid moves only
        4. Select moves to include
        
        **Step 3: Generate Invoice**
        ```
        Invoice Details:
        - Invoice Number: Auto-generated
        - Date: Current date
        - Due Date: Net 30 default
        - Company Details: Pre-filled
        - Line Items: Selected moves
        - Subtotal: Calculated
        - Factor Fee: Deducted
        - Total Due: Final amount
        ```
        
        **Step 4: Review & Send**
        - Preview invoice
        - Add notes if needed
        - Click **Send Invoice**
        - Email to contractor
        
        #### Payment Processing
        
        **Recording Payments:**
        1. Find invoice in system
        2. Click **Record Payment**
        3. Enter payment details:
           - Payment date
           - Amount received
           - Payment method
           - Reference number
        4. Save payment record
        
        **Payment Reports:**
        - Accounts receivable aging
        - Payment history by contractor
        - Outstanding balances
        - Monthly revenue reports
        
        #### Factor Fee Management
        
        **Understanding Factor Fees:**
        - Default: 3% (0.03)
        - Deducted from gross pay
        - Covers financing costs
        
        **Adjusting Rates:**
        - Per contractor basis
        - Volume discounts
        - Special agreements
        
        #### Best Practices:
        - Generate invoices weekly
        - Follow up on overdue payments
        - Maintain payment records
        - Regular financial reconciliation
        """
    },
    'access_instructions': {
        'title': '🔗 Client Access Instructions',
        'duration': '5 minutes',
        'content': """
        ### Accessing Your Progress Dashboard
        
        #### Option 1: Direct Link Access
        
        If you received a link like:
        `http://tracker.smithwilliams.com:8502?token=abc123xyz`
        
        1. **Click the link** or copy/paste into browser
        2. **Dashboard loads automatically**
        3. **No login required** - link contains your access
        
        #### Option 2: Access Code Method
        
        If you received:
        - **URL:** `http://tracker.smithwilliams.com:8502`
        - **Access Code:** `client123`
        
        1. **Go to the URL**
        2. **Enter access code** when prompted
        3. **Click "Access Dashboard"**
        
        #### What You Can See:
        - ✅ Active routes and progress
        - ✅ Completion metrics
        - ✅ Driver performance (no names)
        - ✅ Route statistics
        - ✅ Fleet utilization
        
        #### What You Cannot See:
        - ❌ Financial information
        - ❌ Driver personal details
        - ❌ Internal notes
        - ❌ Edit capabilities
        
        #### Troubleshooting:
        - **"Invalid token"**: Link may have expired, request new one
        - **"Access denied"**: Check access code spelling
        - **Dashboard not loading**: Clear browser cache
        - **Need help?**: Contact your account manager
        """
    },
    'security_best_practices': {
        'title': '🛡️ Security Best Practices',
        'duration': '15 minutes',
        'content': """
        ### System Security Guidelines
        
        #### Password Security
        
        **DO:**
        - ✅ Change default passwords immediately
        - ✅ Use unique passwords for this system
        - ✅ Enable two-factor authentication if available
        - ✅ Use a password manager
        - ✅ Change passwords every 90 days
        
        **DON'T:**
        - ❌ Share passwords with anyone
        - ❌ Write passwords on sticky notes
        - ❌ Use personal information in passwords
        - ❌ Reuse passwords from other sites
        - ❌ Send passwords via email
        
        #### Access Management
        
        **User Account Reviews:**
        - Monthly review of active users
        - Remove terminated employees immediately
        - Audit user roles quarterly
        - Document access changes
        
        **Sharing Dashboard Access:**
        1. Use time-limited tokens
        2. Set appropriate expiration dates
        3. Track who has access
        4. Revoke expired tokens
        
        #### Data Protection
        
        **Backups:**
        - Daily automatic backups
        - Weekly off-site backup
        - Test restore process monthly
        - Encrypt backup files
        
        **Sensitive Data:**
        - Never export financial data to personal devices
        - Use encrypted connections (HTTPS)
        - Lock computer when away
        - Clear browser cache after sensitive work
        
        #### Incident Response
        
        **If you suspect unauthorized access:**
        1. Change your password immediately
        2. Notify administrator
        3. Check recent activity logs
        4. Document the incident
        
        **If you accidentally share credentials:**
        1. Change password immediately
        2. Notify administrator
        3. Review recent system activity
        4. Update security training
        
        #### Compliance Checklist
        - [ ] Passwords changed from defaults
        - [ ] Access reviews conducted
        - [ ] Backups verified
        - [ ] Security training completed
        - [ ] Incident plan reviewed
        """
    }
}

def check_training_access():
    """Check if user has access to training"""
    # Check for training token in URL
    query_params = st.query_params
    if 'token' in query_params:
        return query_params['token'], 'token'
    
    # Check for role parameter
    if 'role' in query_params:
        return query_params['role'], 'role'
    
    # Show role selection
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>📚 Training Center</h1>
        <h3>Smith and Williams Trucking - Trailer Move Tracker</h3>
        <p>Select your role to access the appropriate training materials</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        role = st.selectbox(
            "Select Your Role",
            options=['', 'admin', 'manager', 'viewer', 'client'],
            format_func=lambda x: {
                '': '-- Select Role --',
                'admin': '👨‍💼 Administrator',
                'manager': '👷 Manager',
                'viewer': '👁️ Viewer',
                'client': '🤝 Client'
            }.get(x, x)
        )
        
        if st.button("🎓 Start Training", disabled=not role, use_container_width=True):
            st.query_params['role'] = role
            st.rerun()
    
    return None, None

def show_module(module_key, role):
    """Display a training module"""
    module = MODULE_CONTENT.get(module_key, {})
    
    # Get user-specific information
    user_info = {
        'admin': {'username': 'admin', 'password': 'admin123'},
        'manager': {'username': 'manager', 'password': 'manager123'},
        'viewer': {'username': 'viewer', 'password': 'view123'},
        'client': {'username': 'client', 'password': 'client123'}
    }.get(role, {'username': 'user', 'password': 'password'})
    
    # Format content with user-specific data
    content = module.get('content', '').format(**user_info)
    
    # Display module
    st.markdown(f"## {module.get('title', 'Training Module')}")
    st.markdown(f"**Estimated Duration:** {module.get('duration', 'N/A')}")
    st.markdown("---")
    st.markdown(content)
    
    # Add interactive elements based on module
    if module_key == 'password_management':
        with st.expander("🔐 Practice: Create Your Password"):
            st.text_input("Enter a new password:", type="password", key="practice_pwd")
            if st.button("Check Password Strength"):
                pwd = st.session_state.get('practice_pwd', '')
                score = 0
                feedback = []
                
                if len(pwd) >= 12:
                    score += 25
                    feedback.append("✅ Good length")
                else:
                    feedback.append("❌ Too short (need 12+ characters)")
                
                if any(c.isupper() for c in pwd) and any(c.islower() for c in pwd):
                    score += 25
                    feedback.append("✅ Mixed case")
                else:
                    feedback.append("❌ Add uppercase and lowercase")
                
                if any(c.isdigit() for c in pwd):
                    score += 25
                    feedback.append("✅ Contains numbers")
                else:
                    feedback.append("❌ Add numbers")
                
                if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in pwd):
                    score += 25
                    feedback.append("✅ Contains special characters")
                else:
                    feedback.append("❌ Add special characters")
                
                # Show score
                if score >= 75:
                    st.success(f"Strong Password! Score: {score}/100")
                elif score >= 50:
                    st.warning(f"Moderate Password. Score: {score}/100")
                else:
                    st.error(f"Weak Password! Score: {score}/100")
                
                for f in feedback:
                    st.write(f)

def main():
    # Apply branding
    st.markdown(branding.CUSTOM_CSS, unsafe_allow_html=True)
    
    # Check access
    access_value, access_type = check_training_access()
    if not access_value:
        return
    
    # Determine role
    if access_type == 'role':
        role = access_value
    else:
        # Token-based access - decode role from token
        role = 'viewer'  # Default for token access
    
    # Get training plan for role
    training_plan = TRAINING_MODULES.get(role, {})
    modules = training_plan.get('modules', [])
    
    # Sidebar navigation
    st.sidebar.markdown(f"# 📚 {training_plan.get('title', 'Training Guide')}")
    st.sidebar.markdown(f"**Role:** {role.title()}")
    st.sidebar.markdown("---")
    
    # Progress tracking
    if 'completed_modules' not in st.session_state:
        st.session_state.completed_modules = set()
    
    # Module selection
    st.sidebar.markdown("### 📖 Training Modules")
    
    selected_module = None
    for i, module_key in enumerate(modules, 1):
        module_info = MODULE_CONTENT.get(module_key, {})
        is_completed = module_key in st.session_state.completed_modules
        
        # Create button with completion indicator
        icon = "✅" if is_completed else f"{i}."
        if st.sidebar.button(
            f"{icon} {module_info.get('title', module_key)}",
            key=f"module_{module_key}",
            use_container_width=True
        ):
            selected_module = module_key
    
    # Progress bar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Training Progress")
    progress = len(st.session_state.completed_modules) / len(modules) if modules else 0
    st.sidebar.progress(progress)
    st.sidebar.markdown(f"**{len(st.session_state.completed_modules)}/{len(modules)}** modules completed")
    
    # Quick links
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔗 Quick Links")
    st.sidebar.markdown("""
    - [Download PDF Guide](#)
    - [Watch Video Tutorials](#)
    - [Contact Support](#)
    - [Report an Issue](#)
    """)
    
    # Main content area
    if selected_module:
        # Show selected module
        show_module(selected_module, role)
        
        # Module completion
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if selected_module not in st.session_state.completed_modules:
                if st.button("✅ Mark as Completed", use_container_width=True):
                    st.session_state.completed_modules.add(selected_module)
                    st.success("Module completed! Great job! 🎉")
                    st.balloons()
                    st.rerun()
            else:
                st.success("✅ You've completed this module!")
                if st.button("📖 Review Again", use_container_width=True):
                    pass  # Just stays on the same module
    else:
        # Welcome screen
        st.markdown(f"""
        # Welcome to the Training Center!
        
        ## 👋 Hello, {role.title()}!
        
        This interactive training guide will walk you through everything you need to know about using the Trailer Move Tracker system.
        
        ### 📚 Your Training Plan
        
        You have **{len(modules)} modules** to complete:
        """)
        
        # List modules with descriptions
        for i, module_key in enumerate(modules, 1):
            module_info = MODULE_CONTENT.get(module_key, {})
            is_completed = module_key in st.session_state.completed_modules
            status = "✅" if is_completed else "⏳"
            
            st.markdown(f"""
            **{i}. {module_info.get('title', module_key)}** {status}
            - Duration: {module_info.get('duration', 'N/A')}
            """)
        
        st.markdown("""
        ### 🎯 How to Use This Training
        
        1. **Start with Module 1** - Login & Access basics
        2. **Complete in Order** - Each module builds on the previous
        3. **Practice Along** - Have the main system open in another tab
        4. **Mark Complete** - Track your progress as you go
        5. **Ask Questions** - Contact support if you need help
        
        ### 🏆 Completion Certificate
        
        Complete all modules to receive your training certificate!
        
        ---
        
        **Ready to start?** Select the first module from the sidebar to begin your training.
        """)
        
        # Show completion certificate if all done
        if len(st.session_state.completed_modules) == len(modules):
            st.markdown("---")
            st.success("🎉 **Congratulations!** You've completed all training modules!")
            
            # Generate certificate
            st.markdown(f"""
            <div style="border: 3px solid #DC143C; padding: 2rem; text-align: center; border-radius: 10px;">
                <h2>🏆 Certificate of Completion</h2>
                <p>This certifies that</p>
                <h3>{role.title()} User</h3>
                <p>has successfully completed the</p>
                <h3>Trailer Move Tracker Training Program</h3>
                <p>Date: {datetime.now().strftime('%B %d, %Y')}</p>
                <br>
                <p><small>Smith and Williams Trucking</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🎓 Download Certificate"):
                st.info("Certificate download feature coming soon!")

if __name__ == "__main__":
    main()