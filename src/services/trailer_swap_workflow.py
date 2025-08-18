"""
Trailer Swap Workflow Management
Core business logic for Fleet Memphis trailer swaps
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import database as db
import mileage_calculator as mileage_calc
import base_location_manager as base_mgr

def show_trailer_entry_page():
    """Step 1: Enter trailers into the system BEFORE creating moves"""
    st.title("🚛 Trailer Management")
    
    # Get current base location
    base_location = base_mgr.get_default_base_location()
    st.info(f"📍 Base: **{base_location}** | Enter trailers BEFORE creating moves")
    
    # Get existing trailers
    trailers_df = db.get_all_trailers()
    locations_df = db.get_all_locations()
    location_list = locations_df['location_title'].tolist() if not locations_df.empty else []
    
    # Tabs for different entry methods
    tab1, tab2, tab3 = st.tabs(["➕ Add Pair", "📋 All Trailers", "🔄 Pending"])
    
    with tab1:
        st.markdown("### Enter Trailer Swap Pair")
        st.caption("Enter both the NEW trailer (from Fleet Memphis) and OLD trailer (to be picked up)")
        
        with st.form("trailer_pair_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"#### 🆕 NEW Trailer (From {base_location})")
                new_trailer_number = st.text_input(
                    "New Trailer Number *",
                    placeholder="e.g., TRL-NEW-001",
                    help=f"This trailer will be picked up from {base_location}"
                )
                new_trailer_notes = st.text_area(
                    "New Trailer Notes",
                    placeholder="Any special instructions or conditions"
                )
            
            with col2:
                st.markdown("#### 🔄 OLD Trailer (To Pick Up)")
                old_trailer_number = st.text_input(
                    "Old Trailer Number *",
                    placeholder="e.g., TRL-OLD-001",
                    help="This trailer will be picked up from the swap location"
                )
                
                # Swap location selection
                swap_location = st.selectbox(
                    "Swap Location *",
                    [''] + [loc for loc in location_list if loc != base_location],
                    help="Where the trailer swap will occur"
                )
                
                if swap_location:
                    # Show address for verification
                    loc_data = locations_df[locations_df['location_title'] == swap_location]
                    if not loc_data.empty:
                        address = loc_data.iloc[0].get('location_address', 'No address')
                        st.caption(f"📍 {address}")
            
            st.markdown("---")
            
            # Estimated mileage section
            col1, col2, col3 = st.columns(3)
            with col1:
                if swap_location:
                    # Calculate round trip mileage
                    from_address = mileage_calc.get_location_full_address(base_location)
                    to_address = mileage_calc.get_location_full_address(swap_location)
                    
                    if from_address and to_address:
                        one_way_miles, source = mileage_calc.calculate_mileage_with_cache(
                            base_location, swap_location, from_address, to_address
                        )
                        if one_way_miles:
                            round_trip_miles = one_way_miles * 2
                            st.metric("📏 One Way", f"{one_way_miles} miles")
                            with col2:
                                st.metric("🔄 Round Trip", f"{round_trip_miles} miles")
                            with col3:
                                rate = 2.10
                                factor_fee = 0.03
                                estimated_pay = round_trip_miles * rate * (1 - factor_fee)
                                st.metric("💰 Estimated Pay", f"${estimated_pay:,.2f}")
            
            submitted = st.form_submit_button("✅ Add Trailer Pair", type="primary", use_container_width=True)
            
            if submitted:
                if new_trailer_number and old_trailer_number and swap_location:
                    try:
                        # Add new trailer
                        new_id = db.add_trailer({
                            'trailer_number': new_trailer_number,
                            'trailer_type': 'new',
                            'current_location': base_location,
                            'status': 'available',
                            'swap_location': swap_location,
                            'notes': new_trailer_notes
                        })
                        
                        # Add old trailer
                        old_id = db.add_trailer({
                            'trailer_number': old_trailer_number,
                            'trailer_type': 'old',
                            'current_location': swap_location,
                            'status': 'available',
                            'swap_location': swap_location,
                            'paired_trailer_id': new_id
                        })
                        
                        # Update new trailer with pair
                        db.update_trailer(new_id, {'paired_trailer_id': old_id})
                        
                        st.success(f"""
                        ✅ Trailer pair added successfully!
                        - NEW: {new_trailer_number} (from {base_location})
                        - OLD: {old_trailer_number} (at {swap_location})
                        - Ready for move assignment
                        """)
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"Error adding trailers: {e}")
                else:
                    st.error("Please fill all required fields")
    
    with tab2:
        st.markdown("### All Registered Trailers")
        
        if not trailers_df.empty:
            # Split by type
            new_trailers = trailers_df[trailers_df['trailer_type'] == 'new']
            old_trailers = trailers_df[trailers_df['trailer_type'] == 'old']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🆕 NEW Trailers (From Fleet)")
                if not new_trailers.empty:
                    display_df = new_trailers[['trailer_number', 'status', 'swap_location']].copy()
                    display_df['Status'] = display_df['status'].apply(
                        lambda x: '✅ Available' if x == 'available' else '🚛 Assigned' if x == 'assigned' else '✔️ Completed'
                    )
                    st.dataframe(display_df[['trailer_number', 'Status', 'swap_location']], 
                                use_container_width=True, hide_index=True)
                else:
                    st.info("No new trailers registered")
            
            with col2:
                st.markdown("#### 🔄 OLD Trailers (To Pickup)")
                if not old_trailers.empty:
                    display_df = old_trailers[['trailer_number', 'status', 'current_location']].copy()
                    display_df['Status'] = display_df['status'].apply(
                        lambda x: '⏳ Waiting' if x == 'available' else '🚛 In Transit' if x == 'assigned' else '✔️ Returned'
                    )
                    st.dataframe(display_df[['trailer_number', 'Status', 'current_location']], 
                                use_container_width=True, hide_index=True)
                else:
                    st.info("No old trailers registered")
        else:
            st.info("No trailers registered yet. Use the 'Add New Trailer Pair' tab to begin.")
    
    with tab3:
        st.markdown("### Pending Trailer Swaps")
        
        if not trailers_df.empty:
            # Get available pairs
            available_new = trailers_df[(trailers_df['trailer_type'] == 'new') & 
                                       (trailers_df['status'] == 'available')]
            
            if not available_new.empty:
                st.success(f"🟢 {len(available_new)} trailer pairs ready for assignment")
                
                for _, trailer in available_new.iterrows():
                    with st.expander(f"Swap: {trailer['trailer_number']} ↔️ Location: {trailer.get('swap_location', 'Unknown')}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown("**NEW Trailer**")
                            st.write(f"Number: {trailer['trailer_number']}")
                            st.write("Location: Fleet Memphis")
                        
                        with col2:
                            st.markdown("**Swap Location**")
                            st.write(trailer.get('swap_location', 'Not specified'))
                            
                            # Get mileage if available
                            from_address = mileage_calc.get_location_full_address("Fleet Memphis")
                            to_address = mileage_calc.get_location_full_address(trailer.get('swap_location', ''))
                            if from_address and to_address:
                                miles, _ = mileage_calc.calculate_mileage_with_cache(
                                    "Fleet Memphis", trailer.get('swap_location', ''), 
                                    from_address, to_address
                                )
                                if miles:
                                    st.write(f"Round Trip: {miles * 2:.1f} miles")
                        
                        with col3:
                            # Find paired old trailer
                            if trailer.get('paired_trailer_id'):
                                old_trailer = trailers_df[trailers_df['id'] == trailer['paired_trailer_id']]
                                if not old_trailer.empty:
                                    st.markdown("**OLD Trailer**")
                                    st.write(f"Number: {old_trailer.iloc[0]['trailer_number']}")
                                    st.write(f"Status: Waiting at location")
                        
                        if st.button(f"➡️ Create Move", key=f"create_{trailer['id']}", use_container_width=True):
                            st.session_state.selected_new_trailer = trailer['trailer_number']
                            st.session_state.selected_swap_location = trailer.get('swap_location')
                            st.session_state.page = "create_move"
                            st.rerun()
            else:
                st.warning("No trailer pairs available for assignment. Add trailer pairs first.")
        else:
            st.info("No trailers registered yet.")

def show_create_move_page():
    """Step 2: Create moves ONLY from existing trailer pairs"""
    st.title("➕ Create Move")
    
    # Get current base location
    base_location = base_mgr.get_default_base_location()
    st.info(f"📍 Base: **{base_location}** | Select trailer pair & assign driver")
    
    # Get data
    trailers_df = db.get_all_trailers()
    drivers_df = db.get_all_drivers()
    locations_df = db.get_all_locations()
    
    # Get available trailer pairs
    available_new = trailers_df[(trailers_df['trailer_type'] == 'new') & 
                               (trailers_df['status'] == 'available')]
    
    if available_new.empty:
        st.error("❌ No trailer pairs available. Please add trailers first in Trailer Management.")
        if st.button("Go to Trailer Management"):
            st.session_state.page = "trailer_management"
            st.rerun()
        return
    
    with st.form("create_move_form", clear_on_submit=True):
        st.markdown("### 🚛 Select Trailer Pair")
        
        # Build options for trailer selection
        trailer_options = []
        trailer_map = {}
        
        for _, trailer in available_new.iterrows():
            # Find paired old trailer
            old_trailer_num = "Unknown"
            if trailer.get('paired_trailer_id'):
                old_trailer = trailers_df[trailers_df['id'] == trailer['paired_trailer_id']]
                if not old_trailer.empty:
                    old_trailer_num = old_trailer.iloc[0]['trailer_number']
            
            option = f"NEW: {trailer['trailer_number']} ↔️ OLD: {old_trailer_num} @ {trailer.get('swap_location', 'Unknown')}"
            trailer_options.append(option)
            trailer_map[option] = {
                'new_id': trailer['id'],
                'new_number': trailer['trailer_number'],
                'old_number': old_trailer_num,
                'location': trailer.get('swap_location', ''),
                'paired_id': trailer.get('paired_trailer_id')
            }
        
        selected_pair = st.selectbox(
            "Select Trailer Pair *",
            [''] + trailer_options,
            help="Choose a pre-registered trailer pair"
        )
        
        if selected_pair and selected_pair in trailer_map:
            pair_data = trailer_map[selected_pair]
            
            # Show details
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Route Details**")
                st.write(f"📍 Start: Fleet Memphis")
                st.write(f"🔄 Swap: {pair_data['location']}")
                st.write(f"📍 Return: Fleet Memphis")
            
            with col2:
                st.markdown("**Trailers**")
                st.write(f"🆕 Deliver: {pair_data['new_number']}")
                st.write(f"🔄 Pickup: {pair_data['old_number']}")
            
            with col3:
                # Calculate mileage
                from_address = mileage_calc.get_location_full_address("Fleet Memphis")
                to_address = mileage_calc.get_location_full_address(pair_data['location'])
                
                if from_address and to_address:
                    one_way_miles, _ = mileage_calc.calculate_mileage_with_cache(
                        "Fleet Memphis", pair_data['location'], from_address, to_address
                    )
                    if one_way_miles:
                        round_trip_miles = one_way_miles * 2
                        st.markdown("**Mileage**")
                        st.write(f"➡️ One way: {one_way_miles} miles")
                        st.write(f"🔄 Round trip: {round_trip_miles} miles")
                    else:
                        round_trip_miles = 0
                        st.warning("⚠️ Mileage calculation unavailable")
                else:
                    round_trip_miles = 0
                    st.warning("⚠️ Address incomplete for mileage")
        
        st.markdown("---")
        st.markdown("### 👤 Driver Assignment")
        
        col1, col2 = st.columns(2)
        
        with col1:
            driver_list = drivers_df['driver_name'].tolist() if not drivers_df.empty else []
            assigned_driver = st.selectbox(
                "Assign Driver *",
                [''] + driver_list,
                help="Select the driver for this round trip"
            )
            
            date_assigned = st.date_input(
                "Assignment Date *",
                value=date.today(),
                help="When the driver is assigned"
            )
        
        with col2:
            # Payment details
            rate = st.number_input("Rate per Mile ($)", value=2.10, min_value=0.0, step=0.01)
            factor_fee = st.number_input("Factor Fee (%)", value=3.0, min_value=0.0, max_value=100.0, step=0.1) / 100
            
            if selected_pair and round_trip_miles > 0:
                load_pay = round_trip_miles * rate * (1 - factor_fee)
                st.metric("💰 Total Load Pay", f"${load_pay:,.2f}")
            else:
                load_pay = 0
        
        st.markdown("---")
        st.markdown("### 📝 Additional Information")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            received_ppw = st.checkbox("Received PPW", value=False)
        with col2:
            processed = st.checkbox("Processed", value=False)
        with col3:
            paid = st.checkbox("Paid", value=False)
        
        comments = st.text_area(
            "Comments",
            placeholder="Any special instructions or notes for this move"
        )
        
        submitted = st.form_submit_button("✅ Create Move", type="primary", use_container_width=True)
        
        if submitted:
            if selected_pair and assigned_driver:
                try:
                    pair_data = trailer_map[selected_pair]
                    
                    # Create the move
                    move_data = {
                        'new_trailer': pair_data['new_number'],
                        'old_trailer': pair_data['old_number'],
                        'pickup_location': 'Fleet Memphis',
                        'destination': pair_data['location'],
                        'assigned_driver': assigned_driver,
                        'date_assigned': date_assigned.strftime('%Y-%m-%d'),
                        'miles': round_trip_miles,
                        'one_way_miles': round_trip_miles / 2 if round_trip_miles > 0 else 0,
                        'round_trip_miles': round_trip_miles,
                        'rate': rate,
                        'factor_fee': factor_fee,
                        'load_pay': load_pay,
                        'received_ppw': received_ppw,
                        'processed': processed,
                        'paid': paid,
                        'comments': comments,
                        'is_round_trip': True,
                        'base_location': 'Fleet Memphis'
                    }
                    
                    move_id = db.add_trailer_move(move_data)
                    
                    # Update trailer statuses
                    db.update_trailer(pair_data['new_id'], {
                        'status': 'assigned',
                        'assigned_to_move_id': move_id
                    })
                    
                    if pair_data.get('paired_id'):
                        db.update_trailer(pair_data['paired_id'], {
                            'status': 'assigned',
                            'assigned_to_move_id': move_id
                        })
                    
                    st.success(f"""
                    ✅ Move #{move_id} created successfully!
                    
                    **Round Trip Details:**
                    - Driver: {assigned_driver}
                    - Route: Fleet Memphis → {pair_data['location']} → Fleet Memphis
                    - Distance: {round_trip_miles} miles
                    - Load Pay: ${load_pay:,.2f}
                    """)
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Error creating move: {e}")
            else:
                st.error("Please select a trailer pair and assign a driver")