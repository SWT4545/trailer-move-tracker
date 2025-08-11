"""
Interactive Training System for Smith & Williams Trucking
Complete role-based training modules with step-by-step tutorials
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import json
import time

def show_training_system():
    """Main training system interface"""
    st.title("🎓 Interactive Training System")
    st.caption("Learn how to use the Smith & Williams Trucking system for your role")
    
    # Initialize training session state
    if 'training_progress' not in st.session_state:
        st.session_state.training_progress = {}
    if 'training_step' not in st.session_state:
        st.session_state.training_step = 0
    if 'practice_data' not in st.session_state:
        st.session_state.practice_data = {}
    
    # Get user role
    user_role = st.session_state.get('user_role', 'viewer')
    user_name = st.session_state.get('user_name', 'User')
    
    st.info(f"Welcome to training, {user_name}! Your role: **{user_role.replace('_', ' ').title()}**")
    
    # Training navigation
    tabs = st.tabs(["📚 Overview", "🎯 Role Training", "📝 Interactive Tutorial", 
                     "🎮 Practice Mode", "📊 Progress", "🏆 Certification"])
    
    with tabs[0]:
        show_training_overview(user_role)
    
    with tabs[1]:
        show_role_specific_training(user_role)
    
    with tabs[2]:
        show_interactive_tutorial(user_role)
    
    with tabs[3]:
        show_practice_mode(user_role)
    
    with tabs[4]:
        show_training_progress(user_role)
    
    with tabs[5]:
        show_certification(user_role)

def show_training_overview(role):
    """Show training overview for the role"""
    st.markdown("### 📚 Training Overview")
    
    # Role descriptions
    role_descriptions = {
        'executive': """
        As an **Executive**, you have complete system control. Your training covers:
        - Financial oversight and reporting
        - Team performance management
        - Strategic decision making
        - System administration
        - Growth analytics
        """,
        'admin': """
        As an **Administrator**, you manage the entire system. Your training covers:
        - User management and permissions
        - System configuration
        - Database management
        - Report generation
        - System monitoring
        """,
        'operations_coordinator': """
        As an **Operations Coordinator**, you manage daily operations. Your training covers:
        - Route planning and optimization
        - Driver assignments
        - Location management
        - Communication with team
        - Operational reporting
        """,
        'operations_specialist': """
        As an **Operations Specialist**, you handle data entry and updates. Your training covers:
        - Trailer tracking
        - Location updates
        - Data entry best practices
        - Progress monitoring
        - Accuracy verification
        """,
        'viewer': """
        As a **Viewer**, you have read-only access. Your training covers:
        - Viewing dashboards
        - Understanding metrics
        - Accessing reports
        - Tracking progress
        """,
        'client': """
        As a **Client**, you can track your shipments. Your training covers:
        - Viewing shipment status
        - Understanding delivery timelines
        - Accessing progress updates
        """
    }
    
    st.markdown(role_descriptions.get(role, "Role-specific training"))
    
    # Training modules for role
    st.markdown("### 📋 Your Training Modules")
    
    modules = get_training_modules(role)
    
    for i, module in enumerate(modules, 1):
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(f"**Module {i}:** {module['title']}")
        with col2:
            st.caption(f"⏱️ {module['duration']}")
        with col3:
            status = module.get('status', 'Not Started')
            if status == 'Completed':
                st.success("✅ Done")
            elif status == 'In Progress':
                st.warning("⏳ Active")
            else:
                st.info("📘 Ready")
        with col4:
            if st.button("Start", key=f"start_{i}"):
                st.session_state.current_module = i
                st.session_state.training_tab = 1
                st.rerun()

def get_training_modules(role):
    """Get training modules for specific role"""
    modules = {
        'executive': [
            {'title': 'Executive Dashboard Overview', 'duration': '15 min', 'status': 'Not Started'},
            {'title': 'Financial Reporting & Analytics', 'duration': '20 min', 'status': 'Not Started'},
            {'title': 'Team Performance Management', 'duration': '15 min', 'status': 'Not Started'},
            {'title': 'System Administration', 'duration': '20 min', 'status': 'Not Started'},
            {'title': 'Strategic Planning Tools', 'duration': '15 min', 'status': 'Not Started'}
        ],
        'admin': [
            {'title': 'System Overview', 'duration': '10 min', 'status': 'Not Started'},
            {'title': 'User Management', 'duration': '20 min', 'status': 'Not Started'},
            {'title': 'Database Operations', 'duration': '15 min', 'status': 'Not Started'},
            {'title': 'Report Generation', 'duration': '15 min', 'status': 'Not Started'},
            {'title': 'System Maintenance', 'duration': '10 min', 'status': 'Not Started'}
        ],
        'operations_coordinator': [
            {'title': 'Dashboard Navigation', 'duration': '10 min', 'status': 'Not Started'},
            {'title': 'Adding New Moves', 'duration': '20 min', 'status': 'Not Started'},
            {'title': 'Managing Locations & Drivers', 'duration': '15 min', 'status': 'Not Started'},
            {'title': 'Trailer Management', 'duration': '15 min', 'status': 'Not Started'},
            {'title': 'Communication Tools', 'duration': '10 min', 'status': 'Not Started'},
            {'title': 'Report Generation', 'duration': '10 min', 'status': 'Not Started'}
        ],
        'operations_specialist': [
            {'title': 'Data Entry Basics', 'duration': '10 min', 'status': 'Not Started'},
            {'title': 'Updating Trailer Information', 'duration': '15 min', 'status': 'Not Started'},
            {'title': 'Location Management', 'duration': '10 min', 'status': 'Not Started'},
            {'title': 'Progress Tracking', 'duration': '10 min', 'status': 'Not Started'}
        ],
        'viewer': [
            {'title': 'Dashboard Overview', 'duration': '5 min', 'status': 'Not Started'},
            {'title': 'Understanding Metrics', 'duration': '10 min', 'status': 'Not Started'},
            {'title': 'Viewing Reports', 'duration': '5 min', 'status': 'Not Started'}
        ],
        'client': [
            {'title': 'Accessing Your Dashboard', 'duration': '5 min', 'status': 'Not Started'},
            {'title': 'Tracking Shipments', 'duration': '10 min', 'status': 'Not Started'}
        ]
    }
    
    return modules.get(role, [])

def show_role_specific_training(role):
    """Show detailed role-specific training"""
    st.markdown(f"### 🎯 {role.replace('_', ' ').title()} Training")
    
    if role == 'executive':
        show_executive_training()
    elif role == 'admin':
        show_admin_training()
    elif role == 'operations_coordinator':
        show_coordinator_training()
    elif role == 'operations_specialist':
        show_specialist_training()
    elif role == 'viewer':
        show_viewer_training()
    elif role == 'client':
        show_client_training()

def show_executive_training():
    """Executive role training"""
    st.markdown("## Executive Training Program")
    
    with st.expander("📊 Module 1: Executive Dashboard", expanded=True):
        st.markdown("""
        ### Understanding Your Executive Dashboard
        
        As CEO, your dashboard provides complete visibility into:
        
        **Key Metrics:**
        - 📊 **Total Moves**: Overall trailer movements
        - 💰 **Total Revenue**: Financial performance
        - 📝 **Unpaid Amount**: Outstanding payments
        - 📈 **Profit Margin**: Current profitability
        - 🎯 **YTD Goal**: Year-to-date progress
        
        **Executive Actions:**
        1. **Financial Report** - Access detailed financial analytics
        2. **Team Performance** - Review team metrics and productivity
        3. **Growth Analytics** - Analyze business growth trends
        4. **System Audit** - Review system usage and security
        
        **Try it:** Navigate to your dashboard and identify these elements.
        """)
        
        if st.button("✅ Complete Module 1", key="exec_mod1"):
            st.success("Module 1 completed!")
    
    with st.expander("🏢 Module 2: Base Location Management", expanded=False):
        st.markdown("""
        ### Managing Base Locations (NEW CAPABILITY)
        
        **Executive Control Over Base Locations:**
        
        **Access:** Navigate to 🏢 Base Locations in the menu
        
        **Key Functions:**
        1. **View Current Base Locations**
           - See all active base locations
           - Identify current default (e.g., Fleet Memphis)
           - Review location addresses and details
        
        2. **Add New Base Location**
           - Enter location name (e.g., "Fleet Dallas")
           - Provide full address for mileage calculation
           - Set as default if needed
        
        3. **Change Default Base**
           - Select new default from existing bases
           - Provide reason for change (audit trail)
           - All new moves will use new base
        
        4. **Deactivate Base Location**
           - Remove unused base locations
           - Cannot deactivate current default
           - Maintains historical data
        
        **Business Impact:**
        - Flexibility for expansion
        - Support for multiple vendor locations
        - Accurate mileage from any base
        - Complete audit trail of changes
        
        **Important:** Changing the default base affects ALL new trailer moves!
        """)
        
        if st.button("✅ Complete Module 2", key="exec_mod2"):
            st.success("Module 2 completed!")
    
    with st.expander("💰 Module 3: Financial Management"):
        st.markdown("""
        ### Financial Oversight and Control
        
        **Key Financial Features:**
        
        1. **Revenue Tracking**
           - View daily, weekly, monthly revenue
           - Track payment status
           - Monitor collection rates
        
        2. **Cost Analysis**
           - Factor fees
           - Operational costs
           - Profit margins
        
        3. **Financial Reports**
           - Generate P&L statements
           - Export financial data
           - Create investor reports
        
        **Exercise:** Generate a financial report for the last 30 days.
        """)
        
        if st.button("✅ Complete Module 2", key="exec_mod2"):
            st.success("Module 2 completed!")
    
    with st.expander("👥 Module 3: Team Management"):
        st.markdown("""
        ### Managing Your Team
        
        **User Management:**
        1. Navigate to User Management
        2. Add new users with appropriate roles
        3. Modify permissions
        4. Deactivate users when needed
        
        **Team Performance:**
        - Review individual performance metrics
        - Track productivity trends
        - Identify top performers
        - Address performance issues
        
        **Communication:**
        - Send system-wide announcements
        - Email team members
        - Set up automated notifications
        """)
        
        if st.button("✅ Complete Module 3", key="exec_mod3"):
            st.success("Module 3 completed!")

def show_admin_training():
    """Admin role training"""
    st.markdown("## Administrator Training Program")
    
    with st.expander("🛠️ Module 1: System Administration", expanded=True):
        st.markdown("""
        ### System Administration Basics
        
        **Your Responsibilities:**
        - User account management
        - System configuration
        - Database maintenance
        - Security monitoring
        - Report generation
        - Base location management (NEW)
        
        **Key Areas:**
        1. **User Management** - Create, modify, delete users
        2. **Base Locations** - Manage vendor base locations
        3. **Backup Database** - Regular system backups
        4. **System Reports** - Generate usage reports
        5. **Data Sync** - Ensure data consistency
        
        **Daily Tasks:**
        - Check system health metrics
        - Review user activity logs
        - Monitor error reports
        - Perform routine backups
        """)
        
        if st.button("✅ Complete Module 1", key="admin_mod1"):
            st.success("Module 1 completed!")
    
    with st.expander("🏢 Module 2: Base Location Management", expanded=False):
        st.markdown("""
        ### Managing Base Locations as Administrator
        
        **Access:** 🏢 Base Locations in the navigation menu
        
        **Key Functions:**
        1. **Add New Base Locations**
           - Enter complete address
           - Support expansion
        
        2. **Change Default Base**
           - Update as needed
           - Document changes
        
        3. **Monitor Active Bases**
           - Track all locations
           - Ensure data accuracy
        
        **Impact:** Base location changes affect all new moves!
        """)
        
        if st.button("✅ Complete Base Module", key="admin_base"):
            st.success("Base Location module completed!")
    
    with st.expander("👤 Module 3: User Management"):
        st.markdown("""
        ### Managing System Users
        
        **Step-by-Step User Creation:**
        
        1. **Navigate to User Management**
           - Click "👥 User Management" in sidebar
        
        2. **Add New User Tab**
           - Enter username (unique)
           - Set password (secure)
           - Assign appropriate role
           - Add contact information
        
        3. **Role Assignment:**
           - Executive: Full system access
           - Admin: System management
           - Operations Coordinator: Operational control
           - Operations Specialist: Data entry
           - Viewer: Read-only access
           - Client: Progress tracking only
        
        **Practice:** Create a test user account.
        """)
        
        if st.button("✅ Complete Module 2", key="admin_mod2"):
            st.success("Module 2 completed!")

def show_coordinator_training():
    """Operations Coordinator training - Fleet Memphis Workflow"""
    st.markdown("## Operations Coordinator Training - Fleet Memphis Round Trips")
    
    with st.expander("🚛 Module 1: Fleet Memphis Trailer Swap Process", expanded=True):
        st.markdown("""
        ### Understanding the Trailer Swap Workflow
        
        **CRITICAL: The Proper Process Flow**
        
        **Step 1: TRAILER ENTRY (Must be done FIRST)**
        - Go to 🚛 Trailer Management
        - Check current base location (shown at top)
        - Enter BOTH trailers as a pair:
          - NEW trailer (from base location)
          - OLD trailer (at swap location)
        - Specify the swap location with FULL ADDRESS
        - System calculates round-trip mileage automatically
        
        **Step 2: CREATE MOVE (Only AFTER trailers are entered)**
        - Go to ➕ Create Move
        - Select from EXISTING trailer pairs only
        - Assign a driver
        - Confirm round-trip details:
          - Base Location → Swap Location (deliver NEW)
          - Swap Location → Base Location (pickup OLD)
        
        **Key Points:**
        - ALL moves are ROUND TRIPS from the base location
        - Base location can be changed by Admin/Executive
        - Mileage = One-way × 2
        - Payment calculation: Round-trip miles × Rate × (1 - Factor Fee)
        - Factor company needs accurate mileage for payment processing
        """)
        
        if st.button("✅ Complete Module 1", key="coord_mod1"):
            st.success("Module 1 completed!")
    
    with st.expander("➕ Module 2: Adding New Moves - COMPLETE GUIDE"):
        st.markdown("""
        ### Step-by-Step: Adding a New Trailer Move
        
        **COMPLETE PROCESS:**
        
        **Step 1: Navigate to Add New Move**
        - Click "➕ Add New Move" in sidebar or quick actions
        
        **Step 2: Enter Trailer Information**
        - **New Trailer Number**: Enter trailer ID (e.g., TRL-001)
        - **Pickup Location**: Select from dropdown or add new
        - **Pickup Date**: Select date
        - **Old Trailer** (optional): If swapping trailers
        - **Destination**: Select delivery location
        - **Completion Date**: Leave blank if not completed
        
        **Step 3: Assignment & Mileage**
        - **Driver**: Select from list or add new driver
        - **Miles**: Enter distance (check for cached mileage)
        - **Rate**: Default $2.10/mile (adjust if needed)
        - **Factor Fee**: Default 3% (0.03)
        
        **Step 4: Calculate Load Pay**
        - System automatically calculates: Miles × Rate × (1 - Factor Fee)
        - Example: 100 miles × $2.10 × 0.97 = $203.70
        
        **Step 5: Set Status**
        - ✅ Received PPW (Proof of Pickup/Weight)
        - ✅ Processed
        - ✅ Paid (if payment received)
        
        **Step 6: Add Notes & Submit**
        - Add any special instructions
        - Click "✅ Add Move"
        
        **What Happens Next:**
        - Move is saved to database
        - Trailers are added to management system
        - Driver is assigned
        - Mileage can be cached for future use
        """)
        
        # Interactive demo
        st.info("💡 **Try it:** Add a practice move with these details:")
        st.code("""
        New Trailer: TRL-TEST-001
        Pickup: Dallas Terminal
        Destination: Houston Warehouse
        Driver: John Smith
        Miles: 245
        Rate: $2.10
        """)
        
        if st.button("✅ Complete Module 2", key="coord_mod2"):
            st.success("Module 2 completed!")
    
    with st.expander("📍 Module 3: Location & Driver Management"):
        st.markdown("""
        ### Managing Locations and Drivers
        
        **Adding a New Location:**
        1. Go to "📍 Manage Locations"
        2. Click "➕ Add Location"
        3. Enter location name and address
        4. Click "✅ Add"
        
        **Adding a New Driver:**
        1. Go to "👥 Manage Drivers"
        2. Click "➕ Add Driver"
        3. Enter driver details:
           - Name (required)
           - Truck number
           - Company
           - DOT/MC numbers
           - Insurance info
        4. Click "✅ Add"
        
        **Pro Tips:**
        - Keep location names consistent
        - Always include city/state in location names
        - Verify DOT/MC numbers
        - Update driver info regularly
        """)
        
        if st.button("✅ Complete Module 3", key="coord_mod3"):
            st.success("Module 3 completed!")
    
    with st.expander("📧 Module 4: Communication"):
        st.markdown("""
        ### Using Communication Tools
        
        **Email Center:**
        1. Navigate to "✉️ Email Center"
        2. Compose email:
           - To: Enter recipient email
           - CC: Optional copies
           - Subject: Clear, descriptive
           - Message: Professional content
        3. Add signature (automatic)
        4. Send email
        
        **Email Templates:**
        - Route Assignment
        - Delivery Confirmation
        - Payment Update
        - Welcome Message
        
        **Best Practices:**
        - Use templates for consistency
        - Keep records of important communications
        - Follow up on urgent matters
        """)
        
        if st.button("✅ Complete Module 4", key="coord_mod4"):
            st.success("Module 4 completed!")

def show_specialist_training():
    """Operations Specialist training"""
    st.markdown("## Operations Specialist Training Program")
    
    with st.expander("📝 Module 1: Data Entry Fundamentals", expanded=True):
        st.markdown("""
        ### Data Entry Best Practices
        
        **Your Role:**
        - Update trailer locations
        - Enter new location data
        - Track trailer status
        - Maintain data accuracy
        
        **Key Responsibilities:**
        1. **Accuracy**: Double-check all entries
        2. **Timeliness**: Update information promptly
        3. **Completeness**: Fill all required fields
        4. **Consistency**: Use standard naming conventions
        
        **Dashboard Metrics:**
        - 📝 **Entries Today**: Your daily count
        - 📍 **Locations Updated**: Location changes
        - ✅ **Accuracy**: Your accuracy rate
        - ⏳ **Pending**: Items awaiting update
        """)
        
        if st.button("✅ Complete Module 1", key="spec_mod1"):
            st.success("Module 1 completed!")
    
    with st.expander("🚛 Module 2: Updating Trailer Information"):
        st.markdown("""
        ### How to Update Trailer Status
        
        **Step-by-Step Process:**
        
        1. **Navigate to Trailer Management**
           - Click "🚛 Update Trailers" from your dashboard
        
        2. **Locate Trailer**
           - Find trailer in the list
           - Note current status
        
        3. **Update Information**
           - Current Location
           - Status (available/assigned/completed)
           - Loaded/Empty
           - Add notes if needed
        
        4. **Save Changes**
           - Verify information
           - Submit update
        
        **Important: You can edit but NOT delete records**
        """)
        
        if st.button("✅ Complete Module 2", key="spec_mod2"):
            st.success("Module 2 completed!")
    
    with st.expander("📍 Module 3: Location Updates"):
        st.markdown("""
        ### Managing Location Information
        
        **Adding/Updating Locations:**
        
        1. **Go to Location Management**
           - Click "📍 Update Locations"
        
        2. **Add New Location**
           - Location name (be specific)
           - Full address
           - Any special notes
        
        3. **Naming Convention:**
           - Format: "Company - City, State"
           - Example: "FedEx - Dallas, TX"
           - Be consistent!
        
        **Quality Checks:**
        - Verify addresses are complete
        - Check for duplicates
        - Ensure city/state accuracy
        """)
        
        if st.button("✅ Complete Module 3", key="spec_mod3"):
            st.success("Module 3 completed!")

def show_viewer_training():
    """Viewer role training"""
    st.markdown("## Viewer Training Program")
    
    with st.expander("👁️ Module 1: Understanding Your Access", expanded=True):
        st.markdown("""
        ### Read-Only Access Overview
        
        **What You Can Do:**
        - View dashboard metrics
        - See progress updates
        - Access basic reports
        - Track trailer movements
        
        **What You Cannot Do:**
        - Edit any data
        - Add new records
        - Delete information
        - Access financial data
        
        **Your Dashboard Shows:**
        - 📊 Total Moves
        - 🚛 In Progress
        - ✅ Completed Today
        - 📈 This Week
        """)
        
        if st.button("✅ Complete Module 1", key="viewer_mod1"):
            st.success("Module 1 completed!")
    
    with st.expander("📊 Module 2: Viewing Reports"):
        st.markdown("""
        ### Accessing Progress Dashboard
        
        1. **Click "📊 View Progress Dashboard"**
        2. **Review Metrics:**
           - Today's moves
           - Weekly activity
           - In progress count
           - Completion status
        
        3. **Understanding Tables:**
           - Active Routes: Current movements
           - Recently Completed: Finished deliveries
        
        **Note:** Financial information is hidden from your view
        """)
        
        if st.button("✅ Complete Module 2", key="viewer_mod2"):
            st.success("Module 2 completed!")

def show_client_training():
    """Client role training"""
    st.markdown("## Client Training Program")
    
    with st.expander("📦 Module 1: Tracking Your Shipments", expanded=True):
        st.markdown("""
        ### Welcome to Your Client Portal
        
        **Your Access:**
        - View your shipment progress
        - Track delivery status
        - See estimated arrival times
        
        **Progress Dashboard Features:**
        - Real-time shipment tracking
        - Delivery status updates
        - Route information
        - Completion notifications
        
        **Understanding Status:**
        - 🚛 **In Transit**: Currently moving
        - 📍 **At Location**: Stopped at waypoint
        - ✅ **Delivered**: Completed delivery
        """)
        
        if st.button("✅ Complete Module 1", key="client_mod1"):
            st.success("Module 1 completed!")

def show_interactive_tutorial(role):
    """Interactive step-by-step tutorial"""
    st.markdown("### 📝 Interactive Tutorial")
    
    if 'tutorial_step' not in st.session_state:
        st.session_state.tutorial_step = 0
    
    tutorials = get_role_tutorials(role)
    
    if st.session_state.tutorial_step < len(tutorials):
        current_step = tutorials[st.session_state.tutorial_step]
        
        # Progress bar
        progress = (st.session_state.tutorial_step + 1) / len(tutorials)
        st.progress(progress)
        st.write(f"Step {st.session_state.tutorial_step + 1} of {len(tutorials)}")
        
        # Display current step
        st.markdown(f"### {current_step['title']}")
        st.info(current_step['instruction'])
        
        # Show image or demo if available
        if 'demo' in current_step:
            st.code(current_step['demo'])
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.session_state.tutorial_step > 0:
                if st.button("⬅️ Previous"):
                    st.session_state.tutorial_step -= 1
                    st.rerun()
        
        with col2:
            if st.button("🔄 Restart Tutorial"):
                st.session_state.tutorial_step = 0
                st.rerun()
        
        with col3:
            if st.button("Next ➡️", type="primary"):
                st.session_state.tutorial_step += 1
                st.rerun()
    else:
        st.success("🎉 Tutorial Complete!")
        st.balloons()
        
        if st.button("Start Over"):
            st.session_state.tutorial_step = 0
            st.rerun()

def get_role_tutorials(role):
    """Get interactive tutorials for each role"""
    tutorials = {
        'operations_coordinator': [
            {
                'title': 'Step 1: Understanding Fleet Memphis Round Trips',
                'instruction': 'ALL trailer moves are round trips starting and ending at Fleet Memphis. You swap NEW trailers for OLD trailers.',
                'demo': 'Fleet Memphis → Swap Location → Fleet Memphis'
            },
            {
                'title': 'Step 2: Add Trailer Pairs FIRST',
                'instruction': 'Before creating any move, go to "🚛 Trailer Management" to enter trailer pairs.',
                'demo': 'Navigation: Sidebar → 🚛 Trailer Management'
            },
            {
                'title': 'Step 3: Enter NEW Trailer',
                'instruction': 'Enter the NEW trailer number that will be picked up FROM Fleet Memphis.',
                'demo': 'New Trailer: TRL-NEW-2024-001\nLocation: Fleet Memphis'
            },
            {
                'title': 'Step 4: Enter OLD Trailer',
                'instruction': 'Enter the OLD trailer number that needs to be picked up from the swap location.',
                'demo': 'Old Trailer: TRL-OLD-2023-050\nLocation: Dallas Terminal'
            },
            {
                'title': 'Step 5: Specify Swap Location',
                'instruction': 'Select the location where the trailer swap will occur. Must have FULL ADDRESS for mileage.',
                'demo': 'Swap Location: Dallas Terminal\nAddress: 1234 Main St, Dallas, TX 75201'
            },
            {
                'title': 'Step 6: System Calculates Round Trip',
                'instruction': 'The system automatically calculates ROUND TRIP mileage (one-way × 2).',
                'demo': 'One-way: 245 miles\nRound-trip: 490 miles\nPay: $947.61'
            },
            {
                'title': 'Step 7: Create Move from Existing Pairs',
                'instruction': 'Go to "➕ Create Move" and select from EXISTING trailer pairs only.',
                'demo': 'Select: NEW TRL-2024-001 ↔ OLD TRL-2023-050 @ Dallas'
            },
            {
                'title': 'Step 8: Assign Driver',
                'instruction': 'Select the driver who will complete this round trip.',
                'demo': 'Driver: John Smith\nRoute: 490 miles round trip'
            },
            {
                'title': 'Step 9: Verify Payment Calculation',
                'instruction': 'Confirm load pay: Round-trip miles × Rate × (1 - Factor Fee). This is what the factor company needs.',
                'demo': '490 miles × $2.10 × 0.97 = $998.97'
            },
            {
                'title': 'Step 10: Complete and Track',
                'instruction': 'Submit the move and track progress. Remember: Trailers MUST be entered BEFORE creating moves!',
                'demo': 'Status: Round trip assigned to driver'
            },
            {
                'title': 'Send Updates',
                'instruction': 'Use the Email Center to notify drivers and clients about assignments.',
                'demo': 'Email Center → Compose → Use Templates'
            }
        ],
        'operations_specialist': [
            {
                'title': 'Your Data Entry Dashboard',
                'instruction': 'Focus on your metrics: Entries Today, Locations Updated, and Accuracy.',
                'demo': 'Today: 12 entries | 99.5% accuracy'
            },
            {
                'title': 'Updating Locations',
                'instruction': 'Click "📍 Update Locations" to manage location data.',
                'demo': 'Quick Action → 📍 Update Locations'
            },
            {
                'title': 'Adding a Location',
                'instruction': 'Click "➕ Add Location" and enter the name and address.',
                'demo': 'Name: FedEx - Memphis, TN\nAddress: 123 Logistics Way'
            },
            {
                'title': 'Updating Trailers',
                'instruction': 'Navigate to Trailer Management to update trailer status.',
                'demo': 'Status Options: Available | Assigned | Completed'
            },
            {
                'title': 'Data Entry Standards',
                'instruction': 'Always use consistent naming: "Company - City, State"',
                'demo': 'Correct: "UPS - Atlanta, GA"\nWrong: "ups atlanta"'
            }
        ],
        'admin': [
            {
                'title': 'System Health Check',
                'instruction': 'Start each day by reviewing system health metrics on your dashboard.',
                'demo': 'System Health: 100% | Active Users: 24'
            },
            {
                'title': 'User Management',
                'instruction': 'Access User Management to add, edit, or deactivate users.',
                'demo': 'Navigation: Sidebar → 👥 User Management'
            },
            {
                'title': 'Creating a User',
                'instruction': 'Fill in username, password, role, and contact information.',
                'demo': 'Username: jdoe\nRole: Operations Specialist\nEmail: jdoe@company.com'
            },
            {
                'title': 'Database Backup',
                'instruction': 'Perform regular backups using the backup button on your dashboard.',
                'demo': 'Quick Action → 💾 Backup Database'
            },
            {
                'title': 'System Reports',
                'instruction': 'Generate system usage and activity reports regularly.',
                'demo': 'Reports → System Activity → Last 30 Days'
            }
        ],
        'executive': [
            {
                'title': 'Executive Overview',
                'instruction': 'Your dashboard shows key business metrics at a glance.',
                'demo': 'Revenue: $456,780 | Profit Margin: 24.5%'
            },
            {
                'title': 'Financial Reports',
                'instruction': 'Access detailed financial analytics through Executive Actions.',
                'demo': 'Executive Actions → 📊 Financial Report'
            },
            {
                'title': 'Team Performance',
                'instruction': 'Review team productivity and individual performance metrics.',
                'demo': 'Team Performance → Driver Efficiency → Route Completion'
            },
            {
                'title': 'Strategic Planning',
                'instruction': 'Use Growth Analytics to make data-driven decisions.',
                'demo': 'Growth Analytics → Revenue Trends → Forecast'
            }
        ],
        'viewer': [
            {
                'title': 'Accessing Your Dashboard',
                'instruction': 'Your dashboard shows read-only metrics and progress.',
                'demo': 'View Only: Total Moves | In Progress | Completed'
            },
            {
                'title': 'Progress Dashboard',
                'instruction': 'Click to view detailed progress information.',
                'demo': 'Button: 📊 View Progress Dashboard'
            }
        ],
        'client': [
            {
                'title': 'Your Shipment Dashboard',
                'instruction': 'Access the Progress Dashboard to track your shipments.',
                'demo': 'Progress Dashboard → Your Active Shipments'
            },
            {
                'title': 'Understanding Status',
                'instruction': 'Each shipment shows current status and location.',
                'demo': 'Status: 🚛 In Transit | Location: Dallas, TX'
            }
        ]
    }
    
    return tutorials.get(role, [])

def show_practice_mode(role):
    """Practice mode with sample data"""
    st.markdown("### 🎮 Practice Mode")
    st.info("Practice with sample data without affecting the real system")
    
    if role in ['operations_coordinator', 'admin', 'executive']:
        st.markdown("#### Practice Exercise: Add a New Move")
        
        with st.form("practice_move"):
            col1, col2 = st.columns(2)
            
            with col1:
                trailer = st.text_input("New Trailer Number", value="PRACTICE-001")
                pickup = st.selectbox("Pickup Location", ["Dallas Terminal", "Houston Yard", "Austin Depot"])
                pickup_date = st.date_input("Pickup Date", value=date.today())
            
            with col2:
                destination = st.selectbox("Destination", ["Chicago Hub", "Memphis Fleet", "Atlanta Center"])
                driver = st.selectbox("Driver", ["John Smith", "Jane Doe", "Bob Wilson"])
                miles = st.number_input("Miles", value=250)
            
            submitted = st.form_submit_button("Submit Practice Move")
            
            if submitted:
                st.success("✅ Practice move submitted successfully!")
                st.info(f"""
                **Summary:**
                - Trailer: {trailer}
                - Route: {pickup} → {destination}
                - Driver: {driver}
                - Distance: {miles} miles
                - Load Pay: ${miles * 2.10 * 0.97:.2f}
                """)
                st.balloons()
    
    elif role == 'operations_specialist':
        st.markdown("#### Practice Exercise: Update Location")
        
        with st.form("practice_location"):
            name = st.text_input("Location Name", placeholder="Company - City, State")
            address = st.text_input("Address", placeholder="123 Main St, City, State ZIP")
            
            submitted = st.form_submit_button("Add Practice Location")
            
            if submitted:
                if name and address:
                    st.success(f"✅ Practice location '{name}' added!")
                else:
                    st.error("Please fill all fields")
    
    else:
        st.markdown("#### Practice Exercise: View Dashboard")
        st.info("Navigate through the dashboard to familiarize yourself with the interface")
        
        # Sample data display
        sample_data = pd.DataFrame({
            'Trailer': ['TRL-001', 'TRL-002', 'TRL-003'],
            'Status': ['In Transit', 'Delivered', 'Loading'],
            'Location': ['Dallas', 'Houston', 'Austin'],
            'Driver': ['John Smith', 'Jane Doe', 'Bob Wilson']
        })
        
        st.dataframe(sample_data, use_container_width=True, hide_index=True)

def show_training_progress(role):
    """Show training progress and scores"""
    st.markdown("### 📊 Your Training Progress")
    
    # Calculate progress
    modules = get_training_modules(role)
    completed = sum(1 for m in modules if m.get('status') == 'Completed')
    total = len(modules)
    progress = completed / total if total > 0 else 0
    
    # Display progress
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Modules Completed", f"{completed}/{total}")
        st.progress(progress)
    
    with col2:
        st.metric("Training Score", f"{int(progress * 100)}%")
    
    with col3:
        status = "🏆 Complete" if progress == 1 else "📚 In Progress"
        st.metric("Status", status)
    
    # Module breakdown
    st.markdown("#### Module Status")
    for i, module in enumerate(modules, 1):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"{i}. {module['title']}")
        with col2:
            st.caption(module['duration'])
        with col3:
            if module.get('status') == 'Completed':
                st.success("✅")
            else:
                st.info("⏳")
    
    # Training history
    st.markdown("#### Recent Activity")
    activity = pd.DataFrame({
        'Date': [datetime.now() - timedelta(days=i) for i in range(5)],
        'Module': ['Dashboard Overview', 'Adding Moves', 'Location Management', 'Practice Mode', 'Tutorial'],
        'Score': ['100%', '95%', '100%', '90%', '100%'],
        'Time Spent': ['15 min', '25 min', '20 min', '30 min', '10 min']
    })
    
    st.dataframe(activity, use_container_width=True, hide_index=True)

def show_certification(role):
    """Show certification status and tests"""
    st.markdown("### 🏆 Certification")
    
    # Check if eligible for certification
    modules = get_training_modules(role)
    completed = sum(1 for m in modules if m.get('status') == 'Completed')
    eligible = completed == len(modules)
    
    if eligible:
        st.success("✅ You are eligible for certification!")
        
        st.markdown("#### Certification Test")
        st.info(f"Complete the {role.replace('_', ' ').title()} certification test to receive your certificate")
        
        if st.button("Start Certification Test", type="primary"):
            st.session_state.cert_test = True
            
        if st.session_state.get('cert_test'):
            show_certification_test(role)
    else:
        st.warning(f"⏳ Complete all {len(modules)} training modules to unlock certification")
        st.progress(completed / len(modules))
        st.write(f"Progress: {completed}/{len(modules)} modules completed")

def show_certification_test(role):
    """Show role-specific certification test"""
    st.markdown("#### Certification Test")
    
    questions = get_certification_questions(role)
    
    with st.form("cert_test"):
        answers = []
        
        for i, q in enumerate(questions, 1):
            st.markdown(f"**Question {i}:** {q['question']}")
            answer = st.radio(
                "Select answer:",
                q['options'],
                key=f"q{i}",
                label_visibility="collapsed"
            )
            answers.append(answer == q['correct'])
        
        submitted = st.form_submit_button("Submit Test", type="primary")
        
        if submitted:
            score = sum(answers) / len(answers) * 100
            
            if score >= 80:
                st.success(f"🏆 Congratulations! You passed with {score:.0f}%")
                st.balloons()
                
                # Generate certificate
                st.markdown("### Your Certificate")
                st.info(f"""
                **Smith & Williams Trucking**
                
                This certifies that
                
                **{st.session_state.get('user_name', 'User')}**
                
                has successfully completed the
                
                **{role.replace('_', ' ').title()} Training Program**
                
                Date: {datetime.now().strftime('%B %d, %Y')}
                Score: {score:.0f}%
                
                Certificate ID: SWT-{role.upper()[:3]}-{datetime.now().strftime('%Y%m%d')}
                """)
                
                if st.button("Download Certificate"):
                    st.success("Certificate downloaded!")
            else:
                st.error(f"Score: {score:.0f}%. You need 80% to pass. Please review and try again.")

def get_certification_questions(role):
    """Get certification questions for role"""
    questions = {
        'operations_coordinator': [
            {
                'question': 'What is the formula for calculating load pay?',
                'options': [
                    'Miles × Rate',
                    'Miles × Rate × Factor Fee',
                    'Miles × Rate × (1 - Factor Fee)',
                    'Miles + Rate - Factor Fee'
                ],
                'correct': 'Miles × Rate × (1 - Factor Fee)'
            },
            {
                'question': 'When adding a new move, what information is required?',
                'options': [
                    'Only trailer number',
                    'Trailer number, pickup location, and destination',
                    'Just driver name',
                    'Only mileage'
                ],
                'correct': 'Trailer number, pickup location, and destination'
            },
            {
                'question': 'What happens when you save mileage for a route?',
                'options': [
                    'Nothing',
                    'It deletes old mileage',
                    'It caches for future use on the same route',
                    'It sends an email'
                ],
                'correct': 'It caches for future use on the same route'
            }
        ],
        'operations_specialist': [
            {
                'question': 'What is the correct location naming format?',
                'options': [
                    'company',
                    'city only',
                    'Company - City, State',
                    'Whatever you want'
                ],
                'correct': 'Company - City, State'
            },
            {
                'question': 'Can you delete records as an Operations Specialist?',
                'options': [
                    'Yes, all records',
                    'No, you can only edit',
                    'Only trailer records',
                    'Only old records'
                ],
                'correct': 'No, you can only edit'
            }
        ]
    }
    
    return questions.get(role, [
        {
            'question': 'What is your primary role responsibility?',
            'options': ['Unknown', 'Viewing data', 'Managing system', 'Entering data'],
            'correct': 'Viewing data'
        }
    ])

if __name__ == "__main__":
    # Test the training system
    st.set_page_config(page_title="Training System", layout="wide")
    
    # Mock session state for testing
    if 'user_role' not in st.session_state:
        st.session_state.user_role = st.selectbox(
            "Select role to test:",
            ['executive', 'admin', 'operations_coordinator', 'operations_specialist', 'viewer', 'client']
        )
        st.session_state.user_name = "Test User"
    
    show_training_system()