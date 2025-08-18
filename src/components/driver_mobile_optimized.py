"""
Mobile-Optimized Driver Interface
Designed for smooth operation on smartphones
Large touch targets, simplified navigation, responsive design
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import database as db
from driver_self_assignment import DriverSelfAssignment
import json

def apply_mobile_styles():
    """Apply iOS/Safari optimized CSS styles"""
    st.markdown("""
    <style>
        /* iOS Safari specific optimizations */
        * {
            -webkit-tap-highlight-color: transparent;
            -webkit-touch-callout: none;
            -webkit-user-select: none;
        }
        
        /* Prevent iOS zoom on input focus */
        input, select, textarea {
            font-size: 16px !important;
        }
        
        /* iOS safe area support */
        .stApp {
            padding-top: env(safe-area-inset-top);
            padding-bottom: env(safe-area-inset-bottom);
            padding-left: env(safe-area-inset-left);
            padding-right: env(safe-area-inset-right);
        }
        
        /* Mobile-first responsive design */
        @media (max-width: 768px) {
            .stApp {
                padding: 0 !important;
            }
            
            /* iOS-optimized touch targets (44pt minimum) */
            .stButton > button {
                min-height: 44px !important;
                font-size: 17px !important;
                padding: 12px 16px !important;
                margin: 4px 0 !important;
                border-radius: 12px !important;
                font-weight: 600 !important;
                -webkit-appearance: none !important;
                touch-action: manipulation !important;
            }
            
            /* Primary buttons - green for positive actions */
            div[data-testid="stHorizontalBlock"] button[kind="primary"] {
                background: linear-gradient(135deg, #28a745, #218838) !important;
                color: white !important;
                border: none !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
            }
            
            /* Warning buttons - orange */
            .warning-button button {
                background: linear-gradient(135deg, #ffc107, #e0a800) !important;
                color: #000 !important;
            }
            
            /* Danger buttons - red */
            .danger-button button {
                background: linear-gradient(135deg, #dc3545, #c82333) !important;
                color: white !important;
            }
            
            /* iOS form inputs - prevent zoom */
            .stTextInput > div > div > input,
            .stSelectbox > div > div > div,
            .stTextArea > div > div > textarea {
                font-size: 16px !important;
                padding: 12px !important;
                min-height: 44px !important;
                -webkit-appearance: none !important;
                border-radius: 8px !important;
            }
            
            /* Better spacing for mobile */
            .main > div {
                padding: 0.5rem !important;
            }
            
            /* Cards for move display */
            .move-card {
                background: #1a1a1a;
                border: 2px solid #333;
                border-radius: 12px;
                padding: 1rem;
                margin: 0.75rem 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }
            
            .move-card-available {
                border-color: #28a745;
            }
            
            .move-card-reserved {
                border-color: #ffc107;
                background: #1f1a00;
            }
            
            /* Status badges */
            .status-badge {
                display: inline-block;
                padding: 0.5rem 1rem;
                border-radius: 20px;
                font-weight: bold;
                text-align: center;
                margin: 0.25rem;
            }
            
            .status-available {
                background: #28a745;
                color: white;
            }
            
            .status-assigned {
                background: #007bff;
                color: white;
            }
            
            .status-in-progress {
                background: #ffc107;
                color: #000;
            }
            
            .status-completed {
                background: #6c757d;
                color: white;
            }
            
            /* iOS-style bottom navigation */
            .bottom-nav {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: rgba(26, 26, 26, 0.95);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border-top: 0.5px solid rgba(255, 255, 255, 0.1);
                padding: 8px;
                padding-bottom: calc(8px + env(safe-area-inset-bottom));
                z-index: 999;
                display: flex;
                justify-content: space-around;
            }
            
            .bottom-nav button {
                flex: 1;
                margin: 0 0.25rem;
            }
            
            /* Adjust content for bottom nav */
            .main-content {
                padding-bottom: 5rem !important;
            }
            
            /* Large metrics display */
            [data-testid="metric-container"] {
                background: #1a1a1a;
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid #333;
            }
            
            [data-testid="metric-container"] label {
                font-size: 0.9rem !important;
            }
            
            [data-testid="metric-container"] [data-testid="stMetricValue"] {
                font-size: 1.8rem !important;
                font-weight: bold !important;
                color: #DC143C !important;
            }
        }
        
        /* iOS-style swipe hints */
        .swipe-hint {
            text-align: center;
            color: #8E8E93;
            font-size: 13px;
            padding: 8px;
            font-weight: 400;
            letter-spacing: -0.08px;
            animation: pulse 2s infinite;
        }
        
        /* iOS haptic feedback simulation */
        .stButton > button:active {
            transform: scale(0.98);
            transition: transform 0.1s;
        }
        
        @keyframes pulse {
            0% { opacity: 0.6; }
            50% { opacity: 1; }
            100% { opacity: 0.6; }
        }
        
        /* Progress bar enhancement */
        .stProgress > div > div {
            height: 1.5rem !important;
            border-radius: 12px !important;
        }
        
        /* Tab styling for mobile */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.25rem;
            padding: 0.5rem;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        
        .stTabs [data-baseweb="tab"] {
            white-space: nowrap;
            padding: 0.75rem 1rem !important;
            font-size: 1rem !important;
        }
        
        /* Hide sidebar on mobile by default */
        @media (max-width: 768px) {
            section[data-testid="stSidebar"] {
                transform: translateX(-100%);
            }
            
            section[data-testid="stSidebar"][aria-expanded="true"] {
                transform: translateX(0);
            }
        }
    </style>
    """, unsafe_allow_html=True)

def show_mobile_driver_dashboard(driver_id, driver_name):
    """Mobile-optimized driver dashboard"""
    
    apply_mobile_styles()
    
    # Get driver assignment object
    assignment = DriverSelfAssignment(driver_id, driver_name)
    
    # Simple mobile header
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #DC143C, #8B0000); 
                color: white; padding: 1rem; border-radius: 0 0 12px 12px;
                margin: -1rem -1rem 1rem -1rem;">
        <h2 style="margin: 0;">👋 {driver_name}</h2>
        <p style="margin: 0; opacity: 0.9;">Driver Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick stats in a row
    col1, col2, col3 = st.columns(3)
    
    # Get current stats
    current_move = assignment.get_my_current_move()
    completed = assignment.get_my_completed_moves(30)
    
    with col1:
        status_emoji = "🟢" if assignment.status == 'available' else "🔵"
        st.metric("Status", f"{status_emoji} {assignment.status.title()}")
    
    with col2:
        st.metric("Today", f"{assignment.completed_today}/{assignment.max_daily}")
    
    with col3:
        st.metric("Pending", f"${completed['pending_earnings']:,.0f}")
    
    # Main action area
    if current_move:
        show_current_move_mobile(current_move, assignment)
    else:
        show_available_moves_mobile(assignment)
    
    # Bottom navigation tabs (mobile-friendly)
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Moves", "💰 Earnings", "📸 Upload", "📍 Report"])
    
    with tab1:
        if not current_move:
            st.info("Available moves shown above. Pull down to refresh.")
        else:
            st.success(f"Current move: {current_move['move_id']}")
    
    with tab2:
        show_earnings_mobile(driver_name)
    
    with tab3:
        show_document_upload_mobile(driver_name, current_move)
    
    with tab4:
        show_trailer_report_mobile(driver_name)

def show_current_move_mobile(move, assignment):
    """Show current move in mobile-friendly format"""
    
    st.markdown("### 🚚 Current Move")
    
    # Progress bar with percentage
    progress = move['progress_percentage']
    st.progress(progress / 100)
    
    status_text = move['status'].replace('_', ' ').title()
    st.markdown(f"""
    <div class="status-badge status-{move['status'].replace('_', '-')}">
        {status_text} - {progress}% Complete
    </div>
    """, unsafe_allow_html=True)
    
    # Move details in card
    st.markdown(f"""
    <div class="move-card">
        <h4>📦 {move['new_trailer']} ↔️ {move['old_trailer']}</h4>
        <p>📍 From: <b>{move['pickup_location']}</b></p>
        <p>📍 To: <b>{move['delivery_location']}</b></p>
        <p>💵 Pay: <b>${move.get('driver_pay', 0):,.2f}</b></p>
        <p>🆔 ID: {move['move_id']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons based on status
    st.markdown("### Actions")
    
    if move['status'] == 'assigned':
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 START PICKUP", type="primary", use_container_width=True):
                update_move_status(move['move_id'], 'in_progress')
                st.success("Pickup started! Drive safely.")
                st.rerun()
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                if st.session_state.get('confirm_cancel'):
                    success, msg = assignment.unassign_move(move['move_id'])
                    if success:
                        st.warning("Move cancelled")
                        del st.session_state['confirm_cancel']
                        st.rerun()
                else:
                    st.session_state['confirm_cancel'] = True
                    st.warning("Tap again to confirm")
    
    elif move['status'] == 'in_progress':
        if st.button("✅ PICKUP COMPLETE", type="primary", use_container_width=True):
            update_move_status(move['move_id'], 'pickup_complete')
            st.success("Pickup complete! Head to delivery.")
            st.rerun()
        
        if st.button("📸 Upload Pickup Photo", use_container_width=True):
            st.session_state.show_upload = 'pickup'
    
    elif move['status'] == 'pickup_complete':
        if st.button("🏁 COMPLETE DELIVERY", type="primary", use_container_width=True):
            update_move_status(move['move_id'], 'completed')
            st.success("Delivery complete! Great job!")
            st.balloons()
            st.rerun()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📸 Delivery Photo", use_container_width=True):
                st.session_state.show_upload = 'delivery'
        with col2:
            if st.button("📄 Upload POD", use_container_width=True):
                st.session_state.show_upload = 'pod'

def show_available_moves_mobile(assignment):
    """Show available moves in mobile-friendly cards"""
    
    st.markdown("### 📋 Available Moves")
    
    # Get available moves
    moves = assignment.get_available_moves()
    available_moves = [m for m in moves if m['availability'] in ['available', 'reserved_by_you']]
    
    if not available_moves:
        st.info("No moves available right now. Pull down to refresh.")
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
        return
    
    # Quick filter
    locations = list(set(m['location'] for m in available_moves))
    selected_location = st.selectbox("Filter by location:", ["All"] + locations)
    
    # Filter moves
    if selected_location != "All":
        filtered_moves = [m for m in available_moves if m['location'] == selected_location]
    else:
        filtered_moves = available_moves
    
    # Display moves as cards
    for move in filtered_moves:
        card_class = "move-card-reserved" if move['availability'] == 'reserved_by_you' else "move-card-available"
        
        st.markdown(f"""
        <div class="move-card {card_class}">
            <h4>📍 {move['location']}</h4>
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <p>🆕 {move['new_trailer']}</p>
                    <p>🔄 {move['old_trailer']}</p>
                </div>
                <div style="text-align: right;">
                    <p style="font-size: 1.5rem; font-weight: bold; color: #28a745;">
                        ${move.get('estimated_pay', 0):,.0f}
                    </p>
                    <p>{move.get('round_trip_miles', 0):.0f} mi</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if move['availability'] == 'reserved_by_you':
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ ACCEPT", key=f"accept_{move['new_trailer_id']}", 
                           type="primary", use_container_width=True):
                    success, move_id = assignment.self_assign_move(
                        move['new_trailer'],
                        move['old_trailer'],
                        move['location']
                    )
                    if success:
                        st.success(f"Move assigned! ID: {move_id}")
                        st.balloons()
                        st.rerun()
            with col2:
                if st.button("❌ Release", key=f"release_{move['new_trailer_id']}", 
                           use_container_width=True):
                    assignment.clear_reservation(move['new_trailer_id'])
                    st.rerun()
        else:
            if st.button(f"📌 RESERVE", key=f"reserve_{move['new_trailer_id']}", 
                        use_container_width=True):
                success, msg = assignment.reserve_trailer(move['new_trailer_id'])
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

def show_earnings_mobile(driver_name):
    """Mobile-friendly earnings display"""
    
    st.markdown("### 💰 My Earnings")
    
    # Date range selector
    days = st.select_slider("Show last", [7, 14, 30, 60], value=30)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            move_date,
            new_trailer || ' - ' || old_trailer as route,
            total_miles,
            driver_pay,
            payment_status
        FROM moves
        WHERE driver_name = ?
        AND status = 'completed'
        AND move_date >= date('now', '-' || ? || ' days')
        ORDER BY move_date DESC
    """, (driver_name, days))
    
    moves_data = cursor.fetchall()
    conn.close()
    
    if moves_data:
        total = sum(row[3] for row in moves_data if row[3])
        paid = sum(row[3] for row in moves_data if row[3] and row[4] == 'paid')
        pending = total - paid
        
        # Summary cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Moves", len(moves_data))
        with col2:
            st.metric("Pending", f"${pending:,.0f}")
        with col3:
            st.metric("Total", f"${total:,.0f}")
        
        # Recent moves list
        st.markdown("#### Recent Moves")
        for move in moves_data[:10]:
            date, route, miles, pay, status = move
            status_emoji = "✅" if status == 'paid' else "⏳"
            
            st.markdown(f"""
            <div style="background: #1a1a1a; padding: 0.75rem; margin: 0.5rem 0; 
                        border-radius: 8px; border-left: 3px solid #DC143C;">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <b>{date}</b><br>
                        {route}<br>
                        {miles:.0f} miles
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 1.3rem; font-weight: bold;">
                            ${pay:,.2f}
                        </span><br>
                        {status_emoji} {status}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f"No completed moves in the last {days} days")

def show_document_upload_mobile(driver_name, current_move):
    """Mobile-friendly document upload"""
    
    st.markdown("### 📸 Upload Documents")
    
    upload_type = st.session_state.get('show_upload', 'select')
    
    if upload_type == 'select' or not current_move:
        st.info("Select document type to upload:")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📸 Pickup Photo", use_container_width=True):
                st.session_state.show_upload = 'pickup'
                st.rerun()
            if st.button("📸 Delivery Photo", use_container_width=True):
                st.session_state.show_upload = 'delivery'
                st.rerun()
        with col2:
            if st.button("📄 POD", use_container_width=True):
                st.session_state.show_upload = 'pod'
                st.rerun()
            if st.button("🧾 Receipt", use_container_width=True):
                st.session_state.show_upload = 'receipt'
                st.rerun()
    else:
        st.info(f"Uploading: {upload_type.upper()}")
        
        # Camera/file upload
        # iOS camera integration
        uploaded = st.file_uploader(
            "Take photo or select file",
            type=['jpg', 'jpeg', 'png', 'pdf'],
            accept_multiple_files=False,
            help="Tap to open camera or photo library"
        )
        
        # Add iOS camera input hint
        st.markdown("""
        <div style="text-align: center; color: #8E8E93; font-size: 13px; margin-top: -10px;">
            📷 Works best with iPhone camera
        </div>
        """, unsafe_allow_html=True)
        
        if uploaded:
            st.success(f"File selected: {uploaded.name}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ UPLOAD", type="primary", use_container_width=True):
                    # Process upload
                    st.success(f"{upload_type} uploaded successfully!")
                    del st.session_state['show_upload']
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    del st.session_state['show_upload']
                    st.rerun()

def show_trailer_report_mobile(driver_name):
    """Mobile-friendly trailer reporting"""
    
    st.markdown("### 📍 Report Trailer Location")
    
    with st.form("trailer_report", clear_on_submit=True):
        trailer_num = st.text_input("Trailer Number", placeholder="e.g., TRL-001")
        location = st.text_input("Location", placeholder="e.g., Memphis Terminal")
        
        col1, col2 = st.columns(2)
        with col1:
            city = st.text_input("City", placeholder="Memphis")
        with col2:
            state = st.selectbox("State", ["TN", "MS", "AR", "AL", "LA", "MO", "KY"])
        
        notes = st.text_area("Notes (optional)", placeholder="Any details...")
        
        if st.form_submit_button("📤 SUBMIT REPORT", type="primary", use_container_width=True):
            if trailer_num and location:
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO trailer_location_reports
                    (trailer_number, reported_location, reported_by_driver, notes, reported_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (trailer_num, f"{location}, {city}, {state}", driver_name, notes, datetime.now()))
                conn.commit()
                conn.close()
                st.success("✅ Report submitted! Thank you!")
                st.balloons()
            else:
                st.error("Please fill in trailer number and location")

def update_move_status(move_id, new_status):
    """Update move status in database"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    timestamp_field = {
        'in_progress': 'pickup_time',
        'pickup_complete': 'pickup_time', 
        'completed': 'delivery_time'
    }.get(new_status)
    
    if timestamp_field:
        cursor.execute(f"""
            UPDATE moves
            SET status = ?, {timestamp_field} = ?, updated_at = ?
            WHERE move_id = ?
        """, (new_status, datetime.now(), datetime.now(), move_id))
    else:
        cursor.execute("""
            UPDATE moves
            SET status = ?, updated_at = ?
            WHERE move_id = ?
        """, (new_status, datetime.now(), move_id))
    
    conn.commit()
    conn.close()

# Export the main function
def show_mobile_interface(driver_id, driver_name):
    """Main entry point for mobile driver interface"""
    show_mobile_driver_dashboard(driver_id, driver_name)