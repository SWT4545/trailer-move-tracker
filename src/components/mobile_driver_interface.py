"""
Mobile-optimized driver interface for iPhone/tablet use
Simplified layout and larger touch targets for mobile devices
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
from pathlib import Path

def get_connection():
    return sqlite3.connect('trailer_moves.db')

def mobile_driver_dashboard():
    """Mobile-optimized driver dashboard"""
    
    # Mobile-friendly header
    st.markdown("""
        <style>
        /* Mobile optimizations */
        .stButton > button {
            width: 100%;
            min-height: 50px;
            font-size: 18px;
            margin: 5px 0;
        }
        .stSelectbox > div > div {
            font-size: 18px;
        }
        .stTextInput > div > div > input {
            font-size: 18px;
        }
        .stTextArea > div > div > textarea {
            font-size: 18px;
        }
        div[data-testid="metric-container"] {
            padding: 10px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    driver_name = st.session_state.username
    if driver_name == "brandon" or driver_name == "brandon_driver":
        driver_name = "Brandon Smith"
    
    # Simple mobile header
    st.markdown(f"# 🚛 Driver Portal")
    st.markdown(f"**{driver_name}**")
    
    # Availability toggle - prominent for mobile
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT is_available FROM driver_availability 
        WHERE driver_name = ? ORDER BY last_updated DESC LIMIT 1
    """, (driver_name,))
    
    current_status = cursor.fetchone()
    is_available = current_status[0] if current_status else False
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🟢 AVAILABLE" if not is_available else "✅ AVAILABLE", 
                     type="primary" if is_available else "secondary",
                     disabled=is_available):
            cursor.execute("""
                INSERT OR REPLACE INTO driver_availability 
                (driver_name, is_available, last_updated)
                VALUES (?, 1, CURRENT_TIMESTAMP)
            """, (driver_name,))
            conn.commit()
            st.rerun()
    
    with col2:
        if st.button("🔴 NOT AVAILABLE" if is_available else "⏸️ NOT AVAILABLE",
                     type="primary" if not is_available else "secondary", 
                     disabled=not is_available):
            cursor.execute("""
                INSERT OR REPLACE INTO driver_availability 
                (driver_name, is_available, last_updated)
                VALUES (?, 0, CURRENT_TIMESTAMP)
            """, (driver_name,))
            conn.commit()
            st.rerun()
    
    # Quick stats - mobile friendly
    st.markdown("### 📊 Quick Stats")
    col1, col2, col3 = st.columns(3)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as active
        FROM moves WHERE driver_name = ?
    """, (driver_name,))
    
    stats = cursor.fetchone()
    
    with col1:
        st.metric("Total", stats[0] or 0)
    with col2:
        st.metric("Done", stats[1] or 0)
    with col3:
        st.metric("Active", stats[2] or 0)
    
    conn.close()

def mobile_active_move():
    """Mobile-optimized active move management"""
    st.markdown("# 🚛 Active Move")
    
    driver_name = st.session_state.username
    if driver_name == "brandon" or driver_name == "brandon_driver":
        driver_name = "Brandon Smith"
    
    conn = get_connection()
    
    # Get current active move
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, order_number, customer_name, pickup_location, 
               delivery_location, status, delivery_date
        FROM moves 
        WHERE driver_name = ? AND status = 'in_progress'
        LIMIT 1
    """, (driver_name,))
    
    active_move = cursor.fetchone()
    
    if active_move:
        # Display move info in mobile-friendly format
        st.success(f"**Order #{active_move[1]}**")
        st.info(f"**Customer:** {active_move[2]}")
        st.info(f"**Pickup:** {active_move[3]}")
        st.info(f"**Delivery:** {active_move[4]}")
        st.info(f"**Due:** {active_move[6]}")
        
        st.markdown("---")
        
        # Large mobile-friendly buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📸 Upload Photo", type="primary", use_container_width=True):
                st.session_state.show_photo_upload = True
        
        with col2:
            if st.button("✅ Mark Complete", type="primary", use_container_width=True):
                cursor.execute("""
                    UPDATE moves SET status = 'completed', 
                    completed_date = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (active_move[0],))
                conn.commit()
                st.success("Move completed!")
                st.balloons()
                st.rerun()
        
        # Photo upload section
        if st.session_state.get('show_photo_upload'):
            st.markdown("### 📸 Upload Photo")
            
            photo_type = st.selectbox("Photo Type", [
                "Old Trailer - Pickup",
                "New Trailer - Delivery",
                "POD from Fleet",
                "Damage/Issue"
            ])
            
            uploaded = st.file_uploader("Take/Select Photo", 
                                       type=['jpg', 'jpeg', 'png'],
                                       accept_multiple_files=False)
            
            if uploaded:
                # Save photo
                upload_dir = Path(f"uploads/moves/{active_move[0]}")
                upload_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = upload_dir / f"{timestamp}_{uploaded.name}"
                
                with open(file_path, "wb") as f:
                    f.write(uploaded.getbuffer())
                
                cursor.execute("""
                    INSERT INTO move_documents 
                    (move_id, driver_name, document_type, file_name, file_path)
                    VALUES (?, ?, ?, ?, ?)
                """, (active_move[0], driver_name, photo_type, 
                      uploaded.name, str(file_path)))
                conn.commit()
                
                st.success(f"✅ {photo_type} uploaded!")
                st.session_state.show_photo_upload = False
                st.rerun()
    else:
        st.info("No active move. Check available moves to start.")
        
        # Show assigned moves
        df = pd.read_sql_query("""
            SELECT order_number, customer_name, pickup_location,
                   delivery_location, delivery_date, id
            FROM moves 
            WHERE driver_name = ? AND status = 'assigned'
            ORDER BY delivery_date
        """, conn, params=[driver_name])
        
        if not df.empty:
            st.markdown("### 📋 Assigned Moves")
            
            for idx, row in df.iterrows():
                with st.expander(f"#{row['order_number']} - {row['customer_name']}"):
                    st.write(f"**Pickup:** {row['pickup_location']}")
                    st.write(f"**Delivery:** {row['delivery_location']}")
                    st.write(f"**Date:** {row['delivery_date']}")
                    
                    if st.button(f"▶️ Start This Move", 
                                key=f"start_{row['id']}",
                                type="primary",
                                use_container_width=True):
                        cursor.execute("""
                            UPDATE moves SET status = 'in_progress',
                            started_date = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (row['id'],))
                        conn.commit()
                        st.success("Move started!")
                        st.rerun()
    
    conn.close()

def mobile_self_assign():
    """Mobile-optimized self-assignment"""
    st.markdown("# 📋 Self-Assign")
    
    driver_name = st.session_state.username
    if driver_name == "brandon" or driver_name == "brandon_driver":
        driver_name = "Brandon Smith"
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check availability
    cursor.execute("""
        SELECT is_available FROM driver_availability 
        WHERE driver_name = ? ORDER BY last_updated DESC LIMIT 1
    """, (driver_name,))
    
    available = cursor.fetchone()
    if not available or not available[0]:
        st.warning("⚠️ Set yourself as AVAILABLE first!")
        if st.button("🟢 Set as Available", type="primary", use_container_width=True):
            cursor.execute("""
                INSERT OR REPLACE INTO driver_availability 
                (driver_name, is_available, last_updated)
                VALUES (?, 1, CURRENT_TIMESTAMP)
            """, (driver_name,))
            conn.commit()
            st.rerun()
        conn.close()
        return
    
    # Get available trailers
    cursor.execute("""
        SELECT id, trailer_number, current_location, customer_name
        FROM trailers 
        WHERE status IN ('ready_to_move', 'pending_pickup')
        ORDER BY trailer_number
    """)
    
    trailers = cursor.fetchall()
    
    if trailers:
        st.markdown("### Available Trailers")
        
        # Simple selection
        trailer_options = [f"{t[1]} - {t[2]} ({t[3]})" for t in trailers]
        selected = st.selectbox("Select Trailer", ["None"] + trailer_options)
        
        if selected != "None":
            # Parse selection
            trailer_num = selected.split(" - ")[0]
            trailer_id = None
            location = ""
            
            for t in trailers:
                if t[1] == trailer_num:
                    trailer_id = t[0]
                    location = t[2]
                    break
            
            if st.button("✅ ASSIGN TO ME", type="primary", use_container_width=True):
                # Create assignment
                cursor.execute("""
                    INSERT INTO self_assigned_moves 
                    (driver_name, old_trailer_id, pickup_location, status)
                    VALUES (?, ?, ?, 'assigned')
                """, (driver_name, trailer_id, location))
                
                # Update trailer
                cursor.execute("""
                    UPDATE trailers SET status = 'assigned', 
                    assigned_driver = ? WHERE id = ?
                """, (driver_name, trailer_id))
                
                # Create move
                order_num = f"SA-{datetime.now().strftime('%Y%m%d%H%M')}"
                cursor.execute("""
                    INSERT INTO moves 
                    (order_number, customer_name, pickup_location,
                     delivery_location, driver_name, status, created_by)
                    VALUES (?, 'Self-Assigned', ?, 'TBD', ?, 'assigned', ?)
                """, (order_num, location, driver_name, driver_name))
                
                conn.commit()
                st.success("✅ Trailer assigned to you!")
                st.balloons()
    else:
        st.info("No trailers available right now. Check back later.")
    
    conn.close()

def mobile_quick_message():
    """Mobile-optimized messaging"""
    st.markdown("# 💬 Quick Message")
    
    driver_name = st.session_state.username
    if driver_name == "brandon" or driver_name == "brandon_driver":
        driver_name = "Brandon Smith"
    
    with st.form("quick_message"):
        message = st.text_area("Message to Dispatch", 
                              placeholder="Type your message...",
                              height=100)
        
        priority = st.radio("Priority", ["Normal", "Urgent"], horizontal=True)
        
        if st.form_submit_button("📤 SEND", type="primary", use_container_width=True):
            if message:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO driver_messages 
                    (driver_name, message, priority, sender, message_type)
                    VALUES (?, ?, ?, ?, 'to_management')
                """, (driver_name, message, priority.lower(), driver_name))
                conn.commit()
                conn.close()
                st.success("✅ Message sent!")
            else:
                st.error("Please enter a message")

def show_mobile_driver_interface():
    """Main mobile driver interface with navigation"""
    
    # Check if owner is acting as driver
    is_owner_driver = (st.session_state.username == "brandon" and 
                      st.session_state.get('driver_mode', False))
    
    if is_owner_driver:
        st.markdown("### 🚛 Driver Mode (Owner)")
    
    # Mobile navigation - large buttons
    st.markdown("## Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.mobile_page = "dashboard"
        
        if st.button("🚛 Active Move", use_container_width=True):
            st.session_state.mobile_page = "active_move"
    
    with col2:
        if st.button("📋 Self-Assign", use_container_width=True):
            st.session_state.mobile_page = "self_assign"
        
        if st.button("💬 Message", use_container_width=True):
            st.session_state.mobile_page = "message"
    
    st.markdown("---")
    
    # Display selected page
    page = st.session_state.get('mobile_page', 'dashboard')
    
    if page == "dashboard":
        mobile_driver_dashboard()
    elif page == "active_move":
        mobile_active_move()
    elif page == "self_assign":
        mobile_self_assign()
    elif page == "message":
        mobile_quick_message()