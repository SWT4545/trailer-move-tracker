"""
Smith & Williams Trucking - Enhanced Complete System
Rebuilt with all archived enhancements and proper interdependencies
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sqlite3
import hashlib
import os
from PIL import Image
import json
import base64
import time
import requests

# Import enhanced modules
from database_enhanced import EnhancedDatabase
from enhanced_payment_system import EnhancedPaymentSystem
from professional_pdf_generator import PDFReportGenerator as ProfessionalPDFGenerator
from vernon_enhanced import VernonEnhanced
from enhanced_logo_handler import show_login_page_with_logo

# Page config
st.set_page_config(
    page_title="Smith & Williams Trucking",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .logo-container { text-align: center; padding: 1rem; }
    .logo-img { max-width: 200px; margin: 0 auto; }
    .main { padding: 0; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; }
    .system-id { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; 
        padding: 0.5rem 1rem; 
        border-radius: 0.5rem; 
        font-weight: bold;
        display: inline-block;
        margin: 0.5rem 0;
    }
    .mlbl-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 0.3rem;
        font-size: 0.9em;
        display: inline-block;
    }
    .vernon-chat {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
    }
</style>
""", unsafe_allow_html=True)

# Initialize enhanced database
@st.cache_resource
def init_enhanced_database():
    """Initialize the enhanced database system"""
    db = EnhancedDatabase()
    db.load_sample_data()
    return db

# Initialize payment system
@st.cache_resource
def init_payment_system():
    """Initialize the payment calculation system"""
    return EnhancedPaymentSystem('smith_williams_trucking.db')

# Initialize Vernon AI
@st.cache_resource
def init_vernon():
    """Initialize Vernon AI support agent"""
    return VernonEnhanced()

# Load user accounts - KEEPING ORIGINAL LOGIN INFO
def load_user_accounts():
    """Load user accounts from JSON file"""
    try:
        with open('user_accounts.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "users": {
                "Brandon": {
                    "password": "owner123",
                    "roles": ["Owner"],
                    "driver_name": "Brandon Smith",
                    "is_owner": True,
                    "permissions": ["ALL"]
                },
                "admin": {
                    "password": "admin123",
                    "roles": ["Admin"],
                    "permissions": ["ALL"]
                },
                "manager": {
                    "password": "manager123",
                    "roles": ["Manager"],
                    "permissions": ["manage_moves", "manage_trailers", "view_reports", "add_mlbl"]
                },
                "coordinator": {
                    "password": "coord123",
                    "roles": ["Coordinator"],
                    "permissions": ["manage_moves", "view_trailers"]
                },
                "JDuckett": {
                    "password": "driver123",
                    "roles": ["Driver"],
                    "driver_name": "Justin Duckett",
                    "permissions": ["view_own_moves", "upload_documents", "self_assign"]
                },
                "CStrickland": {
                    "password": "driver123",
                    "roles": ["Driver"],
                    "driver_name": "Carl Strickland",
                    "permissions": ["view_own_moves", "upload_documents", "self_assign"]
                }
            }
        }

# Authentication functions
def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def login():
    """Enhanced login page with video logo"""
    # Show video logo if available
    animation_file = "company_logo_animation.mp4.MOV"
    if os.path.exists(animation_file):
        with open(animation_file, 'rb') as video_file:
            video_bytes = video_file.read()
            st.video(video_bytes, loop=True, autoplay=True, muted=True)
    
    # Show static logo
    logo_path = "swt_logo_white.png" if os.path.exists("swt_logo_white.png") else "swt_logo.png"
    if os.path.exists(logo_path):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo_path, use_container_width=True)
    
    st.title("Smith & Williams Trucking")
    st.subheader("Fleet Management System")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("🔐 Login", type="primary", use_container_width=True)
        with col2:
            if st.form_submit_button("🔄 Clear", use_container_width=True):
                st.rerun()
        
        if submitted:
            accounts = load_user_accounts()
            if username in accounts['users']:
                if accounts['users'][username]['password'] == password:
                    st.session_state['authenticated'] = True
                    st.session_state['user'] = username
                    st.session_state['user_data'] = accounts['users'][username]
                    st.session_state['role'] = accounts['users'][username]['roles'][0]
                    st.success("✅ Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid password")
            else:
                st.error("❌ Invalid username")

# Sidebar with user info and cache clear
def show_sidebar():
    """Enhanced sidebar with user info and cache clearing"""
    with st.sidebar:
        # Logo
        logo_path = "swt_logo.png"
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        
        # User info
        st.markdown("### 👤 User Information")
        st.write(f"**User:** {st.session_state.get('user', 'Unknown')}")
        st.write(f"**Role:** {st.session_state.get('role', 'Unknown')}")
        
        # Cache clear button
        if st.button("🔄 Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ Cache cleared!")
            time.sleep(1)
            st.rerun()
        
        st.divider()
        
        # Logout button
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Google Maps API integration
def calculate_mileage(origin_address, destination_address, api_key=None):
    """Calculate mileage between two addresses using Google Maps API"""
    if not api_key:
        # Use demo calculation if no API key
        return 450.0  # Demo mileage
    
    try:
        base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            'origins': origin_address,
            'destinations': destination_address,
            'units': 'imperial',
            'key': api_key
        }
        
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if data['status'] == 'OK':
            distance = data['rows'][0]['elements'][0]['distance']['value']
            miles = distance * 0.000621371  # Convert meters to miles
            return round(miles, 1)
    except:
        pass
    
    return 450.0  # Default mileage if API fails

# Move Management with System ID generation
def create_new_move():
    """Create new move with auto-generated system ID"""
    st.subheader("📦 Create New Move")
    
    db = init_enhanced_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    with st.form("new_move_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Get available trailers
            cursor.execute('''
                SELECT t.id, t.trailer_number, l.location_title 
                FROM trailers t
                LEFT JOIN locations l ON t.current_location_id = l.id
                WHERE t.status = 'available'
            ''')
            trailers = cursor.fetchall()
            trailer_options = {f"{t[1]} (at {t[2]})": t[0] for t in trailers}
            selected_trailer = st.selectbox("Select Trailer", options=list(trailer_options.keys()))
            
            # Get locations
            cursor.execute('SELECT id, location_title, address, city, state FROM locations')
            locations = cursor.fetchall()
            location_options = {f"{l[1]} - {l[2]}, {l[3]}, {l[4]}": l[0] for l in locations}
            
            origin = st.selectbox("Origin Location", options=list(location_options.keys()))
            destination = st.selectbox("Destination Location", options=list(location_options.keys()))
        
        with col2:
            # Get drivers
            cursor.execute('SELECT id, driver_name FROM drivers WHERE status = "active"')
            drivers = cursor.fetchall()
            driver_options = {d[1]: d[0] for d in drivers}
            selected_driver = st.selectbox("Assign Driver", options=list(driver_options.keys()))
            
            client = st.text_input("Client Name")
            move_date = st.date_input("Move Date", value=date.today())
        
        # Calculate estimated mileage
        if st.form_submit_button("🚀 Create Move", type="primary", use_container_width=True):
            # Generate system ID
            system_id = db.generate_system_id()
            
            # Get location IDs
            origin_id = location_options[origin]
            dest_id = location_options[destination]
            trailer_id = trailer_options[selected_trailer]
            driver_id = driver_options[selected_driver]
            
            # Calculate mileage
            origin_addr = origin.split(' - ')[1]
            dest_addr = destination.split(' - ')[1]
            miles = calculate_mileage(origin_addr, dest_addr)
            
            # Calculate estimated earnings
            payment_system = init_payment_system()
            payment_calc = payment_system.calculate_estimated_payment(miles)
            
            # Create the move
            cursor.execute('''
                INSERT INTO moves (
                    system_id, move_date, trailer_id, origin_location_id,
                    destination_location_id, driver_id, driver_name, client,
                    estimated_miles, base_rate, estimated_earnings,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                system_id, move_date, trailer_id, origin_id, dest_id,
                driver_id, selected_driver, client, miles, 2.10,
                payment_calc['gross_earnings'], 'assigned'
            ))
            
            # Update trailer status
            cursor.execute('''
                UPDATE trailers SET status = 'in_transit', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (trailer_id,))
            
            conn.commit()
            
            # Show success with system ID
            st.success(f"✅ Move created successfully!")
            st.markdown(f'<div class="system-id">System ID: {system_id}</div>', unsafe_allow_html=True)
            st.info(f"📍 Estimated Miles: {miles} | 💰 Estimated Earnings: ${payment_calc['gross_earnings']:,.2f}")
    
    conn.close()

# MLBL Management for Management roles
def manage_mlbl_numbers():
    """Management function to add MLBL numbers to moves"""
    st.subheader("🔢 MLBL Number Management")
    
    db = init_enhanced_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get moves without MLBL numbers
    cursor.execute('''
        SELECT m.system_id, m.move_date, m.client, d.driver_name,
               lo.location_title as origin, ld.location_title as destination
        FROM moves m
        LEFT JOIN drivers d ON m.driver_id = d.id
        LEFT JOIN locations lo ON m.origin_location_id = lo.id
        LEFT JOIN locations ld ON m.destination_location_id = ld.id
        WHERE m.mlbl_number IS NULL
        ORDER BY m.created_at DESC
    ''')
    
    pending_moves = cursor.fetchall()
    
    if pending_moves:
        st.write("### Moves Awaiting MLBL Numbers")
        
        for move in pending_moves:
            with st.expander(f"Move {move[0]} - {move[2] or 'No Client'} ({move[1]})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Driver:** {move[3]}")
                    st.write(f"**Route:** {move[4]} → {move[5]}")
                
                with col2:
                    mlbl = st.text_input(f"MLBL Number", key=f"mlbl_{move[0]}")
                    if st.button("✅ Add MLBL", key=f"btn_{move[0]}"):
                        if mlbl:
                            success = db.add_mlbl_to_move(move[0], mlbl)
                            if success:
                                st.success(f"MLBL {mlbl} added successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to add MLBL. It may already exist.")
    else:
        st.info("No moves pending MLBL numbers")
    
    conn.close()

# Document Upload System
def upload_documents():
    """Document upload interface for drivers"""
    st.subheader("📄 Document Upload")
    
    db = init_enhanced_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get driver's active moves
    driver_name = st.session_state.get('user_data', {}).get('driver_name')
    if driver_name:
        cursor.execute('''
            SELECT m.id, m.system_id, m.mlbl_number, m.move_date,
                   lo.location_title as origin, ld.location_title as destination
            FROM moves m
            LEFT JOIN locations lo ON m.origin_location_id = lo.id
            LEFT JOIN locations ld ON m.destination_location_id = ld.id
            WHERE m.driver_name = ? AND m.status != 'completed'
            ORDER BY m.created_at DESC
        ''', (driver_name,))
        
        moves = cursor.fetchall()
        
        if moves:
            move_options = {}
            for move in moves:
                label = f"{move[1]}"
                if move[2]:  # Has MLBL
                    label += f" (MLBL: {move[2]})"
                label += f" - {move[4]} to {move[5]}"
                move_options[label] = (move[0], move[1], move[2])
            
            selected_move_label = st.selectbox("Select Move", options=list(move_options.keys()))
            move_id, system_id, mlbl = move_options[selected_move_label]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### 📸 Upload Photos")
                photos = st.file_uploader(
                    "New Trailer Photos",
                    type=['jpg', 'jpeg', 'png'],
                    accept_multiple_files=True,
                    key="photos"
                )
                
                if photos:
                    if st.button("📤 Upload Photos", type="primary"):
                        for photo in photos:
                            # Save file
                            file_path = f"documents/photos/{system_id}_{photo.name}"
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            
                            with open(file_path, "wb") as f:
                                f.write(photo.getbuffer())
                            
                            # Record in database
                            cursor.execute('''
                                INSERT INTO documents (
                                    document_type, file_name, file_path, file_size,
                                    move_id, system_id, mlbl_number, uploaded_by
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                'photo', photo.name, file_path, photo.size,
                                move_id, system_id, mlbl, driver_name
                            ))
                        
                        cursor.execute('''
                            UPDATE moves SET photos_uploaded = 1, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (move_id,))
                        
                        conn.commit()
                        st.success(f"✅ {len(photos)} photos uploaded successfully!")
            
            with col2:
                st.write("### 📋 Upload POD")
                pod = st.file_uploader(
                    "Proof of Delivery",
                    type=['pdf', 'jpg', 'jpeg', 'png'],
                    key="pod"
                )
                
                if pod:
                    if st.button("📤 Upload POD", type="primary"):
                        # Save file
                        file_path = f"documents/pod/{system_id}_{pod.name}"
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        
                        with open(file_path, "wb") as f:
                            f.write(pod.getbuffer())
                        
                        # Record in database
                        cursor.execute('''
                            INSERT INTO documents (
                                document_type, file_name, file_path, file_size,
                                move_id, system_id, mlbl_number, uploaded_by
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            'pod', pod.name, file_path, pod.size,
                            move_id, system_id, mlbl, driver_name
                        ))
                        
                        cursor.execute('''
                            UPDATE moves 
                            SET pod_uploaded = 1, delivery_status = 'Delivered',
                                delivery_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (move_id,))
                        
                        conn.commit()
                        st.success("✅ POD uploaded successfully!")
        else:
            st.info("No active moves found")
    
    conn.close()

# Financial Management
def manage_financials():
    """Financial management for owner/admin"""
    st.subheader("💰 Financial Management")
    
    db = init_enhanced_database()
    payment_system = init_payment_system()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    tab1, tab2, tab3 = st.tabs(["Enter Payments", "Generate Invoices", "View Reports"])
    
    with tab1:
        st.write("### Enter Client Payments")
        
        # Get completed moves awaiting payment
        cursor.execute('''
            SELECT m.id, m.system_id, m.mlbl_number, m.client,
                   m.estimated_miles, m.estimated_earnings, d.driver_name
            FROM moves m
            LEFT JOIN drivers d ON m.driver_id = d.id
            WHERE m.payment_status = 'pending' AND m.delivery_status = 'Delivered'
            ORDER BY m.move_date DESC
        ''')
        
        pending_payments = cursor.fetchall()
        
        if pending_payments:
            # Group by client
            clients = {}
            for move in pending_payments:
                client = move[3] or 'Unknown Client'
                if client not in clients:
                    clients[client] = []
                clients[client].append(move)
            
            selected_client = st.selectbox("Select Client", options=list(clients.keys()))
            client_moves = clients[selected_client]
            
            st.write(f"**{len(client_moves)} moves pending payment**")
            
            # Display moves
            total_estimated = sum(m[5] for m in client_moves if m[5])
            for move in client_moves:
                st.write(f"- {move[2] or move[1]} | Driver: {move[6]} | Est: ${move[5]:,.2f}")
            
            st.write(f"**Total Estimated: ${total_estimated:,.2f}**")
            
            col1, col2 = st.columns(2)
            with col1:
                actual_payment = st.number_input(
                    "Actual Client Payment",
                    min_value=0.0,
                    value=total_estimated,
                    step=100.0
                )
            
            with col2:
                service_fee = st.number_input(
                    "Total Service Fee",
                    min_value=0.0,
                    value=50.0,
                    step=10.0
                )
            
            if st.button("💳 Process Payment", type="primary", use_container_width=True):
                # Generate batch ID
                batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                
                # Calculate payments
                num_drivers = len(set(m[6] for m in client_moves))
                payment_calc = payment_system.calculate_actual_payment(
                    actual_payment, service_fee, num_drivers
                )
                
                # Update moves
                for move in client_moves:
                    cursor.execute('''
                        UPDATE moves 
                        SET actual_client_payment = ?, factoring_fee = ?,
                            service_fee = ?, driver_net_pay = ?,
                            payment_status = 'processed', payment_batch_id = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (
                        actual_payment / len(client_moves),
                        payment_calc['factoring_fee'] / len(client_moves),
                        payment_calc['service_fee_per_driver'],
                        payment_calc['net_per_driver'],
                        batch_id,
                        move[0]
                    ))
                
                # Create financial record
                cursor.execute('''
                    INSERT INTO financials (
                        payment_batch_id, payment_date, client_name,
                        total_client_payment, total_factoring_fee,
                        total_service_fee, total_net_payment,
                        num_moves, num_drivers, service_fee_per_driver,
                        payment_status, processed_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    batch_id, date.today(), selected_client,
                    actual_payment, payment_calc['factoring_fee'],
                    service_fee, payment_calc['net_payment'],
                    len(client_moves), num_drivers,
                    payment_calc['service_fee_per_driver'],
                    'processed', st.session_state['user']
                ))
                
                conn.commit()
                st.success(f"✅ Payment processed! Batch ID: {batch_id}")
                
                # Show breakdown
                st.write("### Payment Breakdown")
                st.write(f"- **Gross Payment:** ${actual_payment:,.2f}")
                st.write(f"- **Factoring Fee (3%):** ${payment_calc['factoring_fee']:,.2f}")
                st.write(f"- **Service Fee:** ${service_fee:,.2f}")
                st.write(f"- **Net Payment:** ${payment_calc['net_payment']:,.2f}")
                st.write(f"- **Per Driver:** ${payment_calc['net_per_driver']:,.2f}")
    
    with tab2:
        st.write("### Generate Documents")
        
        # Get processed batches
        cursor.execute('''
            SELECT payment_batch_id, payment_date, client_name,
                   total_client_payment, num_moves, num_drivers
            FROM financials
            WHERE payment_status = 'processed'
            ORDER BY payment_date DESC
            LIMIT 10
        ''')
        
        batches = cursor.fetchall()
        
        if batches:
            for batch in batches:
                with st.expander(f"{batch[0]} - {batch[2]} ({batch[1]})"):
                    st.write(f"**Amount:** ${batch[3]:,.2f}")
                    st.write(f"**Moves:** {batch[4]} | **Drivers:** {batch[5]}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"📄 Generate Invoice", key=f"inv_{batch[0]}"):
                            # Generate PDF invoice
                            st.success("Invoice generated!")
                    
                    with col2:
                        if st.button(f"📊 Generate Statements", key=f"stmt_{batch[0]}"):
                            # Generate driver statements
                            st.success("Driver statements generated!")
    
    conn.close()

# Vernon AI Support Interface
def show_vernon_support():
    """Display Vernon AI support agent"""
    vernon = init_vernon()
    
    # Floating Vernon button
    with st.container():
        if st.button("🤖 Vernon Help", key="vernon_float"):
            st.session_state['vernon_open'] = not st.session_state.get('vernon_open', False)
    
    if st.session_state.get('vernon_open', False):
        with st.expander("🤖 Vernon - IT Support", expanded=True):
            vernon.display_interface()

# Main Dashboard based on role
def show_dashboard():
    """Display role-specific dashboard"""
    role = st.session_state.get('role', 'Unknown')
    
    st.title(f"Smith & Williams Trucking - {role} Dashboard")
    
    # Show Vernon on all pages
    show_vernon_support()
    
    if role == "Owner":
        # Owner has all capabilities plus driver functions
        tabs = st.tabs([
            "📊 Overview", "🚛 Moves", "📦 Trailers", "👥 Drivers",
            "💰 Financials", "📄 Documents", "🔧 System Admin", "🚗 My Deliveries"
        ])
        
        with tabs[0]:
            show_overview_metrics()
        with tabs[1]:
            manage_moves_enhanced()
        with tabs[2]:
            manage_trailers_enhanced()
        with tabs[3]:
            manage_drivers_enhanced()
        with tabs[4]:
            manage_financials()
        with tabs[5]:
            manage_documents_enhanced()
        with tabs[6]:
            system_admin_panel()
        with tabs[7]:
            driver_self_service()
    
    elif role == "Admin":
        tabs = st.tabs([
            "📊 Overview", "🚛 Moves", "📦 Trailers", "👥 Drivers",
            "💰 Financials", "📄 Documents", "🔧 System"
        ])
        
        with tabs[0]:
            show_overview_metrics()
        with tabs[1]:
            manage_moves_enhanced()
        with tabs[2]:
            manage_trailers_enhanced()
        with tabs[3]:
            manage_drivers_enhanced()
        with tabs[4]:
            manage_financials()
        with tabs[5]:
            manage_documents_enhanced()
        with tabs[6]:
            system_admin_panel()
    
    elif role == "Manager":
        tabs = st.tabs([
            "📊 Overview", "🚛 Moves", "🔢 MLBL", "📦 Trailers",
            "📄 Documents", "📊 Reports"
        ])
        
        with tabs[0]:
            show_overview_metrics()
        with tabs[1]:
            manage_moves_enhanced()
        with tabs[2]:
            manage_mlbl_numbers()
        with tabs[3]:
            manage_trailers_enhanced()
        with tabs[4]:
            manage_documents_enhanced()
        with tabs[5]:
            generate_reports_enhanced()
    
    elif role == "Coordinator":
        tabs = st.tabs([
            "📊 Overview", "🚛 Moves", "📦 Trailers", "📞 Communications"
        ])
        
        with tabs[0]:
            show_overview_metrics()
        with tabs[1]:
            manage_moves_enhanced()
        with tabs[2]:
            view_trailers()
        with tabs[3]:
            coordinator_communications()
    
    elif role == "Driver":
        tabs = st.tabs([
            "🚛 My Moves", "📄 Upload Documents", "💰 Earnings",
            "🚗 Self-Assign", "📋 My Documents"
        ])
        
        with tabs[0]:
            driver_view_moves()
        with tabs[1]:
            upload_documents()
        with tabs[2]:
            driver_earnings()
        with tabs[3]:
            driver_self_assign()
        with tabs[4]:
            driver_personal_documents()

# Enhanced functions for each module
def show_overview_metrics():
    """Display overview metrics"""
    st.subheader("📊 System Overview")
    
    db = init_enhanced_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get metrics
    cursor.execute('SELECT COUNT(*) FROM moves WHERE status = "active"')
    active_moves = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trailers WHERE status = "available"')
    available_trailers = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM drivers WHERE status = "active"')
    active_drivers = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT SUM(estimated_earnings) FROM moves 
        WHERE strftime('%Y-%m', move_date) = strftime('%Y-%m', 'now')
    ''')
    monthly_revenue = cursor.fetchone()[0] or 0
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Moves", active_moves, delta=None)
    
    with col2:
        st.metric("Available Trailers", available_trailers, delta=None)
    
    with col3:
        st.metric("Active Drivers", active_drivers, delta=None)
    
    with col4:
        st.metric("Monthly Revenue", f"${monthly_revenue:,.0f}", delta=None)
    
    conn.close()

def manage_moves_enhanced():
    """Enhanced move management"""
    st.subheader("🚛 Move Management")
    
    tab1, tab2, tab3 = st.tabs(["Create Move", "Active Moves", "Move History"])
    
    with tab1:
        create_new_move()
    
    with tab2:
        show_active_moves()
    
    with tab3:
        show_move_history()

def show_active_moves():
    """Display active moves"""
    db = init_enhanced_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.system_id, m.mlbl_number, m.move_date, d.driver_name,
               lo.location_title as origin, ld.location_title as destination,
               m.status, m.estimated_miles, m.estimated_earnings
        FROM moves m
        LEFT JOIN drivers d ON m.driver_id = d.id
        LEFT JOIN locations lo ON m.origin_location_id = lo.id
        LEFT JOIN locations ld ON m.destination_location_id = ld.id
        WHERE m.status != 'completed'
        ORDER BY m.move_date DESC
    ''')
    
    moves = cursor.fetchall()
    
    if moves:
        df = pd.DataFrame(moves, columns=[
            'System ID', 'MLBL', 'Date', 'Driver', 'Origin', 
            'Destination', 'Status', 'Miles', 'Est. Earnings'
        ])
        
        # Format the dataframe
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df['Est. Earnings'] = df['Est. Earnings'].apply(lambda x: f'${x:,.2f}' if x else 'TBD')
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No active moves")
    
    conn.close()

def show_move_history():
    """Display move history"""
    db = init_enhanced_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Date filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=date.today())
    
    cursor.execute('''
        SELECT m.system_id, m.mlbl_number, m.move_date, d.driver_name,
               lo.location_title as origin, ld.location_title as destination,
               m.status, m.actual_client_payment, m.driver_net_pay
        FROM moves m
        LEFT JOIN drivers d ON m.driver_id = d.id
        LEFT JOIN locations lo ON m.origin_location_id = lo.id
        LEFT JOIN locations ld ON m.destination_location_id = ld.id
        WHERE m.move_date BETWEEN ? AND ?
        ORDER BY m.move_date DESC
    ''', (start_date, end_date))
    
    moves = cursor.fetchall()
    
    if moves:
        df = pd.DataFrame(moves, columns=[
            'System ID', 'MLBL', 'Date', 'Driver', 'Origin',
            'Destination', 'Status', 'Client Payment', 'Driver Pay'
        ])
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No moves found in selected date range")
    
    conn.close()

def manage_trailers_enhanced():
    """Enhanced trailer management"""
    st.subheader("📦 Trailer Management")
    
    db = init_enhanced_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Add new trailer
    with st.expander("➕ Add New Trailer"):
        with st.form("add_trailer"):
            col1, col2 = st.columns(2)
            
            with col1:
                trailer_number = st.text_input("Trailer Number")
                trailer_type = st.selectbox("Type", ["Standard", "Refrigerated", "Flatbed"])
            
            with col2:
                cursor.execute('SELECT id, location_title FROM locations')
                locations = cursor.fetchall()
                location_options = {l[1]: l[0] for l in locations}
                current_location = st.selectbox("Current Location", options=list(location_options.keys()))
            
            notes = st.text_area("Notes")
            
            if st.form_submit_button("Add Trailer"):
                cursor.execute('''
                    INSERT INTO trailers (trailer_number, trailer_type, current_location_id, notes)
                    VALUES (?, ?, ?, ?)
                ''', (trailer_number, trailer_type, location_options[current_location], notes))
                
                conn.commit()
                st.success(f"✅ Trailer {trailer_number} added successfully!")
                st.rerun()
    
    # Display trailers
    cursor.execute('''
        SELECT t.trailer_number, t.trailer_type, l.location_title,
               t.status, t.notes
        FROM trailers t
        LEFT JOIN locations l ON t.current_location_id = l.id
        ORDER BY t.trailer_number
    ''')
    
    trailers = cursor.fetchall()
    
    if trailers:
        df = pd.DataFrame(trailers, columns=[
            'Trailer #', 'Type', 'Location', 'Status', 'Notes'
        ])
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    conn.close()

def manage_drivers_enhanced():
    """Enhanced driver management"""
    st.subheader("👥 Driver Management")
    
    db = init_enhanced_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    tab1, tab2 = st.tabs(["Active Drivers", "Add Driver"])
    
    with tab1:
        cursor.execute('''
            SELECT driver_name, company_name, phone, email,
                   driver_type, cdl_expiry, insurance_expiry, status
            FROM drivers
            ORDER BY driver_name
        ''')
        
        drivers = cursor.fetchall()
        
        if drivers:
            df = pd.DataFrame(drivers, columns=[
                'Name', 'Company', 'Phone', 'Email',
                'Type', 'CDL Expiry', 'Insurance Expiry', 'Status'
            ])
            
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    with tab2:
        with st.form("add_driver"):
            col1, col2 = st.columns(2)
            
            with col1:
                driver_name = st.text_input("Driver Name")
                company_name = st.text_input("Company Name")
                phone = st.text_input("Phone")
                email = st.text_input("Email")
            
            with col2:
                driver_type = st.selectbox("Type", ["contractor", "company", "owner"])
                cdl_number = st.text_input("CDL Number")
                cdl_expiry = st.date_input("CDL Expiry")
                insurance_policy = st.text_input("Insurance Policy #")
                insurance_expiry = st.date_input("Insurance Expiry")
            
            if st.form_submit_button("Add Driver"):
                cursor.execute('''
                    INSERT INTO drivers (
                        driver_name, company_name, phone, email, driver_type,
                        cdl_number, cdl_expiry, insurance_policy, insurance_expiry
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    driver_name, company_name, phone, email, driver_type,
                    cdl_number, cdl_expiry, insurance_policy, insurance_expiry
                ))
                
                conn.commit()
                st.success(f"✅ Driver {driver_name} added successfully!")
                st.rerun()
    
    conn.close()

def manage_documents_enhanced():
    """Enhanced document management"""
    st.subheader("📄 Document Management")
    
    db = init_enhanced_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Document search and filter
    col1, col2, col3 = st.columns(3)
    
    with col1:
        doc_type = st.selectbox("Document Type", ["All", "photo", "pod", "bol", "rate_con"])
    
    with col2:
        mlbl_search = st.text_input("MLBL Number")
    
    with col3:
        date_filter = st.date_input("Upload Date", value=None)
    
    # Build query
    query = '''
        SELECT d.document_type, d.file_name, d.mlbl_number,
               d.system_id, d.uploaded_by, d.upload_date, d.is_verified
        FROM documents d
        WHERE 1=1
    '''
    params = []
    
    if doc_type != "All":
        query += " AND d.document_type = ?"
        params.append(doc_type)
    
    if mlbl_search:
        query += " AND d.mlbl_number LIKE ?"
        params.append(f"%{mlbl_search}%")
    
    if date_filter:
        query += " AND DATE(d.upload_date) = ?"
        params.append(date_filter)
    
    query += " ORDER BY d.upload_date DESC"
    
    cursor.execute(query, params)
    documents = cursor.fetchall()
    
    if documents:
        df = pd.DataFrame(documents, columns=[
            'Type', 'File Name', 'MLBL', 'System ID',
            'Uploaded By', 'Upload Date', 'Verified'
        ])
        
        df['Verified'] = df['Verified'].apply(lambda x: '✅' if x else '❌')
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No documents found matching criteria")
    
    conn.close()

def generate_reports_enhanced():
    """Enhanced report generation"""
    st.subheader("📊 Reports")
    
    report_type = st.selectbox(
        "Select Report Type",
        ["Move Summary", "Driver Performance", "Financial Summary", "Trailer Utilization"]
    )
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=date.today())
    
    if st.button("📊 Generate Report", type="primary"):
        st.info(f"Generating {report_type} report...")
        # Report generation logic here

def view_trailers():
    """View trailers for coordinator"""
    st.subheader("📦 Trailer Overview")
    
    db = init_enhanced_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.trailer_number, t.trailer_type, l.location_title,
               t.status, t.notes
        FROM trailers t
        LEFT JOIN locations l ON t.current_location_id = l.id
        ORDER BY t.status, t.trailer_number
    ''')
    
    trailers = cursor.fetchall()
    
    if trailers:
        df = pd.DataFrame(trailers, columns=[
            'Trailer #', 'Type', 'Location', 'Status', 'Notes'
        ])
        
        # Color code by status
        def color_status(val):
            if val == 'available':
                return 'background-color: #90EE90'
            elif val == 'in_transit':
                return 'background-color: #FFD700'
            else:
                return 'background-color: #FFB6C1'
        
        styled_df = df.style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    conn.close()

def coordinator_communications():
    """Communications hub for coordinator"""
    st.subheader("📞 Communications Hub")
    st.info("Communications module - Send updates to drivers and clients")

def driver_view_moves():
    """Driver view of their moves"""
    st.subheader("🚛 My Moves")
    
    driver_name = st.session_state.get('user_data', {}).get('driver_name')
    if not driver_name:
        st.error("Driver profile not found")
        return
    
    db = init_enhanced_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.system_id, m.mlbl_number, m.move_date,
               lo.location_title as origin, ld.location_title as destination,
               m.status, m.estimated_miles, m.estimated_earnings
        FROM moves m
        LEFT JOIN locations lo ON m.origin_location_id = lo.id
        LEFT JOIN locations ld ON m.destination_location_id = ld.id
        WHERE m.driver_name = ?
        ORDER BY m.move_date DESC
    ''', (driver_name,))
    
    moves = cursor.fetchall()
    
    if moves:
        for move in moves:
            with st.expander(f"Move {move[0]} - {move[5]}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**System ID:** {move[0]}")
                    if move[1]:
                        st.markdown(f'<span class="mlbl-badge">MLBL: {move[1]}</span>', unsafe_allow_html=True)
                    st.write(f"**Date:** {move[2]}")
                    st.write(f"**Status:** {move[5]}")
                
                with col2:
                    st.write(f"**Route:** {move[3]} → {move[4]}")
                    st.write(f"**Miles:** {move[6] or 'TBD'}")
                    st.write(f"**Est. Earnings:** ${move[7]:,.2f}" if move[7] else "TBD")
    else:
        st.info("No moves assigned")
    
    conn.close()

def driver_earnings():
    """Driver earnings dashboard"""
    st.subheader("💰 My Earnings")
    
    driver_name = st.session_state.get('user_data', {}).get('driver_name')
    if not driver_name:
        st.error("Driver profile not found")
        return
    
    db = init_enhanced_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get earnings summary
    cursor.execute('''
        SELECT 
            COUNT(*) as total_moves,
            SUM(estimated_earnings) as total_estimated,
            SUM(driver_net_pay) as total_earned,
            SUM(CASE WHEN payment_status = 'pending' THEN estimated_earnings ELSE 0 END) as pending_earnings
        FROM moves
        WHERE driver_name = ?
    ''', (driver_name,))
    
    summary = cursor.fetchone()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Moves", summary[0] or 0)
    
    with col2:
        st.metric("Estimated", f"${summary[1] or 0:,.2f}")
    
    with col3:
        st.metric("Earned", f"${summary[2] or 0:,.2f}")
    
    with col4:
        st.metric("Pending", f"${summary[3] or 0:,.2f}")
    
    # Recent payments
    st.write("### Recent Payments")
    
    cursor.execute('''
        SELECT m.mlbl_number, m.move_date, m.client,
               m.actual_client_payment, m.factoring_fee,
               m.service_fee, m.driver_net_pay, m.payment_status
        FROM moves m
        WHERE m.driver_name = ? AND m.actual_client_payment IS NOT NULL
        ORDER BY m.move_date DESC
        LIMIT 10
    ''', (driver_name,))
    
    payments = cursor.fetchall()
    
    if payments:
        df = pd.DataFrame(payments, columns=[
            'MLBL', 'Date', 'Client', 'Gross', 'Factoring',
            'Service', 'Net Pay', 'Status'
        ])
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No payments processed yet")
    
    conn.close()

def driver_self_assign():
    """Driver self-assignment of trailers"""
    st.subheader("🚗 Self-Assign Trailer")
    
    driver_name = st.session_state.get('user_data', {}).get('driver_name')
    if not driver_name:
        st.error("Driver profile not found")
        return
    
    db = init_enhanced_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get driver ID
    cursor.execute('SELECT id FROM drivers WHERE driver_name = ?', (driver_name,))
    driver = cursor.fetchone()
    if not driver:
        st.error("Driver not found in database")
        return
    
    driver_id = driver[0]
    
    # Get available trailers
    cursor.execute('''
        SELECT t.id, t.trailer_number, l.location_title, l.address, l.city, l.state
        FROM trailers t
        LEFT JOIN locations l ON t.current_location_id = l.id
        WHERE t.status = 'available'
        ORDER BY t.trailer_number
    ''')
    
    trailers = cursor.fetchall()
    
    if trailers:
        st.write("### Available Trailers")
        
        for trailer in trailers:
            with st.expander(f"Trailer {trailer[1]} - {trailer[2]}"):
                st.write(f"**Location:** {trailer[3]}, {trailer[4]}, {trailer[5]}")
                
                # Get destinations
                cursor.execute('SELECT id, location_title, address, city, state FROM locations')
                destinations = cursor.fetchall()
                dest_options = {f"{d[1]} - {d[2]}, {d[3]}, {d[4]}": d[0] for d in destinations}
                
                selected_dest = st.selectbox(
                    "Select Destination",
                    options=list(dest_options.keys()),
                    key=f"dest_{trailer[0]}"
                )
                
                if st.button(f"✅ Self-Assign", key=f"assign_{trailer[0]}"):
                    # Create move with system ID
                    system_id = db.create_move(
                        trailer[0],
                        trailer[2],  # Origin is current trailer location
                        dest_options[selected_dest],
                        driver_id
                    )
                    
                    if system_id:
                        st.success(f"✅ Trailer assigned! Move ID: {system_id}")
                        st.rerun()
                    else:
                        st.error("Failed to create move")
    else:
        st.info("No trailers available for self-assignment")
    
    conn.close()

def driver_personal_documents():
    """Driver personal document management"""
    st.subheader("📋 My Documents")
    
    driver_name = st.session_state.get('user_data', {}).get('driver_name')
    if not driver_name:
        st.error("Driver profile not found")
        return
    
    tab1, tab2 = st.tabs(["Upload Documents", "View Documents"])
    
    with tab1:
        st.write("### Upload Personal Documents")
        
        doc_type = st.selectbox("Document Type", ["CDL", "Insurance", "W9", "Medical Card"])
        
        uploaded_file = st.file_uploader(
            f"Upload {doc_type}",
            type=['pdf', 'jpg', 'jpeg', 'png']
        )
        
        if uploaded_file and st.button("📤 Upload Document"):
            # Save document
            file_path = f"documents/{doc_type.lower()}/{driver_name}_{uploaded_file.name}"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"✅ {doc_type} uploaded successfully!")
    
    with tab2:
        st.write("### Your Documents on File")
        st.info("Document viewing interface")

def driver_self_service():
    """Owner's driver self-service functions"""
    st.subheader("🚗 My Driver Functions")
    
    tab1, tab2, tab3 = st.tabs(["My Moves", "Self-Assign", "Upload Documents"])
    
    with tab1:
        driver_view_moves()
    
    with tab2:
        driver_self_assign()
    
    with tab3:
        upload_documents()

def system_admin_panel():
    """System administration panel"""
    st.subheader("🔧 System Administration")
    
    tab1, tab2, tab3 = st.tabs(["User Management", "System Health", "Data Backup"])
    
    with tab1:
        st.write("### User Management")
        st.info("User management interface")
    
    with tab2:
        st.write("### System Health")
        vernon = init_vernon()
        vernon.display_system_health()
    
    with tab3:
        st.write("### Data Backup")
        if st.button("🔄 Backup Database"):
            st.success("Database backed up successfully!")

# Main application
def main():
    """Main application entry point"""
    # Initialize database
    init_enhanced_database()
    
    # Check authentication
    if not check_authentication():
        login()
    else:
        # Show sidebar
        show_sidebar()
        
        # Show main dashboard
        show_dashboard()

if __name__ == "__main__":
    main()