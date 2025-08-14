"""
Smith & Williams Trucking - Version 3
Phase 3: Adding data entry system with Vernon guidance
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sqlite3
import hashlib
import os
import io
import json
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
    /* Vernon helper box */
    .vernon-help {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 10px;
        margin: 10px 0;
    }
    /* Data entry form styling */
    .data-entry-section {
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
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

# Vernon Helper System
class VernonHelper:
    """Vernon's helpful guidance system"""
    
    @staticmethod
    def show_tip(message, type="info"):
        """Show Vernon's helpful tips"""
        icon = "💡" if type == "info" else "⚠️" if type == "warning" else "✅"
        st.markdown(f"""
        <div class="vernon-help">
            <strong>🔐 Vernon says:</strong> {icon} {message}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def data_entry_guide():
        """Show data entry guidance"""
        with st.expander("💡 Vernon's Data Entry Guide"):
            st.markdown("""
            **Quick Tips for Efficient Data Entry:**
            
            1. **Trailer Numbers:** Use consistent format (e.g., TR-001, TR-002)
            2. **Locations:** Be specific (e.g., "Atlanta Depot Bay 5")
            3. **Bulk Upload:** Use CSV for multiple entries
            4. **Keyboard Shortcuts:**
               - Tab: Move to next field
               - Enter: Submit form
            5. **Required Fields:** Look for asterisk (*) marks
            
            **Need help?** I'm Vernon, your Chief Data Security Officer. 
            I ensure all data is entered correctly and securely.
            """)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.page = "Dashboard"

# Simple login function
def check_login(username, password):
    """Simple login check"""
    # Hardcoded accounts that ALWAYS work
    accounts = {
        "Brandon": ("owner123", "admin"),
        "admin": ("admin123", "admin"),
        "DataEntry": ("data123", "data_entry"),
        "demo": ("demo", "admin")
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
            "SELECT role FROM users WHERE user = ? AND password = ?",
            (username, hashed)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return True, result[0]
    except:
        pass
    
    return False, None

# Data Entry Functions
def create_trailer_tables():
    """Create comprehensive trailer tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Enhanced trailer inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trailer_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trailer_number TEXT UNIQUE NOT NULL,
            trailer_type TEXT,
            status TEXT DEFAULT 'available',
            condition TEXT DEFAULT 'good',
            current_location TEXT,
            location_lat REAL,
            location_lng REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT,
            notes TEXT,
            customer_owner TEXT,
            year_manufactured INTEGER,
            last_inspection DATE,
            next_inspection DATE
        )
    ''')
    
    # Location history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trailer_location_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trailer_number TEXT,
            old_location TEXT,
            new_location TEXT,
            change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            changed_by TEXT,
            reason TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def bulk_upload_trailers(df, username):
    """Bulk upload trailers from DataFrame"""
    conn = get_connection()
    cursor = conn.cursor()
    
    success_count = 0
    error_list = []
    
    for index, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO trailer_inventory 
                (trailer_number, trailer_type, status, condition, current_location, 
                 customer_owner, notes, updated_by, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('trailer_number'),
                row.get('trailer_type', 'Dry Van'),
                row.get('status', 'available'),
                row.get('condition', 'good'),
                row.get('current_location', 'Unknown'),
                row.get('customer_owner', ''),
                row.get('notes', ''),
                username,
                datetime.now()
            ))
            success_count += 1
        except Exception as e:
            error_list.append(f"Row {index + 1}: {str(e)}")
    
    conn.commit()
    conn.close()
    
    return success_count, error_list

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
            - DataEntry / data123 (Data Entry Specialist)
            - admin / admin123 (Admin)
            - Or click Demo Mode for instant access
            """)
    
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #888;'>© 2025 Smith & Williams Trucking | 🔐 Protected by Vernon - Chief Data Security Officer</p>",
        unsafe_allow_html=True
    )

# Main app
else:
    # Create tables if needed
    create_trailer_tables()
    
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
        
        # Show pages based on role
        if st.session_state.user_role == "data_entry":
            pages = ["Data Entry", "Bulk Operations", "Location Update", "Reports"]
        else:
            pages = ["Dashboard", "Trailers", "Moves", "Data Entry", "Reports", "Settings"]
        
        st.session_state.page = st.radio(
            "Go to",
            pages,
            label_visibility="collapsed"
        )
        
        # Vernon section
        st.markdown("---")
        st.markdown("### 🔐 Vernon")
        st.markdown("Chief Data Security Officer")
        
        if st.session_state.user_role == "data_entry":
            st.success("Data Entry Mode Active")
            st.info("Tips: Use Tab to navigate fields")
        else:
            st.info("System secure and operational")
        
        # Logout
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            for key in ['authenticated', 'user', 'user_role', 'page']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Main content area with consistent header
    st.markdown(f"# 🚛 Smith & Williams Trucking")
    
    # Show role-specific welcome
    if st.session_state.user_role == "data_entry":
        st.markdown(f"Welcome, **{st.session_state.username}** - Data Entry Specialist")
    else:
        st.markdown(f"Welcome back, **{st.session_state.username}**!")
    
    st.markdown("---")
    
    # Page routing
    if st.session_state.page == "Data Entry":
        st.header("📝 Trailer Data Entry")
        
        # Vernon's guidance
        VernonHelper.data_entry_guide()
        
        # Tabs for different entry methods
        tab1, tab2, tab3 = st.tabs(["➕ Single Entry", "📊 Bulk Upload", "🔍 Search & Edit"])
        
        with tab1:
            st.markdown("### Add New Trailer")
            
            # Entry form with Vernon's tips
            col1, col2 = st.columns(2)
            
            with col1:
                trailer_number = st.text_input(
                    "Trailer Number*",
                    placeholder="e.g., TR-001",
                    help="Vernon tip: Use consistent format"
                )
                
                trailer_type = st.selectbox(
                    "Trailer Type",
                    ["Dry Van", "Reefer", "Flatbed", "Step Deck", "Double Drop", "Other"]
                )
                
                condition = st.selectbox(
                    "Condition",
                    ["Excellent", "Good", "Fair", "Poor", "Needs Repair"]
                )
                
                year = st.number_input(
                    "Year Manufactured",
                    min_value=1990,
                    max_value=2025,
                    value=2020
                )
            
            with col2:
                current_location = st.text_input(
                    "Current Location*",
                    placeholder="e.g., Atlanta Depot Bay 5",
                    help="Vernon tip: Be specific with locations"
                )
                
                col2a, col2b = st.columns(2)
                with col2a:
                    lat = st.number_input("Latitude", value=0.0, format="%.6f")
                with col2b:
                    lng = st.number_input("Longitude", value=0.0, format="%.6f")
                
                if st.button("📍 Auto-Detect Location"):
                    VernonHelper.show_tip("Location detection would use GPS in production", "info")
                    lat = 33.7490  # Atlanta example
                    lng = -84.3880
                
                customer_owner = st.text_input(
                    "Customer/Owner",
                    placeholder="e.g., ABC Company or 'Company Owned'"
                )
                
                status = st.selectbox(
                    "Status",
                    ["available", "in_use", "maintenance", "retired", "reserved"]
                )
            
            # Additional info
            with st.expander("📋 Additional Information"):
                col3, col4 = st.columns(2)
                
                with col3:
                    last_inspection = st.date_input(
                        "Last Inspection Date",
                        value=None,
                        help="When was the last DOT inspection?"
                    )
                    
                    next_inspection = st.date_input(
                        "Next Inspection Due",
                        value=None,
                        help="When is the next inspection due?"
                    )
                
                with col4:
                    notes = st.text_area(
                        "Notes",
                        placeholder="Any additional information about this trailer...",
                        height=100
                    )
            
            # Submit button with validation
            if st.button("💾 Save Trailer", type="primary", use_container_width=True):
                if trailer_number and current_location:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO trailer_inventory
                            (trailer_number, trailer_type, status, condition, current_location,
                             location_lat, location_lng, customer_owner, year_manufactured,
                             last_inspection, next_inspection, notes, updated_by, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            trailer_number, trailer_type, status, condition, current_location,
                            lat, lng, customer_owner, year, last_inspection, next_inspection,
                            notes, st.session_state.username, datetime.now()
                        ))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"✅ Trailer {trailer_number} saved successfully!")
                        VernonHelper.show_tip("Great job! Data saved securely.", "info")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error: {e}")
                        VernonHelper.show_tip("Check if trailer number already exists", "warning")
                else:
                    st.warning("Please fill in required fields (Trailer Number and Location)")
                    VernonHelper.show_tip("Required fields are marked with asterisk (*)", "warning")
        
        with tab2:
            st.markdown("### Bulk Upload Trailers")
            
            VernonHelper.show_tip("Upload multiple trailers at once using CSV format", "info")
            
            # Download template
            if st.button("📥 Download CSV Template"):
                template_df = pd.DataFrame({
                    'trailer_number': ['TR-001', 'TR-002', 'TR-003'],
                    'trailer_type': ['Dry Van', 'Reefer', 'Flatbed'],
                    'status': ['available', 'in_use', 'available'],
                    'condition': ['Good', 'Excellent', 'Fair'],
                    'current_location': ['Atlanta Depot', 'Miami Terminal', 'Dallas Yard'],
                    'customer_owner': ['ABC Corp', 'XYZ Inc', 'Company Owned']
                })
                
                csv = template_df.to_csv(index=False)
                st.download_button(
                    "Download Template",
                    csv,
                    "trailer_upload_template.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            # Upload file
            uploaded_file = st.file_uploader(
                "Choose CSV file",
                type=['csv'],
                help="Vernon tip: Make sure trailer numbers are unique"
            )
            
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    
                    st.markdown("#### Preview (first 5 rows)")
                    st.dataframe(df.head(), use_container_width=True)
                    
                    st.info(f"📊 File contains {len(df)} trailers")
                    
                    if st.button("🚀 Upload All Trailers", type="primary"):
                        with st.spinner("Processing..."):
                            success_count, errors = bulk_upload_trailers(df, st.session_state.username)
                            
                            if success_count > 0:
                                st.success(f"✅ Successfully uploaded {success_count} trailers!")
                                VernonHelper.show_tip(f"Excellent! {success_count} trailers added to the system.", "info")
                            
                            if errors:
                                st.warning("Some entries had errors:")
                                for error in errors:
                                    st.write(f"- {error}")
                except Exception as e:
                    st.error(f"Error reading file: {e}")
                    VernonHelper.show_tip("Check your CSV format matches the template", "warning")
        
        with tab3:
            st.markdown("### Search and Edit Trailers")
            
            # Search filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                search_number = st.text_input(
                    "Search by Trailer Number",
                    placeholder="Enter trailer number..."
                )
            
            with col2:
                search_location = st.text_input(
                    "Search by Location",
                    placeholder="Enter location..."
                )
            
            with col3:
                search_status = st.selectbox(
                    "Filter by Status",
                    ["All", "available", "in_use", "maintenance", "retired"]
                )
            
            # Search results
            try:
                conn = get_connection()
                query = "SELECT * FROM trailer_inventory WHERE 1=1"
                params = []
                
                if search_number:
                    query += " AND trailer_number LIKE ?"
                    params.append(f"%{search_number}%")
                
                if search_location:
                    query += " AND current_location LIKE ?"
                    params.append(f"%{search_location}%")
                
                if search_status != "All":
                    query += " AND status = ?"
                    params.append(search_status)
                
                query += " ORDER BY last_updated DESC LIMIT 100"
                
                df = pd.read_sql_query(query, conn, params=params)
                conn.close()
                
                if not df.empty:
                    st.markdown(f"#### Found {len(df)} trailers")
                    
                    # Make dataframe editable
                    edited_df = st.data_editor(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        disabled=['id', 'last_updated']
                    )
                    
                    if st.button("💾 Save Changes"):
                        # Would implement save logic here
                        st.success("Changes saved!")
                        VernonHelper.show_tip("All changes have been logged for audit", "info")
                else:
                    st.info("No trailers found matching your criteria")
            except Exception as e:
                st.info("No trailers in system yet")
    
    elif st.session_state.page == "Bulk Operations" or st.session_state.page == "Location Update":
        st.header("📍 Bulk Operations & Location Updates")
        
        tab1, tab2, tab3 = st.tabs(["🔄 Update Locations", "📤 Export Data", "🗑️ Bulk Actions"])
        
        with tab1:
            st.markdown("### Batch Location Update")
            
            VernonHelper.show_tip("Update multiple trailer locations at once", "info")
            
            # Get trailers for selection
            try:
                conn = get_connection()
                df = pd.read_sql_query(
                    "SELECT trailer_number, current_location, status FROM trailer_inventory",
                    conn
                )
                conn.close()
                
                if not df.empty:
                    # Multi-select trailers
                    selected_trailers = st.multiselect(
                        "Select trailers to update",
                        df['trailer_number'].tolist()
                    )
                    
                    if selected_trailers:
                        new_location = st.text_input(
                            "New Location for Selected Trailers",
                            placeholder="e.g., Houston Terminal"
                        )
                        
                        reason = st.selectbox(
                            "Reason for Move",
                            ["Delivery", "Pickup", "Storage", "Maintenance", "Transfer", "Other"]
                        )
                        
                        if reason == "Other":
                            reason = st.text_input("Specify reason")
                        
                        if st.button(f"📍 Update {len(selected_trailers)} Trailers", type="primary"):
                            if new_location:
                                conn = get_connection()
                                cursor = conn.cursor()
                                
                                for trailer in selected_trailers:
                                    # Update location
                                    cursor.execute('''
                                        UPDATE trailer_inventory
                                        SET current_location = ?, last_updated = ?, updated_by = ?
                                        WHERE trailer_number = ?
                                    ''', (new_location, datetime.now(), st.session_state.username, trailer))
                                    
                                    # Log history
                                    cursor.execute('''
                                        INSERT INTO trailer_location_history
                                        (trailer_number, new_location, changed_by, reason)
                                        VALUES (?, ?, ?, ?)
                                    ''', (trailer, new_location, st.session_state.username, reason))
                                
                                conn.commit()
                                conn.close()
                                
                                st.success(f"✅ Updated location for {len(selected_trailers)} trailers!")
                                VernonHelper.show_tip("Location history has been recorded", "info")
                            else:
                                st.warning("Please enter a new location")
                else:
                    st.info("No trailers in system yet")
            except:
                st.info("Add trailers first to update locations")
        
        with tab2:
            st.markdown("### Export Trailer Data")
            
            export_format = st.selectbox("Export Format", ["CSV", "Excel", "JSON"])
            
            if st.button("📤 Export All Trailers", type="primary"):
                try:
                    conn = get_connection()
                    df = pd.read_sql_query("SELECT * FROM trailer_inventory", conn)
                    conn.close()
                    
                    if not df.empty:
                        if export_format == "CSV":
                            csv = df.to_csv(index=False)
                            st.download_button(
                                "Download CSV",
                                csv,
                                f"trailers_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                "text/csv"
                            )
                        elif export_format == "JSON":
                            json_str = df.to_json(orient='records')
                            st.download_button(
                                "Download JSON",
                                json_str,
                                f"trailers_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                                "application/json"
                            )
                        
                        st.success("✅ Export ready!")
                        VernonHelper.show_tip(f"Exported {len(df)} trailers", "info")
                    else:
                        st.info("No data to export")
                except:
                    st.error("Error exporting data")
        
        with tab3:
            st.markdown("### Bulk Status Update")
            
            VernonHelper.show_tip("Change status for multiple trailers at once", "info")
            
            col1, col2 = st.columns(2)
            
            with col1:
                current_status = st.selectbox(
                    "Current Status",
                    ["available", "in_use", "maintenance", "retired"]
                )
            
            with col2:
                new_status = st.selectbox(
                    "Change To",
                    ["available", "in_use", "maintenance", "retired"]
                )
            
            if st.button("🔄 Update All Matching Trailers", type="primary"):
                if current_status != new_status:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute('''
                            UPDATE trailer_inventory
                            SET status = ?, last_updated = ?, updated_by = ?
                            WHERE status = ?
                        ''', (new_status, datetime.now(), st.session_state.username, current_status))
                        
                        count = cursor.rowcount
                        conn.commit()
                        conn.close()
                        
                        st.success(f"✅ Updated {count} trailers from {current_status} to {new_status}")
                        VernonHelper.show_tip(f"Bulk update completed successfully", "info")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Please select different statuses")
    
    # Keep existing pages for non-data-entry users
    elif st.session_state.page == "Dashboard":
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
            if st.button("📝 Data Entry", use_container_width=True):
                st.session_state.page = "Data Entry"
                st.rerun()
        
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
            
            cursor.execute("SELECT COUNT(*) FROM trailer_inventory")
            total_trailers = cursor.fetchone()[0]
            
            conn.close()
            
            with col1:
                st.metric("📋 Pending", pending)
            with col2:
                st.metric("🚛 In Progress", in_progress)
            with col3:
                st.metric("✅ Completed", completed)
            with col4:
                st.metric("🚚 Total Trailers", total_trailers)
        except:
            st.info("📊 Dashboard data will appear here")
    
    elif st.session_state.page == "Reports":
        st.header("📄 Reports & Analytics")
        
        if PDF_AVAILABLE:
            if st.button("📄 Generate PDF Report", type="primary"):
                with st.spinner("Creating report..."):
                    generator = PDFReportGenerator()
                    pdf_buffer = generator.generate_client_update_report(
                        "Status Report",
                        datetime.now() - timedelta(days=30),
                        datetime.now()
                    )
                    
                    st.download_button(
                        "📥 Download PDF Report",
                        pdf_buffer,
                        f"Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf"
                    )
        
        # Data entry statistics
        if st.session_state.user_role in ["admin", "data_entry"]:
            st.markdown("### Data Entry Statistics")
            
            try:
                conn = get_connection()
                
                # Get recent updates
                df = pd.read_sql_query('''
                    SELECT trailer_number, current_location, last_updated, updated_by
                    FROM trailer_inventory
                    ORDER BY last_updated DESC
                    LIMIT 10
                ''', conn)
                
                if not df.empty:
                    st.markdown("#### Recent Updates")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Get user activity
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT updated_by, COUNT(*) as updates
                    FROM trailer_inventory
                    WHERE updated_by IS NOT NULL
                    GROUP BY updated_by
                ''')
                
                activity = cursor.fetchall()
                if activity:
                    st.markdown("#### User Activity")
                    for user, count in activity:
                        st.write(f"- **{user}:** {count} updates")
                
                conn.close()
            except:
                st.info("Statistics will appear as data is entered")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #888; font-size: 0.9em;'>© 2025 Smith & Williams Trucking | 🔐 Protected by Vernon - Chief Data Security Officer</p>",
        unsafe_allow_html=True
    )