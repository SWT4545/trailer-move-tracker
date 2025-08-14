"""
Smith & Williams Trucking - Simplified Working Version
Phase 1: Basic app with working login and core features
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import sqlite3
import hashlib

# Page config
st.set_page_config(
    page_title="Smith & Williams Trucking",
    page_icon="🚛",
    layout="wide"
)

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

# Login page
if not st.session_state.authenticated:
    st.markdown("# Smith & Williams Trucking")
    st.markdown("### Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Login", type="primary", use_container_width=True):
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
            if st.button("Demo Mode", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.username = "demo_user"
                st.session_state.user_role = "admin"
                st.success("✅ Demo mode activated!")
                st.rerun()
        
        st.info("""
        **Test Accounts:**
        - Brandon / owner123
        - admin / admin123
        - Or click Demo Mode
        """)
    
    st.markdown("---")
    st.markdown("© 2025 Smith & Williams Trucking")

# Main app
else:
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        st.markdown(f"Role: {st.session_state.user_role}")
        
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_role = None
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 🔐 Vernon")
        st.markdown("Chief Data Security Officer")
    
    # Main content
    st.title("Smith & Williams Trucking")
    st.markdown(f"Welcome, {st.session_state.username}!")
    
    # Create tabs
    tabs = st.tabs(["📊 Dashboard", "🚚 Trailers", "📦 Moves", "📄 Reports"])
    
    # Dashboard Tab
    with tabs[0]:
        st.header("Dashboard")
        
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get stats
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
                st.metric("Pending Moves", pending)
            with col2:
                st.metric("In Progress", in_progress)
            with col3:
                st.metric("Completed", completed)
            with col4:
                st.metric("Total Trailers", total_trailers)
            
        except Exception as e:
            st.info("No data available yet - this is normal for a new system")
    
    # Trailers Tab
    with tabs[1]:
        st.header("Trailer Management")
        
        # Add new trailer
        with st.expander("➕ Add New Trailer"):
            col1, col2 = st.columns(2)
            with col1:
                trailer_number = st.text_input("Trailer Number")
                trailer_type = st.selectbox("Type", ["Roller Bed", "Dry Van", "Flatbed", "Reefer", "Step Deck", "Double Drop", "Lowboy", "Other"])
            with col2:
                location = st.text_input("Current Location")
                status = st.selectbox("Status", ["available", "in_use", "maintenance"])
            
            if st.button("Add Trailer"):
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    # Create table if not exists
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS trailers (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            trailer_number TEXT UNIQUE,
                            trailer_type TEXT,
                            location TEXT,
                            status TEXT
                        )
                    ''')
                    
                    cursor.execute(
                        "INSERT INTO trailers (trailer_number, trailer_type, location, status) VALUES (?, ?, ?, ?)",
                        (trailer_number, trailer_type, location, status)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Trailer {trailer_number} added!")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        # Display trailers
        try:
            conn = get_connection()
            df = pd.read_sql_query("SELECT * FROM trailers", conn)
            conn.close()
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No trailers added yet")
        except:
            st.info("No trailer data available")
    
    # Moves Tab
    with tabs[2]:
        st.header("Move Management")
        
        # Add new move
        with st.expander("➕ Add New Move"):
            col1, col2 = st.columns(2)
            with col1:
                order_number = st.text_input("Order Number")
                customer = st.text_input("Customer Name")
                origin = st.text_input("Origin City")
            with col2:
                destination = st.text_input("Destination City")
                amount = st.number_input("Amount", min_value=0.0)
                move_status = st.selectbox("Status", ["pending", "in_progress", "completed"])
            
            if st.button("Add Move"):
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO moves (order_number, customer_name, origin_city, destination_city, amount, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (order_number, customer, origin, destination, amount, move_status))
                    
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Move {order_number} added!")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        # Display moves
        try:
            conn = get_connection()
            df = pd.read_sql_query(
                "SELECT order_number, customer_name, origin_city, destination_city, status, amount FROM moves ORDER BY created_at DESC LIMIT 50",
                conn
            )
            conn.close()
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No moves added yet")
        except:
            st.info("No move data available")
    
    # Reports Tab
    with tabs[3]:
        st.header("Reports")
        
        if st.button("📄 Generate PDF Report", type="primary"):
            st.info("PDF report generation will be added in Phase 2")
        
        # Simple summary
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            st.subheader("Quick Summary")
            
            # Get summary data
            cursor.execute("SELECT status, COUNT(*) as count FROM moves GROUP BY status")
            summary = cursor.fetchall()
            
            if summary:
                for status, count in summary:
                    st.write(f"- {status.title()}: {count} moves")
            else:
                st.info("No data for summary")
            
            conn.close()
        except:
            st.info("Summary data not available")
    
    # Footer
    st.markdown("---")
    st.markdown("© 2025 Smith & Williams Trucking | 🔐 Protected by Vernon - Chief Data Security Officer")