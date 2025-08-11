"""
Step-by-Step Walkthrough Guide for Smith & Williams Trucking
Interactive training system for all user roles
"""

import streamlit as st

def show_walkthrough():
    """Main walkthrough interface"""
    st.title("🎓 System Walkthrough")
    st.caption("Learn how to use the Trailer Swap Management System")
    
    role = st.session_state.get('user_role', 'viewer')
    
    # Role-specific walkthroughs
    if role == 'business_administrator':
        show_admin_walkthrough()
    elif role == 'operations_coordinator':
        show_coordinator_walkthrough()
    elif role == 'driver':
        show_driver_walkthrough()
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
            "title": "4️⃣ Payment Processing",
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
            "title": "5️⃣ Managing Drivers",
            "content": """
            **Driver management:**
            1. Go to **👤 Drivers**
            2. Add new drivers with login credentials
            3. Monitor driver availability
            4. Toggle driver status as needed
            
            💡 **Tip:** Drivers can self-toggle availability
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
            "title": "4️⃣ Managing Drivers",
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
            "title": "5️⃣ Manual POD Upload",
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
        }
    ]
    
    for step in steps:
        with st.expander(step["title"], expanded=False):
            st.markdown(step["content"])
    
    st.divider()
    st.warning("⚠️ **Remember:** No login needed for POD upload - just use the link!")

def show_general_walkthrough():
    """General system overview"""
    st.markdown("## System Overview")
    
    st.markdown("""
    ### 🚛 Smith & Williams Trucking - Trailer Swap Management
    
    **Purpose:** Streamline trailer swap operations between Fleet Memphis and customer locations.
    
    **Key Features:**
    - 📊 Role-based dashboards
    - 🚛 Trailer pair management
    - 📍 Automatic mileage calculation
    - 👤 Driver assignment and tracking
    - 📸 Mobile-friendly POD uploads
    - 💰 Payment processing workflow
    
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
            "Submit to factoring before 1 PM EST for same-day payment",
            "Check bank account after factoring confirmation",
            "Keep rate confirmations organized by date",
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