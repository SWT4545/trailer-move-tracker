"""
Practical Walkthrough Guide for Smith & Williams Trucking
Focus on HOW TO USE the system, not technical details
"""

import streamlit as st

def show_walkthrough():
    """Main walkthrough interface"""
    st.title("🎓 System Walkthrough")
    st.caption("Step-by-step guide to using the Trailer Management System")
    
    # Get user role
    role = st.session_state.get('user_role', 'viewer')
    
    # Role-specific walkthroughs
    if role == 'business_administrator':
        show_admin_walkthrough()
    elif role == 'operations_coordinator':
        show_coordinator_walkthrough()
    elif role == 'driver':
        show_driver_walkthrough()
    elif role == 'client_viewer':
        show_client_walkthrough()
    else:
        show_general_walkthrough()

def show_admin_walkthrough():
    """Business Administrator practical guide"""
    st.markdown("## Administrator Quick Start")
    
    steps = [
        {
            "title": "📊 Daily Workflow",
            "content": """
            **Morning Routine:**
            1. Check Dashboard for pending payments
            2. Review completed moves awaiting factoring
            3. Submit to factoring before 1 PM EST for same-day payment
            
            **Key Metrics to Monitor:**
            - Moves ready for payment
            - Driver availability
            - Active swaps in progress
            """
        },
        {
            "title": "🔄 Creating a Trailer Swap",
            "content": """
            1. Go to **➕ Create Move**
            2. Select NEW trailer (you're delivering)
            3. Select OLD trailer (you're picking up)
            4. Choose swap location
            5. Assign available driver
            6. Click Create Swap
            
            The system automatically calculates mileage and driver pay.
            """
        },
        {
            "title": "👤 Adding a New Driver",
            "content": """
            **Company Driver:**
            1. Go to **👤 Drivers** → **➕ Create Driver**
            2. Select "Company Driver"
            3. Enter username, password, name
            4. Add phone, email, CDL info
            5. Click Create Driver
            
            **Contractor:**
            - Same process but select "Contractor"
            - Must provide: Company name, MC#, DOT#, Insurance info
            - Upload insurance certificate
            """
        },
        {
            "title": "💰 Processing Payments",
            "content": """
            1. Go to **💰 Payments**
            2. Select completed moves with PODs
            3. Click "Submit to Factoring"
            4. When payment received, mark as "Paid"
            5. System tracks driver payments automatically
            
            **Important:** Always verify POD is uploaded before submitting
            """
        },
        {
            "title": "📄 Rate Confirmations",
            "content": """
            1. Go to **📄 Rate Cons**
            2. Upload new rate con and BOL
            3. Enter either:
               - Miles and rate per mile, OR
               - Total gross amount
            4. System calculates driver net (after 3% factoring)
            5. Match rate con to completed move
            """
        },
        {
            "title": "🤖 Using Vernon for Help",
            "content": """
            Vernon appears in the sidebar on every page:
            
            **If something isn't working:**
            1. Click Vernon in sidebar
            2. Click "Check This Page"
            3. Click "Auto-Fix Issues"
            
            **To report a problem:**
            1. Click "Report Problem"
            2. Describe the issue
            3. Vernon will investigate and fix
            """
        }
    ]
    
    for i, step in enumerate(steps):
        with st.expander(step["title"], expanded=(i == 0)):
            st.markdown(step["content"])

def show_coordinator_walkthrough():
    """Operations Coordinator practical guide"""
    st.markdown("## Coordinator Quick Start")
    
    steps = [
        {
            "title": "📋 Daily Operations",
            "content": """
            **Your Main Tasks:**
            1. Create and assign moves to drivers
            2. Monitor active swaps
            3. Verify POD uploads
            4. Update move statuses
            
            **Quick Actions:**
            - Dashboard shows all active moves
            - Click on any move to see details
            - Use status buttons to update progress
            """
        },
        {
            "title": "➕ Creating Moves",
            "content": """
            1. Go to **➕ Create Move**
            2. Select trailers and location
            3. Choose available driver
            4. Set pickup date
            5. Create the move
            
            Driver receives notification with all details.
            """
        },
        {
            "title": "📸 Managing PODs",
            "content": """
            **When driver uploads POD:**
            1. Go to move details
            2. Verify POD is complete
            3. Mark move as "Completed"
            4. Move becomes ready for payment processing
            
            **Missing POD?**
            - Contact driver through system
            - Send POD upload link reminder
            """
        }
    ]
    
    for step in steps:
        with st.expander(step["title"], expanded=True):
            st.markdown(step["content"])

def show_driver_walkthrough():
    """Driver practical guide"""
    st.markdown("## Driver Quick Start")
    
    steps = [
        {
            "title": "📱 Your Daily Workflow",
            "content": """
            1. **Check Assigned Moves**
               - Login to see your assignments
               - View pickup/delivery details
               - Note special instructions
            
            2. **Update Your Status**
               - Toggle availability in sidebar
               - Mark moves as "In Progress" when starting
               - Upload POD immediately after delivery
            
            3. **Track Earnings**
               - View completed moves
               - See payment status
               - Check total earnings
            """
        },
        {
            "title": "📸 Uploading POD",
            "content": """
            **After completing delivery:**
            1. Go to **📸 Upload POD**
            2. Select your completed move
            3. Upload photos:
               - BOL/POD document
               - Trailer photos (all sides)
               - Any damage photos
            4. Click Submit
            
            **Important:** Upload immediately to ensure quick payment
            """
        },
        {
            "title": "💰 Viewing Your Pay",
            "content": """
            1. Go to **💰 My Rate Cons**
            2. See all your moves
            3. Check payment status:
               - Pending: Awaiting processing
               - Submitted: Sent to factoring
               - Paid: Payment received
            
            Your net pay (after factoring) is shown for each move.
            """
        }
    ]
    
    for step in steps:
        with st.expander(step["title"], expanded=True):
            st.markdown(step["content"])

def show_client_walkthrough():
    """Client viewer practical guide"""
    st.markdown("## Client Portal Guide")
    
    steps = [
        {
            "title": "📊 Tracking Your Shipments",
            "content": """
            **Your Dashboard Shows:**
            - All active moves for your company
            - Real-time status updates
            - Delivery confirmations
            - POD documents
            
            **Status Meanings:**
            - Assigned: Driver assigned, not started
            - In Progress: Driver en route
            - Completed: Delivery complete
            - Paid: Move processed and paid
            """
        },
        {
            "title": "📄 Accessing Documents",
            "content": """
            1. Click on any completed move
            2. View available documents:
               - Proof of Delivery
               - Bill of Lading
               - Trailer photos
            3. Download for your records
            
            All documents are retained for 90 days.
            """
        }
    ]
    
    for step in steps:
        with st.expander(step["title"], expanded=True):
            st.markdown(step["content"])

def show_general_walkthrough():
    """General system overview"""
    st.markdown("## System Overview")
    
    st.markdown("""
    ### Welcome to Smith & Williams Trucking System
    
    **Main Functions:**
    - **Trailer Swaps:** Coordinate NEW/OLD trailer exchanges
    - **Driver Management:** Track driver assignments and availability
    - **Payment Processing:** Handle factoring and driver payments
    - **Document Management:** PODs, BOLs, Rate Confirmations
    
    **Getting Started:**
    1. Login with your credentials
    2. Navigate using the sidebar menu
    3. Your role determines available features
    4. Use Vernon (🤖 in sidebar) for help
    
    **Need Help?**
    - Click Vernon in the sidebar
    - Describe your issue
    - Vernon will provide assistance
    """)

# Export for use in main app
__all__ = ['show_walkthrough']