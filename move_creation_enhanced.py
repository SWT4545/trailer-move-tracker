"""
Enhanced Move Creation System
Allows manual selection of trailers with dynamic location tracking
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
from mileage_location_manager import calculate_mileage, get_current_rate

def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

def show_move_creation():
    """Enhanced move creation interface"""
    st.markdown("## 🚚 Create New Move")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get available new trailers at Fleet Memphis
    cursor.execute('''SELECT trailer_number 
                     FROM trailers 
                     WHERE type = 'new' 
                     AND status = 'available' 
                     AND current_location = 'Fleet Memphis'
                     ORDER BY trailer_number''')
    new_trailers = [t[0] for t in cursor.fetchall()]
    
    # Get old trailers that need replacement
    cursor.execute('''SELECT trailer_number, current_location 
                     FROM trailers 
                     WHERE type = 'old' 
                     AND status = 'available'
                     ORDER BY current_location, trailer_number''')
    old_trailers = cursor.fetchall()
    
    # Get drivers
    cursor.execute('''SELECT driver_name FROM drivers 
                     WHERE active = 1 
                     ORDER BY driver_name''')
    drivers = [d[0] for d in cursor.fetchall()]
    
    # Get locations
    cursor.execute('''SELECT location_title FROM locations 
                     ORDER BY location_title''')
    locations = [l[0] for l in cursor.fetchall()]
    
    st.markdown("### Move Details")
    
    with st.form("create_move"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### New Trailer Selection")
            st.info("Driver will select new trailer when arriving at Fleet Memphis")
            
            selected_new = st.selectbox(
                "New Trailer (from Fleet Memphis)",
                [""] + new_trailers,
                help="Select the new trailer to be picked up"
            )
            
            st.markdown("#### Delivery Location")
            delivery_location = st.selectbox(
                "Delivery Location",
                locations,
                help="Where the new trailer will be delivered"
            )
        
        with col2:
            st.markdown("#### Old Trailer Selection")
            st.info("Driver will swap with old trailer at delivery location")
            
            # Show old trailers grouped by location
            old_trailer_options = ["Manual Entry"]
            old_trailer_display = ["Enter trailer number manually"]
            
            for trailer, location in old_trailers:
                loc_text = location if location else "Location Unknown"
                old_trailer_options.append(trailer)
                old_trailer_display.append(f"{trailer} - {loc_text}")
            
            old_selection = st.selectbox(
                "Old Trailer to Swap",
                range(len(old_trailer_options)),
                format_func=lambda x: old_trailer_display[x],
                help="Select old trailer or enter manually"
            )
            
            if old_selection == 0:  # Manual entry
                manual_old_trailer = st.text_input(
                    "Enter Old Trailer Number",
                    help="Manually enter trailer number if not in list"
                )
                selected_old = manual_old_trailer
            else:
                selected_old = old_trailer_options[old_selection]
        
        st.markdown("---")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### Assignment")
            assigned_driver = st.selectbox(
                "Assign to Driver",
                ["Unassigned"] + drivers,
                help="Leave unassigned for driver self-assignment"
            )
            
            move_date = st.date_input(
                "Move Date",
                value=date.today(),
                help="Scheduled date for the move"
            )
        
        with col4:
            st.markdown("#### Rate Configuration")
            
            # Get current rates
            rates = get_current_rate()
            
            use_custom_rate = st.checkbox("Use custom rate for this move")
            
            if use_custom_rate:
                custom_rate = st.number_input(
                    "Rate per Mile ($)",
                    value=rates['rate'],
                    min_value=0.50,
                    max_value=10.00,
                    step=0.05
                )
                custom_fee = st.number_input(
                    "Service Fee ($)",
                    value=rates['fee'],
                    min_value=0.00,
                    max_value=50.00,
                    step=1.00
                )
            else:
                custom_rate = rates['rate']
                custom_fee = rates['fee']
                st.info(f"Standard Rate: ${custom_rate}/mile + ${custom_fee} fee")
        
        st.markdown("---")
        
        # Calculate mileage if locations are selected
        if delivery_location:
            mileage_info = calculate_mileage("Fleet Memphis", delivery_location)
            
            if mileage_info['miles']:
                col5, col6, col7 = st.columns(3)
                with col5:
                    st.metric("Calculated Distance", f"{mileage_info['miles']} miles")
                with col6:
                    st.metric("Estimated Drive Time", f"{mileage_info['hours']:.1f} hours")
                with col7:
                    estimated_pay = mileage_info['miles'] * custom_rate
                    st.metric("Driver Pay", f"${estimated_pay:.2f}")
                
                total_miles = mileage_info['miles']
            else:
                st.warning("Distance not pre-calculated. Enter manually:")
                total_miles = st.number_input(
                    "Total Miles",
                    min_value=1,
                    max_value=3000,
                    value=100,
                    help="Enter the total miles for this move"
                )
        
        notes = st.text_area(
            "Notes",
            help="Any special instructions or notes for this move"
        )
        
        submitted = st.form_submit_button("Create Move", type="primary")
        
        if submitted:
            if not selected_new:
                st.error("Please select a new trailer")
            elif not selected_old:
                st.error("Please select or enter an old trailer")
            elif not delivery_location:
                st.error("Please select a delivery location")
            else:
                # Generate move ID
                cursor.execute("SELECT COUNT(*) FROM moves")
                move_count = cursor.fetchone()[0]
                move_id = f"SWT-{datetime.now().year}-{move_count + 1:04d}"
                
                # Calculate driver pay
                driver_pay = total_miles * custom_rate if 'total_miles' in locals() else 0
                
                # Insert move
                cursor.execute('''INSERT INTO moves 
                                 (move_id, new_trailer, old_trailer, 
                                  pickup_location, delivery_location,
                                  driver_name, move_date, status, 
                                  payment_status, total_miles, driver_pay,
                                  notes, created_by, created_at)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (move_id, selected_new, selected_old,
                               "Fleet Memphis", delivery_location,
                               assigned_driver if assigned_driver != "Unassigned" else None,
                               move_date.strftime('%Y-%m-%d'),
                               'pending' if assigned_driver == "Unassigned" else 'assigned',
                               'pending', total_miles, driver_pay,
                               notes, st.session_state.username, datetime.now()))
                
                # Update trailer statuses
                cursor.execute('''UPDATE trailers SET status = 'reserved' 
                                 WHERE trailer_number = ?''', (selected_new,))
                
                # If old trailer location wasn't known, update it
                if selected_old and old_selection == 0:  # Manual entry
                    cursor.execute('''INSERT OR IGNORE INTO trailers 
                                     (trailer_number, type, status, current_location)
                                     VALUES (?, 'old', 'pending_swap', ?)''',
                                  (selected_old, delivery_location))
                
                conn.commit()
                st.success(f"✅ Move {move_id} created successfully!")
                
                # Show summary
                st.markdown("### Move Summary")
                st.info(f"""
                **Move ID:** {move_id}  
                **Route:** Fleet Memphis → {delivery_location}  
                **New Trailer:** {selected_new}  
                **Old Trailer:** {selected_old}  
                **Distance:** {total_miles} miles  
                **Driver:** {assigned_driver if assigned_driver != "Unassigned" else "Available for self-assignment"}  
                **Driver Pay:** ${driver_pay:.2f} (less ${custom_fee} service fee)
                """)
    
    conn.close()
    
    # Show existing moves
    st.markdown("---")
    st.markdown("### Recent Moves")
    
    conn = get_connection()
    df = pd.read_sql_query('''SELECT move_id as 'Move ID',
                                     new_trailer as 'New Trailer',
                                     old_trailer as 'Old Trailer',
                                     delivery_location as 'Destination',
                                     driver_name as 'Driver',
                                     status as 'Status',
                                     total_miles as 'Miles',
                                     driver_pay as 'Pay'
                              FROM moves 
                              ORDER BY created_at DESC 
                              LIMIT 10''', conn)
    conn.close()
    
    if not df.empty:
        # Format pay column
        df['Pay'] = df['Pay'].apply(lambda x: f"${x:.2f}" if x else "TBD")
        st.dataframe(df, use_container_width=True, hide_index=True)

def show_move_management():
    """Show move management interface for coordinators"""
    st.markdown("## 📋 Move Management")
    
    tabs = st.tabs(["Create Move", "Active Moves", "Assign Drivers", "Update Status"])
    
    with tabs[0]:
        show_move_creation()
    
    with tabs[1]:
        st.markdown("### Active Moves")
        
        conn = get_connection()
        df = pd.read_sql_query('''SELECT * FROM moves 
                                  WHERE status IN ('pending', 'assigned', 'in_progress')
                                  ORDER BY move_date''', conn)
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No active moves")
        
        conn.close()
    
    with tabs[2]:
        st.markdown("### Assign Drivers to Moves")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get unassigned moves
        cursor.execute('''SELECT move_id, new_trailer, old_trailer, delivery_location, total_miles
                         FROM moves 
                         WHERE driver_name IS NULL OR driver_name = ''
                         ORDER BY move_date''')
        unassigned = cursor.fetchall()
        
        if unassigned:
            for move in unassigned:
                move_id, new_t, old_t, dest, miles = move
                
                with st.expander(f"📦 {move_id} - {dest}"):
                    st.markdown(f"""
                    **Route:** Fleet Memphis → {dest}  
                    **Trailers:** {new_t} replacing {old_t}  
                    **Distance:** {miles} miles
                    """)
                    
                    # Get available drivers
                    cursor.execute('SELECT driver_name FROM drivers WHERE active = 1')
                    drivers = [d[0] for d in cursor.fetchall()]
                    
                    selected_driver = st.selectbox(
                        "Assign to",
                        [""] + drivers,
                        key=f"assign_{move_id}"
                    )
                    
                    if selected_driver and st.button(f"Assign", key=f"btn_{move_id}"):
                        cursor.execute('''UPDATE moves 
                                        SET driver_name = ?, status = 'assigned'
                                        WHERE move_id = ?''',
                                     (selected_driver, move_id))
                        conn.commit()
                        st.success(f"✅ {move_id} assigned to {selected_driver}")
                        st.rerun()
        else:
            st.info("All moves are assigned")
        
        conn.close()
    
    with tabs[3]:
        st.markdown("### Update Move Status")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get all active moves
        cursor.execute('''SELECT move_id, driver_name, status, old_trailer, new_trailer, delivery_location
                         FROM moves 
                         WHERE status != 'completed'
                         ORDER BY move_date''')
        active_moves = cursor.fetchall()
        
        for move in active_moves:
            move_id, driver, status, old_t, new_t, dest = move
            
            with st.expander(f"🚚 {move_id} - {status}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    **Driver:** {driver or 'Unassigned'}  
                    **Trailers:** {new_t} → {old_t}  
                    **Destination:** {dest}
                    """)
                
                with col2:
                    new_status = st.selectbox(
                        "Update Status",
                        ["pending", "assigned", "in_progress", "completed"],
                        index=["pending", "assigned", "in_progress", "completed"].index(status),
                        key=f"status_{move_id}"
                    )
                    
                    if new_status != status and st.button("Update", key=f"update_{move_id}"):
                        cursor.execute('UPDATE moves SET status = ? WHERE move_id = ?',
                                     (new_status, move_id))
                        
                        # If completed, update trailer locations
                        if new_status == "completed":
                            cursor.execute('UPDATE trailers SET current_location = ? WHERE trailer_number = ?',
                                         (dest, new_t))
                            cursor.execute('UPDATE trailers SET status = "swapped" WHERE trailer_number = ?',
                                         (old_t,))
                        
                        conn.commit()
                        st.success(f"✅ {move_id} status updated to {new_status}")
                        st.rerun()
        
        conn.close()