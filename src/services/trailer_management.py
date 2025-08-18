import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import database as db
import branding
import utils

def show_trailer_management():
    """Main trailer management page"""
    st.title("🚛 Trailer Management System")
    
    # Get trailer statistics
    stats = db.get_trailer_statistics()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Available New", stats['available_new'], delta=None)
    with col2:
        st.metric("Available Old", stats['available_old'], delta=None)
    with col3:
        st.metric("Assigned", stats['assigned'], delta=None)
    with col4:
        st.metric("Completed Today", stats['completed_today'], delta=None)
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Dashboard", 
        "➕ Add New Trailer", 
        "➕ Add Old Trailer",
        "🔄 Matched Trailers",
        "📊 History"
    ])
    
    with tab1:
        show_trailer_dashboard()
    
    with tab2:
        add_new_trailer_form()
    
    with tab3:
        add_old_trailer_form()
    
    with tab4:
        show_matched_trailers()
    
    with tab5:
        show_trailer_history()

def show_trailer_dashboard():
    """Show the main trailer dashboard with available trailers"""
    st.subheader("📋 Trailer Dashboard")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        search_query = st.text_input("🔍 Search Trailer Number", placeholder="Enter trailer number...")
    with col2:
        location_filter = st.selectbox("📍 Filter by Location", ["All"] + db.get_all_locations()['location_title'].tolist())
    with col3:
        days_filter = st.selectbox("📅 Days Available", ["All", "< 1 day", "1-3 days", "3-7 days", "> 7 days"])
    
    # Two columns for new and old trailers
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🆕 Available New Trailers")
        new_trailers = db.get_available_trailers(trailer_type='new')
        
        if not new_trailers.empty:
            # Apply filters
            if search_query:
                new_trailers = new_trailers[new_trailers['trailer_number'].str.contains(search_query, case=False, na=False)]
            if location_filter != "All":
                new_trailers = new_trailers[new_trailers['current_location'] == location_filter]
            
            # Calculate days available
            new_trailers['added_date'] = pd.to_datetime(new_trailers['added_date'], errors='coerce')
            new_trailers['days_available'] = (datetime.now() - new_trailers['added_date']).dt.days
            new_trailers['days_available'] = new_trailers['days_available'].fillna(0).clip(lower=0)
            
            # Apply days filter
            if days_filter == "< 1 day":
                new_trailers = new_trailers[new_trailers['days_available'] < 1]
            elif days_filter == "1-3 days":
                new_trailers = new_trailers[(new_trailers['days_available'] >= 1) & (new_trailers['days_available'] <= 3)]
            elif days_filter == "3-7 days":
                new_trailers = new_trailers[(new_trailers['days_available'] > 3) & (new_trailers['days_available'] <= 7)]
            elif days_filter == "> 7 days":
                new_trailers = new_trailers[new_trailers['days_available'] > 7]
            
            # Display trailers as cards
            for _, trailer in new_trailers.iterrows():
                # Determine if newly added (< 24 hours)
                is_new = trailer['days_available'] == 0
                
                with st.container():
                    card_style = "border-left: 4px solid #28a745;" if is_new else "border-left: 4px solid #DC143C;"
                    
                    st.markdown(f"""
                    <div style="background: white; {card_style} border-radius: 8px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h4 style="margin: 0; color: #000;">Trailer: {trailer['trailer_number']}</h4>
                        <p style="margin: 0.5rem 0; color: #666;">📍 {trailer['current_location']}</p>
                        <p style="margin: 0.5rem 0; color: #666;">
                            {'🔵 Empty' if not trailer['loaded_status'] else '🔴 Loaded'} | 
                            📅 {trailer['days_available']} days available
                            {' | 🆕 New' if is_new else ''}
                        </p>
                        {f"<p style='margin: 0.5rem 0; color: #888; font-style: italic;'>Notes: {trailer['notes']}</p>" if trailer['notes'] else ""}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_a, col_b = st.columns([3, 1])
                    with col_b:
                        if st.button("📝 Edit", key=f"edit_new_{trailer['id']}"):
                            st.session_state[f'edit_trailer_{trailer["id"]}'] = True
                            st.rerun()
        else:
            st.info("No available new trailers. Add trailers using the 'Add New Trailer' tab.")
    
    with col2:
        st.markdown("### 🔄 Available Old Trailers")
        old_trailers = db.get_available_trailers(trailer_type='old')
        
        if not old_trailers.empty:
            # Apply filters
            if search_query:
                old_trailers = old_trailers[old_trailers['trailer_number'].str.contains(search_query, case=False, na=False)]
            if location_filter != "All":
                old_trailers = old_trailers[old_trailers['current_location'] == location_filter]
            
            # Calculate days available
            old_trailers['added_date'] = pd.to_datetime(old_trailers['added_date'], errors='coerce')
            old_trailers['days_available'] = (datetime.now() - old_trailers['added_date']).dt.days
            old_trailers['days_available'] = old_trailers['days_available'].fillna(0).clip(lower=0)
            
            # Apply days filter
            if days_filter == "< 1 day":
                old_trailers = old_trailers[old_trailers['days_available'] < 1]
            elif days_filter == "1-3 days":
                old_trailers = old_trailers[(old_trailers['days_available'] >= 1) & (old_trailers['days_available'] <= 3)]
            elif days_filter == "3-7 days":
                old_trailers = old_trailers[(old_trailers['days_available'] > 3) & (old_trailers['days_available'] <= 7)]
            elif days_filter == "> 7 days":
                old_trailers = old_trailers[old_trailers['days_available'] > 7]
            
            # Display trailers as cards
            for _, trailer in old_trailers.iterrows():
                # Determine if newly added (< 24 hours)
                is_new = trailer['days_available'] == 0
                
                with st.container():
                    card_style = "border-left: 4px solid #28a745;" if is_new else "border-left: 4px solid #DC143C;"
                    
                    st.markdown(f"""
                    <div style="background: white; {card_style} border-radius: 8px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h4 style="margin: 0; color: #000;">Trailer: {trailer['trailer_number']}</h4>
                        <p style="margin: 0.5rem 0; color: #666;">📍 {trailer['current_location']}</p>
                        <p style="margin: 0.5rem 0; color: #666;">
                            {'🔵 Empty' if not trailer['loaded_status'] else '🔴 Loaded'} | 
                            📅 {trailer['days_available']} days available
                            {' | 🆕 New' if is_new else ''}
                        </p>
                        {f"<p style='margin: 0.5rem 0; color: #888; font-style: italic;'>Notes: {trailer['notes']}</p>" if trailer['notes'] else ""}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_a, col_b = st.columns([3, 1])
                    with col_b:
                        if st.button("📝 Edit", key=f"edit_old_{trailer['id']}"):
                            st.session_state[f'edit_trailer_{trailer["id"]}'] = True
                            st.rerun()
        else:
            st.info("No available old trailers. Add trailers using the 'Add Old Trailer' tab.")

def add_new_trailer_form():
    """Form to add a new trailer"""
    st.subheader("➕ Add New Trailer")
    
    with st.form("add_new_trailer_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            trailer_number = st.text_input("Trailer Number *", placeholder="Enter trailer number")
            trailer_type = st.selectbox("Trailer Type *", ["Empty", "Loaded"])
            
            # Location dropdown
            locations_df = db.get_all_locations()
            location_options = utils.create_location_options(locations_df, include_add_new=False)
            current_location = st.selectbox("Current Location *", location_options)
        
        with col2:
            added_date = st.date_input("Date Added", value=datetime.today())
            notes = st.text_area("Notes (Optional)", placeholder="Add any notes about this trailer...")
        
        submitted = st.form_submit_button("➕ Add New Trailer", type="primary", use_container_width=True)
        
        if submitted:
            if trailer_number and current_location:
                # Check for duplicates
                existing = db.get_trailer_by_number(trailer_number)
                if existing and existing['status'] != 'completed':
                    st.error(f"Trailer {trailer_number} already exists and is {existing['status']}")
                else:
                    trailer_data = {
                        'trailer_number': trailer_number,
                        'trailer_type': 'new',
                        'current_location': current_location,
                        'loaded_status': 1 if trailer_type == "Loaded" else 0,
                        'status': 'available',
                        'notes': notes,
                        'added_date': added_date.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    trailer_id = db.add_trailer(trailer_data)
                    st.success(f"✅ New trailer {trailer_number} added successfully!")
                    st.balloons()
                    st.rerun()
            else:
                st.error("Please fill in all required fields")

def add_old_trailer_form():
    """Form to add an old trailer"""
    st.subheader("➕ Add Old Trailer")
    
    with st.form("add_old_trailer_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            trailer_number = st.text_input("Trailer Number *", placeholder="Enter trailer number")
            
            # Location dropdown
            locations_df = db.get_all_locations()
            location_options = utils.create_location_options(locations_df, include_add_new=False)
            current_location = st.selectbox("Current Location *", location_options)
            
            loaded_status = st.selectbox("Loaded Status *", ["No", "Yes"])
        
        with col2:
            available_date = st.date_input("Date Available", value=datetime.today())
            notes = st.text_area("Notes (Optional)", placeholder="Add any notes about this trailer...")
        
        submitted = st.form_submit_button("➕ Add Old Trailer", type="primary", use_container_width=True)
        
        if submitted:
            if trailer_number and current_location:
                # Check for duplicates
                existing = db.get_trailer_by_number(trailer_number)
                if existing and existing['status'] != 'completed':
                    st.error(f"Trailer {trailer_number} already exists and is {existing['status']}")
                else:
                    trailer_data = {
                        'trailer_number': trailer_number,
                        'trailer_type': 'old',
                        'current_location': current_location,
                        'loaded_status': 1 if loaded_status == "Yes" else 0,
                        'status': 'available',
                        'notes': notes,
                        'added_date': available_date.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    trailer_id = db.add_trailer(trailer_data)
                    st.success(f"✅ Old trailer {trailer_number} added successfully!")
                    st.balloons()
                    st.rerun()
            else:
                st.error("Please fill in all required fields")

def show_matched_trailers():
    """Show trailers that are currently matched/assigned to routes"""
    st.subheader("🔄 Matched Trailers on Active Routes")
    
    # Get assigned trailers
    assigned_trailers = db.get_all_trailers(status='assigned')
    
    if not assigned_trailers.empty:
        # Get move information for each trailer
        for _, trailer in assigned_trailers.iterrows():
            if trailer['assigned_to_move_id']:
                move = db.get_trailer_move_by_id(trailer['assigned_to_move_id'])
                if move:
                    st.markdown(f"""
                    <div style="background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h4 style="margin: 0; color: #000;">🚛 {trailer['trailer_type'].title()} Trailer: {trailer['trailer_number']}</h4>
                        <p style="margin: 0.5rem 0; color: #666;">
                            📍 Route: {move['pickup_location']} → {move['destination']}<br>
                            👤 Driver: {move['assigned_driver']}<br>
                            📅 Assigned: {utils.format_date(move['date_assigned'])}<br>
                            ⏳ Status: Pending Completion
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No trailers currently matched to active routes")

def show_trailer_history():
    """Show completed trailer history"""
    st.subheader("📊 Completed Trailer History")
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From Date", value=datetime.now() - timedelta(days=7))
    with col2:
        end_date = st.date_input("To Date", value=datetime.now())
    
    # Get completed trailers
    completed_trailers = db.get_all_trailers(status='completed')
    
    if not completed_trailers.empty:
        # Filter by date range
        completed_trailers['completed_date'] = pd.to_datetime(completed_trailers['completed_date'])
        mask = (completed_trailers['completed_date'].dt.date >= start_date) & (completed_trailers['completed_date'].dt.date <= end_date)
        completed_trailers = completed_trailers.loc[mask]
        
        if not completed_trailers.empty:
            # Display as table
            display_df = completed_trailers[['trailer_number', 'trailer_type', 'current_location', 'completed_date']].copy()
            display_df['completed_date'] = display_df['completed_date'].dt.strftime('%m/%d/%Y %I:%M %p')
            display_df.columns = ['Trailer Number', 'Type', 'Last Location', 'Completed Date']
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Archive old completed trailers
            old_trailers = completed_trailers[completed_trailers['completed_date'] < (datetime.now() - timedelta(days=7))]
            if len(old_trailers) > 0:
                if st.button(f"📦 Archive {len(old_trailers)} old completed trailers"):
                    for _, trailer in old_trailers.iterrows():
                        db.delete_trailer(trailer['id'], soft_delete=True)
                    st.success(f"Archived {len(old_trailers)} trailers")
                    st.rerun()
        else:
            st.info("No completed trailers in the selected date range")
    else:
        st.info("No completed trailer history available")

def get_trailer_selection_dropdown(trailer_type='new'):
    """Get a list of available trailers for dropdown selection"""
    available = db.get_available_trailers(trailer_type=trailer_type)
    
    if not available.empty:
        options = []
        for _, trailer in available.iterrows():
            loaded_status = "Loaded" if trailer['loaded_status'] else "Empty"
            option_text = f"{trailer['trailer_number']} - {trailer['current_location']} ({loaded_status})"
            options.append((trailer['id'], option_text))
        return options
    return []