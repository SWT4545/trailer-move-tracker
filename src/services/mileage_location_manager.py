"""
Mileage Calculator and Location Manager
Handles distance calculations and dynamic trailer location tracking
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

def calculate_mileage(from_location, to_location):
    """Calculate mileage between two locations"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if we have pre-calculated distance
    cursor.execute('''SELECT distance_miles, drive_time_hours, route_notes 
                     FROM location_distances 
                     WHERE from_location = ? AND to_location = ?''',
                  (from_location, to_location))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'miles': result[0],
            'hours': result[1],
            'route': result[2]
        }
    else:
        # Return estimate if not in database
        return {
            'miles': None,
            'hours': None,
            'route': 'Distance not pre-calculated - manual entry required'
        }

def get_all_locations():
    """Get all locations with full details"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''SELECT location_title, address, city, state, zip_code, notes 
                     FROM locations ORDER BY location_title''')
    locations = cursor.fetchall()
    conn.close()
    
    return locations

def update_trailer_location(trailer_number, new_location, updated_by=None):
    """Update trailer location dynamically"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Update trailer location
    cursor.execute('''UPDATE trailers 
                     SET current_location = ?, 
                         last_known_location = current_location,
                         location_confirmed_by = ?,
                         location_confirmed_at = ?
                     WHERE trailer_number = ?''',
                  (new_location, updated_by, datetime.now(), trailer_number))
    
    # Log the change
    cursor.execute('''INSERT INTO trailer_location_history 
                     (trailer_number, location, updated_by, updated_at)
                     VALUES (?, ?, ?, ?)''',
                  (trailer_number, new_location, updated_by, datetime.now()))
    
    conn.commit()
    conn.close()
    
    return True

def show_location_management():
    """Show location management interface"""
    st.markdown("## 📍 Location & Mileage Management")
    
    tabs = st.tabs(["📊 Mileage Calculator", "🚚 Trailer Locations", "📍 Location Directory", "⚙️ Rate Configuration"])
    
    with tabs[0]:  # Mileage Calculator
        st.markdown("### Calculate Move Distance")
        
        locations = get_all_locations()
        location_names = [loc[0] for loc in locations]
        
        col1, col2 = st.columns(2)
        with col1:
            from_loc = st.selectbox("From Location", location_names, index=0 if "Fleet Memphis" in location_names else 0)
        with col2:
            to_loc = st.selectbox("To Location", location_names, index=1)
        
        if st.button("Calculate Distance", type="primary"):
            if from_loc and to_loc:
                result = calculate_mileage(from_loc, to_loc)
                
                if result['miles']:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Distance", f"{result['miles']} miles")
                    with col2:
                        st.metric("Drive Time", f"{result['hours']:.1f} hours")
                    with col3:
                        st.metric("Estimated Pay", f"${result['miles'] * 2.10:.2f}")
                    
                    st.info(f"**Route:** {result['route']}")
                else:
                    st.warning("Distance not in database. Please enter manually:")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        manual_miles = st.number_input("Miles", min_value=1, max_value=3000)
                    with col2:
                        manual_hours = st.number_input("Hours", min_value=0.1, max_value=50.0, step=0.5)
                    
                    if st.button("Save Distance"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute('''INSERT OR REPLACE INTO location_distances 
                                        (from_location, to_location, distance_miles, drive_time_hours)
                                        VALUES (?, ?, ?, ?)''',
                                     (from_loc, to_loc, manual_miles, manual_hours))
                        conn.commit()
                        conn.close()
                        st.success("Distance saved!")
        
        # Show distance matrix
        st.markdown("### Pre-Calculated Distances")
        conn = get_connection()
        df = pd.read_sql_query('''SELECT from_location as 'From', 
                                         to_location as 'To', 
                                         distance_miles as 'Miles',
                                         drive_time_hours as 'Hours'
                                  FROM location_distances 
                                  ORDER BY from_location, to_location''', conn)
        conn.close()
        
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    with tabs[1]:  # Trailer Locations
        st.markdown("### Update Trailer Locations")
        st.info("Trailer locations are dynamic. Update when location is confirmed.")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get trailers needing location updates
        cursor.execute('''SELECT trailer_number, type, current_location, 
                                last_known_location, location_confirmed_at
                         FROM trailers 
                         WHERE type = 'old' 
                         ORDER BY trailer_number''')
        trailers = cursor.fetchall()
        
        # Allow filtering
        search = st.text_input("Search trailer number")
        
        if search:
            trailers = [t for t in trailers if search.upper() in t[0].upper()]
        
        for trailer in trailers:
            trailer_num, t_type, current_loc, last_loc, confirmed_at = trailer
            
            with st.expander(f"🚚 Trailer {trailer_num}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    **Current Location:** {current_loc or 'Unknown'}  
                    **Last Known:** {last_loc or 'N/A'}  
                    **Last Updated:** {confirmed_at or 'Never'}
                    """)
                
                with col2:
                    new_location = st.selectbox(
                        "Update Location",
                        [""] + location_names,
                        key=f"loc_{trailer_num}"
                    )
                    
                    if new_location and st.button(f"Update", key=f"update_{trailer_num}"):
                        if update_trailer_location(trailer_num, new_location, st.session_state.username):
                            st.success(f"✅ {trailer_num} location updated to {new_location}")
                            st.rerun()
        
        conn.close()
    
    with tabs[2]:  # Location Directory
        st.markdown("### Location Directory")
        
        locations = get_all_locations()
        
        for loc in locations:
            title, address, city, state, zip_code, notes = loc
            
            with st.expander(f"📍 {title}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    **Address:**  
                    {address}  
                    {city}, {state} {zip_code}
                    """)
                
                with col2:
                    st.markdown(f"""
                    **Contact:**  
                    {notes}
                    """)
                
                # Show trailers at this location
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute('''SELECT trailer_number, type 
                                 FROM trailers 
                                 WHERE current_location = ?''',
                              (title,))
                trailers_here = cursor.fetchall()
                conn.close()
                
                if trailers_here:
                    st.markdown("**Trailers at this location:**")
                    for trailer, t_type in trailers_here:
                        st.markdown(f"- {trailer} ({t_type})")
    
    with tabs[3]:  # Rate Configuration
        st.markdown("### Rate Configuration")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get current rate
        cursor.execute('''SELECT rate_per_mile, service_fee 
                         FROM rate_configuration 
                         WHERE rate_name = 'standard' ''')
        current_rate = cursor.fetchone()
        
        if current_rate:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Current Rate", f"${current_rate[0]}/mile")
            with col2:
                st.metric("Service Fee", f"${current_rate[1]}")
        
        st.markdown("### Adjust Rates")
        st.warning("⚠️ Rate changes affect new moves only")
        
        with st.form("rate_adjustment"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_rate = st.number_input(
                    "Rate per Mile ($)",
                    value=current_rate[0] if current_rate else 2.10,
                    min_value=0.50,
                    max_value=10.00,
                    step=0.05
                )
            
            with col2:
                new_fee = st.number_input(
                    "Service Fee ($)",
                    value=current_rate[1] if current_rate else 6.00,
                    min_value=0.00,
                    max_value=50.00,
                    step=1.00
                )
            
            notes = st.text_area("Notes (reason for change)")
            
            if st.form_submit_button("Update Rates", type="primary"):
                cursor.execute('''UPDATE rate_configuration 
                                 SET rate_per_mile = ?, service_fee = ?, notes = ?
                                 WHERE rate_name = 'standard' ''',
                              (new_rate, new_fee, notes))
                conn.commit()
                st.success(f"✅ Rates updated: ${new_rate}/mile with ${new_fee} service fee")
                st.rerun()
        
        conn.close()

def get_current_rate():
    """Get current rate configuration"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''SELECT rate_per_mile, service_fee 
                     FROM rate_configuration 
                     WHERE rate_name = 'standard' ''')
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {'rate': result[0], 'fee': result[1]}
    else:
        return {'rate': 2.10, 'fee': 6.00}  # Default values