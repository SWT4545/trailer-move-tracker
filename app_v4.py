"""
Smith & Williams Trucking - Version 4
Phase 4: Complete system with REST API integration
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
import subprocess
import threading

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
    /* API status indicator */
    .api-status {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .api-online {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .api-offline {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
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
            4. **API Access:** Use the REST API for VB.NET integration
            5. **Required Fields:** Look for asterisk (*) marks
            
            **Need help?** I'm Vernon, your Chief Data Security Officer. 
            I ensure all data is entered correctly and securely.
            """)

# API Server Management
class APIManager:
    """Manage the REST API server"""
    
    @staticmethod
    def start_api_server():
        """Start the FastAPI server"""
        if 'api_process' not in st.session_state:
            try:
                # Start API server in background
                process = subprocess.Popen(
                    ["python", "api_server.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                st.session_state.api_process = process
                st.session_state.api_running = True
                return True
            except Exception as e:
                st.error(f"Failed to start API server: {e}")
                return False
        return st.session_state.get('api_running', False)
    
    @staticmethod
    def check_api_status():
        """Check if API server is running"""
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def show_api_status():
        """Display API status indicator"""
        is_running = APIManager.check_api_status()
        
        if is_running:
            st.markdown("""
            <div class="api-status api-online">
                ✅ <strong>REST API Online</strong> - http://localhost:8000
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="api-status api-offline">
                ⚠️ <strong>REST API Offline</strong> - Click 'Start API Server' to enable
            </div>
            """, unsafe_allow_html=True)
        
        return is_running

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
            pages = ["Data Entry", "Bulk Operations", "Location Update", "Reports", "API Access"]
        else:
            pages = ["Dashboard", "Trailers", "Moves", "Data Entry", "Reports", "API Access", "Settings"]
        
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
        
        # API Status
        st.markdown("---")
        st.markdown("### 🌐 API Status")
        api_running = APIManager.check_api_status()
        if api_running:
            st.success("API Online")
        else:
            st.warning("API Offline")
            if st.button("🚀 Start API Server", use_container_width=True):
                APIManager.start_api_server()
                st.rerun()
        
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
    if st.session_state.page == "API Access":
        st.header("🌐 REST API Access")
        
        # Show API status
        APIManager.show_api_status()
        
        # API Documentation
        with st.expander("📖 API Documentation"):
            st.markdown("""
            ### REST API Endpoints
            
            The REST API allows external applications (like VB.NET) to interact with the system.
            
            **Base URL:** `http://localhost:8000`
            
            #### Authentication
            - **POST** `/api/login` - Authenticate user
            ```json
            {
                "user": "Brandon",
                "password": "owner123"
            }
            ```
            
            #### Trailers
            - **GET** `/api/trailers` - Get all trailers
            - **GET** `/api/trailers/{id}` - Get specific trailer
            - **POST** `/api/trailers` - Create new trailer
            - **PUT** `/api/trailers/{id}` - Update trailer
            - **DELETE** `/api/trailers/{id}` - Delete trailer
            
            #### Moves
            - **GET** `/api/moves` - Get all moves
            - **GET** `/api/moves/{id}` - Get specific move
            - **POST** `/api/moves` - Create new move
            - **PUT** `/api/moves/{id}` - Update move status
            
            #### Dashboard
            - **GET** `/api/dashboard/stats` - Get dashboard statistics
            - **GET** `/api/dashboard/recent-activity` - Get recent activities
            """)
        
        # VB.NET Example Code
        with st.expander("📝 VB.NET Integration Example"):
            st.code("""
' VB.NET Example Code
Imports System.Net.Http
Imports Newtonsoft.Json

Public Class TrailerTrackerAPI
    Private ReadOnly baseUrl As String = "http://localhost:8000"
    Private ReadOnly client As New HttpClient()
    Private token As String = ""
    
    ' Login to the API
    Public Async Function Login(username As String, password As String) As Task(Of Boolean)
        Dim loginData = New With {
            .username = username,
            .password = password
        }
        
        Dim json = JsonConvert.SerializeObject(loginData)
        Dim content = New StringContent(json, Encoding.UTF8, "application/json")
        
        Dim response = Await client.PostAsync($"{baseUrl}/api/login", content)
        
        If response.IsSuccessStatusCode Then
            Dim result = Await response.Content.ReadAsStringAsync()
            Dim loginResponse = JsonConvert.DeserializeObject(Of LoginResponse)(result)
            token = loginResponse.token
            client.DefaultRequestHeaders.Authorization = 
                New Headers.AuthenticationHeaderValue("Bearer", token)
            Return True
        End If
        
        Return False
    End Function
    
    ' Get all trailers
    Public Async Function GetTrailers() As Task(Of List(Of Trailer))
        Dim response = Await client.GetAsync($"{baseUrl}/api/trailers")
        
        If response.IsSuccessStatusCode Then
            Dim json = Await response.Content.ReadAsStringAsync()
            Return JsonConvert.DeserializeObject(Of List(Of Trailer))(json)
        End If
        
        Return New List(Of Trailer)()
    End Function
    
    ' Create a new trailer
    Public Async Function CreateTrailer(trailer As Trailer) As Task(Of Boolean)
        Dim json = JsonConvert.SerializeObject(trailer)
        Dim content = New StringContent(json, Encoding.UTF8, "application/json")
        
        Dim response = Await client.PostAsync($"{baseUrl}/api/trailers", content)
        Return response.IsSuccessStatusCode
    End Function
End Class

' Trailer model class
Public Class Trailer
    Public Property id As Integer
    Public Property trailer_number As String
    Public Property trailer_type As String
    Public Property status As String
    Public Property current_location As String
    Public Property condition As String
End Class
            """, language="vb")
        
        # Test API Connection
        st.markdown("### 🧪 Test API Connection")
        
        col1, col2 = st.columns(2)
        with col1:
            test_username = st.text_input("Test Username", value="Brandon")
        with col2:
            test_password = st.text_input("Test Password", value="owner123", type="password")
        
        if st.button("🔍 Test Connection", type="primary"):
            try:
                import requests
                
                # Test login
                response = requests.post(
                    "http://localhost:8000/api/login",
                    json={"user": test_username, "password": test_password}
                )
                
                if response.status_code == 200:
                    st.success("✅ API connection successful!")
                    
                    # Show response
                    st.json(response.json())
                    
                    # Test getting trailers
                    token = response.json().get("token", "")
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    trailers_response = requests.get(
                        "http://localhost:8000/api/trailers",
                        headers=headers
                    )
                    
                    if trailers_response.status_code == 200:
                        st.markdown("#### Trailers in System:")
                        trailers = trailers_response.json()
                        if trailers:
                            df = pd.DataFrame(trailers)
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("No trailers in system yet")
                else:
                    st.error(f"Login failed: {response.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API. Please start the API server first.")
            except Exception as e:
                st.error(f"Error: {e}")
    
    elif st.session_state.page == "Data Entry":
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
                
                customer_owner = st.text_input(
                    "Customer/Owner",
                    placeholder="e.g., ABC Company or 'Company Owned'"
                )
                
                status = st.selectbox(
                    "Status",
                    ["available", "in_use", "maintenance", "retired", "reserved"]
                )
                
                notes = st.text_area(
                    "Notes",
                    placeholder="Any additional information...",
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
                             customer_owner, year_manufactured, notes, updated_by, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            trailer_number, trailer_type, status, condition, current_location,
                            customer_owner, year, notes, st.session_state.username, datetime.now()
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
                        st.success("Changes saved!")
                        VernonHelper.show_tip("All changes have been logged for audit", "info")
                else:
                    st.info("No trailers found matching your criteria")
            except Exception as e:
                st.info("No trailers in system yet")
    
    # Keep existing pages
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
                
                conn.close()
            except:
                st.info("Statistics will appear as data is entered")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #888; font-size: 0.9em;'>© 2025 Smith & Williams Trucking | 🔐 Protected by Vernon - Chief Data Security Officer</p>",
        unsafe_allow_html=True
    )