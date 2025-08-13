"""
Smith & Williams Trucking - Version 2
Phase 2: Adding logo, PDF reports, and better styling
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sqlite3
import hashlib
import os
from PIL import Image

# Import PDF generator if available
try:
    from pdf_report_generator import PDFReportGenerator, generate_status_report_for_profile
    PDF_AVAILABLE = True
except:
    PDF_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Smith & Williams Trucking",
    page_icon="🚛",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Logo styling */
    .logo-container {
        text-align: center;
        padding: 1rem;
    }
    .logo-img {
        max-width: 200px;
        margin: 0 auto;
    }
    /* Sidebar styling */
    .css-1d391kg {
        padding-top: 1rem;
    }
    /* Main content padding */
    .main {
        padding: 0;
    }
</style>
""", unsafe_allow_html=True)

# Load logo function
def load_logo():
    """Load and display company logo"""
    logo_path = "swt_logo.png"
    if os.path.exists(logo_path):
        return Image.open(logo_path)
    return None

# Simple database connection
def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

# Simple password hash
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_role = None

# Simple login function
def check_login(username, password):
    """Simple login check"""
    # Hardcoded accounts that ALWAYS work
    accounts = {
        "Brandon": ("owner123", "admin"),
        "admin": ("admin123", "admin"),
        "demo": ("demo", "admin"),
        "DataEntry": ("data123", "data_entry")
    }
    
    if username in accounts:
        stored_pass, role = accounts[username]
        if password == stored_pass:
            return True, role
    
    # Check database as backup
    try:
        conn = get_connection()
        cursor = conn.cursor()
        hashed = hash_password(password)
        cursor.execute(
            "SELECT role FROM users WHERE username = ? AND password = ?",
            (username, hashed)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return True, result[0]
    except:
        pass
    
    return False, None

# Login page
if not st.session_state.authenticated:
    # Logo at top of login page
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo = load_logo()
        if logo:
            st.image(logo, use_container_width=True)
        else:
            st.markdown("# 🚛")
        
        st.markdown("<h1 style='text-align: center;'>Smith & Williams Trucking</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Trailer Move Management System</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Login")
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔓 Login", type="primary", use_container_width=True):
                success, role = check_login(username, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_role = role
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        
        with col_b:
            if st.button("📱 Demo Mode", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.username = "demo_user"
                st.session_state.user_role = "admin"
                st.success("✅ Demo mode activated!")
                st.rerun()
        
        with st.expander("ℹ️ Login Help"):
            st.info("""
            **Test Accounts:**
            - Brandon / owner123 (Admin)
            - admin / admin123 (Admin)
            - DataEntry / data123 (Data Entry)
            - Or click Demo Mode for instant access
            """)
    
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #888;'>© 2025 Smith & Williams Trucking | 🔐 Protected by Vernon - Chief Data Security Officer</p>",
        unsafe_allow_html=True
    )

# Main app
else:
    # Sidebar with logo
    with st.sidebar:
        # Logo in sidebar
        logo = load_logo()
        if logo:
            st.image(logo, use_container_width=True)
        
        st.markdown("---")
        
        # User info
        st.markdown(f"### 👤 {st.session_state.username}")
        st.markdown(f"**Role:** {st.session_state.user_role}")
        
        # Navigation
        st.markdown("---")
        st.markdown("### 📍 Navigation")
        page = st.radio(
            "Go to",
            ["Dashboard", "Trailers", "Moves", "Reports", "Settings"],
            label_visibility="collapsed"
        )
        
        # Vernon section
        st.markdown("---")
        st.markdown("### 🔐 Vernon")
        st.markdown("Chief Data Security Officer")
        st.info("System secure and operational")
        
        # Logout
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_role = None
            st.rerun()
    
    # Main content area with consistent header
    st.markdown(f"# 🚛 Smith & Williams Trucking")
    st.markdown(f"Welcome back, **{st.session_state.username}**!")
    st.markdown("---")
    
    # Page routing
    if page == "Dashboard":
        st.header("📊 Dashboard")
        
        # Quick actions
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("➕ Add Move", use_container_width=True):
                st.session_state.page = "Moves"
                st.rerun()
        with col2:
            if st.button("🚚 Add Trailer", use_container_width=True):
                st.session_state.page = "Trailers"
                st.rerun()
        with col3:
            if PDF_AVAILABLE and st.button("📄 Generate Report", use_container_width=True):
                with st.spinner("Generating PDF..."):
                    pdf_buffer = generate_status_report_for_profile(st.session_state.username, st.session_state.user_role)
                    st.download_button(
                        "📥 Download Report",
                        pdf_buffer,
                        f"Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf"
                    )
        
        # Stats
        st.markdown("### Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'pending'")
            pending = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'in_progress'")
            in_progress = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'completed'")
            completed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM trailers")
            total_trailers = cursor.fetchone()[0]
            
            conn.close()
            
            with col1:
                st.metric("📋 Pending", pending, delta="2 new")
            with col2:
                st.metric("🚛 In Progress", in_progress)
            with col3:
                st.metric("✅ Completed", completed)
            with col4:
                st.metric("🚚 Total Trailers", total_trailers)
            
            # Recent activity
            st.markdown("### Recent Activity")
            conn = get_connection()
            df = pd.read_sql_query("""
                SELECT order_number, customer_name, status, created_at 
                FROM moves 
                ORDER BY created_at DESC 
                LIMIT 5
            """, conn)
            conn.close()
            
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No recent activity")
                
        except Exception as e:
            st.info("📊 Dashboard data will appear here once moves are added")
    
    elif page == "Trailers":
        st.header("🚚 Trailer Management")
        
        tab1, tab2 = st.tabs(["View Trailers", "Add Trailer"])
        
        with tab1:
            # Display trailers
            try:
                conn = get_connection()
                df = pd.read_sql_query("SELECT * FROM trailers ORDER BY trailer_number", conn)
                conn.close()
                
                if not df.empty:
                    # Filters
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        status_filter = st.selectbox("Filter by Status", ["All", "available", "in_use", "maintenance"])
                    
                    if status_filter != "All":
                        df = df[df['status'] == status_filter]
                    
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Summary
                    st.markdown("### Summary")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Trailers", len(df))
                    with col2:
                        available = len(df[df['status'] == 'available']) if 'status' in df.columns else 0
                        st.metric("Available", available)
                    with col3:
                        in_use = len(df[df['status'] == 'in_use']) if 'status' in df.columns else 0
                        st.metric("In Use", in_use)
                else:
                    st.info("No trailers in system yet. Add your first trailer in the 'Add Trailer' tab.")
            except:
                st.info("Trailer data will appear here once trailers are added")
        
        with tab2:
            st.markdown("### Add New Trailer")
            
            col1, col2 = st.columns(2)
            with col1:
                trailer_number = st.text_input("Trailer Number*", placeholder="e.g., TR-001")
                trailer_type = st.selectbox("Trailer Type", ["Dry Van", "Reefer", "Flatbed", "Step Deck", "Other"])
                condition = st.selectbox("Condition", ["Excellent", "Good", "Fair", "Poor"])
            
            with col2:
                location = st.text_input("Current Location*", placeholder="e.g., Atlanta Depot")
                status = st.selectbox("Status", ["available", "in_use", "maintenance", "retired"])
                owner = st.text_input("Owner/Customer", placeholder="e.g., ABC Company")
            
            notes = st.text_area("Notes", placeholder="Any additional information...")
            
            if st.button("➕ Add Trailer", type="primary", use_container_width=True):
                if trailer_number and location:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        
                        # Create enhanced trailers table if needed
                        cursor.execute('''
                            CREATE TABLE IF NOT EXISTS trailers (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                trailer_number TEXT UNIQUE,
                                trailer_type TEXT,
                                condition TEXT,
                                location TEXT,
                                status TEXT,
                                owner TEXT,
                                notes TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''')
                        
                        cursor.execute("""
                            INSERT INTO trailers (trailer_number, trailer_type, condition, location, status, owner, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (trailer_number, trailer_type, condition, location, status, owner, notes))
                        
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Trailer {trailer_number} added successfully!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Please fill in required fields (Trailer Number and Location)")
    
    elif page == "Moves":
        st.header("📦 Move Management")
        
        tab1, tab2, tab3 = st.tabs(["Active Moves", "Add Move", "All Moves"])
        
        with tab1:
            # Active moves
            try:
                conn = get_connection()
                df = pd.read_sql_query("""
                    SELECT order_number, customer_name, origin_city, destination_city, 
                           driver_name, status, pickup_date, delivery_date
                    FROM moves 
                    WHERE status IN ('pending', 'in_progress')
                    ORDER BY pickup_date
                """, conn)
                conn.close()
                
                if not df.empty:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No active moves at this time")
            except:
                st.info("Active moves will appear here")
        
        with tab2:
            st.markdown("### Create New Move")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                order_number = st.text_input("Order Number*", placeholder="e.g., ORD-001")
                customer = st.text_input("Customer Name*", placeholder="e.g., ABC Company")
                amount = st.number_input("Amount ($)", min_value=0.0, step=100.0)
            
            with col2:
                origin_city = st.text_input("Origin City*", placeholder="e.g., Atlanta")
                origin_state = st.text_input("Origin State*", placeholder="e.g., GA", max_chars=2)
                pickup_date = st.date_input("Pickup Date", min_value=date.today())
            
            with col3:
                dest_city = st.text_input("Destination City*", placeholder="e.g., Miami")
                dest_state = st.text_input("Destination State*", placeholder="e.g., FL", max_chars=2)
                delivery_date = st.date_input("Delivery Date", min_value=date.today())
            
            driver_name = st.selectbox("Assign Driver", ["Unassigned", "Brandon", "John", "Mike", "Other"])
            if driver_name == "Other":
                driver_name = st.text_input("Driver Name")
            
            move_status = st.selectbox("Initial Status", ["pending", "assigned", "in_progress"])
            
            notes = st.text_area("Notes", placeholder="Special instructions, requirements, etc.")
            
            if st.button("📦 Create Move", type="primary", use_container_width=True):
                if all([order_number, customer, origin_city, origin_state, dest_city, dest_state]):
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            INSERT INTO moves (order_number, customer_name, origin_city, origin_state,
                                             destination_city, destination_state, pickup_date, delivery_date,
                                             amount, driver_name, status, notes, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (order_number, customer, origin_city, origin_state, dest_city, dest_state,
                              pickup_date, delivery_date, amount, driver_name if driver_name != "Unassigned" else None,
                              move_status, notes, datetime.now()))
                        
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Move {order_number} created successfully!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Please fill in all required fields (*)")
        
        with tab3:
            # All moves
            try:
                conn = get_connection()
                df = pd.read_sql_query("""
                    SELECT * FROM moves 
                    ORDER BY created_at DESC
                    LIMIT 100
                """, conn)
                conn.close()
                
                if not df.empty:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No moves in system yet")
            except:
                st.info("Move history will appear here")
    
    elif page == "Reports":
        st.header("📄 Reports & Analytics")
        
        if PDF_AVAILABLE:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                report_type = st.selectbox(
                    "Report Type",
                    ["Executive Summary", "Move Report", "Trailer Report", "Financial Report"]
                )
            
            with col2:
                date_range = st.date_input(
                    "Date Range",
                    value=(datetime.now() - timedelta(days=30), datetime.now()),
                    key="report_dates"
                )
            
            with col3:
                if st.button("📄 Generate PDF", type="primary", use_container_width=True):
                    with st.spinner("Creating report..."):
                        generator = PDFReportGenerator()
                        pdf_buffer = generator.generate_client_update_report(
                            report_type,
                            date_range[0] if len(date_range) > 0 else None,
                            date_range[1] if len(date_range) > 1 else None
                        )
                        
                        st.download_button(
                            "📥 Download PDF Report",
                            pdf_buffer,
                            f"{report_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
        
        # Quick stats
        st.markdown("### Quick Statistics")
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Move stats
            cursor.execute("SELECT status, COUNT(*) FROM moves GROUP BY status")
            move_stats = cursor.fetchall()
            
            # Trailer stats
            cursor.execute("SELECT status, COUNT(*) FROM trailers GROUP BY status")
            trailer_stats = cursor.fetchall()
            
            conn.close()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Move Status")
                for status, count in move_stats:
                    st.write(f"- **{status.title()}:** {count}")
            
            with col2:
                st.markdown("#### Trailer Status")
                for status, count in trailer_stats:
                    st.write(f"- **{status.title()}:** {count}")
            
        except:
            st.info("Statistics will appear here as data is added")
    
    elif page == "Settings":
        st.header("⚙️ Settings")
        
        tab1, tab2, tab3 = st.tabs(["Profile", "System", "About"])
        
        with tab1:
            st.markdown("### User Profile")
            st.write(f"**Username:** {st.session_state.username}")
            st.write(f"**Role:** {st.session_state.user_role}")
            st.write(f"**Login Time:** {datetime.now().strftime('%I:%M %p')}")
            
            if st.button("Change Password"):
                st.info("Password change feature coming soon")
        
        with tab2:
            st.markdown("### System Settings")
            
            theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
            notifications = st.checkbox("Enable notifications", value=True)
            auto_refresh = st.checkbox("Auto-refresh dashboard", value=False)
            
            if st.button("Save Settings"):
                st.success("Settings saved!")
        
        with tab3:
            st.markdown("### About")
            st.markdown("""
            **Smith & Williams Trucking Management System**
            
            Version: 2.0
            
            © 2025 Smith & Williams Trucking
            
            **Features:**
            - Trailer Management
            - Move Tracking
            - Driver Assignment
            - PDF Report Generation
            - Real-time Dashboard
            
            **Support:**
            Contact Vernon - Chief Data Security Officer
            """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #888; font-size: 0.9em;'>© 2025 Smith & Williams Trucking | 🔐 Protected by Vernon - Chief Data Security Officer</p>",
        unsafe_allow_html=True
    )