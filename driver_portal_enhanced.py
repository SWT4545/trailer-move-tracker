"""
Enhanced Driver Portal with Self-Assignment
Includes all database fixes and UI improvements from previous iterations
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import database as db
import hashlib
import json
from driver_self_assignment import DriverSelfAssignment, show_self_assignment_interface
from database_connection_manager import db_manager, get_all_drivers_safe
import mileage_calculator as mileage_calc
import sqlite3

# Ensure tables exist
def ensure_driver_tables():
    """Ensure all driver-related tables exist"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if driver availability table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS driver_availability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_id INTEGER NOT NULL,
                status TEXT DEFAULT 'available',
                current_move_id TEXT,
                last_known_location TEXT,
                completed_moves_today INTEGER DEFAULT 0,
                max_daily_moves INTEGER DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Ensure password_hash column exists in drivers table
        cursor.execute("PRAGMA table_info(drivers)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'password_hash' not in columns:
            cursor.execute("ALTER TABLE drivers ADD COLUMN password_hash TEXT")
        
        if 'can_self_assign' not in columns:
            cursor.execute("ALTER TABLE drivers ADD COLUMN can_self_assign BOOLEAN DEFAULT 1")
        
        conn.commit()
    except Exception as e:
        st.error(f"Database initialization error: {e}")
    finally:
        conn.close()

def hash_password(password):
    """Hash password for security"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_driver(username, password):
    """Authenticate driver login"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        
        cursor.execute("""
            SELECT id, driver_name, driver_type, can_self_assign
            FROM drivers
            WHERE user = ? AND password_hash = ?
            AND (active = 1 OR active IS NULL)
        """, (username, password_hash))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'id': result[0],
                'driver_name': result[1],
                'driver_type': result[2] or 'contractor',
                'can_self_assign': result[3] if result[3] is not None else True
            }
        return None
        
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return None
    finally:
        conn.close()

def show_driver_login():
    """Enhanced driver login page"""
    
    # Initialize tables if needed
    ensure_driver_tables()
    
    st.markdown("""
    <style>
        .login-container {
            max-width: 500px;
            margin: auto;
            padding: 2rem;
            background: #1a1a1a;
            border-radius: 10px;
            border: 2px solid #DC143C;
        }
        .stButton > button {
            background-color: #DC143C;
            color: white;
            font-weight: bold;
        }
        .stButton > button:hover {
            background-color: #8B0000;
            border-color: #8B0000;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1 style="color: #DC143C;">🚛 Smith & Williams Trucking</h1>
        <h2>Driver Portal - Self Assignment System</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown("### 🔐 Driver Login")
            
            with st.form("driver_login_form", clear_on_submit=False):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                remember_me = st.checkbox("Remember me for 7 days")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    submitted = st.form_submit_button("🚀 Login", type="primary", use_container_width=True)
                with col_b:
                    if st.form_submit_button("📞 Contact Support", use_container_width=True):
                        st.info("Contact dispatch at (555) 123-4567 for password reset")
                
                if submitted:
                    if username and password:
                        driver = authenticate_driver(username, password)
                        
                        if driver:
                            st.session_state['driver_authenticated'] = True
                            st.session_state['driver_id'] = driver['id']
                            st.session_state['driver_name'] = driver['driver_name']
                            st.session_state['driver_type'] = driver['driver_type']
                            st.session_state['can_self_assign'] = driver['can_self_assign']
                            
                            # Set session timeout based on remember me
                            if remember_me:
                                st.session_state['session_timeout'] = datetime.now() + timedelta(days=7)
                            else:
                                st.session_state['session_timeout'] = datetime.now() + timedelta(hours=8)
                            
                            st.success(f"Welcome, {driver['driver_name']}!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
                    else:
                        st.error("⚠️ Please enter both username and password")
        
        with st.expander("ℹ️ Login Help"):
            st.markdown("""
            **First Time Users:**
            - Username provided by dispatch
            - Temporary password sent via text
            - You'll change password on first login
            
            **Self-Assignment System:**
            - View available moves in real-time
            - Self-assign moves instantly
            - Track progress and earnings
            - No waiting for coordinator assignment
            
            **Support:** Call dispatch for assistance
            """)

def update_move_progress(move_id, new_status, driver_name):
    """Update move progress with proper database handling"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("BEGIN TRANSACTION")
        
        # Update move status
        timestamp_field = None
        timestamp_value = datetime.now()
        
        if new_status == 'in_progress':
            timestamp_field = 'pickup_time'
        elif new_status == 'pickup_complete':
            timestamp_field = 'pickup_time'
        elif new_status == 'completed':
            timestamp_field = 'delivery_time'
        
        if timestamp_field:
            cursor.execute(f"""
                UPDATE moves
                SET status = ?,
                    {timestamp_field} = ?,
                    updated_at = ?
                WHERE move_id = ?
            """, (new_status, timestamp_value, timestamp_value, move_id))
        else:
            cursor.execute("""
                UPDATE moves
                SET status = ?,
                    updated_at = ?
                WHERE move_id = ?
            """, (new_status, timestamp_value, move_id))
        
        # Update driver availability if completed
        if new_status == 'completed':
            cursor.execute("""
                UPDATE driver_availability
                SET status = 'available',
                    current_move_id = NULL,
                    completed_moves_today = completed_moves_today + 1,
                    updated_at = ?
                WHERE driver_id = (
                    SELECT id FROM drivers WHERE driver_name = ?
                )
            """, (timestamp_value, driver_name))
        
        # Log the progress update
        cursor.execute("""
            INSERT INTO assignment_history (
                move_id, driver_name, action, action_by, action_type, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (move_id, driver_name, new_status, driver_name, 'self', timestamp_value))
        
        cursor.execute("COMMIT")
        conn.commit()
        return True, "Progress updated successfully"
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        return False, str(e)
    finally:
        conn.close()

def show_driver_dashboard():
    """Enhanced driver dashboard with self-assignment"""
    
    # Check session timeout
    if 'session_timeout' in st.session_state:
        if datetime.now() > st.session_state['session_timeout']:
            st.warning("Session expired. Please login again.")
            for key in ['driver_authenticated', 'driver_id', 'driver_name']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    driver_id = st.session_state.get('driver_id')
    driver_name = st.session_state.get('driver_name')
    can_self_assign = st.session_state.get('can_self_assign', True)
    
    if not driver_id:
        st.error("Please login first")
        return
    
    # Header with driver info and actions
    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div style="padding: 1rem; background: #1a1a1a; border-radius: 8px; border: 2px solid #DC143C;">
            <h2 style="margin: 0; color: #DC143C;">Welcome, {driver_name}</h2>
            <p style="margin: 0; color: #888;">{st.session_state.get('driver_type', 'Contractor').title()} Driver</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    with col4:
        if st.button("🔒 Logout", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.markdown("---")
    
    # Main navigation tabs
    if can_self_assign:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎯 Self-Assign Move",
            "📊 Current Move",
            "💰 My Earnings",
            "📍 Report Trailer",
            "⚙️ Settings"
        ])
    else:
        tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Current Move",
            "💰 My Earnings",
            "📍 Report Trailer",
            "⚙️ Settings"
        ])
        tab1 = None
    
    # Self-Assignment Tab
    if tab1:
        with tab1:
            show_self_assignment_interface(driver_id, driver_name)
    
    # Current Move Tab
    with tab2:
        st.markdown("### 🚚 Current Move Status")
        
        # Get current move
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                move_id, new_trailer, old_trailer,
                pickup_location, delivery_location,
                status, total_miles, driver_pay,
                pickup_time, delivery_time,
                self_assigned, created_at
            FROM moves
            WHERE driver_name = ?
            AND status IN ('assigned', 'in_progress', 'pickup_complete')
            ORDER BY created_at DESC
            LIMIT 1
        """, (driver_name,))
        
        current_move = cursor.fetchone()
        conn.close()
        
        if current_move:
            move_id, new_trailer, old_trailer, pickup_loc, delivery_loc, status, miles, pay, pickup_time, delivery_time, self_assigned, created_at = current_move
            
            # Progress indicator
            progress_map = {
                'assigned': 25,
                'in_progress': 50,
                'pickup_complete': 75,
                'completed': 100
            }
            
            progress = progress_map.get(status, 0)
            st.progress(progress / 100)
            st.caption(f"Status: **{status.replace('_', ' ').title()}** ({progress}% complete)")
            
            # Move details in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**📦 Trailers**")
                st.write(f"NEW: {new_trailer}")
                st.write(f"OLD: {old_trailer}")
                st.write(f"Move ID: {move_id}")
            
            with col2:
                st.markdown("**📍 Route**")
                st.write(f"From: {pickup_loc}")
                st.write(f"To: {delivery_loc}")
                if miles:
                    st.write(f"Distance: {miles} miles")
            
            with col3:
                st.markdown("**💵 Earnings**")
                if pay:
                    st.write(f"Pay: ${pay:,.2f}")
                else:
                    st.write("Pay: Calculating...")
                st.write(f"Type: {'Self-Assigned' if self_assigned else 'Assigned'}")
            
            st.markdown("---")
            
            # Action buttons based on current status
            col1, col2, col3, col4 = st.columns(4)
            
            if status == 'assigned':
                with col1:
                    if st.button("🚀 Start Pickup", type="primary", use_container_width=True):
                        success, msg = update_move_progress(move_id, 'in_progress', driver_name)
                        if success:
                            st.success("Pickup started! Drive safely.")
                            st.rerun()
                        else:
                            st.error(f"Error: {msg}")
                
                with col4:
                    if st.button("❌ Cancel Move", use_container_width=True):
                        if st.session_state.get('confirm_cancel'):
                            success, msg = update_move_progress(move_id, 'cancelled', driver_name)
                            if success:
                                st.warning("Move cancelled")
                                del st.session_state['confirm_cancel']
                                st.rerun()
                        else:
                            st.session_state['confirm_cancel'] = True
                            st.warning("Click again to confirm cancellation")
            
            elif status == 'in_progress':
                with col1:
                    if st.button("✅ Pickup Complete", type="primary", use_container_width=True):
                        success, msg = update_move_progress(move_id, 'pickup_complete', driver_name)
                        if success:
                            st.success("Pickup completed! Proceed to delivery.")
                            st.rerun()
                        else:
                            st.error(f"Error: {msg}")
                
                with col2:
                    st.button("📸 Upload Pickup Photo", use_container_width=True)
            
            elif status == 'pickup_complete':
                with col1:
                    if st.button("🏁 Complete Delivery", type="primary", use_container_width=True):
                        success, msg = update_move_progress(move_id, 'completed', driver_name)
                        if success:
                            st.success("Delivery completed! Great job!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"Error: {msg}")
                
                with col2:
                    st.button("📸 Upload Delivery Photo", use_container_width=True)
                
                with col3:
                    st.button("📄 Upload POD", use_container_width=True)
        
        else:
            st.info("No active move. Check the Self-Assign tab to get started!")
    
    # Earnings Tab
    with tab3:
        st.markdown("### 💰 Earnings & Payment History")
        
        # Date range selector
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            days_back = st.selectbox("Show last", [7, 14, 30, 60, 90], index=2)
        
        with col3:
            if st.button("🔄 Refresh Earnings"):
                st.rerun()
        
        # Get earnings data
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                move_date,
                move_id,
                new_trailer,
                old_trailer,
                delivery_location,
                total_miles,
                driver_pay,
                payment_status,
                driver_paid
            FROM moves
            WHERE driver_name = ?
            AND status = 'completed'
            AND move_date >= date('now', '-' || ? || ' days')
            ORDER BY move_date DESC
        """, (driver_name, days_back))
        
        moves_data = cursor.fetchall()
        conn.close()
        
        if moves_data:
            # Calculate totals
            total_earnings = sum(row[6] for row in moves_data if row[6])
            paid_earnings = sum(row[6] for row in moves_data if row[6] and row[8])
            pending_earnings = total_earnings - paid_earnings
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Moves", len(moves_data))
            with col2:
                st.metric("Total Earnings", f"${total_earnings:,.2f}")
            with col3:
                st.metric("Paid", f"${paid_earnings:,.2f}")
            with col4:
                st.metric("Pending", f"${pending_earnings:,.2f}")
            
            st.markdown("---")
            
            # Create DataFrame for display
            df = pd.DataFrame(moves_data, columns=[
                'Date', 'Move ID', 'New Trailer', 'Old Trailer',
                'Location', 'Miles', 'Pay', 'Status', 'Paid Date'
            ])
            
            # Format columns
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%m/%d/%Y')
            df['Pay'] = df['Pay'].apply(lambda x: f"${x:,.2f}" if x else "TBD")
            df['Status'] = df['Status'].str.title()
            df['Paid Date'] = pd.to_datetime(df['Paid Date']).dt.strftime('%m/%d/%Y')
            df['Paid Date'] = df['Paid Date'].fillna('Pending')
            
            # Display table
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Date": st.column_config.DateColumn("Date", width="small"),
                    "Miles": st.column_config.NumberColumn("Miles", width="small"),
                    "Pay": st.column_config.TextColumn("Pay", width="small"),
                }
            )
        else:
            st.info(f"No completed moves in the last {days_back} days")
    
    # Report Trailer Tab
    with tab4:
        st.markdown("### 📍 Report Trailer Location")
        st.info("Help the team by confirming trailer locations as you see them")
        
        with st.form("report_trailer_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                trailer_number = st.text_input(
                    "Trailer Number *",
                    placeholder="e.g., TRL-001",
                    help="Enter the trailer number you spotted"
                )
                
                location = st.text_input(
                    "Location *",
                    placeholder="e.g., Memphis Terminal",
                    help="Where did you see this trailer?"
                )
            
            with col2:
                city = st.text_input("City", placeholder="e.g., Memphis")
                state = st.selectbox("State", [""] + ["TN", "MS", "AR", "AL", "MO", "KY", "GA", "TX"])
                
                notes = st.text_area(
                    "Notes",
                    placeholder="Any additional details (condition, accessibility, etc.)"
                )
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                photo_upload = st.file_uploader("Photo (optional)", type=['jpg', 'jpeg', 'png'])
            
            with col2:
                submit_report = st.form_submit_button("📤 Submit Report", type="primary", use_container_width=True)
            
            with col3:
                cancel_report = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if submit_report:
                if trailer_number and location:
                    # Save report to database
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    
                    try:
                        full_location = f"{location}, {city}, {state}" if city and state else location
                        
                        cursor.execute("""
                            INSERT INTO trailer_location_reports (
                                trailer_number, reported_location,
                                reported_by_driver, notes, reported_at
                            ) VALUES (?, ?, ?, ?, ?)
                        """, (trailer_number, full_location, driver_name, notes, datetime.now()))
                        
                        conn.commit()
                        st.success(f"✅ Thank you! Trailer {trailer_number} location reported.")
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"Error saving report: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("Please fill in required fields")
    
    # Settings Tab
    with tab5:
        st.markdown("### ⚙️ Driver Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔔 Notifications")
            email_notif = st.checkbox("Email notifications", value=True)
            sms_notif = st.checkbox("SMS notifications", value=True)
            
            st.markdown("#### 🚚 Preferences")
            max_daily = st.number_input(
                "Max daily moves",
                min_value=1,
                max_value=5,
                value=1,
                help="Maximum number of moves you want per day"
            )
        
        with col2:
            st.markdown("#### 🔐 Security")
            
            with st.form("change_password_form"):
                st.markdown("**Change Password**")
                current_pw = st.text_input("Current Password", type="password")
                new_pw = st.text_input("New Password", type="password")
                confirm_pw = st.text_input("Confirm Password", type="password")
                
                if st.form_submit_button("Update Password"):
                    if new_pw == confirm_pw:
                        # Update password logic here
                        st.success("Password updated successfully")
                    else:
                        st.error("Passwords don't match")
        
        if st.button("💾 Save Settings", type="primary"):
            st.success("Settings saved successfully")


def main():
    """Main entry point for enhanced driver portal"""
    
    # Page config
    st.set_page_config(
        page_title="Driver Portal - Smith & Williams",
        page_icon="🚛",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
        .stApp {
            background-color: #0E0E0E;
        }
        .stTabs [data-baseweb="tab-list"] {
            background-color: #1a1a1a;
            border-radius: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            color: white;
            font-weight: bold;
        }
        .stTabs [aria-selected="true"] {
            background-color: #DC143C;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Check authentication
    if not st.session_state.get('driver_authenticated'):
        show_driver_login()
    else:
        show_driver_dashboard()


if __name__ == "__main__":
    main()