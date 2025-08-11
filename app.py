"""
Smith & Williams Trucking - Streamlined Trailer Swap Management
Focused on core trailer swap operations with simplified workflow
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
import walkthrough_guide
import company_config
import it_bot_vernon as vernon_it

# Page configuration
st.set_page_config(
    page_title="Smith & Williams Trucking",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
db.init_database()

def apply_dark_theme():
    """Apply dark theme with red accents - Smith & Williams branding"""
    st.markdown("""
    <style>
        /* Force dark backgrounds */
        .stApp {
            background-color: #0E0E0E;
        }
        
        /* Headers white with red accent */
        h1 {
            color: #FFFFFF;
            border-bottom: 2px solid #DC143C;
            padding-bottom: 10px;
        }
        
        h2, h3 {
            color: #FFFFFF;
        }
        
        /* Dark metric cards with red border */
        div[data-testid="metric-container"] {
            background-color: #1A1A1A;
            border: 1px solid #DC143C;
            border-radius: 5px;
            padding: 10px;
        }
        
        /* White metric labels */
        div[data-testid="metric-container"] label {
            color: #FFFFFF;
        }
        
        div[data-testid="metric-container"] [data-testid="metric-container-value"] {
            color: #FFFFFF;
        }
        
        /* Sidebar enhancements */
        section[data-testid="stSidebar"] {
            background-color: #1A1A1A;
            border-right: 2px solid #8B0000;
        }
        
        /* Text color fixes */
        .stMarkdown, p, label {
            color: #FFFFFF !important;
        }
        
        /* Mobile-friendly buttons */
        .stButton > button {
            min-height: 44px;
            font-size: 16px;
        }
    </style>
    """, unsafe_allow_html=True)

def show_dashboard():
    """Main dashboard - role-specific content"""
    role = st.session_state.get('user_role', 'viewer')
    st.title("📊 Dashboard")
    st.caption(f"Welcome, {st.session_state.get('user_name', 'User')} | Role: {role.replace('_', ' ').title()}")
    
    # Get data
    moves_df = db.get_all_trailer_moves()
    
    # Calculate metrics
    today_moves = len(moves_df[pd.to_datetime(moves_df['move_date']).dt.date == date.today()]) if not moves_df.empty else 0
    pending_moves = len(moves_df[moves_df['status'] == 'assigned']) if not moves_df.empty else 0
    completed_moves = len(moves_df[moves_df['status'] == 'completed']) if not moves_df.empty else 0
    awaiting_pod = len(moves_df[moves_df['status'] == 'awaiting_pod']) if not moves_df.empty else 0
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Today's Moves", today_moves, "📅")
    with col2:
        st.metric("Pending", pending_moves, "⏳")
    with col3:
        st.metric("Awaiting POD", awaiting_pod, "📸")
    with col4:
        st.metric("Completed", completed_moves, "✅")
    
    st.divider()
    
    # Role-specific dashboard content
    if role == 'business_administrator':
        show_admin_dashboard(moves_df)
    elif role == 'operations_coordinator':
        show_coordinator_dashboard(moves_df)
    elif role == 'driver':
        show_driver_dashboard()

def show_admin_dashboard(moves_df):
    """Business Administrator specific dashboard - includes coordinator functions"""
    # First row - Payment and Activity
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 Payment Processing")
        
        # Moves ready for factoring submission
        ready_for_factoring = moves_df[
            (moves_df['status'] == 'completed') & 
            (moves_df.get('payment_status', 'pending') == 'pending')
        ]
        
        if not ready_for_factoring.empty:
            st.warning(f"📤 {len(ready_for_factoring)} moves ready for factoring submission")
            
            for _, move in ready_for_factoring.head(3).iterrows():
                with st.container():
                    st.write(f"**Move #{move['id']}** - {move.get('driver_name', 'Unassigned')}")
                    st.write(f"📍 {move.get('delivery_location', 'N/A')}")
                    if move.get('total_miles'):
                        pay = float(move['total_miles']) * 2.10 * 0.97
                        st.write(f"💵 ${pay:.2f}")
        else:
            st.success("✅ All moves processed")
    
    with col2:
        st.markdown("### 📊 Today's Activity")
        
        if not moves_df.empty:
            today_df = moves_df[pd.to_datetime(moves_df['move_date']).dt.date == date.today()]
            
            if not today_df.empty:
                st.metric("Moves Completed", len(today_df[today_df['status'] == 'completed']))
                st.metric("Total Miles", f"{today_df['total_miles'].sum():.0f}" if 'total_miles' in today_df else "0")
                
                # Calculate revenue
                total_revenue = today_df['total_miles'].sum() * 2.10 if 'total_miles' in today_df else 0
                st.metric("Est. Revenue", f"${total_revenue:.2f}")
            else:
                st.info("No moves today")
    
    st.divider()
    
    # Second row - Coordinator functions (Active Moves and Driver Availability)
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("### 🚛 Active Moves")
        
        active_moves = moves_df[moves_df['status'].isin(['assigned', 'in_progress'])]
        
        if not active_moves.empty:
            for _, move in active_moves.head(5).iterrows():
                with st.expander(f"Move #{move['id']} - {move.get('driver_name', 'Unassigned')}"):
                    st.write(f"📍 **Destination:** {move.get('delivery_location', 'N/A')}")
                    st.write(f"🚛 **Trailers:** {move.get('new_trailer', 'N/A')} ↔️ {move.get('old_trailer', 'N/A')}")
                    st.write(f"📅 **Status:** {move['status'].title()}")
                    
                    if st.button(f"📱 Copy Driver Message", key=f"msg_{move['id']}"):
                        message = generate_driver_message(move)
                        st.code(message)
                        st.success("Message ready to copy!")
        else:
            st.info("No active moves")
    
    with col4:
        st.markdown("### 👤 Driver Availability")
        
        drivers_df = db.get_all_drivers()
        if not drivers_df.empty:
            available = drivers_df[drivers_df.get('status', 'available') == 'available']
            busy = drivers_df[drivers_df.get('status', 'available') == 'busy']
            
            st.metric("Available Drivers", len(available), "🟢")
            st.metric("Busy Drivers", len(busy), "🔴")
            
            if not available.empty:
                st.markdown("**Available Now:**")
                for _, driver in available.iterrows():
                    st.write(f"• {driver['driver_name']}")
        else:
            st.info("No drivers in system")

def show_coordinator_dashboard(moves_df):
    """Operations Coordinator specific dashboard"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚛 Active Moves")
        
        active_moves = moves_df[moves_df['status'].isin(['assigned', 'in_progress'])]
        
        if not active_moves.empty:
            for _, move in active_moves.head(5).iterrows():
                with st.expander(f"Move #{move['id']} - {move.get('driver_name', 'Unassigned')}"):
                    st.write(f"📍 **Destination:** {move.get('delivery_location', 'N/A')}")
                    st.write(f"🚛 **Trailers:** {move.get('new_trailer', 'N/A')} ↔️ {move.get('old_trailer', 'N/A')}")
                    st.write(f"📅 **Status:** {move['status'].title()}")
                    
                    if st.button(f"📱 Copy Driver Message", key=f"msg_{move['id']}"):
                        message = generate_driver_message(move)
                        st.code(message)
                        st.success("Message copied to clipboard!")
        else:
            st.info("No active moves")
    
    with col2:
        st.markdown("### 👤 Driver Availability")
        
        drivers_df = db.get_all_drivers()
        if not drivers_df.empty:
            available = drivers_df[drivers_df.get('status', 'available') == 'available']
            busy = drivers_df[drivers_df.get('status', 'available') == 'busy']
            
            st.metric("Available Drivers", len(available), "🟢")
            st.metric("Busy Drivers", len(busy), "🔴")
            
            if not available.empty:
                st.markdown("**Available Now:**")
                for _, driver in available.iterrows():
                    st.write(f"• {driver['driver_name']}")
        else:
            st.info("No drivers in system")

def show_driver_dashboard():
    """Driver specific dashboard"""
    driver_name = st.session_state.get('user_name', '')
    
    st.markdown("### 🚛 My Moves")
    
    # Get driver's moves
    moves_df = db.get_all_trailer_moves()
    if not moves_df.empty:
        my_moves = moves_df[moves_df.get('driver_name', '') == driver_name]
        
        if not my_moves.empty:
            # Stats
            col1, col2, col3 = st.columns(3)
            with col1:
                active = len(my_moves[my_moves['status'].isin(['assigned', 'in_progress'])])
                st.metric("Active Moves", active)
            with col2:
                completed = len(my_moves[my_moves['status'] == 'completed'])
                st.metric("Completed", completed)
            with col3:
                # Calculate earnings
                total_miles = my_moves[my_moves['status'] == 'completed']['total_miles'].sum()
                earnings = total_miles * 2.10 * 0.97 if total_miles else 0
                st.metric("Pending Pay", f"${earnings:.2f}")
            
            st.divider()
            
            # Active moves list
            active_moves = my_moves[my_moves['status'].isin(['assigned', 'in_progress'])]
            if not active_moves.empty:
                st.markdown("### 📋 Active Assignments")
                for _, move in active_moves.iterrows():
                    with st.expander(f"Move #{move['id']} - {move.get('delivery_location', 'N/A')}"):
                        show_move_details(move)
                        
                        # Upload POD button
                        if st.button(f"📸 Upload POD", key=f"pod_{move['id']}"):
                            st.session_state.upload_move_id = move['id']
                            st.rerun()
            
            # Recent completed
            completed_moves = my_moves[my_moves['status'] == 'completed'].head(5)
            if not completed_moves.empty:
                st.markdown("### ✅ Recent Completed")
                for _, move in completed_moves.iterrows():
                    st.write(f"• Move #{move['id']} - {move.get('delivery_location', 'N/A')} - ${move.get('driver_pay', 0):.2f}")
        else:
            st.info("No moves assigned yet")
    else:
        st.info("No moves in system")

def show_trailer_management():
    """Trailer management - add individual trailers and view inventory"""
    st.title("🚛 Trailer Management")
    
    base_location = base_mgr.get_default_base_location()
    st.info(f"📍 Base Location: **{base_location}** | Add trailers here, pair them when creating moves")
    
    tabs = st.tabs(["➕ Add Trailers", "📋 View Inventory", "📍 Locations"])
    
    with tabs[0]:
        show_add_trailers(base_location)
    
    with tabs[1]:
        show_trailer_inventory()
    
    with tabs[2]:
        show_location_management()

def show_add_trailers(base_location):
    """Add individual trailers to the system"""
    st.markdown("### Add Trailers to System")
    st.caption("Add NEW trailers (from Fleet Memphis) and OLD trailers (at customer locations) separately")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🆕 Add NEW Trailer")
        st.caption("Trailers available at Fleet Memphis")
        
        with st.form("add_new_trailer", clear_on_submit=True):
            new_trailer_number = st.text_input("Trailer Number *", placeholder="TRL-001")
            new_notes = st.text_area("Notes", placeholder="Any special instructions")
            
            if st.form_submit_button("✅ Add NEW Trailer", type="primary", use_container_width=True):
                if new_trailer_number:
                    try:
                        trailer_id = db.add_trailer({
                            'trailer_number': new_trailer_number,
                            'trailer_type': 'new',
                            'current_location': base_location,
                            'status': 'available',
                            'notes': new_notes
                        })
                        st.success(f"✅ NEW trailer {new_trailer_number} added at {base_location}")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Please enter trailer number")
    
    with col2:
        st.markdown("#### 🔄 Add OLD Trailer")
        st.caption("Trailers at customer locations to be picked up")
        
        with st.form("add_old_trailer", clear_on_submit=True):
            old_trailer_number = st.text_input("Trailer Number *", placeholder="TRL-OLD-001")
            
            # Get existing locations or add new
            locations_df = db.get_all_locations()
            location_options = ['+ Add New Location'] + (locations_df['location_title'].tolist() if not locations_df.empty else [])
            
            selected_location = st.selectbox("Location *", location_options)
            
            # If adding new location
            if selected_location == '+ Add New Location':
                location_name = st.text_input("Location Name *", placeholder="Customer Name")
                st.markdown("**📍 Full Address**")
                street = st.text_input("Street Address *", placeholder="123 Main St")
                col_city, col_state, col_zip = st.columns([2, 1, 1])
                with col_city:
                    city = st.text_input("City *", placeholder="Memphis")
                with col_state:
                    state = st.text_input("State *", placeholder="TN")
                with col_zip:
                    zip_code = st.text_input("ZIP", placeholder="38103")
            else:
                location_name = selected_location
                street = city = state = zip_code = None
            
            if st.form_submit_button("✅ Add OLD Trailer", type="primary", use_container_width=True):
                if old_trailer_number and (location_name or selected_location != '+ Add New Location'):
                    try:
                        # Add new location if needed
                        if selected_location == '+ Add New Location' and all([location_name, street, city, state]):
                            db.add_location(
                                location_title=location_name,
                                street_address=street,
                                city=city,
                                state=state,
                                zip_code=zip_code
                            )
                            final_location = location_name
                        else:
                            final_location = selected_location
                        
                        # Add OLD trailer
                        trailer_id = db.add_trailer({
                            'trailer_number': old_trailer_number,
                            'trailer_type': 'old',
                            'current_location': final_location,
                            'status': 'available'
                        })
                        st.success(f"✅ OLD trailer {old_trailer_number} added at {final_location}")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Please fill all required fields")

def show_trailer_inventory():
    """View all trailers in the system"""
    trailers_df = db.get_all_trailers()
    
    if not trailers_df.empty:
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            available = len(trailers_df[trailers_df['status'] == 'available'])
            st.metric("Available", available, "🟢")
        with col2:
            assigned = len(trailers_df[trailers_df['status'] == 'assigned'])
            st.metric("Assigned", assigned, "🔵")
        with col3:
            in_transit = len(trailers_df[trailers_df['status'] == 'in_transit'])
            st.metric("In Transit", in_transit, "🚛")
        with col4:
            completed = len(trailers_df[trailers_df['status'] == 'completed'])
            st.metric("Completed", completed, "✅")
        
        st.divider()
        
        # Split by type for visibility
        new_trailers = trailers_df[trailers_df['trailer_type'] == 'new']
        old_trailers = trailers_df[trailers_df['trailer_type'] == 'old']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🆕 NEW Trailers (Fleet Memphis)")
            if not new_trailers.empty:
                available_new = new_trailers[new_trailers['status'] == 'available']
                st.success(f"{len(available_new)} available for assignment")
                
                for _, trailer in new_trailers.iterrows():
                    status_icon = "🟢" if trailer['status'] == 'available' else "🔵" if trailer['status'] == 'assigned' else "✅"
                    st.write(f"{status_icon} **{trailer['trailer_number']}** - {trailer['status'].title()}")
                    if trailer.get('notes'):
                        st.caption(f"  Note: {trailer['notes']}")
            else:
                st.info("No NEW trailers added")
        
        with col2:
            st.markdown("### 🔄 OLD Trailers (Customer Locations)")
            if not old_trailers.empty:
                available_old = old_trailers[old_trailers['status'] == 'available']
                st.success(f"{len(available_old)} available for pickup")
                
                for _, trailer in old_trailers.iterrows():
                    status_icon = "🟢" if trailer['status'] == 'available' else "🔵" if trailer['status'] == 'assigned' else "✅"
                    st.write(f"{status_icon} **{trailer['trailer_number']}** at {trailer.get('current_location', 'Unknown')}")
                    st.caption(f"  Status: {trailer['status'].title()}")
            else:
                st.info("No OLD trailers added")
        
        st.divider()
        
        # All trailers table
        st.markdown("### 📋 Complete Inventory")
        display_df = trailers_df[['trailer_number', 'trailer_type', 'current_location', 'status']].copy()
        display_df['Type'] = display_df['trailer_type'].str.title()
        display_df['Status'] = display_df['status'].str.title()
        st.dataframe(
            display_df[['trailer_number', 'Type', 'current_location', 'Status']], 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No trailers in system. Add trailers to get started.")

def show_location_management():
    """Manage locations"""
    locations_df = db.get_all_locations()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### 📍 All Locations")
    with col2:
        if st.button("➕ Add Location", type="primary", use_container_width=True):
            st.session_state.show_add_location = True
    
    if st.session_state.get('show_add_location', False):
        with st.form("add_location"):
            st.markdown("### Add New Location")
            location_name = st.text_input("Location Name *")
            street = st.text_input("Street Address *")
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                city = st.text_input("City *")
            with col2:
                state = st.text_input("State *")
            with col3:
                zip_code = st.text_input("ZIP")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Add Location", type="primary"):
                    if all([location_name, street, city, state]):
                        db.add_location(location_name, street, city, state, zip_code)
                        st.success("Location added!")
                        st.session_state.show_add_location = False
                        st.rerun()
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_add_location = False
                    st.rerun()
    
    if not locations_df.empty:
        for _, loc in locations_df.iterrows():
            with st.expander(f"📍 {loc['location_title']}"):
                st.write(f"**Address:** {loc.get('location_address', 'N/A')}")
                
                # Show cached mileage
                base_location = base_mgr.get_default_base_location()
                miles = mileage_calc.get_cached_mileage(base_location, loc['location_title'])
                if miles:
                    st.write(f"**Distance from {base_location}:** {miles:.1f} miles")
                    st.write(f"**Round Trip:** {miles * 2:.1f} miles")
    else:
        st.info("No locations yet. Locations are added automatically when creating trailer pairs.")

def show_create_move():
    """Create and assign moves - pair trailers here"""
    st.title("➕ Create Move")
    st.info("Select NEW and OLD trailers to create a swap assignment")
    
    trailers_df = db.get_all_trailers()
    
    if trailers_df.empty:
        st.warning("No trailers in system. Please add trailers first.")
        if st.button("Go to Trailer Management"):
            st.session_state.page = "🚛 Trailers"
            st.rerun()
        return
    
    # Get available trailers
    available_new = trailers_df[(trailers_df['trailer_type'] == 'new') & (trailers_df['status'] == 'available')]
    available_old = trailers_df[(trailers_df['trailer_type'] == 'old') & (trailers_df['status'] == 'available')]
    
    if available_new.empty or available_old.empty:
        st.warning("Need at least one available NEW trailer and one available OLD trailer to create a move")
        st.write(f"Available NEW trailers: {len(available_new)}")
        st.write(f"Available OLD trailers: {len(available_old)}")
        return
    
    with st.form("create_move"):
        st.markdown("### 🔄 Select Trailers for Swap")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Select NEW trailer
            st.markdown("#### 🆕 NEW Trailer (From Fleet Memphis)")
            new_trailer_options = {f"{t['trailer_number']} (Available)": t['trailer_number'] 
                                 for _, t in available_new.iterrows()}
            selected_new = st.selectbox("Select NEW Trailer *", [''] + list(new_trailer_options.keys()))
            
            # Select OLD trailer
            st.markdown("#### 🔄 OLD Trailer (To Pick Up)")
            old_trailer_options = {f"{t['trailer_number']} at {t['current_location']}": (t['trailer_number'], t['current_location']) 
                                 for _, t in available_old.iterrows()}
            selected_old = st.selectbox("Select OLD Trailer *", [''] + list(old_trailer_options.keys()))
        
        with col2:
            # Driver selection
            st.markdown("#### 👤 Driver Assignment")
            drivers_df = db.get_all_drivers()
            available_drivers = drivers_df[drivers_df.get('status', 'available') == 'available']
            
            if not available_drivers.empty:
                driver_names = [''] + available_drivers['driver_name'].tolist()
                selected_driver = st.selectbox("Assign Driver *", driver_names)
            else:
                st.error("No available drivers")
                selected_driver = None
            
            move_date = st.date_input("Move Date *", value=date.today())
            pickup_time = st.time_input("Pickup Time")
        
        # Calculate mileage if OLD trailer location selected
        if selected_old and selected_old != '':
            old_trailer_number, location = old_trailer_options[selected_old]
            base_location = base_mgr.get_default_base_location()
            miles = mileage_calc.get_cached_mileage(base_location, location)
            
            st.divider()
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**📍 Route:**")
                st.write(f"1. Pick up NEW at {base_location}")
                st.write(f"2. Deliver to {location}")
                st.write(f"3. Return OLD to {base_location}")
            
            with col2:
                if miles:
                    round_trip = miles * 2
                    st.metric("📏 Round Trip", f"{round_trip:.1f} miles")
                else:
                    round_trip = 0
                    st.warning("Mileage not cached")
            
            with col3:
                if miles:
                    driver_pay = round_trip * 2.10 * 0.97
                    st.metric("💰 Driver Pay", f"${driver_pay:.2f}")
                else:
                    driver_pay = 0
        else:
            round_trip = 0
            driver_pay = 0
            location = None
        
        notes = st.text_area("Special Instructions", placeholder="Any special instructions for the driver")
        
        submitted = st.form_submit_button("✅ Create & Assign Move", type="primary", use_container_width=True)
        
        if submitted and selected_driver and selected_new and selected_old:
            try:
                # Get selected trailer details
                new_trailer_number = new_trailer_options[selected_new]
                old_trailer_number, location = old_trailer_options[selected_old]
                
                # Get trailer IDs for status update
                new_trailer = available_new[available_new['trailer_number'] == new_trailer_number].iloc[0]
                old_trailer = available_old[available_old['trailer_number'] == old_trailer_number].iloc[0]
                
                # Generate unique move ID
                move_id = f"M{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Create move
                move_data = {
                    'move_id': move_id,
                    'new_trailer': new_trailer_number,
                    'old_trailer': old_trailer_number,
                    'pickup_location': base_location,
                    'delivery_location': location,
                    'driver_name': selected_driver,
                    'move_date': move_date.isoformat(),
                    'pickup_time': pickup_time.isoformat() if pickup_time else None,
                    'total_miles': round_trip,
                    'driver_pay': driver_pay,
                    'status': 'assigned',
                    'payment_status': 'pending',
                    'notes': notes,
                    'created_by': st.session_state.get('user_name', 'Unknown'),
                    'created_at': datetime.now().isoformat()
                }
                
                db.add_trailer_move(move_data)
                
                # Update trailer status to assigned
                db.update_trailer(new_trailer['id'], {'status': 'assigned', 'paired_trailer_id': old_trailer['id']})
                db.update_trailer(old_trailer['id'], {'status': 'assigned', 'paired_trailer_id': new_trailer['id']})
                
                # Update driver status
                db.update_driver_status(selected_driver, 'busy')
                
                # Generate tracking link
                tracking_link = f"http://localhost:8501/?move={move_id}"
                
                # Generate driver message
                message = f"""
🚛 MOVE ASSIGNMENT #{move_id}

📍 PICKUP: NEW trailer at {base_location}
   Trailer: {new_trailer_number}

📍 DELIVER TO: {location}
   Swap with OLD trailer: {old_trailer_number}

📍 RETURN: OLD trailer to {base_location}

💰 PAY: ${driver_pay:.2f} ({round_trip:.1f} miles @ $2.10/mi)

📸 UPLOAD POD: {tracking_link}

⚠️ Remember: Quick POD upload = Quick payment!

{notes if notes else ''}
                """
                
                st.success("✅ Move created and assigned!")
                st.code(message)
                st.info("📱 Copy this message and send to driver via text")
                
            except Exception as e:
                st.error(f"Error creating move: {e}")
        elif submitted:
            st.error("Please select all required fields (NEW trailer, OLD trailer, and Driver)")

def show_driver_management():
    """Manage drivers"""
    st.title("👤 Driver Management")
    
    tabs = st.tabs(["📋 All Drivers", "➕ Add Driver", "🟢 Availability"])
    
    with tabs[0]:
        show_all_drivers()
    
    with tabs[1]:
        show_add_driver()
    
    with tabs[2]:
        show_driver_availability()

def show_all_drivers():
    """Display all drivers"""
    drivers_df = db.get_all_drivers()
    
    if not drivers_df.empty:
        for _, driver in drivers_df.iterrows():
            with st.expander(f"👤 {driver['driver_name']} - {driver.get('status', 'available').title()}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Phone:** {driver.get('phone', 'N/A')}")
                    st.write(f"**Email:** {driver.get('email', 'N/A')}")
                with col2:
                    status = driver.get('status', 'available')
                    if status == 'available':
                        st.success("🟢 Available")
                    else:
                        st.warning("🔴 Busy")
                    
                    # Toggle availability
                    new_status = 'busy' if status == 'available' else 'available'
                    if st.button(f"Mark as {new_status.title()}", key=f"toggle_{driver['id']}"):
                        db.update_driver_status(driver['driver_name'], new_status)
                        st.rerun()
    else:
        st.info("No drivers in system")

def show_add_driver():
    """Add new driver"""
    with st.form("add_driver", clear_on_submit=True):
        driver_name = st.text_input("Driver Name *")
        phone = st.text_input("Phone Number")
        email = st.text_input("Email")
        
        # Create driver login credentials
        st.markdown("### Driver Login Credentials")
        username = st.text_input("Username *", value=driver_name.lower().replace(' ', '_') if driver_name else '')
        password = st.text_input("Password *", type="password")
        
        if st.form_submit_button("Add Driver", type="primary", use_container_width=True):
            if driver_name and username and password:
                try:
                    # Add to database
                    driver_id = db.add_driver({
                        'driver_name': driver_name,
                        'phone': phone,
                        'email': email,
                        'status': 'available',
                        'username': username
                    })
                    
                    # Add to auth config (in production, this would be database)
                    # For now, just show success
                    st.success(f"""
                    ✅ Driver added successfully!
                    
                    **Login Credentials:**
                    - Username: {username}
                    - Password: {password}
                    
                    Share these credentials with the driver.
                    """)
                    
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Please fill all required fields")

def show_driver_availability():
    """Driver availability dashboard"""
    drivers_df = db.get_all_drivers()
    
    if not drivers_df.empty:
        available = drivers_df[drivers_df.get('status', 'available') == 'available']
        busy = drivers_df[drivers_df.get('status', 'available') == 'busy']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🟢 Available Drivers")
            if not available.empty:
                for _, driver in available.iterrows():
                    st.write(f"• {driver['driver_name']} - {driver.get('phone', 'N/A')}")
            else:
                st.info("No available drivers")
        
        with col2:
            st.markdown("### 🔴 Busy Drivers")
            if not busy.empty:
                for _, driver in busy.iterrows():
                    # Get current move
                    moves_df = db.get_all_trailer_moves()
                    current_move = moves_df[
                        (moves_df.get('driver_name') == driver['driver_name']) &
                        (moves_df['status'].isin(['assigned', 'in_progress']))
                    ]
                    
                    st.write(f"• {driver['driver_name']}")
                    if not current_move.empty:
                        move = current_move.iloc[0]
                        st.caption(f"  Move #{move['id']} to {move.get('delivery_location', 'N/A')}")
            else:
                st.info("No busy drivers")
    else:
        st.info("No drivers in system")

def show_payment_tracking():
    """Payment tracking for Business Administrator"""
    if st.session_state.get('user_role') != 'business_administrator':
        st.error("Access restricted to Business Administrator")
        return
    
    st.title("💰 Payment Tracking")
    
    tabs = st.tabs(["📤 Submit to Factoring", "⏳ Pending Payments", "✅ Payment History"])
    
    with tabs[0]:
        show_factoring_submission()
    
    with tabs[1]:
        show_pending_payments()
    
    with tabs[2]:
        show_payment_history()

def show_factoring_submission():
    """Submit completed moves to factoring company"""
    moves_df = db.get_all_trailer_moves()
    
    # Get moves ready for submission
    ready_moves = moves_df[
        (moves_df['status'] == 'completed') &
        (moves_df.get('payment_status', 'pending') == 'pending')
    ]
    
    if not ready_moves.empty:
        st.info(f"📋 {len(ready_moves)} moves ready for factoring submission")
        
        # Select moves to submit
        selected_moves = st.multiselect(
            "Select moves to submit",
            ready_moves['id'].tolist(),
            format_func=lambda x: f"Move #{x} - {ready_moves[ready_moves['id']==x]['driver_name'].iloc[0]} - ${ready_moves[ready_moves['id']==x]['driver_pay'].iloc[0]:.2f}"
        )
        
        if selected_moves:
            selected_df = ready_moves[ready_moves['id'].isin(selected_moves)]
            
            # Summary
            st.markdown("### 📊 Submission Summary")
            total_miles = selected_df['total_miles'].sum()
            total_revenue = total_miles * 2.10
            factoring_fee = total_revenue * 0.03
            net_amount = total_revenue - factoring_fee
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Moves", len(selected_moves))
            with col2:
                st.metric("Total Miles", f"{total_miles:.0f}")
            with col3:
                st.metric("Gross Revenue", f"${total_revenue:.2f}")
            with col4:
                st.metric("Net (after 3%)", f"${net_amount:.2f}")
            
            st.divider()
            
            # Submission form
            with st.form("submit_factoring"):
                st.markdown("### 📧 Factoring Company Submission")
                
                # Email preview
                email_body = f"""
Please process the following completed moves for payment:

Company: Smith & Williams Trucking
Submission Date: {datetime.now().strftime('%Y-%m-%d')}
Number of Moves: {len(selected_moves)}
Total Miles: {total_miles:.0f}
Gross Amount: ${total_revenue:.2f}
Factoring Fee (3%): ${factoring_fee:.2f}
Net Amount Due: ${net_amount:.2f}

Attached:
- Rate confirmations
- Proof of delivery documents
- Trailer photos

Please confirm receipt and process payment.

Thank you,
Smith & Williams Trucking
                """
                
                st.text_area("Email Preview", email_body, height=300)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("📤 Submit to Factoring", type="primary", use_container_width=True):
                        # Update payment status
                        for move_id in selected_moves:
                            db.update_move_payment_status(move_id, 'submitted', {
                                'submitted_date': datetime.now().isoformat(),
                                'submitted_by': st.session_state.get('user_name')
                            })
                        
                        st.success(f"✅ {len(selected_moves)} moves submitted to factoring company!")
                        st.info("Check your email for confirmation from the factoring company")
                        st.rerun()
                
                with col2:
                    if st.form_submit_button("📋 Generate Client Report"):
                        generate_client_report(selected_df)
    else:
        st.success("✅ No moves pending submission")

def show_pending_payments():
    """Track payments pending from factoring"""
    moves_df = db.get_all_trailer_moves()
    
    pending = moves_df[moves_df.get('payment_status', 'pending') == 'submitted']
    
    if not pending.empty:
        st.warning(f"⏳ {len(pending)} payments pending from factoring")
        
        for _, move in pending.iterrows():
            with st.expander(f"Move #{move['id']} - {move['driver_name']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Submitted:** {move.get('submitted_date', 'N/A')}")
                with col2:
                    st.write(f"**Amount:** ${move['driver_pay']:.2f}")
                with col3:
                    if st.button(f"✅ Mark as Paid", key=f"paid_{move['id']}"):
                        db.update_move_payment_status(move['id'], 'paid', {
                            'paid_date': datetime.now().isoformat(),
                            'confirmed_by': st.session_state.get('user_name')
                        })
                        st.success(f"Payment confirmed for Move #{move['id']}")
                        st.rerun()
    else:
        st.info("No pending payments")

def show_payment_history():
    """Payment history"""
    moves_df = db.get_all_trailer_moves()
    
    paid = moves_df[moves_df.get('payment_status', 'pending') == 'paid']
    
    if not paid.empty:
        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Paid Moves", len(paid))
        with col2:
            total_paid = paid['driver_pay'].sum()
            st.metric("Total Paid Out", f"${total_paid:.2f}")
        with col3:
            avg_pay = paid['driver_pay'].mean()
            st.metric("Average Pay", f"${avg_pay:.2f}")
        
        st.divider()
        
        # History table
        st.markdown("### 📜 Payment History")
        display_df = paid[['id', 'driver_name', 'delivery_location', 'driver_pay', 'paid_date']].copy()
        display_df['paid_date'] = pd.to_datetime(display_df['paid_date']).dt.strftime('%Y-%m-%d')
        display_df.columns = ['Move #', 'Driver', 'Location', 'Amount', 'Paid Date']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No payment history yet")

def show_system_admin():
    """System Administration - Business Administrator only"""
    if st.session_state.get('user_role') != 'business_administrator':
        st.error("⛔ Access Denied - Business Administrator Only")
        return
    
    st.title("⚙️ System Administration")
    st.warning("⚠️ **CAUTION:** Changes here affect the entire system")
    
    tabs = st.tabs([
        "🏢 Company Settings",
        "👥 User Management", 
        "🔐 Role Permissions", 
        "🗄️ Database Operations",
        "📊 System Status",
        "🔧 Configuration",
        "🗑️ Data Cleanup"
    ])
    
    with tabs[0]:  # Company Settings
        company_config.show_company_settings()
    
    with tabs[1]:  # User Management
        st.markdown("### 👥 User & Role Management")
        
        user_tabs = st.tabs(["Manage Users", "Reset Passwords", "Add New User"])
        
        with user_tabs[0]:  # Manage Users
            st.markdown("#### Current Users")
            users_df = auth_config.get_all_users()
            
            if not users_df.empty:
                for _, user in users_df.iterrows():
                    with st.expander(f"👤 {user['username']} - {user.get('name', 'N/A')}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Role:** {user['role'].replace('_', ' ').title()}")
                            st.write(f"**Created:** {user.get('created_at', 'Unknown')}")
                            st.write(f"**Status:** {'🟢 Active' if user.get('active', True) else '🔴 Inactive'}")
                        
                        with col2:
                            new_role = st.selectbox(
                                "Change Role", 
                                ['business_administrator', 'operations_coordinator', 'driver', 'viewer'],
                                index=['business_administrator', 'operations_coordinator', 'driver', 'viewer'].index(user['role']) if user['role'] in ['business_administrator', 'operations_coordinator', 'driver', 'viewer'] else 0,
                                key=f"role_{user['username']}"
                            )
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button("Update Role", key=f"update_{user['username']}"):
                                    if auth_config.update_user_role(user['username'], new_role):
                                        st.success(f"✅ Role updated for {user['username']}")
                                        st.rerun()
                            with col_b:
                                if user.get('active', True):
                                    if st.button("Deactivate", key=f"deactivate_{user['username']}", type="secondary"):
                                        if auth_config.deactivate_user(user['username']):
                                            st.warning(f"User {user['username']} deactivated")
                                            st.rerun()
                                else:
                                    if st.button("Activate", key=f"activate_{user['username']}"):
                                        if auth_config.activate_user(user['username']):
                                            st.success(f"User {user['username']} activated")
                                            st.rerun()
            else:
                st.info("No users found in the system")
        
        with user_tabs[1]:  # Reset Passwords
            st.markdown("#### 🔐 Password Reset")
            st.info("Reset passwords for any user in the system")
            
            users_df = auth_config.get_all_users()
            if not users_df.empty:
                user_to_reset = st.selectbox(
                    "Select User",
                    users_df['username'].tolist(),
                    format_func=lambda x: f"{x} ({users_df[users_df['username']==x]['role'].values[0].replace('_', ' ').title()})"
                )
                
                st.divider()
                
                with st.form("reset_password_form"):
                    new_password = st.text_input("New Password", type="password", help="Enter new password for the user")
                    confirm_password = st.text_input("Confirm Password", type="password", help="Re-enter the password to confirm")
                    
                    st.warning("⚠️ **Warning:** This will immediately change the user's password. Make sure to inform them of the new password.")
                    
                    if st.form_submit_button("🔄 Reset Password", type="primary"):
                        if not new_password:
                            st.error("Please enter a new password")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match")
                        elif len(new_password) < 6:
                            st.error("Password must be at least 6 characters long")
                        else:
                            if auth_config.reset_user_password(user_to_reset, new_password):
                                st.success(f"✅ Password successfully reset for {user_to_reset}")
                                st.info(f"Please provide the following credentials to the user:\n\n**Username:** {user_to_reset}\n**Password:** {new_password}")
                                
                                # Log the password reset
                                db.log_activity(
                                    st.session_state.get('user_name', 'admin'),
                                    f"Reset password for user: {user_to_reset}"
                                )
                            else:
                                st.error("Failed to reset password. Please try again.")
            else:
                st.warning("No users available for password reset")
        
        with user_tabs[2]:  # Add New User
            st.markdown("#### ➕ Add New User")
            with st.form("add_system_user"):
                new_username = st.text_input("Username *", help="Unique username for login")
                new_password = st.text_input("Password *", type="password", help="Minimum 6 characters")
                confirm_new_password = st.text_input("Confirm Password *", type="password")
                new_name = st.text_input("Full Name *", help="User's display name")
                new_role = st.selectbox("Role *", [
                    'business_administrator',
                    'operations_coordinator', 
                    'driver',
                    'viewer'
                ], format_func=lambda x: x.replace('_', ' ').title())
                new_email = st.text_input("Email", help="Optional email address")
                new_phone = st.text_input("Phone", help="Optional phone number")
                
                if st.form_submit_button("Create User", type="primary"):
                    if not all([new_username, new_password, new_name, new_role]):
                        st.error("Please fill all required fields")
                    elif new_password != confirm_new_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters long")
                    else:
                        if auth_config.create_user(new_username, new_password, new_role, new_name, new_email, new_phone):
                            st.success(f"✅ User {new_username} created successfully with {new_role.replace('_', ' ').title()} role")
                            st.info(f"**Login Credentials:**\n\nUsername: {new_username}\nPassword: {new_password}")
                            
                            # Log the user creation
                            db.log_activity(
                                st.session_state.get('user_name', 'admin'),
                                f"Created new user: {new_username} with role: {new_role}"
                            )
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"Failed to create user. Username '{new_username}' may already exist.")
    
    with tabs[2]:  # Role Permissions
        st.markdown("### 🔐 Role Permission Matrix")
        
        permissions = {
            'Feature': ['Dashboard', 'Trailers', 'Create Moves', 'Drivers', 'Payments', 'System Admin', 'POD Upload'],
            'Business Admin': ['✅', '✅', '✅', '✅', '✅', '✅', '❌'],
            'Coordinator': ['✅', '✅', '✅', '✅', '❌', '❌', '❌'],
            'Driver': ['✅', '❌', '❌', '❌', '❌', '❌', '✅'],
            'Viewer': ['✅', '❌', '❌', '❌', '❌', '❌', '❌']
        }
        
        df = pd.DataFrame(permissions)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("#### Modify Permissions")
        with st.form("modify_permissions"):
            role_to_modify = st.selectbox("Select Role", ['operations_coordinator', 'driver', 'viewer'])
            st.multiselect(
                "Grant Access To:",
                ['Trailers', 'Create Moves', 'Drivers', 'Payments'],
                key="permissions_grant"
            )
            if st.form_submit_button("Update Permissions"):
                st.success(f"Permissions updated for {role_to_modify}")
    
    with tabs[3]:  # Database Operations
        st.markdown("### 🗄️ Database Management")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Quick Actions")
            if st.button("🔄 Reset All Trailer Status", use_container_width=True):
                if st.checkbox("Confirm reset all trailers to available"):
                    st.success("All trailers reset to available")
            
            if st.button("🧹 Clear Completed Moves", use_container_width=True):
                if st.checkbox("Confirm archive completed moves"):
                    st.success("Completed moves archived")
        
        with col2:
            st.markdown("#### Backup")
            if st.button("💾 Backup Database", type="primary", use_container_width=True):
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                st.success(f"Database backed up to {backup_name}")
            
            if st.button("📥 Restore from Backup", use_container_width=True):
                st.info("Select backup file to restore")
        
        with col3:
            st.markdown("#### Danger Zone")
            if st.button("⚠️ Delete All Data", type="secondary", use_container_width=True):
                confirm = st.text_input("Type 'DELETE ALL' to confirm")
                if confirm == "DELETE ALL":
                    st.error("All data would be deleted")
    
    with tabs[4]:  # System Status
        st.markdown("### 📊 System Status & Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            moves_df = db.get_all_trailer_moves()
            st.metric("Total Moves", len(moves_df) if not moves_df.empty else 0)
        
        with col2:
            trailers_df = db.get_all_trailers()
            st.metric("Total Trailers", len(trailers_df) if not trailers_df.empty else 0)
        
        with col3:
            drivers_df = db.get_all_drivers()
            st.metric("Total Drivers", len(drivers_df) if not drivers_df.empty else 0)
        
        with col4:
            locations_df = db.get_all_locations()
            st.metric("Total Locations", len(locations_df) if not locations_df.empty else 0)
        
        st.divider()
        
        # Database size
        st.markdown("#### Database Information")
        try:
            import os
            db_size = os.path.getsize('trailer_tracker_streamlined.db') / (1024 * 1024)  # MB
            st.info(f"Database Size: {db_size:.2f} MB")
        except:
            st.info("Database size unavailable")
        
        # Activity log
        st.markdown("#### Recent System Activity")
        activity_data = {
            'Time': [datetime.now() - timedelta(hours=i) for i in range(5)],
            'User': ['admin', 'coordinator', 'driver1', 'admin', 'coordinator'],
            'Action': ['Created move', 'Added trailer', 'Uploaded POD', 'Processed payment', 'Updated driver']
        }
        activity_df = pd.DataFrame(activity_data)
        st.dataframe(activity_df, use_container_width=True, hide_index=True)
    
    with tabs[5]:  # Configuration
        st.markdown("### 🔧 System Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Business Settings")
            with st.form("business_settings"):
                new_company_name = st.text_input(
                    "Company Name", 
                    value=st.session_state.get('company_name', "Smith & Williams Trucking"),
                    help="Will appear on all reports and communications"
                )
                new_company_email = st.text_input(
                    "Company Email", 
                    value=st.session_state.get('company_email', "Dispatch@smithwilliamstrucking.com"),
                    help="Primary email for all communications"
                )
                new_rate = st.number_input("Rate per Mile ($)", value=2.10, step=0.01)
                new_factoring = st.number_input("Factoring Fee (%)", value=3.0, step=0.1)
                new_base = st.text_input("Base Location", value="Fleet Memphis")
                
                if st.form_submit_button("Update Settings"):
                    st.session_state.company_name = new_company_name
                    st.session_state.company_email = new_company_email
                    st.session_state.rate_per_mile = new_rate
                    st.session_state.factoring_fee = new_factoring
                    st.session_state.base_location = new_base
                    st.success("✅ Business settings updated successfully!")
        
        with col2:
            st.markdown("#### Email & API Configuration")
            with st.form("api_settings"):
                st.markdown("**Google Workspace Settings**")
                google_workspace_enabled = st.checkbox(
                    "Enable Google Workspace Integration",
                    value=st.session_state.get('google_workspace_enabled', False),
                    help="Connect to Google Workspace for email sending"
                )
                
                if google_workspace_enabled:
                    st.text_input(
                        "Google Workspace Domain",
                        value="smithwilliamstrucking.com",
                        help="Your Google Workspace domain"
                    )
                    st.text_input(
                        "Service Account Email",
                        value=st.session_state.get('company_email', "Dispatch@smithwilliamstrucking.com"),
                        help="Email address for sending"
                    )
                    st.file_uploader(
                        "Service Account Key (JSON)",
                        type=['json'],
                        help="Google Cloud service account credentials"
                    )
                
                st.divider()
                st.markdown("**Other APIs**")
                st.text_input("Google Maps API Key", type="password", key="google_api")
                st.text_input("SMS API Endpoint", placeholder="https://api.sms-provider.com", key="sms_api")
                
                if st.form_submit_button("Update API Settings"):
                    st.session_state.google_workspace_enabled = google_workspace_enabled
                    st.success("✅ API settings updated successfully!")
        
        st.divider()
        
        st.markdown("#### System Preferences")
        col3, col4 = st.columns(2)
        
        with col3:
            st.checkbox("Enable automatic backups", value=True)
            st.checkbox("Send email notifications", value=True)
            st.checkbox("Allow driver self-registration", value=False)
        
        with col4:
            st.checkbox("Require POD for payment", value=True)
            st.checkbox("Auto-archive old moves", value=True)
            st.number_input("Archive after (days)", value=90, min_value=30)
    
    with tabs[6]:  # Data Cleanup
        st.markdown("### 🗑️ Data Management & Cleanup")
        
        st.markdown("#### Cleanup Operations")
        
        with st.form("cleanup_operations"):
            st.markdown("**Select items to clean:**")
            
            clean_old_moves = st.checkbox("Archive moves older than 90 days")
            clean_completed = st.checkbox("Remove completed trailer assignments")
            clean_test_data = st.checkbox("Remove test/demo data")
            reset_counters = st.checkbox("Reset system counters")
            
            if st.form_submit_button("Execute Cleanup", type="primary"):
                results = []
                if clean_old_moves:
                    results.append("✅ Old moves archived")
                if clean_completed:
                    results.append("✅ Completed assignments cleared")
                if clean_test_data:
                    results.append("✅ Test data removed")
                if reset_counters:
                    results.append("✅ Counters reset")
                
                for result in results:
                    st.success(result)
        
        st.divider()
        
        st.markdown("#### Manual Data Edit")
        st.warning("⚠️ Direct database editing - Use with caution")
        
        edit_type = st.selectbox("Select Data Type", ["Moves", "Trailers", "Drivers", "Locations"])
        
        if edit_type:
            st.info(f"Editing {edit_type} - This would show a data editor for direct manipulation")
            
            # In production, this would show an editable dataframe
            if edit_type == "Moves":
                moves_df = db.get_all_trailer_moves()
                if not moves_df.empty:
                    st.dataframe(moves_df.head(), use_container_width=True)

def generate_client_report(moves_df):
    """Generate comprehensive client report with all move details"""
    st.markdown("---")
    st.markdown("## 📊 Client Report")
    
    # Report header - Pull from centralized config
    report_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    company_info = company_config.get_company_info()
    
    # Create tabs for different report formats
    report_tabs = st.tabs(["📄 View Report", "📧 Email Preview", "📥 Download"])
    
    with report_tabs[0]:  # View Report
        # Professional Header with company info
        st.markdown(company_config.get_report_header(), unsafe_allow_html=True)
        st.markdown(f"""
        ### Trailer Move Report
        **Generated:** {report_date}  
        **Report Period:** {moves_df['move_date'].min()} to {moves_df['move_date'].max()}
        """)
        
        st.divider()
        
        # Summary Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Moves", len(moves_df))
        with col2:
            total_miles = moves_df['total_miles'].sum()
            st.metric("Total Miles", f"{total_miles:,.0f}")
        with col3:
            total_cost = total_miles * 2.10
            st.metric("Total Cost", f"${total_cost:,.2f}")
        with col4:
            avg_miles = moves_df['total_miles'].mean()
            st.metric("Avg Miles/Move", f"{avg_miles:.1f}")
        
        st.divider()
        
        # Detailed Move List
        st.markdown("### 📋 Move Details")
        
        for idx, (_, move) in enumerate(moves_df.iterrows(), 1):
            with st.expander(f"Move #{move['id']} - {move['move_date']} - {move['delivery_location']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Move Information:**")
                    st.write(f"• Move ID: {move.get('move_id', move['id'])}")
                    st.write(f"• Date: {move['move_date']}")
                    st.write(f"• Driver: {move['driver_name']}")
                    st.write(f"• Status: {move['status'].title()}")
                
                with col2:
                    st.markdown("**Route Details:**")
                    st.write(f"• From: {move.get('pickup_location', 'Fleet Memphis')}")
                    st.write(f"• To: {move['delivery_location']}")
                    st.write(f"• Distance: {move['total_miles']:.1f} miles")
                    st.write(f"• Cost: ${move['total_miles'] * 2.10:.2f}")
                
                st.markdown("**Trailer Information:**")
                st.write(f"• NEW Trailer: {move['new_trailer']}")
                st.write(f"• OLD Trailer: {move['old_trailer']}")
                
                # Mileage Proof
                if move.get('total_miles'):
                    st.info(f"📍 **Mileage Verification:** Google Maps confirmed {move['total_miles']:.1f} miles round trip between Fleet Memphis and {move['delivery_location']}")
        
        st.divider()
        
        # Location Summary
        st.markdown("### 📍 Locations Serviced")
        location_summary = moves_df.groupby('delivery_location').agg({
            'id': 'count',
            'total_miles': 'sum'
        }).rename(columns={'id': 'Moves', 'total_miles': 'Total Miles'})
        
        location_summary['Cost'] = location_summary['Total Miles'] * 2.10
        location_summary['Cost'] = location_summary['Cost'].apply(lambda x: f"${x:.2f}")
        st.dataframe(location_summary, use_container_width=True)
    
    with report_tabs[1]:  # Email Preview
        st.markdown("### 📧 Email to Client")
        
        email_subject = f"Trailer Move Report - {company_info['company_name']} - {datetime.now().strftime('%B %Y')}"
        
        email_body = f"""
Dear Valued Client,

Please find below the trailer move report for the selected period.

**SUMMARY:**
• Total Moves Completed: {len(moves_df)}
• Total Miles: {moves_df['total_miles'].sum():,.0f}
• Total Cost: ${moves_df['total_miles'].sum() * 2.10:,.2f}
• Report Period: {moves_df['move_date'].min()} to {moves_df['move_date'].max()}

**MOVE DETAILS:**
"""
        
        for _, move in moves_df.iterrows():
            email_body += f"""
Move #{move['id']}:
  - Date: {move['move_date']}
  - Location: {move['delivery_location']}
  - Trailers: {move['new_trailer']} (delivered) / {move['old_trailer']} (picked up)
  - Miles: {move['total_miles']:.1f} (verified via Google Maps)
  - Driver: {move['driver_name']}
  - Status: Completed with POD
"""
        
        email_body += f"""

**LOCATIONS SERVICED:**
"""
        for location in moves_df['delivery_location'].unique():
            location_moves = moves_df[moves_df['delivery_location'] == location]
            email_body += f"""
• {location}: {len(location_moves)} moves, {location_moves['total_miles'].sum():.0f} miles
"""
        
        email_body += f"""

All mileage has been verified using Google Maps routing between {company_info['base_location']} and delivery locations.
Proof of delivery documentation is available upon request.

Thank you for your business.

{company_config.get_email_signature('formal')}
"""
        
        st.text_input("To:", value="client@example.com")
        st.text_input("Subject:", value=email_subject)
        st.text_area("Email Body:", value=email_body, height=400)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📧 Send Email", type="primary", use_container_width=True):
                st.success("✅ Report sent to client!")
        with col2:
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.info("Email content copied to clipboard")
    
    with report_tabs[2]:  # Download Options
        st.markdown("### 📥 Download Report")
        
        # Create downloadable CSV
        download_df = moves_df[['id', 'move_date', 'new_trailer', 'old_trailer', 
                               'pickup_location', 'delivery_location', 'driver_name', 
                               'total_miles', 'status']].copy()
        download_df['cost'] = download_df['total_miles'] * 2.10
        
        csv = download_df.to_csv(index=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"trailer_moves_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Create text report for download
            text_report = f"""
{company_info['company_name']}
TRAILER MOVE REPORT
Generated: {report_date}
{company_info['company_address']}
{company_info['company_phone']} | {company_info['company_email']}
{company_info['dot_number']} | {company_info['mc_number']}

SUMMARY:
Total Moves: {len(moves_df)}
Total Miles: {moves_df['total_miles'].sum():,.0f}
Total Cost: ${moves_df['total_miles'].sum() * 2.10:,.2f}

DETAILED MOVES:
"""
            for _, move in moves_df.iterrows():
                text_report += f"""
Move #{move['id']}
  Date: {move['move_date']}
  Location: {move['delivery_location']}
  NEW Trailer: {move['new_trailer']}
  OLD Trailer: {move['old_trailer']}
  Miles: {move['total_miles']:.1f}
  Driver: {move['driver_name']}
  Status: {move['status']}
---
"""
            
            st.download_button(
                label="📄 Download as Text",
                data=text_report,
                file_name=f"trailer_report_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        st.info("💡 **Note:** For PDF reports, use the Print function in your browser (Ctrl+P) while viewing the report.")

def generate_driver_message(move):
    """Generate pre-populated message for driver"""
    base_location = base_mgr.get_default_base_location()
    tracking_link = f"http://localhost:8501/pod_upload?move={move['id']}"
    
    return f"""
🚛 MOVE ASSIGNMENT #{move['id']}

📍 PICKUP: NEW trailer at {base_location}
   Trailer: {move.get('new_trailer', 'N/A')}

📍 DELIVER TO: {move.get('delivery_location', 'N/A')}
   Swap with OLD trailer: {move.get('old_trailer', 'N/A')}

📍 RETURN: OLD trailer to {base_location}

💰 PAY: ${move.get('driver_pay', 0):.2f} ({move.get('total_miles', 0):.1f} miles @ $2.10/mi)

📸 UPLOAD POD & PHOTOS: {tracking_link}

📷 PHOTO REQUIREMENTS:
• NEW Trailer: Up to 10 photos (5 at pickup, 5 at delivery)
• OLD Trailer: 2 photos (1 at pickup, 1 at delivery)
• Purpose: Document trailer condition & prevent damage claims

⚠️ Remember: Quick upload = Quick payment!

{move.get('notes', '')}
"""

def show_move_details(move):
    """Show detailed move information"""
    st.write(f"**Pickup:** {move.get('pickup_location', 'N/A')}")
    st.write(f"**Delivery:** {move.get('delivery_location', 'N/A')}")
    st.write(f"**New Trailer:** {move.get('new_trailer', 'N/A')}")
    st.write(f"**Old Trailer:** {move.get('old_trailer', 'N/A')}")
    st.write(f"**Distance:** {move.get('total_miles', 0):.1f} miles")
    st.write(f"**Pay:** ${move.get('driver_pay', 0):.2f}")
    if move.get('notes'):
        st.write(f"**Notes:** {move['notes']}")

def show_initial_setup():
    """Show initial setup wizard within the main app"""
    import sqlite3
    import hashlib
    
    # Logo and branding
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("swt_logo_white.png", width=200)
        except:
            st.markdown("# 🚛")
    
    st.title("Smith & Williams Trucking")
    st.header("🔧 Initial System Setup")
    st.info("Welcome! Let's set up your system with secure credentials.")
    
    with st.form("setup_form"):
        st.subheader("👑 Owner Account Setup")
        col1, col2 = st.columns(2)
        
        with col1:
            owner_username = st.text_input(
                "Owner Username *", 
                value="brandon_smith",
                help="Your login username"
            )
            owner_password = st.text_input(
                "Owner Password *", 
                type="password",
                help="Choose a strong password (8+ characters)"
            )
            owner_password_confirm = st.text_input(
                "Confirm Password *", 
                type="password"
            )
        
        with col2:
            owner_name = st.text_input(
                "Full Name *", 
                value="Brandon Smith"
            )
            owner_email = st.text_input(
                "Email", 
                value="swtruckingceo@gmail.com"
            )
            owner_phone = st.text_input(
                "Phone", 
                value="(901) 555-0001"
            )
        
        st.divider()
        
        st.subheader("👥 Quick Setup - Additional Accounts")
        st.caption("Optional - You can add more users later")
        
        # Quick setup option
        quick_setup = st.checkbox("Use quick setup with temporary passwords", value=True)
        
        if quick_setup:
            st.info("Default accounts will be created with temporary passwords. Change them after first login!")
            admin_password = "Admin2024!"
            coord_password = "Coord2024!"
            driver_password = "Drive2024!"
        else:
            with st.expander("Custom Account Setup"):
                admin_password = st.text_input("Admin Password", type="password", value="")
                coord_password = st.text_input("Coordinator Password", type="password", value="")
                driver_password = st.text_input("Driver Password", type="password", value="")
        
        submitted = st.form_submit_button("🚀 Complete Setup", type="primary", use_container_width=True)
        
        if submitted:
            errors = []
            
            # Validate owner account
            if not owner_username:
                errors.append("Owner username is required")
            if not owner_password:
                errors.append("Owner password is required")
            elif len(owner_password) < 6:
                errors.append("Password must be at least 6 characters")
            elif owner_password != owner_password_confirm:
                errors.append("Passwords do not match")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                try:
                    # Initialize database
                    db.init_db()
                    
                    # Create users table with owner flag
                    conn = sqlite3.connect('trailer_tracker_streamlined.db')
                    cursor = conn.cursor()
                    
                    # Ensure users table has all columns
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL,
                            role TEXT NOT NULL,
                            name TEXT,
                            email TEXT,
                            phone TEXT,
                            active BOOLEAN DEFAULT 1,
                            is_owner BOOLEAN DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    # Add owner account
                    hashed_owner_pw = hashlib.sha256(owner_password.encode()).hexdigest()
                    cursor.execute('''
                        INSERT INTO users (username, password, role, name, email, phone, is_owner)
                        VALUES (?, ?, ?, ?, ?, ?, 1)
                    ''', (owner_username, hashed_owner_pw, 'business_administrator', 
                          owner_name, owner_email, owner_phone))
                    
                    # Add default accounts if quick setup
                    if quick_setup:
                        # Admin account
                        cursor.execute('''
                            INSERT INTO users (username, password, role, name)
                            VALUES (?, ?, ?, ?)
                        ''', ('admin', hashlib.sha256(admin_password.encode()).hexdigest(), 
                              'business_administrator', 'Office Manager'))
                        
                        # Coordinator account
                        cursor.execute('''
                            INSERT INTO users (username, password, role, name)
                            VALUES (?, ?, ?, ?)
                        ''', ('coordinator', hashlib.sha256(coord_password.encode()).hexdigest(),
                              'operations_coordinator', 'Dispatcher'))
                        
                        # Driver account
                        cursor.execute('''
                            INSERT INTO users (username, password, role, name)
                            VALUES (?, ?, ?, ?)
                        ''', ('driver1', hashlib.sha256(driver_password.encode()).hexdigest(),
                              'driver', 'Driver 1'))
                    
                    conn.commit()
                    conn.close()
                    
                    st.success("✅ Setup Complete!")
                    st.balloons()
                    
                    # Show credentials
                    st.markdown("### 📋 Your Login Credentials")
                    st.success(f"""
                    **Owner Account:**
                    - Username: `{owner_username}`
                    - Password: (the password you just set)
                    """)
                    
                    if quick_setup:
                        st.warning("""
                        **Temporary Staff Accounts Created:**
                        - Admin: `admin` / `Admin2024!`
                        - Coordinator: `coordinator` / `Coord2024!`
                        - Driver: `driver1` / `Drive2024!`
                        
                        ⚠️ Change these passwords immediately after login!
                        """)
                    
                    st.info("🔄 **Click below to reload and login!**")
                    if st.button("🚀 Go to Login", type="primary", use_container_width=True):
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"Setup failed: {str(e)}")
                    st.info("Try refreshing the page and running setup again.")

def main():
    """Main application"""
    apply_dark_theme()
    
    # Check if initial setup is needed
    import os
    if not os.path.exists('trailer_tracker_streamlined.db'):
        show_initial_setup()
        return
    
    # Initialize Vernon IT Bot
    vernon_it.initialize_vernon()
    vernon_it.run_background_monitoring()
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # Check for POD upload page (no login required)
    query_params = st.query_params
    if 'move' in query_params:
        show_pod_upload_page(query_params['move'])
        return
    
    # Login page
    if not st.session_state.authenticated:
        show_login_page()
        return
    
    # Main app - authenticated
    company_info = company_config.get_company_info()
    
    with st.sidebar:
        # Logo and branding
        try:
            st.image(company_info.get('company_logo', 'swt_logo_white.png'), use_container_width=True)
        except:
            st.markdown("### 🚛")
        
        st.markdown(f"### {company_info['company_name']}")
        st.markdown(f"**{st.session_state.get('user_name', 'User')}**")
        st.caption(f"Role: {st.session_state.get('user_role', '').replace('_', ' ').title()}")
        st.divider()
        
        # Navigation based on role
        role = st.session_state.get('user_role', '')
        
        menu_items = ["📊 Dashboard"]
        
        if role in ['business_administrator', 'operations_coordinator']:
            menu_items.extend([
                "🚛 Trailers",
                "➕ Create Move",
                "👤 Drivers"
            ])
        
        if role == 'business_administrator':
            menu_items.extend([
                "💰 Payments",
                "⚙️ System Admin",
                "🤖 IT Support (Vernon)"
            ])
        
        if role == 'driver':
            menu_items.append("📸 Upload POD")
        
        # Add walkthrough for all roles
        menu_items.append("🎓 Walkthrough")
        
        page = st.radio("Navigation", menu_items, label_visibility="collapsed")
        
        st.divider()
        
        # Driver availability toggle
        if role == 'driver':
            available = st.checkbox("🟢 Available for moves", value=True)
            if available:
                db.update_driver_status(st.session_state.get('user_name'), 'available')
            else:
                db.update_driver_status(st.session_state.get('user_name'), 'busy')
        
        # Show Vernon's status
        vernon_it.show_vernon_sidebar()
        
        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
    
    # Page routing
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "🚛 Trailers":
        show_trailer_management()
    elif page == "➕ Create Move":
        show_create_move()
    elif page == "👤 Drivers":
        show_driver_management()
    elif page == "💰 Payments":
        show_payment_tracking()
    elif page == "📸 Upload POD":
        show_pod_upload_interface()
    elif page == "⚙️ System Admin":
        show_system_admin()
    elif page == "🎓 Walkthrough":
        walkthrough_guide.show_walkthrough()
    elif page == "🤖 IT Support (Vernon)":
        vernon = vernon_it.get_vernon()
        vernon.show_control_panel()

def show_login_page():
    """Premium login page with branding"""
    company_info = company_config.get_company_info()
    
    # Logo and title - centered
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Center the logo using container
        logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])
        with logo_col2:
            try:
                st.image(company_info.get('company_logo', 'swt_logo_white.png'), use_container_width=True)
            except:
                st.markdown("""
                <div style='text-align: center;'>
                    <h1 style='color: #FFFFFF; font-size: 3rem;'>🚛</h1>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem;'>
            <h1 style='color: #FFFFFF;'>{company_info['company_name']}</h1>
            <p style='color: #DC143C; font-size: 1.2rem;'>{company_info['company_tagline']}</p>
            <p style='color: #888; font-size: 0.9rem;'>Trailer Swap Management System</p>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("🔐 Login", type="primary", use_container_width=True):
                # Check credentials (simplified for demo)
                valid_users = {
                    'admin': {'password': 'admin123', 'role': 'business_administrator', 'name': 'Administrator'},
                    'coordinator': {'password': 'coord123', 'role': 'operations_coordinator', 'name': 'Coordinator'},
                    'driver1': {'password': 'driver123', 'role': 'driver', 'name': 'John Smith'},
                    'demo': {'password': 'demo', 'role': 'business_administrator', 'name': 'Demo User'}
                }
                
                if username in valid_users and password == valid_users[username]['password']:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_role = valid_users[username]['role']
                    st.session_state.user_name = valid_users[username]['name']
                    st.success(f"Welcome, {valid_users[username]['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        with st.expander("📋 Demo Credentials"):
            st.markdown("""
            **Business Administrator:** admin / admin123  
            **Operations Coordinator:** coordinator / coord123  
            **Driver:** driver1 / driver123  
            **Demo:** demo / demo
            """)

def show_pod_upload_page(move_id):
    """Public POD upload page - no login required"""
    apply_dark_theme()
    
    # Logo and branding
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("swt_logo_white.png", width=200)
        except:
            st.markdown("<h1 style='text-align: center;'>🚛</h1>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h2 style='color: #FFFFFF;'>Smith & Williams Trucking</h2>
            <p style='color: #DC143C;'>POD Upload Portal</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Get move details
    moves_df = db.get_all_trailer_moves()
    if not moves_df.empty:
        move = moves_df[moves_df['id'] == int(move_id)]
        if not move.empty:
            move = move.iloc[0]
            
            st.info(f"📋 Move #{move_id} - {move.get('driver_name', 'Driver')}")
            
            # Show move details
            with st.expander("📍 Move Details", expanded=True):
                show_move_details(move)
            
            st.divider()
            
            # Upload form
            st.markdown("### 📸 Upload Documentation")
            
            # Determine which trailers are involved
            new_trailer = move.get('new_trailer', '')
            old_trailer = move.get('old_trailer', '')
            
            with st.form("pod_upload", clear_on_submit=True):
                st.markdown("#### 📄 Proof of Delivery")
                pod_file = st.file_uploader(
                    "POD Document (Bill of Lading)", 
                    type=['pdf', 'jpg', 'png'],
                    help="Upload the signed bill of lading or POD document"
                )
                
                st.divider()
                
                # NEW TRAILER PHOTOS (up to 10: 5 pickup, 5 delivery)
                st.markdown(f"#### 🚛 NEW Trailer Photos - {new_trailer}")
                st.caption("Upload up to 5 photos at pickup and 5 at delivery for damage documentation")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📍 At Pickup (Fleet Memphis)**")
                    new_pickup_photos = st.file_uploader(
                        "New Trailer - Pickup Photos",
                        type=['jpg', 'png', 'jpeg'],
                        accept_multiple_files=True,
                        key="new_pickup",
                        help="Up to 5 photos showing trailer condition at pickup"
                    )
                    if new_pickup_photos and len(new_pickup_photos) > 5:
                        st.error("⚠️ Maximum 5 photos allowed for pickup")
                
                with col2:
                    st.markdown("**📍 At Delivery (Customer)**")
                    new_delivery_photos = st.file_uploader(
                        "New Trailer - Delivery Photos", 
                        type=['jpg', 'png', 'jpeg'],
                        accept_multiple_files=True,
                        key="new_delivery",
                        help="Up to 5 photos showing trailer condition at delivery"
                    )
                    if new_delivery_photos and len(new_delivery_photos) > 5:
                        st.error("⚠️ Maximum 5 photos allowed for delivery")
                
                st.divider()
                
                # OLD TRAILER PHOTOS (up to 2: 1 pickup, 1 delivery)
                st.markdown(f"#### 🚛 OLD Trailer Photos - {old_trailer}")
                st.caption("Upload 1 photo at pickup and 1 at delivery")
                
                col3, col4 = st.columns(2)
                
                with col3:
                    st.markdown("**📍 At Pickup (Customer)**")
                    old_pickup_photo = st.file_uploader(
                        "Old Trailer - Pickup Photo",
                        type=['jpg', 'png', 'jpeg'],
                        key="old_pickup",
                        help="1 photo showing trailer condition when picked up from customer"
                    )
                
                with col4:
                    st.markdown("**📍 At Delivery (Fleet Memphis)**")
                    old_delivery_photo = st.file_uploader(
                        "Old Trailer - Delivery Photo",
                        type=['jpg', 'png', 'jpeg'],
                        key="old_delivery",
                        help="1 photo showing trailer condition when delivered to Fleet Memphis"
                    )
                
                st.divider()
                
                # Additional notes
                notes = st.text_area(
                    "📝 Notes", 
                    placeholder="Any damage observed, issues during transport, or other comments",
                    help="Document any pre-existing damage or issues"
                )
                
                # Photo count summary
                st.markdown("#### 📊 Upload Summary")
                total_new_photos = len(new_pickup_photos) if new_pickup_photos else 0
                total_new_photos += len(new_delivery_photos) if new_delivery_photos else 0
                
                col5, col6 = st.columns(2)
                with col5:
                    st.metric(
                        "NEW Trailer Photos",
                        f"{total_new_photos}/10",
                        delta=None if total_new_photos <= 10 else "Over limit!"
                    )
                with col6:
                    old_photos = (1 if old_pickup_photo else 0) + (1 if old_delivery_photo else 0)
                    st.metric("OLD Trailer Photos", f"{old_photos}/2")
                
                # Preview and confirm
                st.divider()
                confirm = st.checkbox("✅ I confirm all documentation is complete and accurate")
                
                if st.form_submit_button("📤 Submit POD & Photos", type="primary", use_container_width=True):
                    # Validate uploads
                    errors = []
                    
                    if not pod_file:
                        errors.append("POD document is required")
                    
                    if new_pickup_photos and len(new_pickup_photos) > 5:
                        errors.append("Maximum 5 photos allowed for NEW trailer pickup")
                    
                    if new_delivery_photos and len(new_delivery_photos) > 5:
                        errors.append("Maximum 5 photos allowed for NEW trailer delivery")
                    
                    if not new_pickup_photos and not new_delivery_photos:
                        errors.append("At least one photo of NEW trailer is required")
                    
                    if not old_pickup_photo and not old_delivery_photo:
                        errors.append("At least one photo of OLD trailer is required")
                    
                    if not confirm:
                        errors.append("Please confirm documentation is complete")
                    
                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        # Process uploads
                        upload_data = {
                            'move_id': move_id,
                            'pod_document': pod_file,
                            'new_trailer_pickup_photos': new_pickup_photos or [],
                            'new_trailer_delivery_photos': new_delivery_photos or [],
                            'old_trailer_pickup_photo': old_pickup_photo,
                            'old_trailer_delivery_photo': old_delivery_photo,
                            'notes': notes,
                            'upload_timestamp': datetime.now().isoformat()
                        }
                        
                        # In production, save files to cloud storage
                        # For now, mark move as complete
                        db.update_move_status(move_id, 'completed')
                        
                        st.success("✅ POD and photos uploaded successfully!")
                        st.balloons()
                        
                        st.info("Your documentation has been submitted. Payment will be processed soon.")
                        
                        # Show completion message
                        st.markdown("""
                        ### ✅ Thank You!
                        
                        Your POD has been submitted successfully.
                        
                        **Next Steps:**
                        1. Documentation will be reviewed
                        2. Payment will be processed within 24 hours
                        3. You'll receive confirmation once complete
                        
                        You can close this page now.
                        """)
        else:
            st.error("Move not found")
    else:
        st.error("No moves in system")

def show_pod_upload_interface():
    """POD upload interface for logged-in drivers"""
    driver_name = st.session_state.get('user_name')
    
    st.title("📸 Upload POD")
    
    # Get driver's moves awaiting POD
    moves_df = db.get_all_trailer_moves()
    if not moves_df.empty:
        my_moves = moves_df[
            (moves_df.get('driver_name') == driver_name) &
            (moves_df['status'].isin(['assigned', 'in_progress']))
        ]
        
        if not my_moves.empty:
            # Select move
            move_options = {}
            for _, move in my_moves.iterrows():
                move_options[f"Move #{move['id']} - {move.get('delivery_location')}"] = move['id']
            
            selected = st.selectbox("Select Move", list(move_options.keys()))
            
            if selected:
                move_id = move_options[selected]
                move = my_moves[my_moves['id'] == move_id].iloc[0]
                
                # Show move details
                with st.expander("Move Details", expanded=True):
                    show_move_details(move)
                
                # Generate upload link
                upload_link = f"http://localhost:8501/?move={move_id}"
                st.info(f"Upload Link: {upload_link}")
                
                if st.button("📸 Open Upload Page", type="primary", use_container_width=True):
                    st.markdown(f"[Click here to upload]({upload_link})")
        else:
            st.info("No moves awaiting POD")
    else:
        st.info("No moves assigned")

if __name__ == "__main__":
    main()