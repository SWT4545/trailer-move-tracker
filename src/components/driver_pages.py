"""
Driver Pages Module - Complete functionality for driver role
Handles all driver-specific pages and operations
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import os
from pathlib import Path

def get_connection():
    """Create database connection"""
    return sqlite3.connect('trailer_moves.db')

def init_driver_tables():
    """Initialize all driver-related database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Driver profiles table - Updated with contractor company info
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS driver_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        full_name TEXT,
        phone TEXT,
        email TEXT,
        cdl_number TEXT,
        cdl_state TEXT,
        cdl_class TEXT,
        years_experience INTEGER,
        address TEXT,
        birth_date DATE,
        driver_type TEXT DEFAULT 'contractor',
        company_name TEXT,
        company_address TEXT,
        company_phone TEXT,
        company_email TEXT,
        mc_number TEXT,
        dot_number TEXT,
        insurance_company TEXT,
        insurance_policy_number TEXT,
        w9_on_file BOOLEAN DEFAULT 0,
        emergency_contact_name TEXT,
        emergency_contact_phone TEXT,
        emergency_contact_relationship TEXT,
        bank_name TEXT,
        routing_number TEXT,
        account_number TEXT,
        account_type TEXT,
        payment_method TEXT DEFAULT 'navy_federal_transfer',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Driver availability table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS driver_availability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER,
        driver_name TEXT,
        is_available BOOLEAN DEFAULT 1,
        available_from DATE,
        available_to DATE,
        availability_notes TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Driver schedule table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS driver_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER,
        driver_name TEXT,
        scheduled_date DATE,
        scheduled_time TEXT,
        schedule_type TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Driver messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS driver_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER,
        driver_name TEXT,
        message TEXT,
        message_type TEXT,
        priority TEXT DEFAULT 'normal',
        is_read BOOLEAN DEFAULT 0,
        sender TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Move documents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS move_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        move_id INTEGER,
        driver_id INTEGER,
        driver_name TEXT,
        document_type TEXT,
        file_name TEXT,
        file_path TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    )
    ''')
    
    # Driver documents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS driver_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER,
        driver_name TEXT,
        document_type TEXT,
        file_name TEXT,
        file_path TEXT,
        expiry_date DATE,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    )
    ''')
    
    # Self-assigned moves table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS self_assigned_moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER,
        driver_name TEXT,
        old_trailer_id INTEGER,
        new_trailer_id INTEGER,
        pickup_location TEXT,
        delivery_location TEXT,
        assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'assigned',
        completed_date TIMESTAMP,
        notes TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

def show_driver_dashboard():
    """Display driver dashboard with availability and messaging"""
    st.header("🏠 Driver Dashboard")
    
    # Initialize tables if needed
    init_driver_tables()
    
    driver_name = st.session_state.username
    driver_id = st.session_state.get('user_id', 1)
    
    # Top row - Availability and Status
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📍 Availability Status")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get current availability
        cursor.execute("""
            SELECT is_available, available_from, available_to, availability_notes 
            FROM driver_availability 
            WHERE driver_name = ? 
            ORDER BY last_updated DESC 
            LIMIT 1
        """, (driver_name,))
        
        availability = cursor.fetchone()
        current_status = availability[0] if availability else False
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            is_available = st.toggle("🟢 Available for Work", value=current_status, key="availability_toggle")
            
            if is_available != current_status:
                cursor.execute("""
                    INSERT OR REPLACE INTO driver_availability 
                    (driver_id, driver_name, is_available, last_updated)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (driver_id, driver_name, is_available))
                conn.commit()
                st.success("✅ Availability updated!")
        
        with col_b:
            if is_available:
                st.success("✅ You are AVAILABLE for assignments")
            else:
                st.warning("⏸️ You are NOT available for assignments")
        
        # Schedule availability
        st.markdown("#### 📅 Schedule Future Availability")
        
        with st.expander("Set Future Availability"):
            col_1, col_2 = st.columns(2)
            
            with col_1:
                available_from = st.date_input("Available From", value=date.today())
                schedule_time = st.time_input("Start Time")
            
            with col_2:
                available_to = st.date_input("Available To", value=date.today() + timedelta(days=7))
                schedule_notes = st.text_area("Notes (optional)", height=60)
            
            if st.button("📅 Schedule Availability", type="primary"):
                cursor.execute("""
                    INSERT INTO driver_schedule 
                    (driver_id, driver_name, scheduled_date, scheduled_time, schedule_type, notes)
                    VALUES (?, ?, ?, ?, 'availability', ?)
                """, (driver_id, driver_name, available_from, str(schedule_time), schedule_notes))
                
                cursor.execute("""
                    UPDATE driver_availability 
                    SET available_from = ?, available_to = ?, availability_notes = ?
                    WHERE driver_name = ?
                """, (available_from, available_to, schedule_notes, driver_name))
                
                conn.commit()
                st.success("✅ Future availability scheduled!")
        
        conn.close()
    
    with col2:
        st.markdown("### 📊 Quick Stats")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get driver stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_moves,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as active
            FROM moves 
            WHERE driver_name = ? OR driver_name = ?
        """, (driver_name, driver_name.replace('driver', 'Driver')))
        
        stats = cursor.fetchone()
        
        if stats:
            st.metric("Total Moves", stats[0] or 0)
            st.metric("Completed", stats[1] or 0)
            st.metric("Active", stats[2] or 0)
        
        conn.close()
    
    # Messages section
    st.markdown("---")
    st.markdown("### 💬 Messages & Announcements")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Display messages
    cursor.execute("""
        SELECT message, message_type, priority, sender, created_at 
        FROM driver_messages 
        WHERE driver_name = ? AND is_read = 0
        ORDER BY created_at DESC 
        LIMIT 5
    """, (driver_name,))
    
    messages = cursor.fetchall()
    
    if messages:
        for msg in messages:
            if msg[2] == 'urgent':
                st.error(f"🚨 **URGENT from {msg[3]}**: {msg[0]}")
            elif msg[1] == 'assignment':
                st.info(f"📋 **New Assignment**: {msg[0]}")
            else:
                st.info(f"💬 **{msg[3]}**: {msg[0]}")
        
        if st.button("✓ Mark All as Read"):
            cursor.execute("""
                UPDATE driver_messages 
                SET is_read = 1 
                WHERE driver_name = ?
            """, (driver_name,))
            conn.commit()
            st.rerun()
    else:
        st.info("No new messages")
    
    # Send message to management
    st.markdown("#### 📤 Send Message to Management")
    
    with st.form("send_message"):
        message = st.text_area("Your Message", placeholder="Let management know about schedule changes, issues, etc.")
        priority = st.selectbox("Priority", ["Normal", "Important", "Urgent"])
        
        if st.form_submit_button("Send Message", type="primary"):
            if message:
                cursor.execute("""
                    INSERT INTO driver_messages 
                    (driver_id, driver_name, message, message_type, priority, sender)
                    VALUES (?, ?, ?, 'to_management', ?, ?)
                """, (driver_id, driver_name, message, priority.lower(), driver_name))
                conn.commit()
                st.success("✅ Message sent to management!")
            else:
                st.error("Please enter a message")
    
    conn.close()
    
    # Active moves summary
    st.markdown("---")
    st.markdown("### 🚛 Active Moves Summary")
    
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT 
            order_number as 'Order #',
            customer_name as 'Customer',
            pickup_location as 'Pickup',
            delivery_location as 'Delivery',
            delivery_date as 'Date',
            status as 'Status'
        FROM moves 
        WHERE (driver_name = ? OR driver_name = ?)
        AND status IN ('assigned', 'in_progress')
        ORDER BY delivery_date ASC
        LIMIT 5
    """, conn, params=[driver_name, driver_name.replace('driver', 'Driver')])
    
    conn.close()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No active moves. Check Self-Assign to pick up available trailers!")

def show_self_assign_page():
    """Self-assignment page for drivers to pick trailers"""
    st.header("📋 Self-Assign Trailers")
    
    driver_name = st.session_state.username
    driver_id = st.session_state.get('user_id', 1)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if driver is available
    cursor.execute("""
        SELECT is_available 
        FROM driver_availability 
        WHERE driver_name = ? 
        ORDER BY last_updated DESC 
        LIMIT 1
    """, (driver_name,))
    
    availability = cursor.fetchone()
    is_available = availability[0] if availability else False
    
    if not is_available:
        st.warning("⚠️ You must be marked as available to self-assign trailers. Please update your availability in the Dashboard.")
        conn.close()
        return
    
    st.success("✅ You are available for assignments")
    
    # Get available trailers marked as ready to move
    cursor.execute("""
        SELECT 
            id,
            trailer_number,
            current_location,
            destination,
            customer_name,
            notes,
            status
        FROM trailers 
        WHERE status IN ('ready_to_move', 'pending_pickup')
        AND id NOT IN (
            SELECT old_trailer_id FROM self_assigned_moves WHERE status = 'assigned'
            UNION
            SELECT new_trailer_id FROM self_assigned_moves WHERE status = 'assigned'
        )
        ORDER BY trailer_number
    """)
    
    available_trailers = cursor.fetchall()
    
    if available_trailers:
        st.markdown("### 🚛 Available Trailers for Pickup")
        
        # Create selection interface
        with st.form("self_assign_form"):
            st.markdown("#### Select Old Trailer (Pickup)")
            
            old_trailer_options = ["None - No old trailer"] + [
                f"{t[1]} - {t[2]} ({t[4]})" 
                for t in available_trailers
            ]
            
            old_trailer_selection = st.selectbox(
                "Old Trailer to Pick Up",
                old_trailer_options,
                help="Select the old trailer you will pick up from the customer"
            )
            
            st.markdown("#### Select New Trailer (Delivery)")
            
            new_trailer_options = ["None - No new trailer"] + [
                f"{t[1]} - Currently at {t[2]} → {t[3]} ({t[4]})" 
                for t in available_trailers
            ]
            
            new_trailer_selection = st.selectbox(
                "New Trailer to Deliver",
                new_trailer_options,
                help="Select the new trailer you will deliver to the customer"
            )
            
            # Additional details
            col1, col2 = st.columns(2)
            
            with col1:
                pickup_date = st.date_input("Planned Pickup Date", value=date.today())
                pickup_time = st.time_input("Pickup Time")
            
            with col2:
                delivery_date = st.date_input("Planned Delivery Date", value=date.today() + timedelta(days=1))
                delivery_time = st.time_input("Delivery Time")
            
            notes = st.text_area("Notes (optional)", placeholder="Any special instructions or notes")
            
            submitted = st.form_submit_button("✅ Assign to Me", type="primary", use_container_width=True)
            
            if submitted:
                if old_trailer_selection == "None - No old trailer" and new_trailer_selection == "None - No new trailer":
                    st.error("Please select at least one trailer")
                else:
                    # Parse selections
                    old_trailer_id = None
                    new_trailer_id = None
                    pickup_location = ""
                    delivery_location = ""
                    
                    if old_trailer_selection != "None - No old trailer":
                        old_trailer_num = old_trailer_selection.split(" - ")[0]
                        for t in available_trailers:
                            if t[1] == old_trailer_num:
                                old_trailer_id = t[0]
                                pickup_location = t[2]
                                break
                    
                    if new_trailer_selection != "None - No new trailer":
                        new_trailer_num = new_trailer_selection.split(" - ")[0]
                        for t in available_trailers:
                            if t[1] == new_trailer_num:
                                new_trailer_id = t[0]
                                delivery_location = t[3] if t[3] else t[2]
                                break
                    
                    # Create self-assigned move
                    cursor.execute("""
                        INSERT INTO self_assigned_moves 
                        (driver_id, driver_name, old_trailer_id, new_trailer_id, 
                         pickup_location, delivery_location, status, notes)
                        VALUES (?, ?, ?, ?, ?, ?, 'assigned', ?)
                    """, (driver_id, driver_name, old_trailer_id, new_trailer_id,
                          pickup_location, delivery_location, notes))
                    
                    # Update trailer status
                    if old_trailer_id:
                        cursor.execute("""
                            UPDATE trailers 
                            SET status = 'assigned', assigned_driver = ?
                            WHERE id = ?
                        """, (driver_name, old_trailer_id))
                    
                    if new_trailer_id:
                        cursor.execute("""
                            UPDATE trailers 
                            SET status = 'assigned', assigned_driver = ?
                            WHERE id = ?
                        """, (driver_name, new_trailer_id))
                    
                    # Create a move record
                    cursor.execute("""
                        INSERT INTO moves 
                        (order_number, customer_name, pickup_location, delivery_location,
                         pickup_date, delivery_date, driver_name, status, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'assigned', ?)
                    """, (f"SA-{datetime.now().strftime('%Y%m%d%H%M')}", 
                          "Self-Assigned", pickup_location, delivery_location,
                          pickup_date, delivery_date, driver_name, driver_name))
                    
                    conn.commit()
                    st.success("✅ Trailers successfully assigned to you! Check 'My Moves' to manage this assignment.")
                    st.balloons()
    else:
        st.info("No trailers are currently available for self-assignment. Check back later or contact dispatch.")
    
    # Show current assignments
    st.markdown("---")
    st.markdown("### 📋 Your Current Self-Assignments")
    
    df = pd.read_sql_query("""
        SELECT 
            id,
            COALESCE((SELECT trailer_number FROM trailers WHERE id = old_trailer_id), 'N/A') as 'Old Trailer',
            COALESCE((SELECT trailer_number FROM trailers WHERE id = new_trailer_id), 'N/A') as 'New Trailer',
            pickup_location as 'Pickup Location',
            delivery_location as 'Delivery Location',
            assigned_date as 'Assigned Date',
            status as 'Status'
        FROM self_assigned_moves
        WHERE driver_name = ? AND status != 'completed'
        ORDER BY assigned_date DESC
    """, conn, params=[driver_name])
    
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No current self-assignments")
    
    conn.close()

def show_my_moves_page():
    """Active moves management page"""
    st.header("🚛 My Active Moves")
    
    driver_name = st.session_state.username
    
    conn = get_connection()
    
    # Get active moves
    df = pd.read_sql_query("""
        SELECT 
            id,
            order_number,
            customer_name,
            pickup_location,
            delivery_location,
            pickup_date,
            delivery_date,
            status,
            amount,
            notes
        FROM moves 
        WHERE (driver_name = ? OR driver_name = ?)
        AND status IN ('assigned', 'in_progress', 'ready_for_pickup')
        ORDER BY 
            CASE status 
                WHEN 'in_progress' THEN 1 
                WHEN 'ready_for_pickup' THEN 2
                WHEN 'assigned' THEN 3 
            END,
            delivery_date ASC
    """, conn, params=[driver_name, driver_name.replace('driver', 'Driver')])
    
    if not df.empty:
        # Show current active move
        st.markdown("### 🔴 Current Active Move")
        
        active_moves = df[df['status'] == 'in_progress']
        if not active_moves.empty:
            current_move = active_moves.iloc[0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info(f"**Order #:** {current_move['order_number']}")
                st.info(f"**Customer:** {current_move['customer_name']}")
            
            with col2:
                st.info(f"**Pickup:** {current_move['pickup_location']}")
                st.info(f"**Delivery:** {current_move['delivery_location']}")
            
            with col3:
                st.info(f"**Delivery Date:** {current_move['delivery_date']}")
                st.info(f"**Status:** {current_move['status'].upper()}")
            
            # Move actions
            st.markdown("#### 📍 Update Move Status")
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                if st.button("📸 Upload Documents", type="primary", use_container_width=True):
                    st.session_state.upload_move_id = current_move['id']
                    st.session_state.show_upload = True
            
            with col_b:
                if st.button("✅ Mark as Delivered", type="primary", use_container_width=True):
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE moves 
                        SET status = 'completed', completed_date = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (current_move['id'],))
                    conn.commit()
                    st.success("✅ Move marked as completed!")
                    st.rerun()
            
            with col_c:
                if st.button("❌ Report Issue", use_container_width=True):
                    st.session_state.report_issue = True
            
            # Document upload section
            if st.session_state.get('show_upload', False):
                st.markdown("---")
                st.markdown("#### 📸 Upload Move Documents")
                
                with st.form("upload_docs"):
                    doc_type = st.selectbox("Document Type", [
                        "Old Trailer Photo - Pickup",
                        "New Trailer Photo - Delivery",
                        "POD (Proof of Delivery)",
                        "Fleet Receipt",
                        "Other"
                    ])
                    
                    uploaded_file = st.file_uploader(
                        "Select Photo/Document",
                        type=['jpg', 'jpeg', 'png', 'pdf'],
                        key="move_doc_upload"
                    )
                    
                    notes = st.text_area("Notes (optional)")
                    
                    if st.form_submit_button("Upload Document", type="primary"):
                        if uploaded_file:
                            # Create upload directory
                            upload_dir = Path(f"uploads/moves/{current_move['id']}")
                            upload_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Save file
                            file_path = upload_dir / uploaded_file.name
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            # Save to database
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO move_documents 
                                (move_id, driver_id, driver_name, document_type, 
                                 file_name, file_path, notes)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (current_move['id'], st.session_state.get('user_id', 1),
                                  driver_name, doc_type, uploaded_file.name, 
                                  str(file_path), notes))
                            conn.commit()
                            
                            st.success(f"✅ {doc_type} uploaded successfully!")
                            st.session_state.show_upload = False
                            st.rerun()
                        else:
                            st.error("Please select a file to upload")
        else:
            st.info("No move currently in progress")
        
        # Assigned moves ready to start
        st.markdown("---")
        st.markdown("### 📋 Assigned Moves")
        
        assigned_moves = df[df['status'].isin(['assigned', 'ready_for_pickup'])]
        
        if not assigned_moves.empty:
            for idx, move in assigned_moves.iterrows():
                with st.expander(f"Order #{move['order_number']} - {move['customer_name']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Pickup:** {move['pickup_location']}")
                        st.write(f"**Delivery:** {move['delivery_location']}")
                        st.write(f"**Pickup Date:** {move['pickup_date']}")
                        st.write(f"**Delivery Date:** {move['delivery_date']}")
                    
                    with col2:
                        st.write(f"**Status:** {move['status']}")
                        st.write(f"**Amount:** ${move['amount']:,.2f}" if move['amount'] else "**Amount:** TBD")
                        if move['notes']:
                            st.write(f"**Notes:** {move['notes']}")
                    
                    if st.button(f"▶️ Start This Move", key=f"start_{move['id']}", type="primary"):
                        cursor = conn.cursor()
                        
                        # Update current in_progress moves to assigned
                        cursor.execute("""
                            UPDATE moves 
                            SET status = 'assigned'
                            WHERE driver_name = ? AND status = 'in_progress'
                        """, (driver_name,))
                        
                        # Set this move to in_progress
                        cursor.execute("""
                            UPDATE moves 
                            SET status = 'in_progress', started_date = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (move['id'],))
                        
                        conn.commit()
                        st.success("✅ Move started! This is now your active move.")
                        st.rerun()
    else:
        st.info("No active moves. Check 'Self-Assign' to pick up available trailers!")
    
    # Move history
    st.markdown("---")
    st.markdown("### 📜 Recent Completed Moves")
    
    history_df = pd.read_sql_query("""
        SELECT 
            order_number as 'Order #',
            customer_name as 'Customer',
            delivery_location as 'Delivered To',
            completed_date as 'Completed',
            amount as 'Amount',
            status as 'Status'
        FROM moves 
        WHERE (driver_name = ? OR driver_name = ?)
        AND status = 'completed'
        ORDER BY completed_date DESC
        LIMIT 10
    """, conn, params=[driver_name, driver_name.replace('driver', 'Driver')])
    
    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True, hide_index=True)
    else:
        st.info("No completed moves yet")
    
    conn.close()

def show_documents_page():
    """Documents page for move-related uploads"""
    st.header("📄 Move Documents")
    
    driver_name = st.session_state.username
    driver_id = st.session_state.get('user_id', 1)
    
    tabs = st.tabs(["📸 Upload Move Photos", "📂 View Documents", "📋 Active Move Docs"])
    
    with tabs[0]:
        st.markdown("### Upload Move Documentation")
        
        conn = get_connection()
        
        # Get active moves for this driver
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, order_number, customer_name, status
            FROM moves 
            WHERE (driver_name = ? OR driver_name = ?)
            AND status IN ('assigned', 'in_progress')
            ORDER BY delivery_date ASC
        """, (driver_name, driver_name.replace('driver', 'Driver')))
        
        active_moves = cursor.fetchall()
        
        if active_moves:
            move_options = [f"{m[1]} - {m[2]} ({m[3]})" for m in active_moves]
            selected_move = st.selectbox("Select Move", move_options)
            move_id = active_moves[move_options.index(selected_move)][0]
            
            st.info("""
            📸 **Required Photos for Each Move:**
            - Old Trailer at Pickup
            - New Trailer at Delivery  
            - POD (Proof of Delivery) from Fleet
            - Any damage or issues
            """)
            
            with st.form("move_doc_upload"):
                doc_type = st.selectbox("Document Type", [
                    "Old Trailer - Before Pickup",
                    "Old Trailer - After Pickup",
                    "New Trailer - Before Delivery",
                    "New Trailer - After Delivery",
                    "POD from Fleet",
                    "Damage Report",
                    "Other"
                ])
                
                uploaded_file = st.file_uploader(
                    "Select Photo/Document",
                    type=['jpg', 'jpeg', 'png', 'pdf']
                )
                
                notes = st.text_area("Description/Notes", 
                    placeholder="Describe what's shown in the photo, any issues, etc.")
                
                if st.form_submit_button("📤 Upload Document", type="primary", use_container_width=True):
                    if uploaded_file:
                        # Create upload directory
                        upload_dir = Path(f"uploads/moves/{move_id}")
                        upload_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Save file with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        file_name = f"{timestamp}_{uploaded_file.name}"
                        file_path = upload_dir / file_name
                        
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Save to database
                        cursor.execute("""
                            INSERT INTO move_documents 
                            (move_id, driver_id, driver_name, document_type, 
                             file_name, file_path, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (move_id, driver_id, driver_name, doc_type, 
                              file_name, str(file_path), notes))
                        conn.commit()
                        
                        st.success(f"✅ {doc_type} uploaded successfully!")
                        st.balloons()
                    else:
                        st.error("Please select a file to upload")
        else:
            st.info("No active moves. Documents can be uploaded when you have an assigned move.")
        
        conn.close()
    
    with tabs[1]:
        st.markdown("### Your Uploaded Documents")
        
        conn = get_connection()
        
        # Get all documents uploaded by this driver
        df = pd.read_sql_query("""
            SELECT 
                md.document_type as 'Document Type',
                m.order_number as 'Move Order',
                m.customer_name as 'Customer',
                md.uploaded_at as 'Uploaded',
                md.notes as 'Notes'
            FROM move_documents md
            JOIN moves m ON md.move_id = m.id
            WHERE md.driver_name = ?
            ORDER BY md.uploaded_at DESC
            LIMIT 50
        """, conn, params=[driver_name])
        
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No documents uploaded yet")
        
        conn.close()
    
    with tabs[2]:
        st.markdown("### Active Move Documentation Status")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get active move
        cursor.execute("""
            SELECT id, order_number, customer_name
            FROM moves 
            WHERE (driver_name = ? OR driver_name = ?)
            AND status = 'in_progress'
            LIMIT 1
        """, (driver_name, driver_name.replace('driver', 'Driver')))
        
        active_move = cursor.fetchone()
        
        if active_move:
            st.info(f"📋 **Active Move:** {active_move[1]} - {active_move[2]}")
            
            # Check which documents have been uploaded
            cursor.execute("""
                SELECT document_type, COUNT(*) as count
                FROM move_documents
                WHERE move_id = ?
                GROUP BY document_type
            """, (active_move[0],))
            
            uploaded_docs = {row[0]: row[1] for row in cursor.fetchall()}
            
            required_docs = [
                "Old Trailer - Before Pickup",
                "Old Trailer - After Pickup", 
                "New Trailer - Before Delivery",
                "New Trailer - After Delivery",
                "POD from Fleet"
            ]
            
            st.markdown("#### 📑 Documentation Checklist")
            
            for doc in required_docs:
                if doc in uploaded_docs:
                    st.success(f"✅ {doc} - Uploaded ({uploaded_docs[doc]} file(s))")
                else:
                    st.warning(f"⏳ {doc} - Not uploaded yet")
            
            # Additional uploaded docs
            for doc_type, count in uploaded_docs.items():
                if doc_type not in required_docs:
                    st.info(f"📎 {doc_type} - {count} file(s)")
        else:
            st.info("No active move. Start a move from 'My Moves' page.")
        
        conn.close()

def show_profile_page():
    """Driver profile management page"""
    st.header("👤 Driver Profile")
    
    driver_name = st.session_state.username
    driver_id = st.session_state.get('user_id', 1)
    
    # Initialize profile if needed
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM driver_profiles WHERE user_id = ?
    """, (driver_id,))
    
    profile = cursor.fetchone()
    
    tabs = st.tabs([
        "📝 Personal Info",
        "🏢 Company Info", 
        "🚨 Emergency Contact", 
        "💳 Payment Info",
        "📄 Documents",
        "🎓 Certifications"
    ])
    
    with tabs[0]:
        st.markdown("### Personal Information")
        st.info("🚛 **Driver Type:** Independent Contractor")
        
        with st.form("personal_info"):
            col1, col2 = st.columns(2)
            
            with col1:
                full_name = st.text_input("Full Name", 
                    value=profile[2] if profile else driver_name)
                phone = st.text_input("Personal Phone", 
                    value=profile[3] if profile else "",
                    placeholder="(555) 123-4567")
                email = st.text_input("Personal Email", 
                    value=profile[4] if profile else "",
                    placeholder="driver@example.com")
                birth_date = st.date_input("Date of Birth",
                    value=pd.to_datetime(profile[10]) if profile and profile[10] else date.today() - timedelta(days=365*25))
            
            with col2:
                cdl_number = st.text_input("CDL Number",
                    value=profile[5] if profile else "")
                cdl_state = st.selectbox("CDL State",
                    ["TN", "MS", "AR", "AL", "GA", "KY", "MO", "LA", "TX", "FL", "Other"],
                    index=["TN", "MS", "AR", "AL", "GA", "KY", "MO", "LA", "TX", "FL", "Other"].index(profile[6]) if profile and profile[6] else 0)
                cdl_class = st.selectbox("CDL Class",
                    ["Class A", "Class B"],
                    index=["Class A", "Class B"].index(profile[7]) if profile and profile[7] else 0)
                years_exp = st.number_input("Years of Experience",
                    min_value=0, max_value=50,
                    value=profile[8] if profile and profile[8] else 0)
            
            address = st.text_area("Home Address",
                value=profile[9] if profile else "")
            
            if st.form_submit_button("💾 Update Personal Info", type="primary"):
                if profile:
                    cursor.execute("""
                        UPDATE driver_profiles 
                        SET full_name=?, phone=?, email=?, cdl_number=?, 
                            cdl_state=?, cdl_class=?, years_experience=?, 
                            address=?, birth_date=?, updated_at=CURRENT_TIMESTAMP
                        WHERE user_id=?
                    """, (full_name, phone, email, cdl_number, cdl_state, 
                          cdl_class, years_exp, address, birth_date, driver_id))
                else:
                    cursor.execute("""
                        INSERT INTO driver_profiles 
                        (user_id, full_name, phone, email, cdl_number, cdl_state,
                         cdl_class, years_experience, address, birth_date, driver_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'contractor')
                    """, (driver_id, full_name, phone, email, cdl_number, 
                          cdl_state, cdl_class, years_exp, address, birth_date))
                
                conn.commit()
                st.success("✅ Personal information updated!")
                st.rerun()
    
    with tabs[1]:
        st.markdown("### Contractor Company Information")
        st.info("📋 Required information for Independent Contractors")
        
        with st.form("company_info"):
            st.markdown("#### Company Details")
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input("Company Name",
                    value=profile[12] if profile and len(profile) > 12 else "",
                    placeholder="Your trucking company name")
                company_phone = st.text_input("Company Phone",
                    value=profile[14] if profile and len(profile) > 14 else "",
                    placeholder="(555) 123-4567")
                company_email = st.text_input("Company Email",
                    value=profile[15] if profile and len(profile) > 15 else "",
                    placeholder="company@example.com")
            
            with col2:
                mc_number = st.text_input("MC Number",
                    value=profile[16] if profile and len(profile) > 16 else "",
                    placeholder="MC-123456")
                dot_number = st.text_input("DOT Number",
                    value=profile[17] if profile and len(profile) > 17 else "",
                    placeholder="1234567")
                w9_on_file = st.checkbox("W9 Form on File",
                    value=profile[20] if profile and len(profile) > 20 else False)
            
            company_address = st.text_area("Company Address",
                value=profile[13] if profile and len(profile) > 13 else "",
                placeholder="Company street address, city, state, zip")
            
            st.markdown("#### Insurance Information")
            col3, col4 = st.columns(2)
            
            with col3:
                insurance_company = st.text_input("Insurance Company Name",
                    value=profile[18] if profile and len(profile) > 18 else "",
                    placeholder="Insurance provider name")
            
            with col4:
                insurance_policy = st.text_input("Insurance Policy Number",
                    value=profile[19] if profile and len(profile) > 19 else "",
                    placeholder="Policy #12345678")
            
            st.info("📄 Certificate of Insurance (COI) should be uploaded in the Documents tab")
            
            if st.form_submit_button("💾 Update Company Info", type="primary"):
                if profile:
                    cursor.execute("""
                        UPDATE driver_profiles 
                        SET company_name=?, company_address=?, company_phone=?, 
                            company_email=?, mc_number=?, dot_number=?, 
                            insurance_company=?, insurance_policy_number=?, 
                            w9_on_file=?, updated_at=CURRENT_TIMESTAMP
                        WHERE user_id=?
                    """, (company_name, company_address, company_phone, company_email,
                          mc_number, dot_number, insurance_company, insurance_policy,
                          w9_on_file, driver_id))
                else:
                    cursor.execute("""
                        INSERT INTO driver_profiles 
                        (user_id, company_name, company_address, company_phone,
                         company_email, mc_number, dot_number, insurance_company,
                         insurance_policy_number, w9_on_file, driver_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'contractor')
                    """, (driver_id, company_name, company_address, company_phone,
                          company_email, mc_number, dot_number, insurance_company,
                          insurance_policy, w9_on_file))
                
                conn.commit()
                st.success("✅ Company information updated!")
                st.rerun()
    
    with tabs[2]:
        st.markdown("### Emergency Contact Information")
        
        with st.form("emergency_contact"):
            col1, col2 = st.columns(2)
            
            with col1:
                emergency_name = st.text_input("Contact Name",
                    value=profile[21] if profile and len(profile) > 21 else "")
                emergency_relationship = st.selectbox("Relationship",
                    ["Spouse", "Parent", "Child", "Sibling", "Friend", "Other"],
                    index=["Spouse", "Parent", "Child", "Sibling", "Friend", "Other"].index(profile[23]) 
                    if profile and len(profile) > 23 and profile[23] else 0)
            
            with col2:
                emergency_phone = st.text_input("Contact Phone",
                    value=profile[22] if profile and len(profile) > 22 else "",
                    placeholder="(555) 123-4567")
                emergency_email = st.text_input("Contact Email (Optional)")
            
            if st.form_submit_button("💾 Update Emergency Contact", type="primary"):
                cursor.execute("""
                    UPDATE driver_profiles 
                    SET emergency_contact_name=?, emergency_contact_phone=?, 
                        emergency_contact_relationship=?, updated_at=CURRENT_TIMESTAMP
                    WHERE user_id=?
                """, (emergency_name, emergency_phone, emergency_relationship, driver_id))
                conn.commit()
                st.success("✅ Emergency contact updated!")
    
    with tabs[3]:
        st.markdown("### Payment Information")
        
        st.info("💰 **Smith & Williams Trucking uses Navy Federal for all contractor payments**")
        
        payment_method = st.radio("Preferred Payment Method",
            ["Navy Federal Account Transfer", "Check"],
            index=0 if not profile or not profile[28] or profile[28] == 'navy_federal_transfer' else 1,
            help="Navy Federal account transfers are processed same-day. Checks take 3-5 business days.")
        
        if payment_method == "Navy Federal Account Transfer":
            st.success("✅ Fast, secure same-day transfers through Navy Federal")
            
            with st.form("banking_info"):
                st.markdown("#### Your Navy Federal Account Information")
                col1, col2 = st.columns(2)
                
                with col1:
                    has_navy_federal = st.checkbox("I have a Navy Federal account", 
                        value=True if profile and profile[24] == "Navy Federal" else False)
                    
                    if has_navy_federal:
                        account_type = st.selectbox("Account Type",
                            ["Checking", "Savings"],
                            index=["checking", "savings"].index(profile[27].lower()) 
                            if profile and profile[27] else 0)
                    else:
                        st.warning("⚠️ Navy Federal account required for same-day transfers")
                        other_bank = st.text_input("Your Bank Name",
                            value=profile[24] if profile and profile[24] != "Navy Federal" else "")
                
                with col2:
                    if has_navy_federal:
                        account_number = st.text_input("Navy Federal Account Number",
                            value="****" + profile[26][-4:] if profile and profile[26] else "",
                            type="password",
                            help="Your Navy Federal account number")
                        member_number = st.text_input("Navy Federal Member Number",
                            placeholder="Your member number",
                            help="Found on your Navy Federal card or statement")
                    else:
                        routing = st.text_input("Routing Number",
                            value=profile[25] if profile and profile[25] else "",
                            max_chars=9,
                            help="9-digit routing number")
                        account = st.text_input("Account Number",
                            value="****" + profile[26][-4:] if profile and profile[26] else "",
                            type="password")
                
                st.info("🔒 Your banking information is encrypted and secure")
                
                if st.form_submit_button("💾 Save Payment Info", type="primary"):
                    if has_navy_federal:
                        cursor.execute("""
                            UPDATE driver_profiles 
                            SET bank_name='Navy Federal', account_number=?, 
                                account_type=?, payment_method='navy_federal_transfer',
                                updated_at=CURRENT_TIMESTAMP
                            WHERE user_id=?
                        """, (account_number, account_type.lower(), driver_id))
                    else:
                        cursor.execute("""
                            UPDATE driver_profiles 
                            SET bank_name=?, routing_number=?, account_number=?, 
                                account_type='checking', payment_method='ach',
                                updated_at=CURRENT_TIMESTAMP
                            WHERE user_id=?
                        """, (other_bank, routing, account, driver_id))
                    
                    conn.commit()
                    st.success("✅ Payment information saved securely!")
                    st.rerun()
        
        elif payment_method == "Check":
            st.info("📬 Paper checks will be mailed to your address on file (3-5 business days)")
            
            with st.form("check_info"):
                mailing_address = st.text_area("Mailing Address",
                    value=profile[9] if profile else "",
                    placeholder="Address where checks should be mailed")
                
                if st.form_submit_button("💾 Save Check Preference", type="primary"):
                    cursor.execute("""
                        UPDATE driver_profiles 
                        SET payment_method='check', address=?, updated_at=CURRENT_TIMESTAMP
                        WHERE user_id=?
                    """, (mailing_address, driver_id))
                    conn.commit()
                    st.success("✅ Payment method updated to Check")
    
    with tabs[4]:
        st.markdown("### Required Documents")
        
        st.info("""
        📋 **Required Documents for Independent Contractors:**
        - Valid CDL
        - Current DOT Medical Certificate  
        - Certificate of Insurance (COI)
        - W9 Form
        - Vehicle Registration (if owner-operator)
        - Operating Authority (if applicable)
        """)
        
        with st.form("contractor_docs"):
            st.markdown("#### Upload Contractor Documents")
            
            doc_type = st.selectbox("Document Type", [
                "CDL",
                "DOT Medical Certificate",
                "Certificate of Insurance (COI)",
                "W9 Form",
                "Vehicle Registration",
                "Operating Authority",
                "Hazmat Endorsement",
                "TWIC Card",
                "Other"
            ])
            
            uploaded_file = st.file_uploader(
                f"Upload {doc_type}",
                type=['pdf', 'jpg', 'jpeg', 'png']
            )
            
            if doc_type in ["CDL", "DOT Medical Certificate", "Certificate of Insurance (COI)", "Hazmat Endorsement", "TWIC Card"]:
                expiry_date = st.date_input(f"{doc_type} Expiry Date")
            else:
                expiry_date = None
            
            notes = st.text_area("Notes (Optional)")
            
            if st.form_submit_button("📤 Upload Document", type="primary"):
                if uploaded_file:
                    # Create upload directory
                    upload_dir = Path(f"uploads/drivers/{driver_id}")
                    upload_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Save file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_name = f"{timestamp}_{uploaded_file.name}"
                    file_path = upload_dir / file_name
                    
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Save to database
                    cursor.execute("""
                        INSERT INTO driver_documents 
                        (driver_id, driver_name, document_type, file_name, 
                         file_path, expiry_date, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (driver_id, driver_name, doc_type, file_name,
                          str(file_path), expiry_date, notes))
                    conn.commit()
                    
                    st.success(f"✅ {doc_type} uploaded successfully!")
                else:
                    st.error("Please select a file to upload")
        
        # Show uploaded documents
        st.markdown("#### Your Documents")
        
        doc_df = pd.read_sql_query("""
            SELECT 
                document_type as 'Document',
                file_name as 'File',
                expiry_date as 'Expires',
                uploaded_at as 'Uploaded'
            FROM driver_documents
            WHERE driver_id = ?
            ORDER BY uploaded_at DESC
        """, conn, params=[driver_id])
        
        if not doc_df.empty:
            st.dataframe(doc_df, use_container_width=True, hide_index=True)
        else:
            st.info("No documents uploaded yet")
    
    with tabs[5]:
        st.markdown("### Certifications & Endorsements")
        
        certifications = [
            "Hazmat Endorsement",
            "Tanker Endorsement",
            "Doubles/Triples",
            "TWIC Card",
            "Forklift Certification",
            "Crane Operator",
            "Other"
        ]
        
        st.multiselect("Select Your Certifications", certifications)
        
        if st.button("💾 Save Certifications", type="primary"):
            st.success("✅ Certifications updated!")
    
    conn.close()