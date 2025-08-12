"""
Step-by-Step Walkthrough Guide for Smith & Williams Trucking
Interactive training system for all user roles
"""

import streamlit as st

def show_walkthrough():
    """Main walkthrough interface"""
    st.title("🎓 System Walkthrough")
    st.caption("Learn how to use the Trailer Swap Management System")
    
    # Check for dual roles
    user_roles = st.session_state.get('user_roles', [st.session_state.get('user_role', 'viewer')])
    role = st.session_state.get('user_role', 'viewer')
    
    # Show dual-role notice if applicable
    if len(user_roles) > 1:
        st.info(f"🔄 **Dual-Role User**: You have access to multiple roles: {', '.join([r.replace('_', ' ').title() for r in user_roles])}. Use the role switcher in the sidebar to change views.")
    
    # Role-specific walkthroughs
    if role == 'business_administrator':
        show_admin_walkthrough()
    elif role == 'operations_coordinator':
        show_coordinator_walkthrough()
    elif role == 'driver':
        show_driver_walkthrough()
    elif role == 'viewer':
        show_viewer_walkthrough()
    elif role == 'client_viewer':
        show_client_walkthrough()
    else:
        show_general_walkthrough()

def show_admin_walkthrough():
    """Business Administrator walkthrough"""
    st.markdown("## Business Administrator Guide")
    
    steps = [
        {
            "title": "1️⃣ Dashboard Overview",
            "content": """
            **Your main dashboard shows:**
            - Payment processing queue
            - Today's activity metrics
            - Moves ready for factoring submission
            - Revenue tracking
            
            💡 **Tip:** Check this daily for pending payments
            """
        },
        {
            "title": "2️⃣ Managing Trailer Swaps",
            "content": """
            **To add a new trailer swap:**
            1. Go to **🚛 Trailers**
            2. Click **➕ Add Trailer Pair** tab
            3. Enter NEW trailer number (from Fleet Memphis)
            4. Enter OLD trailer number and customer location
            5. System auto-calculates mileage and pay
            
            💡 **Tip:** Always verify addresses for accurate mileage
            """
        },
        {
            "title": "3️⃣ Creating & Assigning Moves",
            "content": """
            **To assign a move to a driver:**
            1. Go to **🚛 Trailers** → **📋 View Inventory**
            2. Find an available trailer pair
            3. Click **➡️ Create Move**
            4. Select driver and date
            5. Copy the generated message to send to driver
            
            📷 **Photo Documentation:**
            - Drivers must upload multiple photos
            - Protects against damage claims
            - Serves as additional/alternative POD
            - All photos stored with move record
            
            💡 **Tip:** The message includes photo requirements
            """
        },
        {
            "title": "4️⃣ Rate Confirmation Management",
            "content": """
            **Managing Rate Cons (NEW!):**
            1. Go to **📄 Rate Cons**
            2. **📥 Inbox** tab:
               - Choose calculation method:
                 • "Enter miles and rate" - if Rate Con shows miles
                 • "Calculate from total amount" - if only gross pay shown
               - MLBL number is OPTIONAL (can add/change later)
               - Upload Rate Con and BOL documents
               - System shows driver net pay (after 3% factoring)
            3. **🔄 Match Rate Cons** tab:
               - Match Rate Cons to completed moves
               - Use pickup/delivery addresses to identify correct move
               - Each move can have only ONE Rate Con
            4. **✅ Verification** tab:
               - Review mile deltas between client and calculated
               - Flag discrepancies over 5%
            
            💡 **Tip:** Rate Cons can arrive after moves are completed - match them retroactively
            """
        },
        {
            "title": "5️⃣ Payment Processing",
            "content": """
            **To process payments:**
            1. Go to **💰 Payments**
            2. **Submit to Factoring** tab:
               - Select completed moves
               - Review the email preview
               - Click Submit to Factoring
            3. **Pending Payments** tab:
               - Track submitted payments
               - Mark as paid when received
            4. **Payment History** tab:
               - View all processed payments
            
            💡 **Tip:** Submit to factoring before 1 PM EST for same-day payment
            """
        },
        {
            "title": "6️⃣ User & Driver Management",
            "content": """
            **User Management:**
            1. Go to **⚙️ System Admin** → **User Management** tab
            2. **Add Users:** Create accounts with single or dual roles
            3. **Edit Roles:** Upgrade users (e.g., driver to coordinator)
            4. **Reset Passwords:** Change any user's password
            5. **Remove Users:** Delete accounts (except owner)
            
            **Key Features:**
            - No code editing required!
            - Changes saved to user_accounts.json
            - Dual-role support (Driver + Coordinator)
            - Owner account protected
            
            **Driver Management:**
            1. Go to **👤 Drivers** for availability
            2. Drivers auto-added when they login
            3. Monitor driver status
            
            💡 **Tip:** Users with driver role automatically appear in assignment list
            """
        },
        {
            "title": "7️⃣ Client Portal Setup (NEW!)",
            "content": """
            **Setting up client access:**
            1. Go to **⚙️ System Admin** → **User Management**
            2. Click **➕ Add User** tab
            3. Create client account:
               - Username: `client_[companyname]`
               - Role: Select **client_viewer**
               - Password: Something secure
               - Name: Client company name
            
            **What clients can do:**
            - View only their moves (filtered by company)
            - Upload Rate Cons and BOLs (optional)
            - Track real-time status
            - See progress indicators
            
            **What clients CAN'T see:**
            - Driver names or contact info
            - Internal costs/pricing
            - Other clients' data
            - System administration
            
            💡 **Tip:** Clients can still email docs - portal upload is optional!
            """
        },
        {
            "title": "8️⃣ Vernon IT Support",
            "content": """
            **Using Vernon for maintenance:**
            1. Go to **🤖 IT Support (Vernon)**
            2. Vernon monitors automatically:
               - Database health
               - Client portal status
               - Document uploads
               - System performance
            
            **Vernon's control panel:**
            - 🔍 **Run Full Diagnostic** - Complete system check
            - 🔧 **Auto-Fix Issues** - Fixes common problems
            - ✅ **Validate System** - Verifies everything works
            - 👥 **Check Client Portal** - Monitor client features
            
            **Vernon fixes automatically:**
            - Stuck documents (pending > 7 days)
            - Old audit logs cleanup
            - Missing database tables
            - Session issues
            
            💡 **Vernon speaks friendly messages to keep you informed!**
            """
        }
    ]
    
    for step in steps:
        with st.expander(step["title"], expanded=False):
            st.markdown(step["content"])
    
    st.divider()
    st.info("📧 **Remember:** You handle all client and factoring company communications")

def show_coordinator_walkthrough():
    """Operations Coordinator walkthrough"""
    st.markdown("## Operations Coordinator Guide")
    
    # Check if user also has driver role
    user_roles = st.session_state.get('user_roles', [])
    if len(user_roles) > 1 and 'driver' in user_roles:
        st.success("💡 **Dual Role**: You also have Driver access! Switch to Driver role in the sidebar to upload PODs and view your assignments.")
    
    steps = [
        {
            "title": "1️⃣ Dashboard Overview",
            "content": """
            **Your dashboard shows:**
            - Active moves in progress
            - Driver availability status
            - Quick access to driver messages
            
            💡 **Tip:** Monitor this throughout the day
            """
        },
        {
            "title": "2️⃣ Adding Trailer Pairs",
            "content": """
            **To add trailers:**
            1. Go to **🚛 Trailers**
            2. Use **➕ Add Trailer Pair** tab
            3. Enter both trailer numbers
            4. Add complete customer address
            5. System calculates mileage automatically
            
            💡 **Tip:** Double-check addresses for accuracy
            """
        },
        {
            "title": "3️⃣ Creating Moves",
            "content": """
            **To create and assign moves:**
            1. Select available trailer pair
            2. Click **➡️ Create Move**
            3. Choose available driver
            4. Set date and time
            5. Copy message for driver
            6. Send via text message
            
            💡 **Tip:** The link in the message lets drivers upload POD without login
            """
        },
        {
            "title": "4️⃣ Rate Con Management",
            "content": """
            **Managing Rate Confirmations:**
            1. Go to **📄 Rate Cons**
            2. **📥 Inbox:** Upload Rate Cons and BOLs
               - MLBL is optional (can add/edit later)
               - Choose calculation method:
                 • Enter miles and rate (if shown on Rate Con)
                 • Calculate from total (if only gross amount shown)
               - Attach both Rate Con and BOL (one each per move)
            3. **🔄 Match:** Link Rate Cons to moves
               - Use pickup/delivery addresses to identify
               - One Rate Con + One BOL per move
            4. **✅ Verify:** Check mile deltas
               - System shows driver net (minus 3% factoring)
               - Flag discrepancies over 5%
            
            💡 **Tip:** Rate Cons often arrive after moves - match them retroactively!
            """
        },
        {
            "title": "5️⃣ Managing Drivers",
            "content": """
            **Driver coordination:**
            - Check driver availability before assigning
            - Copy and send driver messages via text
            - Monitor POD uploads
            - Handle reassignments if driver declines
            
            💡 **Tip:** Keep driver phone numbers handy
            """
        },
        {
            "title": "6️⃣ Manual POD Upload",
            "content": """
            **If driver can't upload:**
            1. Receive POD and photos via text/email
            2. Access the move's upload link
            3. Upload on driver's behalf:
               - POD document
               - NEW trailer: up to 10 photos total
               - OLD trailer: up to 2 photos total
            4. Mark move as complete
            
            📸 **Photo Requirements:**
            - NEW trailer: 5 pickup + 5 delivery photos
            - OLD trailer: 1 pickup + 1 delivery photo
            - Purpose: Damage documentation & proof
            
            💡 **Tip:** Save PODs and photos to backup folder
            """
        }
    ]
    
    for step in steps:
        with st.expander(step["title"], expanded=False):
            st.markdown(step["content"])
    
    st.divider()
    st.success("🚛 **Your Role:** Coordinate all trailer swaps and driver assignments")

def show_driver_walkthrough():
    """Driver walkthrough"""
    st.markdown("## Driver Guide")
    
    # Check if user also has coordinator role
    user_roles = st.session_state.get('user_roles', [])
    if len(user_roles) > 1 and 'operations_coordinator' in user_roles:
        st.success("💡 **Dual Role**: You also have Coordinator access! Switch to Coordinator role in the sidebar to create moves and manage trailer assignments.")
    
    steps = [
        {
            "title": "1️⃣ Your Dashboard",
            "content": """
            **Dashboard shows:**
            - Active moves assigned to you
            - Completed moves
            - Pending payment amount
            
            💡 **Tip:** Check daily for new assignments
            """
        },
        {
            "title": "2️⃣ Availability Toggle",
            "content": """
            **Set your availability:**
            - Use the **🟢 Available for moves** checkbox in sidebar
            - Check ON when ready for assignments
            - Check OFF when busy or unavailable
            
            💡 **Tip:** Update this in real-time
            """
        },
        {
            "title": "3️⃣ Receiving Assignments",
            "content": """
            **You'll receive via text:**
            - Move number
            - Pickup and delivery locations
            - Trailer numbers
            - Payment amount
            - POD upload link
            
            💡 **Tip:** Save the upload link immediately
            """
        },
        {
            "title": "4️⃣ Uploading POD",
            "content": """
            **After completing delivery:**
            1. Click the POD upload link from text
            2. Upload required documents:
               - **POD document** (Bill of Lading)
               - **NEW Trailer Photos:**
                 • Up to 5 photos at pickup (Fleet Memphis)
                 • Up to 5 photos at delivery (Customer)
               - **OLD Trailer Photos:**
                 • 1 photo at pickup (Customer)
                 • 1 photo at delivery (Fleet Memphis)
            3. Add notes about any damage or issues
            4. Check confirmation box
            5. Submit
            
            📸 **Photo Tips:**
            - Take clear photos showing trailer condition
            - Document any pre-existing damage
            - Photos protect you and the company
            - More photos = better documentation
            
            💡 **Tip:** Upload immediately for faster payment
            """
        },
        {
            "title": "5️⃣ Payment Tracking",
            "content": """
            **Track your earnings:**
            - View pending payments on dashboard
            - See completed moves history
            - Payment = Miles × $2.10 × 97%
            
            💡 **Tip:** Quick POD upload = Quick payment
            """
        },
        {
            "title": "6️⃣ Your Rate Cons (NEW!)",
            "content": """
            **View your Rate Confirmations:**
            1. Go to **💰 My Rate Cons**
            2. See all your completed moves with Rate Cons
            3. View your NET pay (after 3% factoring fee):
               - Gross pay (what client pays)
               - Minus 3% factoring fee
               - = Your NET pay
            4. Download both Rate Con and BOL documents
            5. Payment summary shows total net earnings
            
            💡 **Example:** $1,000 gross = $970 net (you get $970)
            💡 **Dual-Role Users:** Switch to Coordinator to upload Rate Cons yourself
            """
        }
    ]
    
    for step in steps:
        with st.expander(step["title"], expanded=False):
            st.markdown(step["content"])
    
    st.divider()
    st.warning("⚠️ **Remember:** No login needed for POD upload - just use the link!")

def show_client_walkthrough():
    """Client viewer walkthrough"""
    st.markdown("## Client Portal Guide")
    
    st.info("📋 **Your Portal:** Track your moves and manage documents in one place")
    
    steps = [
        {
            "title": "1️⃣ Understanding Your Dashboard",
            "content": """
            **Your Move Status Portal shows:**
            - 🟡 **Pending** - Move scheduled, awaiting driver
            - 🔵 **In Transit** - Driver actively completing
            - 📸 **Awaiting POD** - Completed, documentation coming
            - ✅ **Completed** - Move finished with docs
            
            💡 **Tip:** Refresh to see real-time updates
            """
        },
        {
            "title": "2️⃣ Document Management (NEW!)",
            "content": """
            **Two ways to submit documents:**
            
            **Option 1: Traditional Email**
            - Continue emailing your coordinator
            - No change to your current process
            - We'll handle the upload for you
            
            **Option 2: Self-Service Portal**
            - Click **📤 Upload Documents** tab
            - Drag & drop files (PDF, JPG, PNG)
            - Max file size: 10MB
            - Instant confirmation when uploaded
            
            💡 **Choose what works best for you!**
            """
        },
        {
            "title": "3️⃣ Uploading Rate Confirmations",
            "content": """
            **When to upload Rate Cons:**
            - When status shows 🟡 **Pending**
            - After route is assigned to driver
            
            **How to upload:**
            1. Go to **Upload Documents** tab
            2. Select the move from dropdown
            3. Drag & drop your signed Rate Con
            4. Click **Submit Rate Con**
            5. See instant confirmation ✅
            
            📧 **Alternative:** Email to coordinator as usual
            """
        },
        {
            "title": "4️⃣ Uploading Bills of Lading",
            "content": """
            **When to upload BOLs:**
            - When status shows ✅ **Completed**
            - After POD is received from driver
            
            **How to upload:**
            1. Go to **Upload Documents** tab
            2. Select completed move
            3. Drag & drop signed BOL
            4. Click **Submit BOL**
            5. See instant confirmation ✅
            
            📧 **Alternative:** Email to coordinator as usual
            """
        },
        {
            "title": "5️⃣ Tracking Move Progress",
            "content": """
            **Understanding progress bars:**
            - 25% = Awaiting driver dispatch
            - 50% = Driver en route
            - 75% = Delivered, awaiting docs
            - 100% = Move complete
            
            **Filter your moves:**
            - Use status dropdown to filter
            - View All, Pending, In Transit, or Completed
            - Click any move to expand details
            
            💡 **Tip:** Check **Pending Actions** tab for required docs
            """
        },
        {
            "title": "6️⃣ What You Can See",
            "content": """
            **Your portal shows:**
            - Only YOUR company's moves
            - Move status and progress
            - Trailer numbers
            - Pickup/delivery locations
            - Document status
            
            **What's hidden (for security):**
            - Driver names/contact info
            - Internal costs and pricing
            - Other clients' information
            - System administration
            
            🔒 **Your data is private and secure**
            """
        },
        {
            "title": "7️⃣ Getting Help",
            "content": """
            **If you need assistance:**
            
            **Portal issues:**
            - Contact your coordinator
            - They can reset passwords
            - Help with document uploads
            
            **Can't see your moves?**
            - Moves filtered by company name
            - Contact coordinator if missing
            
            **Wrong document uploaded?**
            - Contact coordinator immediately
            - They can correct the submission
            
            📞 **Your coordinator is always available to help!**
            """
        }
    ]
    
    # Show walkthrough steps
    for step in steps:
        with st.expander(step["title"], expanded=False):
            st.markdown(step["content"])
    
    # Quick reference card
    st.divider()
    st.markdown("### 📋 Quick Reference")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Status Meanings:**
        - 🟡 Pending = Send Rate Con
        - 🔵 In Transit = Driver working
        - ✅ Completed = Send BOL
        """)
    
    with col2:
        st.markdown("""
        **Document Types:**
        - Rate Confirmations → When assigned
        - Bills of Lading → When completed
        - Both can be emailed or uploaded
        """)

def show_viewer_walkthrough():
    """Viewer role walkthrough"""
    st.markdown("## Viewer Guide (Read-Only Access)")
    
    st.info("👁️ **Your Role:** View-only access to monitor operations without making changes")
    
    steps = [
        {
            "title": "1️⃣ Dashboard Access",
            "content": """
            **What you can see:**
            - Overall system metrics
            - Active moves in progress
            - Completed moves summary
            - Driver availability status
            
            💡 **Tip:** Perfect for clients or trainees learning the system
            """
        },
        {
            "title": "2️⃣ Progress Dashboard",
            "content": """
            **Monitor operations:**
            - Track move progress in real-time
            - View completion status
            - See POD upload status
            - Monitor overall workflow
            
            💡 **Tip:** Refresh page to see latest updates
            """
        },
        {
            "title": "3️⃣ Limited Access",
            "content": """
            **What you CANNOT do:**
            - Create or edit moves
            - Modify trailer information
            - Change driver assignments
            - Access payment information
            - Edit system settings
            
            💡 **Note:** Contact an administrator if you need edit access
            """
        },
        {
            "title": "4️⃣ Upgrading Your Access",
            "content": """
            **To get more access:**
            1. Contact your administrator
            2. Request role upgrade
            3. Admin can upgrade you to:
               - Driver (upload PODs)
               - Coordinator (manage moves)
               - Dual-role (both abilities)
            
            💡 **Tip:** No system restart needed for role changes!
            """
        }
    ]
    
    for step in steps:
        with st.expander(step["title"], expanded=False):
            st.markdown(step["content"])
    
    st.divider()
    st.success("📚 **Your Purpose:** Learn the system and monitor operations")

def show_general_walkthrough():
    """General system overview"""
    st.markdown("## System Overview")
    
    st.markdown("""
    ### 🚛 Smith & Williams Trucking - Trailer Swap Management
    
    **Purpose:** Streamline trailer swap operations between Fleet Memphis and customer locations.
    
    **Key Features:**
    - 📊 Role-based dashboards
    - 🔄 **Dual-role support** - Switch between Driver/Coordinator
    - 👥 **In-app user management** - Add/edit users without code
    - 🚛 Trailer pair management
    - 📍 Automatic mileage calculation
    - 👤 Driver assignment and tracking
    - 📸 Mobile-friendly POD uploads
    - 📄 Rate Confirmation management (1:1 with moves)
    - 💰 Payment processing workflow
    - 🔢 3% factoring fee calculations
    
    **Workflow:**
    1. **Setup:** Add trailer pairs and locations
    2. **Assign:** Create moves and assign to drivers
    3. **Execute:** Drivers complete swaps
    4. **Document:** Upload PODs via mobile link
    5. **Payment:** Process through factoring company
    
    **Mobile Optimization:**
    - Works on phones, tablets, and computers
    - No app installation required
    - Direct POD upload links (no login needed)
    
    **Support:**
    - Contact your coordinator for move issues
    - Contact administrator for payment questions
    """)

def show_quick_tips():
    """Display quick tips based on role"""
    role = st.session_state.get('user_role', '')
    
    st.markdown("### 💡 Quick Tips")
    
    if role == 'business_administrator':
        tips = [
            "Use System Admin → User Management to add/edit users",
            "Submit to factoring before 1 PM EST for same-day payment",
            "Rate Cons can be uploaded without MLBL numbers",
            "Users with dual roles can switch in the sidebar",
            "Archive old moves monthly to keep system fast"
        ]
    elif role == 'operations_coordinator':
        tips = [
            "Verify addresses before creating trailer pairs",
            "Check driver availability before assigning",
            "Copy driver messages immediately after creating move",
            "Keep a backup of driver phone numbers"
        ]
    elif role == 'driver':
        tips = [
            "Save POD upload links immediately",
            "Take clear photos of trailers",
            "Upload POD same day for faster payment",
            "Update availability status regularly"
        ]
    else:
        tips = [
            "Contact support for login issues",
            "Use Chrome or Safari for best experience",
            "Works on mobile devices",
            "Bookmark the site for easy access"
        ]
    
    for tip in tips:
        st.write(f"• {tip}")

# Integration function for main app
def add_walkthrough_to_menu():
    """Add walkthrough option to navigation menu"""
    return "🎓 Walkthrough"

def should_show_walkthrough():
    """Check if user should see walkthrough"""
    # Show for new users or on request
    if 'walkthrough_seen' not in st.session_state:
        return True
    return st.session_state.get('show_walkthrough', False)