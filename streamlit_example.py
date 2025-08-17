"""
Streamlit Example App - Trailer Move Tracker
Smith & Williams Trucking LLC
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import json
import hashlib

# Page config
st.set_page_config(
    page_title="Smith & Williams Trucking",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
DB_PATH = 'swt_fleet.db'

def init_database():
    """Initialize database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create moves table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_id TEXT UNIQUE,
            order_number TEXT,
            driver_name TEXT,
            move_date DATE,
            pickup_date DATE,
            completed_date DATE,
            status TEXT DEFAULT 'active',
            new_trailer TEXT,
            old_trailer TEXT,
            origin_location TEXT,
            destination_location TEXT,
            delivery_location TEXT,
            estimated_miles REAL,
            actual_miles REAL,
            estimated_earnings REAL,
            amount REAL,
            client TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create trailers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trailers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trailer_number TEXT UNIQUE,
            type TEXT,
            status TEXT DEFAULT 'available',
            current_location TEXT,
            last_inspection DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create locations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            type TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create drivers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            phone TEXT,
            email TEXT,
            license_number TEXT,
            hire_date DATE,
            status TEXT DEFAULT 'active',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def check_authentication():
    """Check if user is logged in"""
    return st.session_state.get('authenticated', False)

def login():
    """Display login page"""
    st.title("🚛 Smith & Williams Trucking")
    st.subheader("Fleet Management System")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if submit:
                # Simple authentication (in production, use proper hashing)
                users = {
                    "Brandon": {"password": "owner123", "role": "Owner"},
                    "admin": {"password": "admin123", "role": "Admin"},
                    "driver": {"password": "driver123", "role": "Driver"}
                }
                
                if username in users and users[username]["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.role = users[username]["role"]
                    st.rerun()
                else:
                    st.error("Invalid username or password")

def show_sidebar():
    """Display sidebar navigation"""
    with st.sidebar:
        st.title("Navigation")
        st.write(f"Welcome, {st.session_state.get('username', 'User')}")
        st.write(f"Role: {st.session_state.get('role', 'Unknown')}")
        
        st.divider()
        
        # Navigation menu
        menu_items = {
            "Dashboard": "📊",
            "Active Moves": "🚛",
            "Completed Moves": "✅",
            "Trailers": "📦",
            "Drivers": "👥",
            "Locations": "📍",
            "Reports": "📄"
        }
        
        # Add admin menu for owners/admins
        if st.session_state.get('role') in ['Owner', 'Admin']:
            menu_items["Admin Panel"] = "⚙️"
        
        selected_page = st.radio(
            "Select Page",
            list(menu_items.keys()),
            format_func=lambda x: f"{menu_items[x]} {x}"
        )
        
        st.divider()
        
        if st.button("Logout", type="secondary", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        
        return selected_page

def show_dashboard():
    """Display main dashboard"""
    st.title("📊 Dashboard")
    
    # Get metrics from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Count active moves
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'active'")
    active_moves = cursor.fetchone()[0]
    
    # Count completed moves this month
    cursor.execute("""
        SELECT COUNT(*) FROM moves 
        WHERE status = 'completed' 
        AND move_date >= date('now', 'start of month')
    """)
    completed_month = cursor.fetchone()[0]
    
    # Count available trailers
    cursor.execute("SELECT COUNT(*) FROM trailers WHERE status = 'available'")
    available_trailers = cursor.fetchone()[0]
    
    # Count active drivers
    cursor.execute("SELECT COUNT(*) FROM drivers WHERE status = 'active'")
    active_drivers = cursor.fetchone()[0]
    
    conn.close()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Moves", active_moves, delta="2 new today")
    
    with col2:
        st.metric("Completed This Month", completed_month, delta="+15%")
    
    with col3:
        st.metric("Available Trailers", available_trailers)
    
    with col4:
        st.metric("Active Drivers", active_drivers)
    
    st.divider()
    
    # Recent activity
    st.subheader("Recent Activity")
    
    conn = sqlite3.connect(DB_PATH)
    
    # Get recent moves
    recent_moves = pd.read_sql_query("""
        SELECT system_id as 'Move ID', 
               driver_name as 'Driver',
               new_trailer as 'Trailer',
               destination_location as 'Destination',
               status as 'Status',
               move_date as 'Date'
        FROM moves
        ORDER BY created_at DESC
        LIMIT 10
    """, conn)
    
    conn.close()
    
    if not recent_moves.empty:
        st.dataframe(recent_moves, use_container_width=True, hide_index=True)
    else:
        st.info("No recent moves to display")

def show_active_moves():
    """Display active moves page"""
    st.title("🚛 Active Moves")
    
    conn = sqlite3.connect(DB_PATH)
    
    # Get active moves
    active_moves = pd.read_sql_query("""
        SELECT system_id as 'Move ID',
               driver_name as 'Driver',
               new_trailer as 'New Trailer',
               old_trailer as 'Return Trailer',
               origin_location as 'Origin',
               destination_location as 'Destination',
               estimated_miles as 'Miles',
               status as 'Status'
        FROM moves
        WHERE status IN ('active', 'in_transit', 'at_destination')
        ORDER BY move_date DESC
    """, conn)
    
    conn.close()
    
    if not active_moves.empty:
        # Add filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            driver_filter = st.selectbox(
                "Filter by Driver",
                ["All"] + active_moves['Driver'].unique().tolist()
            )
        
        with col2:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All"] + active_moves['Status'].unique().tolist()
            )
        
        # Apply filters
        filtered_moves = active_moves.copy()
        if driver_filter != "All":
            filtered_moves = filtered_moves[filtered_moves['Driver'] == driver_filter]
        if status_filter != "All":
            filtered_moves = filtered_moves[filtered_moves['Status'] == status_filter]
        
        # Display data
        st.dataframe(
            filtered_moves,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Miles": st.column_config.NumberColumn(format="%.1f"),
                "Status": st.column_config.SelectboxColumn(
                    options=["active", "in_transit", "at_destination", "completed"]
                )
            }
        )
        
        # Update status buttons
        if st.session_state.get('role') in ['Owner', 'Admin', 'Manager']:
            st.subheader("Update Move Status")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                move_id = st.selectbox("Select Move", filtered_moves['Move ID'].tolist())
            
            with col2:
                new_status = st.selectbox(
                    "New Status",
                    ["in_transit", "at_destination", "completed"]
                )
            
            with col3:
                if st.button("Update Status", type="primary"):
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE moves SET status = ?, updated_at = ? WHERE system_id = ?",
                        (new_status, datetime.now(), move_id)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Move {move_id} updated to {new_status}")
                    st.rerun()
    else:
        st.info("No active moves at this time")

def show_admin_panel():
    """Display admin panel"""
    st.title("⚙️ Admin Panel")
    
    tabs = st.tabs([
        "Manage Moves",
        "Manage Trailers", 
        "Manage Locations",
        "Manage Drivers",
        "Database Manager"
    ])
    
    with tabs[0]:
        st.subheader("Add New Move")
        
        with st.form("new_move_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                driver_name = st.text_input("Driver Name")
                new_trailer = st.text_input("New Trailer Number")
                old_trailer = st.text_input("Return Trailer Number")
                origin = st.text_input("Origin Location")
            
            with col2:
                destination = st.text_input("Destination Location")
                miles = st.number_input("Estimated Miles", min_value=0.0)
                client = st.text_input("Client Name")
                move_date = st.date_input("Move Date", value=date.today())
            
            if st.form_submit_button("Create Move", type="primary"):
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Generate system ID
                system_id = f"SWT-{datetime.now().year}-{datetime.now().strftime('%m%d%H%M')}"
                
                # Calculate earnings (round trip)
                earnings = miles * 2 * 2.10
                
                cursor.execute("""
                    INSERT INTO moves (
                        system_id, driver_name, new_trailer, old_trailer,
                        origin_location, destination_location, delivery_location,
                        estimated_miles, estimated_earnings, client, 
                        move_date, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    system_id, driver_name, new_trailer, old_trailer,
                    origin, destination, destination, miles, earnings,
                    client, move_date, 'active'
                ))
                
                conn.commit()
                conn.close()
                
                st.success(f"Move {system_id} created successfully!")
                st.balloons()
    
    with tabs[1]:
        st.subheader("Add New Trailer")
        
        with st.form("new_trailer_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                trailer_number = st.text_input("Trailer Number")
                trailer_type = st.selectbox(
                    "Trailer Type",
                    ["53ft Dry Van", "48ft Flatbed", "53ft Reefer"]
                )
            
            with col2:
                location = st.text_input("Current Location")
                status = st.selectbox(
                    "Status",
                    ["available", "in_transit", "maintenance"]
                )
            
            if st.form_submit_button("Add Trailer", type="primary"):
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                try:
                    cursor.execute("""
                        INSERT INTO trailers (
                            trailer_number, type, status, current_location
                        ) VALUES (?, ?, ?, ?)
                    """, (trailer_number, trailer_type, status, location))
                    
                    conn.commit()
                    st.success(f"Trailer {trailer_number} added successfully!")
                except sqlite3.IntegrityError:
                    st.error("Trailer number already exists!")
                finally:
                    conn.close()

def main():
    """Main application"""
    # Initialize database
    init_database()
    
    # Check authentication
    if not check_authentication():
        login()
    else:
        # Show sidebar and get selected page
        page = show_sidebar()
        
        # Route to appropriate page
        if page == "Dashboard":
            show_dashboard()
        elif page == "Active Moves":
            show_active_moves()
        elif page == "Completed Moves":
            st.title("✅ Completed Moves")
            st.info("Completed moves page - Coming soon!")
        elif page == "Trailers":
            st.title("📦 Trailer Management")
            st.info("Trailer management page - Coming soon!")
        elif page == "Drivers":
            st.title("👥 Driver Management")
            st.info("Driver management page - Coming soon!")
        elif page == "Locations":
            st.title("📍 Location Management")
            st.info("Location management page - Coming soon!")
        elif page == "Reports":
            st.title("📄 Reports")
            st.info("Reports page - Coming soon!")
        elif page == "Admin Panel":
            if st.session_state.get('role') in ['Owner', 'Admin']:
                show_admin_panel()
            else:
                st.error("Access denied. Admin privileges required.")

if __name__ == "__main__":
    main()