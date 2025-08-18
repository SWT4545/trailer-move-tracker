"""
Enhanced Trailer Management System with Location Tracking
Smith and Williams Trucking
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import database as db
import branding
import utils

def show_trailer_management():
    """Main trailer management page with enhanced features"""
    st.title("🚛 Enhanced Trailer Management System")
    
    # Get location trailer counts for priority display
    location_counts = db.get_location_trailer_counts()
    
    # Display priority locations with high trailer counts
    if not location_counts.empty:
        high_priority = location_counts[location_counts['old_trailer_count'] >= 5]
        if not high_priority.empty:
            st.error("⚠️ **Locations Needing Immediate Attention**")
            cols = st.columns(len(high_priority) if len(high_priority) <= 4 else 4)
            for idx, (_, loc) in enumerate(high_priority.iterrows()):
                col_idx = idx % len(cols)
                with cols[col_idx]:
                    st.markdown(f"""
                    <div style="background: #ffebee; border: 2px solid #dc3545; border-radius: 8px; padding: 1rem; text-align: center;">
                        <h4 style="margin: 0; color: #dc3545;">{loc['location_title']}</h4>
                        <p style="margin: 0.5rem 0; font-size: 1.5rem; font-weight: bold; color: #dc3545;">
                            {loc['old_trailer_count']} trailers
                        </p>
                        <p style="margin: 0; color: #666; font-size: 0.9rem;">HIGH PRIORITY</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Get trailer statistics
    stats = db.get_trailer_statistics()
    
    # Display enhanced metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Available New", stats['available_new'], delta=None)
    with col2:
        st.metric("Available Old", stats['available_old'], delta=None)
    with col3:
        st.metric("Assigned", stats['assigned'], delta=None)
    with col4:
        st.metric("Completed Today", stats['completed_today'], delta=None)
    with col5:
        total_old = location_counts['old_trailer_count'].sum() if not location_counts.empty else 0
        st.metric("Total Old at Locations", total_old, 
                 delta=f"{len(location_counts[location_counts['alert_status'] == 'red'])} critical" if not location_counts.empty else None)
    
    # Enhanced tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Dashboard", 
        "➕ Add New Trailer", 
        "➕ Add Old Trailer",
        "📍 Location Overview",
        "🔄 Matched Trailers",
        "📊 History"
    ])
    
    with tab1:
        show_enhanced_dashboard()
    
    with tab2:
        add_new_trailer_enhanced()
    
    with tab3:
        add_old_trailer_enhanced()
    
    with tab4:
        show_location_overview()
    
    with tab5:
        show_matched_trailers()
    
    with tab6:
        show_trailer_history()

def show_enhanced_dashboard():
    """Enhanced dashboard with location-based intelligence"""
    st.subheader("📋 Enhanced Trailer Dashboard")
    
    # Location summary widget
    st.markdown("### 📍 Location Trailer Distribution")
    location_counts = db.get_location_trailer_counts()
    
    if not location_counts.empty:
        # Sort by count descending
        location_counts = location_counts.sort_values('old_trailer_count', ascending=False)
        
        # Display as cards
        for _, loc in location_counts.head(10).iterrows():
            if loc['old_trailer_count'] > 0:
                # Determine color based on count
                if loc['old_trailer_count'] >= 5:
                    color = "#dc3545"  # Red
                    status = "HIGH"
                elif loc['old_trailer_count'] >= 3:
                    color = "#ffc107"  # Yellow
                    status = "MEDIUM"
                else:
                    color = "#28a745"  # Green
                    status = "LOW"
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.markdown(f"**{loc['location_title']}**")
                with col2:
                    st.markdown(f"<span style='color: {color}; font-weight: bold;'>{loc['old_trailer_count']} trailers</span>", 
                              unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<span style='color: {color};'>{status}</span>", unsafe_allow_html=True)
                with col4:
                    if st.button("Create Route", key=f"route_{loc['id']}"):
                        st.session_state['suggested_location'] = loc['location_title']
                        st.info(f"Suggested route to {loc['location_title']} - Go to 'Add New Move' to create")
    
    st.divider()
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        search_query = st.text_input("🔍 Search Trailer Number", placeholder="Enter trailer number...")
    with col2:
        all_locations = db.get_all_locations()['location_title'].tolist() if not db.get_all_locations().empty else []
        location_filter = st.selectbox("📍 Filter by Location", ["All"] + all_locations)
    with col3:
        days_filter = st.selectbox("📅 Days Available", ["All", "< 1 day", "1-3 days", "3-7 days", "> 7 days"])
    
    # Two columns for new and old trailers
    col1, col2 = st.columns(2)
    
    with col1:
        display_trailer_list("new", search_query, location_filter, days_filter)
    
    with col2:
        display_trailer_list("old", search_query, location_filter, days_filter)

def display_trailer_list(trailer_type, search_query, location_filter, days_filter):
    """Display list of trailers with enhanced formatting"""
    title = "🆕 Available New Trailers" if trailer_type == "new" else "🔄 Available Old Trailers"
    st.markdown(f"### {title}")
    
    trailers = db.get_available_trailers(trailer_type=trailer_type)
    
    if not trailers.empty:
        # Apply filters
        if search_query:
            trailers = trailers[trailers['trailer_number'].str.contains(search_query, case=False, na=False)]
        if location_filter != "All":
            trailers = trailers[trailers['current_location'] == location_filter]
        
        # Calculate days available
        trailers['added_date'] = pd.to_datetime(trailers['added_date'], errors='coerce')
        trailers['days_available'] = (datetime.now() - trailers['added_date']).dt.days
        trailers['days_available'] = trailers['days_available'].fillna(0).clip(lower=0)
        
        # Apply days filter
        if days_filter == "< 1 day":
            trailers = trailers[trailers['days_available'] < 1]
        elif days_filter == "1-3 days":
            trailers = trailers[(trailers['days_available'] >= 1) & (trailers['days_available'] <= 3)]
        elif days_filter == "3-7 days":
            trailers = trailers[(trailers['days_available'] > 3) & (trailers['days_available'] <= 7)]
        elif days_filter == "> 7 days":
            trailers = trailers[trailers['days_available'] > 7]
        
        # Display trailers as enhanced cards
        for _, trailer in trailers.iterrows():
            display_trailer_card(trailer, trailer_type)
    else:
        st.info(f"No available {trailer_type} trailers. Add trailers using the 'Add {trailer_type.title()} Trailer' tab.")

def display_trailer_card(trailer, trailer_type):
    """Display an individual trailer card with enhanced styling"""
    # Determine if newly added (< 24 hours)
    is_new = trailer['days_available'] == 0
    
    # Get location trailer count if old trailer
    location_info = ""
    if trailer_type == "old" and trailer['current_location']:
        counts = db.get_location_trailer_counts()
        if not counts.empty:
            loc_data = counts[counts['location_title'] == trailer['current_location']]
            if not loc_data.empty:
                count = loc_data.iloc[0]['old_trailer_count']
                if count > 1:
                    location_info = f" ({count} trailers here)"
    
    with st.container():
        card_style = "border-left: 4px solid #28a745;" if is_new else "border-left: 4px solid #DC143C;"
        
        st.markdown(f"""
        <div style="background: white; {card_style} border: 2px solid #000; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h4 style="margin: 0; color: #000;">Trailer: {trailer['trailer_number']}</h4>
            <p style="margin: 0.5rem 0; color: #666;">📍 {trailer['current_location']}{location_info}</p>
            <p style="margin: 0.5rem 0; color: #666;">
                {'🔵 Empty' if not trailer['loaded_status'] else '🔴 Loaded'} | 
                📅 {trailer['days_available']} days available
                {' | 🆕 New' if is_new else ''}
            </p>
            {f"<p style='margin: 0.5rem 0; color: #888; font-style: italic;'>Notes: {trailer['notes']}</p>" if trailer['notes'] else ""}
        </div>
        """, unsafe_allow_html=True)

def add_new_trailer_enhanced():
    """Enhanced form for adding new trailers"""
    st.subheader("➕ Add New Trailer")
    
    with st.form("add_new_trailer_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            trailer_number = st.text_input("Trailer Number *", placeholder="e.g., 18V00327")
            trailer_type_option = st.selectbox("Trailer Status", ["Empty", "Loaded"])
            loaded_status = trailer_type_option == "Loaded"
        
        with col2:
            # Get all locations for dropdown
            locations_df = db.get_all_locations()
            location_options = ["Fleet Memphis"] + (locations_df['location_title'].tolist() if not locations_df.empty else [])
            current_location = st.selectbox("Current Location *", location_options)
            
        notes = st.text_area("Notes (optional)", placeholder="Any special notes about this trailer...")
        
        submitted = st.form_submit_button("➕ Add New Trailer", use_container_width=True)
        
        if submitted:
            if trailer_number and current_location:
                # Check for duplicates
                existing = db.get_trailer_by_number(trailer_number)
                if existing and existing['status'] != 'completed':
                    st.error(f"⚠️ Trailer {trailer_number} already exists and is {existing['status']}")
                else:
                    # Add the trailer
                    data = {
                        'trailer_number': trailer_number,
                        'trailer_type': 'new',
                        'current_location': current_location,
                        'loaded_status': loaded_status,
                        'notes': notes
                    }
                    trailer_id = db.add_trailer(data)
                    st.success(f"✅ New trailer {trailer_number} added successfully!")
                    st.rerun()
            else:
                st.error("⚠️ Please fill in all required fields")

def add_old_trailer_enhanced():
    """Enhanced form for adding old trailers with location tracking"""
    st.subheader("➕ Add Old Trailer with Location Tracking")
    
    # Show current location counts
    st.info("💡 **Tip**: The system tracks how many old trailers are at each location. High counts indicate priority pickup locations.")
    
    with st.form("add_old_trailer_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            trailer_number = st.text_input("Trailer Number *", placeholder="e.g., 18V98765")
        
        with col2:
            # Enhanced location dropdown with counts
            locations_df = db.get_all_locations()
            location_counts = db.get_location_trailer_counts()
            
            # Build location options with counts
            location_options = []
            location_display = []
            
            if not locations_df.empty:
                for _, loc in locations_df.iterrows():
                    location_name = loc['location_title']
                    location_options.append(location_name)
                    
                    # Get count for this location
                    if not location_counts.empty:
                        count_data = location_counts[location_counts['location_title'] == location_name]
                        if not count_data.empty:
                            count = count_data.iloc[0]['old_trailer_count']
                            if count > 0:
                                location_display.append(f"{location_name} ({count} old trailers)")
                            else:
                                location_display.append(location_name)
                        else:
                            location_display.append(location_name)
                    else:
                        location_display.append(location_name)
            
            # Add option to create new location
            location_options.append("➕ Add New Location")
            location_display.append("➕ Add New Location")
            
            selected_location = st.selectbox(
                "Current Location * (shows existing trailer count)",
                options=location_options,
                format_func=lambda x: location_display[location_options.index(x)]
            )
        
        # If Add New Location is selected, show inline form
        if selected_location == "➕ Add New Location":
            st.markdown("#### 📍 Add New Location")
            col1, col2 = st.columns(2)
            with col1:
                new_location_name = st.text_input("Location Name *", placeholder="e.g., FedEx Chicago")
                street_address = st.text_input("Street Address *", placeholder="123 Main St")
                city = st.text_input("City *", placeholder="Chicago")
            with col2:
                state = st.text_input("State *", placeholder="IL")
                zip_code = st.text_input("ZIP Code *", placeholder="60601")
                contact_phone = st.text_input("Contact Phone (optional)", placeholder="(555) 123-4567")
            
            location_to_use = new_location_name
        else:
            location_to_use = selected_location
            new_location_name = None
        
        col1, col2 = st.columns(2)
        with col1:
            loaded_status_option = st.selectbox("Loaded Status", ["No", "Yes"])
            loaded_status = loaded_status_option == "Yes"
        
        with col2:
            notes = st.text_area("Notes (optional)", placeholder="Any special notes...")
        
        submitted = st.form_submit_button("➕ Add Old Trailer", use_container_width=True)
        
        if submitted:
            if trailer_number and (location_to_use or new_location_name):
                # If new location, add it first
                if selected_location == "➕ Add New Location":
                    if new_location_name and street_address and city and state and zip_code:
                        # Add new location
                        location_data = {
                            'location_title': new_location_name,
                            'location_address': f"{street_address}, {city}, {state} {zip_code}",
                            'street_address': street_address,
                            'city': city,
                            'state': state,
                            'zip_code': zip_code,
                            'contact_phone': contact_phone
                        }
                        db.add_location(location_data)
                        location_to_use = new_location_name
                        st.success(f"✅ New location '{new_location_name}' added!")
                    else:
                        st.error("⚠️ Please fill in all required location fields")
                        st.stop()
                
                # Check for duplicate trailer
                existing = db.get_trailer_by_number(trailer_number)
                if existing and existing['status'] != 'completed':
                    st.error(f"⚠️ Trailer {trailer_number} already exists and is {existing['status']}")
                else:
                    # Add the old trailer
                    data = {
                        'trailer_number': trailer_number,
                        'trailer_type': 'old',
                        'current_location': location_to_use,
                        'loaded_status': loaded_status,
                        'notes': notes
                    }
                    trailer_id = db.add_trailer(data)
                    
                    # Update location trailer count
                    db.update_location_trailer_count(location_to_use, 1)
                    
                    st.success(f"✅ Old trailer {trailer_number} added at {location_to_use}!")
                    
                    # Check if location needs attention
                    location_counts = db.get_location_trailer_counts()
                    if not location_counts.empty:
                        loc_data = location_counts[location_counts['location_title'] == location_to_use]
                        if not loc_data.empty and loc_data.iloc[0]['old_trailer_count'] >= 5:
                            st.warning(f"⚠️ {location_to_use} now has {loc_data.iloc[0]['old_trailer_count']} old trailers - consider prioritizing pickup!")
                    
                    st.rerun()
            else:
                st.error("⚠️ Please fill in all required fields")

def show_location_overview():
    """Show overview of all locations with trailer counts and priorities"""
    st.subheader("📍 Location Overview - Old Trailer Distribution")
    
    location_counts = db.get_location_trailer_counts()
    
    if location_counts.empty:
        st.info("No old trailers currently at any locations")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_locations = len(location_counts[location_counts['old_trailer_count'] > 0])
        st.metric("Active Locations", total_locations)
    with col2:
        total_trailers = location_counts['old_trailer_count'].sum()
        st.metric("Total Old Trailers", total_trailers)
    with col3:
        high_priority = len(location_counts[location_counts['old_trailer_count'] >= 5])
        st.metric("High Priority", high_priority, delta="5+ trailers")
    with col4:
        medium_priority = len(location_counts[(location_counts['old_trailer_count'] >= 3) & (location_counts['old_trailer_count'] < 5)])
        st.metric("Medium Priority", medium_priority, delta="3-4 trailers")
    
    st.divider()
    
    # Display locations by priority
    st.markdown("### Priority Locations")
    
    # High Priority (5+ trailers)
    high = location_counts[location_counts['old_trailer_count'] >= 5]
    if not high.empty:
        st.markdown("#### 🔴 **High Priority (5+ trailers)**")
        for _, loc in high.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{loc['location_title']}**")
            with col2:
                st.markdown(f"<span style='color: #dc3545; font-weight: bold; font-size: 1.2rem;'>{loc['old_trailer_count']} trailers</span>", 
                          unsafe_allow_html=True)
            with col3:
                if st.button("Create Route", key=f"loc_route_{loc['id']}"):
                    st.session_state['suggested_location'] = loc['location_title']
                    st.info(f"Go to 'Add New Move' to create route for {loc['location_title']}")
    
    # Medium Priority (3-4 trailers)
    medium = location_counts[(location_counts['old_trailer_count'] >= 3) & (location_counts['old_trailer_count'] < 5)]
    if not medium.empty:
        st.markdown("#### 🟡 **Medium Priority (3-4 trailers)**")
        for _, loc in medium.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{loc['location_title']}**")
            with col2:
                st.markdown(f"<span style='color: #ffc107; font-weight: bold;'>{loc['old_trailer_count']} trailers</span>", 
                          unsafe_allow_html=True)
            with col3:
                if st.button("Create Route", key=f"loc_route_{loc['id']}"):
                    st.session_state['suggested_location'] = loc['location_title']
                    st.info(f"Go to 'Add New Move' to create route for {loc['location_title']}")
    
    # Low Priority (1-2 trailers)
    low = location_counts[(location_counts['old_trailer_count'] > 0) & (location_counts['old_trailer_count'] < 3)]
    if not low.empty:
        st.markdown("#### 🟢 **Low Priority (1-2 trailers)**")
        for _, loc in low.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"{loc['location_title']}")
            with col2:
                st.markdown(f"<span style='color: #28a745;'>{loc['old_trailer_count']} trailer(s)</span>", 
                          unsafe_allow_html=True)
    
    # Visualization
    if not location_counts.empty:
        st.divider()
        st.markdown("### 📊 Visual Analysis")
        
        # Bar chart of trailer distribution
        import plotly.express as px
        
        # Filter to only locations with trailers
        chart_data = location_counts[location_counts['old_trailer_count'] > 0].copy()
        chart_data = chart_data.sort_values('old_trailer_count', ascending=True)
        
        # Assign colors based on count
        chart_data['color'] = chart_data['old_trailer_count'].apply(
            lambda x: '#dc3545' if x >= 5 else ('#ffc107' if x >= 3 else '#28a745')
        )
        
        fig = px.bar(
            chart_data, 
            y='location_title', 
            x='old_trailer_count',
            orientation='h',
            title='Old Trailers by Location',
            labels={'old_trailer_count': 'Number of Trailers', 'location_title': 'Location'},
            color='color',
            color_discrete_map={'#dc3545': '#dc3545', '#ffc107': '#ffc107', '#28a745': '#28a745'}
        )
        
        fig.update_layout(
            showlegend=False,
            height=400,
            xaxis_title="Number of Old Trailers",
            yaxis_title=""
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_matched_trailers():
    """Show trailers that are currently matched to routes"""
    st.subheader("🔄 Matched Trailers on Active Routes")
    
    # Get active moves with trailer assignments
    active_moves = db.get_all_trailer_moves()
    active_moves = active_moves[active_moves['completion_date'].isna()]
    
    if active_moves.empty:
        st.info("No active routes with matched trailers")
        return
    
    # Display active assignments
    for _, move in active_moves.iterrows():
        with st.container():
            st.markdown(f"""
            <div style="background: #fff3cd; border-left: 5px solid #ffc107; border: 2px solid #000; 
                        border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <h4 style="margin: 0;">Route #{move['id']} - {move['assigned_driver']}</h4>
                <p style="margin: 0.5rem 0;">
                    📦 New: {move['new_trailer']} | 
                    🔄 Old: {move['old_trailer'] if move['old_trailer'] else 'TBD'}
                </p>
                <p style="margin: 0.5rem 0;">
                    📍 {move['pickup_location']} → {move['destination']}
                </p>
                <p style="margin: 0;">
                    📅 Assigned: {pd.to_datetime(move['date_assigned']).strftime('%m/%d/%Y')}
                </p>
            </div>
            """, unsafe_allow_html=True)

def show_trailer_history():
    """Show historical trailer movements"""
    st.subheader("📊 Trailer History")
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From Date", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("To Date", value=datetime.now())
    
    # Get completed trailers
    all_trailers = db.get_all_trailers()
    completed = all_trailers[all_trailers['status'] == 'completed']
    
    if not completed.empty:
        # Filter by date
        completed['completed_date'] = pd.to_datetime(completed['completed_date'])
        completed = completed[
            (completed['completed_date'].dt.date >= start_date) &
            (completed['completed_date'].dt.date <= end_date)
        ]
        
        if not completed.empty:
            st.markdown(f"### Found {len(completed)} completed trailer assignments")
            
            # Display as table
            display_df = completed[['trailer_number', 'trailer_type', 'current_location', 'completed_date']].copy()
            display_df['completed_date'] = display_df['completed_date'].dt.strftime('%m/%d/%Y')
            display_df.columns = ['Trailer #', 'Type', 'Last Location', 'Completed']
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info(f"No completed trailers found between {start_date} and {end_date}")
    else:
        st.info("No trailer history available yet")