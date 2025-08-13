"""
Smith & Williams Trucking - Complete System with Self-Assignment
Main application with all features integrated
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import database as db
import auth_config
import mileage_calculator as mileage_calc
import base_location_manager as base_mgr
import uuid
import json
import time
import sqlite3

# Existing imports
import walkthrough_guide
import walkthrough_guide_enhanced
import walkthrough_practical
import company_config
import it_bot_vernon as vernon_it
import vernon_sidebar
import rate_con_manager
import rate_con_redesigned
import user_manager
import client_portal
import enhanced_user_manager
import enhanced_data_management
from payment_receipt_system import show_payment_receipt_interface
import move_editor
import w9_manager

# New imports for PDF and data entry
try:
    from pdf_report_generator import show_pdf_report_interface, generate_status_report_for_profile
    from trailer_data_entry_system import show_trailer_data_entry_interface
    PDF_REPORTS_AVAILABLE = True
except ImportError:
    PDF_REPORTS_AVAILABLE = False

# Enhanced modules for fixes
import ui_responsiveness_fix as ui_fix
import driver_management_enhanced
import vernon_enhanced
import trailer_swap_enhanced

# NEW SELF-ASSIGNMENT IMPORTS
try:
    from driver_self_assignment import DriverSelfAssignment, show_self_assignment_interface
    from driver_portal_enhanced import show_driver_login, show_driver_dashboard
    from driver_mobile_optimized import show_mobile_interface
    from database_self_assignment_migration import run_migration, verify_migration
    from vernon_it_personality import Vernon, show_vernon_chat_interface, integrate_vernon_everywhere
    from walkthrough_self_assignment import show_walkthrough_interface as show_self_assignment_walkthrough
    from realtime_sync_manager import RealtimeSyncManager, show_realtime_notifications, auto_refresh_check
    from document_management_enhanced import show_driver_document_upload, show_admin_document_management, show_document_dashboard
    from trailer_submission_approval_system import show_driver_trailer_submission, show_coordinator_approval_queue
    SELF_ASSIGNMENT_AVAILABLE = True
except ImportError as e:
    print(f"Self-assignment modules not available: {e}")
    SELF_ASSIGNMENT_AVAILABLE = False

# Page configuration
try:
    st.set_page_config(
        page_title="Smith & Williams Trucking",
        page_icon="🚛",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    if 'cache_cleared' not in st.session_state:
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.cache_cleared = True
except:
    pass

# Initialize database
db.init_database()

# Run self-assignment migration if available and needed
if SELF_ASSIGNMENT_AVAILABLE and 'migration_checked' not in st.session_state:
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='driver_availability'")
        if not cursor.fetchone():
            with st.spinner("🔄 Upgrading system for self-assignment features..."):
                run_migration()
                verify_migration()
            st.success("✅ Self-assignment features activated!")
        conn.close()
        st.session_state.migration_checked = True
    except Exception as e:
        print(f"Migration check error: {e}")

# Ensure all tables exist
try:
    from database_connection_manager import db_manager
    db_manager.ensure_tables()
except:
    pass

# Run standard migration
try:
    import database_migration
    if 'migration_done' not in st.session_state:
        migration = database_migration.DatabaseMigration()
        migration.run_safe_migration()
        st.session_state.migration_done = True
except:
    pass

def apply_dark_theme():
    """Apply dark theme with red accents"""
    st.markdown("""
    <style>
        .stApp {
            background-color: #0E0E0E;
        }
        div[data-baseweb="select"] > div {
            background-color: #1a1a1a !important;
            border: 1px solid #DC143C !important;
        }
        /* Role switcher badge */
        .role-badge {
            background: linear-gradient(135deg, #DC143C, #8B0000);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: bold;
            display: inline-block;
            margin: 0.5rem 0;
        }
        /* Mobile optimizations for iOS */
        @media (max-width: 768px) {
            .stButton > button {
                min-height: 44px !important;
                font-size: 16px !important;
            }
            input, select, textarea {
                font-size: 16px !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

apply_dark_theme()

def check_dual_role(username):
    """Check if user has dual role capabilities"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT role FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0]:
        role = result[0]
        if '+' in role:  # Has dual role
            return True, role.split('+')
        # Check if they have a driver profile
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM drivers WHERE username = ?", (username,))
        has_driver = cursor.fetchone()
        conn.close()
        if has_driver:
            return True, [role, 'Driver']
    return False, None

def show_role_switcher():
    """Show role switching interface in sidebar"""
    if st.session_state.get('has_dual_role'):
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔄 Role Switcher")
        
        roles = st.session_state.get('available_roles', ['Owner', 'Driver'])
        current_mode = st.session_state.get('current_mode', roles[0])
        
        for role in roles:
            if st.sidebar.button(
                f"{'👔' if 'Admin' in role or 'Owner' in role else '🚛'} {role} Mode",
                type="primary" if current_mode == role else "secondary",
                use_container_width=True,
                disabled=(current_mode == role)
            ):
                st.session_state.current_mode = role
                st.session_state.user_role = role
                if role == 'Driver':
                    st.session_state.driver_authenticated = True
                st.rerun()
        
        st.sidebar.markdown(
            f'<div class="role-badge">Current: {current_mode}</div>',
            unsafe_allow_html=True
        )

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Main app logic
if not st.session_state.authenticated:
    auth_config.show_login()
else:
    user_role = st.session_state.user_role
    username = st.session_state.username
    
    # Check for dual role
    if SELF_ASSIGNMENT_AVAILABLE:
        has_dual, roles = check_dual_role(username)
        if has_dual:
            st.session_state.has_dual_role = True
            st.session_state.available_roles = roles
            if 'current_mode' not in st.session_state:
                st.session_state.current_mode = roles[0]
            user_role = st.session_state.current_mode
    
    # Sidebar
    with st.sidebar:
        # Vernon IT Support (Super IT Man)
        if SELF_ASSIGNMENT_AVAILABLE:
            vernon = Vernon()
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e3a8a, #3b82f6);
                        padding: 1rem; border-radius: 8px; color: white; margin-bottom: 1rem;">
                <h4>🔐 Vernon - CDSO</h4>
                <p style="margin: 0; font-size: 0.9rem;">Chief Data Security Officer</p>
                <p style="margin: 0; font-size: 0.8rem;">📞 Ext. 1337 | Secure Line 24/7</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("💬 Chat with Vernon", use_container_width=True):
                st.session_state.show_vernon_chat = True
        else:
            vernon_sidebar.show_vernon_sidebar()
        
        # Role switcher for dual-role users
        if st.session_state.get('has_dual_role'):
            show_role_switcher()
        
        # Real-time notifications
        if SELF_ASSIGNMENT_AVAILABLE:
            show_realtime_notifications()
    
    # Show Vernon chat if requested
    if SELF_ASSIGNMENT_AVAILABLE and st.session_state.get('show_vernon_chat'):
        show_vernon_chat_interface()
        if st.button("Close Chat"):
            st.session_state.show_vernon_chat = False
            st.rerun()
    
    # Main content based on role
    elif user_role in ["Admin", "Owner", "business_administrator", "executive"]:
        st.title("🚛 Smith & Williams Trucking - Admin Dashboard")
        
        # Enhanced tabs with self-assignment
        tab_list = ["🏠 Dashboard", "🚚 Trailers", "📦 Moves", "👥 Drivers", 
                   "📍 Locations", "💰 Payments", "📊 Analytics", "📋 Documents"]
        
        # Add PDF reports tab if available
        if PDF_REPORTS_AVAILABLE:
            tab_list.append("📄 PDF Reports")
        
        # Add data entry tab for testing
        if st.session_state.get('demo_mode'):
            tab_list.append("📝 Data Entry")
        
        if SELF_ASSIGNMENT_AVAILABLE:
            tab_list.extend(["🎯 Self-Assignment", "📝 Trailer Approvals"])
        
        tab_list.extend(["📚 Training", "⚙️ Settings"])
        
        tabs = st.tabs(tab_list)
        
        tab_index = 0
        with tabs[tab_index]:  # Dashboard
            trailer_swap_enhanced.show_admin_dashboard()
            tab_index += 1
            
        with tabs[tab_index]:  # Trailers
            trailer_swap_enhanced.show_trailer_entry_page()
            tab_index += 1
            
        with tabs[tab_index]:  # Moves
            trailer_swap_enhanced.show_move_assignment_page()
            tab_index += 1
            
        with tabs[tab_index]:  # Drivers
            driver_management_enhanced.show_driver_management()
            tab_index += 1
            
        with tabs[tab_index]:  # Locations
            base_mgr.show_location_management()
            tab_index += 1
            
        with tabs[tab_index]:  # Payments
            show_payment_receipt_interface()
            tab_index += 1
            
        with tabs[tab_index]:  # Analytics
            trailer_swap_enhanced.show_analytics_dashboard()
            tab_index += 1
            
        with tabs[tab_index]:  # Documents
            if SELF_ASSIGNMENT_AVAILABLE:
                try:
                    show_document_dashboard()
                except Exception as e:
                    st.info("📋 No documents to display yet - this is normal for new system")
            else:
                st.info("📋 Document management module not loaded - this is normal if not configured")
            tab_index += 1
        
        # PDF Reports tab
        if PDF_REPORTS_AVAILABLE:
            with tabs[tab_index]:  # PDF Reports
                show_pdf_report_interface()
            tab_index += 1
        
        # Data Entry tab (for demo mode)
        if st.session_state.get('demo_mode'):
            with tabs[tab_index]:  # Data Entry
                show_trailer_data_entry_interface(username)
            tab_index += 1
        
        if SELF_ASSIGNMENT_AVAILABLE:
            with tabs[tab_index]:  # Self-Assignment Monitor
                st.markdown("## 🎯 Self-Assignment System")
                
                # Stats
                col1, col2, col3, col4 = st.columns(4)
                conn = db.get_connection()
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM moves WHERE self_assigned = 1 AND date(created_at) = date('now')")
                today_self = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM driver_availability WHERE status = 'available'")
                available_drivers = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM trailers WHERE is_reserved = 1")
                reserved = cursor.fetchone()[0]
                
                conn.close()
                
                with col1:
                    st.metric("Self-Assigned Today", today_self)
                with col2:
                    st.metric("Available Drivers", available_drivers)
                with col3:
                    st.metric("Reserved Trailers", reserved)
                with col4:
                    if st.button("🔄 Refresh"):
                        st.rerun()
                
                # Recent self-assignments
                st.markdown("### Recent Self-Assignments")
                conn = db.get_connection()
                df = pd.read_sql_query("""
                    SELECT 
                        move_id as 'Move ID',
                        driver_name as 'Driver',
                        new_trailer || ' ↔ ' || old_trailer as 'Trailers',
                        delivery_location as 'Location',
                        status as 'Status',
                        datetime(assigned_at, 'localtime') as 'Assigned'
                    FROM moves
                    WHERE self_assigned = 1
                    ORDER BY assigned_at DESC
                    LIMIT 20
                """, conn)
                conn.close()
                
                if not df.empty:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No self-assignments yet")
                tab_index += 1
            
            with tabs[tab_index]:  # Trailer Approvals
                show_coordinator_approval_queue()
                tab_index += 1
        
        with tabs[tab_index]:  # Training
            training_type = st.selectbox(
                "Select Training Module",
                ["Basic", "Enhanced", "Practical", "Self-Assignment"] if SELF_ASSIGNMENT_AVAILABLE 
                else ["Basic", "Enhanced", "Practical"]
            )
            
            if training_type == "Self-Assignment" and SELF_ASSIGNMENT_AVAILABLE:
                show_self_assignment_walkthrough('admin')
            elif training_type == "Basic":
                walkthrough_guide.show_walkthrough()
            elif training_type == "Enhanced":
                walkthrough_guide_enhanced.show_enhanced_walkthrough()
            else:
                walkthrough_practical.show_practical_walkthrough()
            tab_index += 1
            
        with tabs[tab_index]:  # Settings
            company_config.show_company_settings()
    
    elif user_role == "Coordinator":
        st.title("🚛 Coordinator Dashboard")
        
        tab_list = ["🏠 Dashboard", "📋 Assign Moves", "📊 Monitor", "📝 Documents"]
        
        if SELF_ASSIGNMENT_AVAILABLE:
            tab_list.extend(["🎯 Self-Assignments", "📝 Trailer Approvals"])
        
        tab_list.append("📚 Training")
        
        tabs = st.tabs(tab_list)
        
        tab_index = 0
        with tabs[tab_index]:
            trailer_swap_enhanced.show_coordinator_dashboard()
            tab_index += 1
            
        with tabs[tab_index]:
            trailer_swap_enhanced.show_move_assignment_page()
            tab_index += 1
            
        with tabs[tab_index]:
            trailer_swap_enhanced.show_move_tracking()
            tab_index += 1
            
        with tabs[tab_index]:
            if SELF_ASSIGNMENT_AVAILABLE:
                show_document_dashboard()
            else:
                st.info("Document management coming soon")
            tab_index += 1
        
        if SELF_ASSIGNMENT_AVAILABLE:
            with tabs[tab_index]:  # Self-Assignments
                st.markdown("## 🎯 Driver Self-Assignments")
                
                # Monitor self-assignments
                conn = db.get_connection()
                df = pd.read_sql_query("""
                    SELECT 
                        move_id, driver_name, 
                        new_trailer || ' ↔ ' || old_trailer as trailers,
                        delivery_location, status,
                        datetime(assigned_at, 'localtime') as assigned_time
                    FROM moves
                    WHERE self_assigned = 1
                    AND assigned_at >= datetime('now', '-24 hours')
                    ORDER BY assigned_at DESC
                """, conn)
                conn.close()
                
                if not df.empty:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No self-assignments in the last 24 hours")
                tab_index += 1
            
            with tabs[tab_index]:  # Trailer Approvals
                show_coordinator_approval_queue()
                tab_index += 1
        
        with tabs[tab_index]:  # Training
            if SELF_ASSIGNMENT_AVAILABLE:
                show_self_assignment_walkthrough('coordinator')
            else:
                walkthrough_guide.show_walkthrough()
    
    elif user_role == "data_entry":
        # Data Entry Specialist Interface
        st.title("📝 Trailer Data Management Center")
        
        # Vernon helper in sidebar already shown
        
        # Show the data entry interface
        if PDF_REPORTS_AVAILABLE:
            show_trailer_data_entry_interface(username)
        else:
            st.error("Data entry module not available")
    
    elif user_role == "Driver":
        # Check if on mobile
        is_mobile = st.session_state.get('is_mobile', False)
        
        if SELF_ASSIGNMENT_AVAILABLE:
            # Get driver info
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, driver_name FROM drivers WHERE username = ?", (username,))
            driver_info = cursor.fetchone()
            conn.close()
            
            if driver_info:
                driver_id, driver_name = driver_info
                
                if is_mobile:
                    # Mobile optimized interface
                    show_mobile_interface(driver_id, driver_name)
                else:
                    # Full driver dashboard
                    st.title(f"🚛 Driver Portal - {driver_name}")
                    
                    tabs = st.tabs([
                        "🎯 Self-Assign",
                        "📊 Current Move",
                        "💰 Earnings",
                        "📸 Documents",
                        "📍 Report Trailer",
                        "📚 Training"
                    ])
                    
                    with tabs[0]:  # Self-Assignment
                        show_self_assignment_interface(driver_id, driver_name)
                    
                    with tabs[1]:  # Current Move
                        trailer_swap_enhanced.show_driver_moves(driver_name)
                    
                    with tabs[2]:  # Earnings
                        trailer_swap_enhanced.show_driver_earnings(driver_name)
                    
                    with tabs[3]:  # Documents
                        # Get current move
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT move_id FROM moves 
                            WHERE driver_name = ? 
                            AND status IN ('assigned', 'in_progress', 'pickup_complete', 'completed')
                            ORDER BY created_at DESC LIMIT 1
                        """, (driver_name,))
                        result = cursor.fetchone()
                        conn.close()
                        
                        if result:
                            show_driver_document_upload(driver_name, result[0])
                        else:
                            st.info("No active move for document upload")
                    
                    with tabs[4]:  # Report Trailer
                        show_driver_trailer_submission(driver_name)
                    
                    with tabs[5]:  # Training
                        show_self_assignment_walkthrough('driver')
            else:
                st.error("Driver profile not found. Please contact admin.")
        else:
            # Original driver interface
            st.title(f"🚛 Driver Portal")
            tabs = st.tabs(["📊 My Moves", "📸 Documents", "💰 Earnings", "📚 Training"])
            
            with tabs[0]:
                trailer_swap_enhanced.show_driver_moves(username)
            with tabs[1]:
                trailer_swap_enhanced.show_document_upload(username)
            with tabs[2]:
                trailer_swap_enhanced.show_driver_earnings(username)
            with tabs[3]:
                walkthrough_guide.show_walkthrough()
    
    else:
        # Other roles
        st.title(f"🚛 {user_role} Dashboard")
        st.info(f"Welcome {username}! Your role-specific features are being developed.")
        
        # Show basic features
        tabs = st.tabs(["📊 Overview", "📚 Training"])
        
        with tabs[0]:
            st.info("Dashboard coming soon")
        
        with tabs[1]:
            try:
                walkthrough_guide.show_walkthrough()
            except Exception:
                st.info("📚 Training materials will be available here - no data yet (this is normal)")
    
    # Auto-refresh for real-time updates
    if SELF_ASSIGNMENT_AVAILABLE:
        auto_refresh_check()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        Smith & Williams Trucking © 2025 | Professional Trailer Management System
        <br>🔐 Protected by Vernon - Chief Data Security Officer
    </div>
    """,
    unsafe_allow_html=True
)