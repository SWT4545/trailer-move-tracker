"""
Role-Specific Walkthrough Guides
Each role sees only their relevant tasks and features
"""

import streamlit as st
from datetime import datetime

def show_role_based_walkthrough():
    """Display role-specific walkthrough based on user's role"""
    role = st.session_state.get('user_role', 'viewer')
    username = st.session_state.get('user', 'User')
    
    st.title("📚 Role-Specific Training Guide")
    st.caption(f"Customized for: {username} ({role.replace('_', ' ').title()})")
    
    # Special case for Brandon - Owner who drives
    if username == "Brandon" and role == "Owner":
        show_brandon_owner_driver_guide()
    elif role == "Owner":
        show_owner_guide()
    elif role == "Admin" or role == "business_administrator":
        show_admin_guide()
    elif role == "driver":
        show_driver_guide()
    elif role in ["coordinator", "operations_coordinator", "dispatcher"]:
        show_coordinator_guide()
    else:
        show_viewer_guide()

def show_brandon_owner_driver_guide():
    """Special guide for Brandon - Owner who also drives"""
    st.markdown("## 👑 Owner & Driver Combined Guide")
    st.success("You have unique dual access as both Owner and Driver")
    
    tabs = st.tabs(["Owner Tasks", "Driver Tasks", "Daily Workflow", "Priority Actions"])
    
    with tabs[0]:  # Owner Tasks
        st.markdown("### Your Owner Responsibilities")
        
        with st.expander("1️⃣ Morning Priority - Factoring Submissions", expanded=True):
            st.error("⏰ CRITICAL: Submit factoring by 11AM EST for next-day payout!")
            st.markdown("""
            **Daily Factoring Workflow:**
            1. Go to **💰 Payment Processing**
            2. Click **💳 Factoring Submission** tab
            3. Review completed moves with documents
            4. Submit batch to factoring company
            5. Note the batch reference number
            
            **Timing is Critical:**
            - Before 11AM EST = Next business day payout
            - After 11AM EST = 2 business days wait
            - Friday after 11AM = Tuesday payout
            """)
        
        with st.expander("2️⃣ Payment Processing"):
            st.markdown("""
            **Processing Driver Payments:**
            1. Go to **💰 Payment Processing**
            2. Review moves ready for payment
            3. Enter actual service fees (varies by factoring amount)
            4. Process Navy Federal transfers
            5. Drivers get automatic notifications
            
            **Service Fee Guidelines:**
            - Standard: 3% of gross amount
            - May vary based on factoring terms
            - Always verify with factoring statement
            """)
        
        with st.expander("3️⃣ Financial Management"):
            st.markdown("""
            **Your Financial Controls:**
            - View all revenue metrics
            - Track payment status
            - Monitor factoring submissions
            - Review driver earnings
            - Generate financial reports
            
            **Only you can see:**
            - Total revenue figures
            - Payment amounts
            - Service fee details
            - Profit margins
            """)
    
    with tabs[1]:  # Driver Tasks
        st.markdown("### Your Driver Capabilities")
        
        with st.expander("1️⃣ Self-Assignment"):
            st.markdown("""
            **Claiming Moves:**
            1. Go to **🚚 Available Moves**
            2. Review available assignments
            3. Check estimated pay (after 3% factoring)
            4. Click **Accept Move** to claim
            5. Trailers automatically reserved for you
            
            **Your Advantage:**
            - First pick of profitable routes
            - No approval needed
            - Instant assignment
            """)
        
        with st.expander("2️⃣ Your Money Bag"):
            st.markdown("""
            **Tracking Your Earnings:**
            - View total earnings to date
            - See your "money bag" grow
            - Track progress to milestones
            - Compare weekly earnings
            
            **Earning Milestones:**
            - 💵 < $5,000: Getting Started
            - 💰 < $10,000: Building Up  
            - 💰💰 < $25,000: Strong Earner
            - 💰💰💰 $25,000+: Top Performer
            """)
    
    with tabs[2]:  # Daily Workflow
        st.markdown("### Recommended Daily Workflow")
        
        st.markdown("""
        **Morning (Before 11AM EST):**
        1. ☕ Check Executive Dashboard
        2. 🚨 Review priority alerts
        3. 💳 Submit factoring if needed (BEFORE 11AM!)
        4. 📄 Collect any missing documents
        
        **Midday:**
        1. 🚚 Check available moves for yourself
        2. 📋 Assign moves to other drivers
        3. 💰 Process any pending payments
        4. 📊 Review operational metrics
        
        **Afternoon:**
        1. 📱 Complete your driving assignments
        2. 📸 Upload PODs immediately
        3. ✅ Update move statuses
        4. 💵 Check your money bag progress
        
        **End of Day:**
        1. 📊 Review daily performance
        2. 💰 Verify all payments processed
        3. 📄 Ensure documents collected
        4. 🎯 Plan tomorrow's priorities
        """)
    
    with tabs[3]:  # Priority Actions
        st.markdown("### Today's Priority Actions")
        
        current_hour = datetime.now().hour
        is_business_day = datetime.now().weekday() < 5
        
        if is_business_day and current_hour < 11:
            st.error("🚨 URGENT: Check for factoring submissions needed before 11AM!")
        
        st.markdown("""
        **Quick Action Checklist:**
        - [ ] Submit factoring (if before 11AM)
        - [ ] Process pending payments
        - [ ] Check your assigned moves
        - [ ] Review money bag earnings
        - [ ] Collect missing documents
        - [ ] Assign unassigned moves
        """)

def show_owner_guide():
    """Guide for Owner role (general, not Brandon)"""
    st.markdown("## 👑 Owner Guide")
    
    with st.expander("1️⃣ Executive Dashboard", expanded=True):
        st.markdown("""
        **Your Command Center:**
        - Real-time operational metrics
        - Financial performance tracking
        - Priority alerts and deadlines
        - Quick access to all functions
        
        **Key Metrics:**
        - Revenue tracking
        - Payment status
        - Active operations
        - Driver performance
        """)
    
    with st.expander("2️⃣ Financial Management"):
        st.markdown("""
        **Payment & Factoring:**
        1. Submit to factoring by 11AM EST daily
        2. Process driver payments after factoring
        3. Track service fees and margins
        4. Monitor cash flow
        
        **Reports:**
        - Generate financial statements
        - Export payment history
        - Review profitability
        """)

def show_admin_guide():
    """Guide for Admin/Business Administrator role"""
    st.markdown("## 💼 Administrator Guide")
    
    with st.expander("1️⃣ Dashboard Overview", expanded=True):
        st.markdown("""
        **Your Administrative View:**
        - Operational metrics (no financials)
        - System performance
        - User activity
        - Document status
        
        **Daily Tasks:**
        - Review system health
        - Manage user accounts
        - Monitor operations
        - Generate reports
        """)
    
    with st.expander("2️⃣ User Management"):
        st.markdown("""
        **Managing Users:**
        1. Create new accounts
        2. Assign appropriate roles
        3. Reset passwords
        4. Activate/deactivate users
        
        **Role Assignment:**
        - Driver: Field operations
        - Coordinator: Document management
        - Viewer: Read-only access
        """)
    
    with st.expander("3️⃣ System Administration"):
        st.markdown("""
        **System Tasks:**
        - Database maintenance
        - Backup management
        - Security monitoring
        - Performance optimization
        
        **Regular Maintenance:**
        - Weekly system checks
        - Monthly user audits
        - Quarterly security reviews
        """)

def show_driver_guide():
    """Guide for Driver role"""
    st.markdown("## 🚚 Driver Guide")
    
    with st.expander("1️⃣ Your Dashboard", expanded=True):
        st.markdown("""
        **Driver Portal Features:**
        - View your money bag (total earnings)
        - Track active moves
        - See payment status
        - Monitor performance metrics
        
        **Money Bag Milestones:**
        - Track total earnings to date
        - See progress to next milestone
        - Compare weekly performance
        """)
    
    with st.expander("2️⃣ Self-Assignment"):
        st.markdown("""
        **Getting Moves:**
        1. Go to **Available Moves**
        2. Review routes and pay
        3. Click **Accept Move**
        4. Start when ready
        
        **Payment Info:**
        - Rate: $2.10/mile
        - Service fee: ~3%
        - Weekly payments
        """)
    
    with st.expander("3️⃣ Completing Moves"):
        st.markdown("""
        **Move Workflow:**
        1. Accept available move
        2. Click **Start Move** when beginning
        3. Complete delivery
        4. Upload POD immediately
        5. Mark as **Complete**
        
        **Document Requirements:**
        - Clear POD photo
        - Signature if required
        - Any special documentation
        """)
    
    with st.expander("4️⃣ Getting Paid"):
        st.markdown("""
        **Payment Process:**
        - Complete move with POD
        - Management processes payment
        - Receive Navy Federal transfer
        - Check money bag for totals
        
        **Timing:**
        - Moves completed by Thursday
        - Paid by Friday
        - Check your money bag dashboard
        """)

def show_coordinator_guide():
    """Guide for Coordinator/Dispatcher role"""
    st.markdown("## 📋 Coordinator Guide")
    st.info("Note: You do not have access to financial information")
    
    with st.expander("1️⃣ Your Dashboard", expanded=True):
        st.markdown("""
        **Coordinator View:**
        - Active moves status
        - Document collection tasks
        - Driver assignments
        - Operational metrics only
        
        **What You DON'T See:**
        - Payment amounts
        - Revenue figures
        - Service fees
        - Financial reports
        """)
    
    with st.expander("2️⃣ Document Management", expanded=True):
        st.markdown("""
        **Critical Task - Document Collection:**
        1. Monitor completed moves
        2. Identify missing documents
        3. Contact drivers for PODs
        4. Upload Rate Confirmations
        5. Upload BOLs
        
        **Priority Documents:**
        - Rate Confirmation (from customer)
        - Bill of Lading (from pickup)
        - Proof of Delivery (from driver)
        
        ⚠️ **IMPORTANT:** All docs needed before payment!
        """)
    
    with st.expander("3️⃣ Move Coordination"):
        st.markdown("""
        **Assigning Moves:**
        1. Review unassigned moves
        2. Check driver availability
        3. Make assignments
        4. Monitor progress
        
        **Status Tracking:**
        - Pending → Assigned
        - Assigned → In Progress
        - In Progress → Completed
        - Completed → (Docs needed)
        """)
    
    with st.expander("4️⃣ Daily Priorities"):
        st.markdown("""
        **Your Daily Checklist:**
        - [ ] Collect PODs from completed moves
        - [ ] Upload Rate Confirmations
        - [ ] Upload BOLs
        - [ ] Assign pending moves
        - [ ] Update move statuses
        - [ ] Follow up on missing docs
        
        **Time-Sensitive:**
        - Docs needed ASAP for factoring
        - Help meet 11AM submission deadline
        - No financial details needed from you
        """)

def show_viewer_guide():
    """Guide for Viewer/Read-only role"""
    st.markdown("## 👁️ Viewer Guide")
    st.info("You have read-only access to monitor operations")
    
    with st.expander("What You Can Do", expanded=True):
        st.markdown("""
        **View Access:**
        - Dashboard metrics
        - Move status
        - Trailer locations
        - Basic reports
        
        **Monitoring:**
        - Track operations
        - View progress
        - Check statuses
        - Read documentation
        """)
    
    with st.expander("What You Cannot Do"):
        st.markdown("""
        **No Access To:**
        - Creating/editing data
        - Financial information
        - User management
        - System settings
        
        **Contact admin for:**
        - Data corrections
        - Additional access
        - Report generation
        - System issues
        """)

def show_quick_reference():
    """Show quick reference card for current role"""
    role = st.session_state.get('user_role', 'viewer')
    
    st.markdown("### ⚡ Quick Reference Card")
    
    if role == "Owner":
        st.markdown("""
        **Owner Quick Actions:**
        - 🚨 Submit factoring by 11AM EST
        - 💰 Process payments
        - 📊 Review financials
        - 👥 Manage users
        - 🚚 Oversee operations
        """)
    elif role == "driver":
        st.markdown("""
        **Driver Quick Actions:**
        - 🚚 Accept available moves
        - 📸 Upload PODs
        - ✅ Complete deliveries
        - 💰 Check money bag
        - 📊 View earnings
        """)
    elif role in ["coordinator", "operations_coordinator"]:
        st.markdown("""
        **Coordinator Quick Actions:**
        - 📄 Collect documents
        - 🚛 Assign moves
        - 📋 Track status
        - 📤 Upload docs
        - ⏰ Meet deadlines
        """)
    else:
        st.markdown("""
        **Viewer Quick Actions:**
        - 📊 Monitor dashboard
        - 📋 Check statuses
        - 📍 View locations
        - 📖 Read reports
        """)

# Export functions
__all__ = ['show_role_based_walkthrough', 'show_quick_reference']