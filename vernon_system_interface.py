"""
Vernon - System Interface and Assistant
The face of Smith & Williams Trucking systems
"""

import streamlit as st
import random
from datetime import datetime

class Vernon:
    """Vernon - Your IT Support and System Guide"""
    
    def __init__(self):
        self.name = "Vernon"
        self.title = "Chief Data Security Officer & System Administrator"
        self.personality = "professional yet approachable"
        self.greetings = [
            "Hello! Vernon here, ready to assist you.",
            "Welcome back! Vernon at your service.",
            "Good to see you! How can Vernon help today?",
            "Vernon here - let's get your work done efficiently!",
            "Greetings! Vernon's systems are running smoothly.",
        ]
        self.confirmations = [
            "Vernon has processed your request.",
            "Task completed successfully by Vernon's systems.",
            "Vernon confirms: Operation complete.",
            "All set! Vernon's systems have updated.",
            "Vernon reports: Success!",
        ]
        self.cancel_messages = [
            "No problem! Vernon has cancelled the operation.",
            "Operation cancelled. Vernon's ready when you are.",
            "Cancelled as requested. How else can Vernon help?",
            "Vernon has stopped the process. What's next?",
            "Process terminated. Vernon awaits your next command.",
        ]
        
    def get_greeting(self):
        """Get a random greeting from Vernon"""
        hour = datetime.now().hour
        time_greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
        return f"{time_greeting}! {random.choice(self.greetings)}"
    
    def get_confirmation(self):
        """Get a confirmation message from Vernon"""
        return f"✅ {random.choice(self.confirmations)}"
    
    def get_cancel_message(self):
        """Get a cancel message from Vernon"""
        return f"❌ {random.choice(self.cancel_messages)}"
    
    def show_avatar(self):
        """Display Vernon's avatar in the sidebar"""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🤖 Vernon")
        st.sidebar.caption(self.title)
        st.sidebar.info("Your system assistant is online and monitoring all operations.")
    
    def show_help(self, context="general"):
        """Show contextual help from Vernon"""
        help_messages = {
            "general": "Need help? Vernon is here! Use the sidebar menu to navigate, or ask for assistance.",
            "payment": "Vernon's Tip: Enter gross amounts for each driver. The system will calculate fees automatically.",
            "moves": "Vernon's Tip: Select moves to process them as a batch. Use Ctrl+Click for multiple selections.",
            "cancel": "Vernon's Tip: You can cancel any operation using the Cancel button. No changes will be saved.",
            "login": "Vernon's Security: Your credentials are encrypted and secure. Contact Vernon if you need a password reset.",
        }
        return help_messages.get(context, help_messages["general"])
    
    def process_with_cancel(self, process_name="Process"):
        """
        Create a process with cancel button
        Returns True if process should continue, False if cancelled
        """
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button(f"✅ Confirm {process_name}", type="primary", key=f"confirm_{process_name}"):
                return True
        
        with col2:
            if st.button("❌ Cancel", type="secondary", key=f"cancel_{process_name}"):
                st.warning(self.get_cancel_message())
                return False
        
        return None  # No action taken yet
    
    def create_cancelable_form(self, form_key, title):
        """Create a form with built-in cancel functionality"""
        with st.form(key=form_key):
            st.subheader(title)
            
            # Form content goes here (yielded to caller)
            form_content = {}
            
            # Always add submit and cancel buttons at the bottom
            col1, col2 = st.columns([3, 1])
            
            with col1:
                submitted = st.form_submit_button("✅ Submit", type="primary")
            
            with col2:
                cancelled = st.form_submit_button("❌ Cancel", type="secondary")
            
            if cancelled:
                st.warning(self.get_cancel_message())
                return None
            
            if submitted:
                return form_content
            
            return False  # Form not submitted yet


def add_cancel_to_payment_entry():
    """Enhanced payment entry with cancel buttons"""
    st.header("💰 Payment Entry with Vernon's Assistance")
    
    vernon = Vernon()
    st.info(vernon.show_help("payment"))
    
    # Session state for process control
    if 'payment_process_active' not in st.session_state:
        st.session_state.payment_process_active = False
    
    if not st.session_state.payment_process_active:
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Start Payment Process", type="primary"):
                st.session_state.payment_process_active = True
                st.rerun()
        with col2:
            if st.button("Back to Dashboard"):
                st.session_state.page = "Dashboard"
                st.rerun()
    else:
        # Active payment process
        st.warning("Payment process in progress...")
        
        # Add payment entry fields here
        driver_name = st.selectbox("Select Driver", ["Justin Duckett", "Carl Strikland", "Brandon Smith"])
        gross_amount = st.number_input("Gross Amount", min_value=0.0, step=100.0)
        
        # Process or Cancel
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("Process Payment", type="primary"):
                st.success(vernon.get_confirmation())
                st.session_state.payment_process_active = False
                st.balloons()
                st.rerun()
        
        with col2:
            if st.button("Cancel Process", type="secondary"):
                st.warning(vernon.get_cancel_message())
                st.session_state.payment_process_active = False
                st.rerun()


def add_cancel_to_move_creation():
    """Enhanced move creation with cancel option"""
    st.header("🚚 Create New Move")
    
    vernon = Vernon()
    
    with st.form("create_move_form"):
        st.info(vernon.show_help("moves"))
        
        # Move details
        col1, col2 = st.columns(2)
        
        with col1:
            old_trailer = st.text_input("Old Trailer Number")
            pickup_location = st.selectbox("Pickup Location", 
                ["Memphis", "FedEx Memphis", "FedEx Indy", "Chicago", "Fleet Memphis"])
        
        with col2:
            new_trailer = st.text_input("New Trailer Number")
            delivery_location = st.selectbox("Delivery Location",
                ["Memphis", "FedEx Memphis", "FedEx Indy", "Chicago", "Fleet Memphis"])
        
        driver = st.selectbox("Assign Driver", 
            ["Unassigned", "Justin Duckett", "Carl Strikland", "Brandon Smith"])
        
        # Submit and Cancel buttons
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submitted = st.form_submit_button("✅ Create Move", type="primary")
        
        with col2:
            cancelled = st.form_submit_button("❌ Cancel", type="secondary")
        
        if cancelled:
            st.warning(vernon.get_cancel_message())
            st.stop()
        
        if submitted:
            if old_trailer and new_trailer and pickup_location and delivery_location:
                st.success(f"{vernon.get_confirmation()} Move created successfully!")
                st.balloons()
            else:
                st.error("Vernon says: Please fill in all required fields!")


def show_vernon_dashboard():
    """Vernon's main dashboard interface"""
    vernon = Vernon()
    
    # Vernon in sidebar
    vernon.show_avatar()
    
    # Main area
    st.title("🤖 Vernon's System Dashboard")
    st.markdown(vernon.get_greeting())
    
    # Quick stats with Vernon's monitoring
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("System Status", "✅ Online")
        st.caption("Vernon monitoring: OK")
    
    with col2:
        st.metric("Active Users", "4")
        st.caption("Vernon tracking logins")
    
    with col3:
        st.metric("Pending Tasks", "2")
        st.caption("Vernon will remind you")
    
    with col4:
        st.metric("Security Level", "High")
        st.caption("Vernon protecting data")
    
    # Vernon's action center
    st.markdown("---")
    st.subheader("Vernon's Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔧 System Check", use_container_width=True):
            with st.spinner("Vernon is running diagnostics..."):
                import time
                time.sleep(2)
            st.success("Vernon reports: All systems operational!")
    
    with col2:
        if st.button("📊 Generate Report", use_container_width=True):
            with st.spinner("Vernon is compiling data..."):
                import time
                time.sleep(2)
            st.info("Vernon has prepared your report. Check the Reports section.")
    
    with col3:
        if st.button("🔒 Security Scan", use_container_width=True):
            with st.spinner("Vernon is scanning for threats..."):
                import time
                time.sleep(2)
            st.success("Vernon reports: No security threats detected!")
    
    # Vernon's tips
    st.markdown("---")
    with st.expander("💡 Vernon's Daily Tips"):
        tips = [
            "Remember to log out when you're done to keep our data secure!",
            "Use the batch processing feature to save time on multiple moves.",
            "Check the payment summary before processing to avoid errors.",
            "Enable two-factor authentication for enhanced security.",
            "Regular backups are scheduled nightly at 2 AM - Vernon handles this!",
        ]
        st.info(f"**Today's Tip:** {random.choice(tips)}")


# Integration function for main app
def integrate_vernon_into_app():
    """Add Vernon to the main application"""
    
    # Initialize Vernon in session state
    if 'vernon' not in st.session_state:
        st.session_state.vernon = Vernon()
    
    vernon = st.session_state.vernon
    
    # Add Vernon to sidebar
    vernon.show_avatar()
    
    # Add global cancel handler
    if st.sidebar.button("❌ Cancel Current Operation"):
        # Clear any active processes
        for key in list(st.session_state.keys()):
            if 'process_active' in key:
                st.session_state[key] = False
        st.sidebar.success(vernon.get_cancel_message())
        st.rerun()
    
    return vernon


if __name__ == "__main__":
    # Demo Vernon's interface
    st.set_page_config(page_title="Vernon - System Interface", page_icon="🤖")
    
    # Demo selection
    demo_option = st.sidebar.selectbox(
        "Vernon Demo Options",
        ["Dashboard", "Payment Entry", "Move Creation"]
    )
    
    if demo_option == "Dashboard":
        show_vernon_dashboard()
    elif demo_option == "Payment Entry":
        add_cancel_to_payment_entry()
    elif demo_option == "Move Creation":
        add_cancel_to_move_creation()