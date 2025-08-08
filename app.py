import streamlit as st
import pandas as pd
from datetime import datetime, date
import database as db
import utils
import data_import

# Page configuration
st.set_page_config(
    page_title="Trailer Move Tracker",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
db.init_database()

# Password Protection
def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if 'password' in st.secrets and st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.text_input(
            "Password", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error
        st.text_input(
            "Password", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct
        return True

# Main app
def main():
    if not check_password():
        st.stop()
    
    # Sidebar navigation
    st.sidebar.title("🚛 Trailer Move Tracker")
    
    page = st.sidebar.radio(
        "Navigation",
        ["📊 Dashboard", "➕ Add New Move", "📍 Manage Locations", 
         "👥 Manage Drivers", "🛣️ Manage Mileage", "📁 Import/Export"]
    )
    
    # Add logout button
    if st.sidebar.button("🔒 Logout"):
        st.session_state["password_correct"] = False
        st.rerun()
    
    # Route to appropriate page
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "➕ Add New Move":
        add_new_move()
    elif page == "📍 Manage Locations":
        manage_locations()
    elif page == "👥 Manage Drivers":
        manage_drivers()
    elif page == "🛣️ Manage Mileage":
        manage_mileage()
    elif page == "📁 Import/Export":
        import_export_page()

def show_dashboard():
    """Main dashboard showing all trailer moves"""
    st.title("📊 Trailer Move Dashboard")
    
    # Get summary statistics
    stats = db.get_summary_stats()
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Moves", stats['total_moves'])
    with col2:
        st.metric("Unpaid Moves", stats['unpaid_moves'])
    with col3:
        st.metric("Total Unpaid", utils.format_currency(stats['total_unpaid']))
    with col4:
        st.metric("In Progress", stats['in_progress'])
    with col5:
        st.metric("Total Miles", f"{stats['total_miles']:,.0f}" if stats['total_miles'] else "0")
    
    # Filter options
    st.subheader("Filters")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        filter_status = st.selectbox(
            "Status Filter",
            ["All", "Unpaid", "Paid", "In Progress", "Completed"]
        )
    
    with col2:
        filter_driver = st.selectbox(
            "Driver Filter",
            ["All"] + db.get_all_drivers()['driver_name'].tolist()
        )
    
    with col3:
        filter_date_from = st.date_input("From Date", value=None)
    
    with col4:
        filter_date_to = st.date_input("To Date", value=None)
    
    # Get trailer moves
    moves_df = db.get_all_trailer_moves()
    
    # Apply filters
    if filter_status != "All":
        if filter_status == "Unpaid":
            moves_df = moves_df[moves_df['paid'] == False]
        elif filter_status == "Paid":
            moves_df = moves_df[moves_df['paid'] == True]
        elif filter_status == "In Progress":
            moves_df = moves_df[moves_df['completion_date'].isna()]
        elif filter_status == "Completed":
            moves_df = moves_df[moves_df['completion_date'].notna()]
    
    if filter_driver != "All":
        moves_df = moves_df[moves_df['assigned_driver'] == filter_driver]
    
    if filter_date_from:
        moves_df = moves_df[pd.to_datetime(moves_df['date_assigned']) >= pd.to_datetime(filter_date_from)]
    
    if filter_date_to:
        moves_df = moves_df[pd.to_datetime(moves_df['date_assigned']) <= pd.to_datetime(filter_date_to)]
    
    # Display moves in editable data editor
    st.subheader(f"Trailer Moves ({len(moves_df)} records)")
    
    if not moves_df.empty:
        # Format display columns
        display_df = moves_df.copy()
        
        # Format dates for display
        if 'date_assigned' in display_df.columns:
            display_df['date_assigned'] = pd.to_datetime(display_df['date_assigned']).dt.strftime('%m/%d/%Y')
        if 'completion_date' in display_df.columns:
            display_df['completion_date'] = pd.to_datetime(display_df['completion_date'], errors='coerce').dt.strftime('%m/%d/%Y')
        
        # Format currency
        if 'load_pay' in display_df.columns:
            display_df['load_pay'] = display_df['load_pay'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "$0.00")
        
        # Select columns to display
        display_columns = ['id', 'new_trailer', 'pickup_location', 'destination', 
                          'assigned_driver', 'date_assigned', 'completion_date',
                          'miles', 'load_pay', 'paid', 'comments']
        
        # Filter to only existing columns
        display_columns = [col for col in display_columns if col in display_df.columns]
        
        # Configure column settings for data editor
        column_config = {
            'id': st.column_config.NumberColumn('ID', width=60, disabled=True),
            'new_trailer': st.column_config.TextColumn('New Trailer', width=100),
            'pickup_location': st.column_config.TextColumn('Pickup', width=150),
            'destination': st.column_config.TextColumn('Destination', width=150),
            'assigned_driver': st.column_config.TextColumn('Driver', width=120),
            'date_assigned': st.column_config.TextColumn('Assigned', width=100),
            'completion_date': st.column_config.TextColumn('Completed', width=100),
            'miles': st.column_config.NumberColumn('Miles', width=80),
            'load_pay': st.column_config.TextColumn('Load Pay', width=100),
            'paid': st.column_config.CheckboxColumn('Paid', width=60),
            'comments': st.column_config.TextColumn('Comments', width=200),
        }
        
        # Display editable data grid
        edited_df = st.data_editor(
            display_df[display_columns],
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            key="moves_editor"
        )
        
        # Add action buttons for each row
        st.subheader("Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            move_id = st.number_input("Enter Move ID", min_value=1, step=1, key="action_move_id")
        
        with col2:
            if st.button("📝 Edit Details", key="edit_btn"):
                if move_id and move_id in moves_df['id'].values:
                    st.session_state['edit_move_id'] = move_id
                    st.session_state['show_edit_form'] = True
                else:
                    st.error("Please enter a valid Move ID")
        
        with col3:
            if st.button("🗑️ Delete", type="secondary", key="delete_btn"):
                if move_id and move_id in moves_df['id'].values:
                    db.delete_trailer_move(move_id)
                    st.success(f"Move {move_id} deleted")
                    st.rerun()
                else:
                    st.error("Please enter a valid Move ID")
        
        # Show edit form if requested
        if st.session_state.get('show_edit_form', False):
            edit_move_form(st.session_state.get('edit_move_id'))
    else:
        st.info("No trailer moves found. Add your first move using the '➕ Add New Move' page.")

def edit_move_form(move_id):
    """Show edit form for a specific move"""
    st.subheader(f"Edit Move #{move_id}")
    
    move = db.get_trailer_move_by_id(move_id)
    if not move:
        st.error("Move not found")
        return
    
    with st.form("edit_move_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_trailer = st.text_input("New Trailer", value=move.get('new_trailer', ''))
            pickup_location = st.text_input("Pickup Location", value=move.get('pickup_location', ''))
            destination = st.text_input("Destination", value=move.get('destination', ''))
            old_trailer = st.text_input("Old Trailer", value=move.get('old_trailer', ''))
            old_pickup = st.text_input("Old Pickup", value=move.get('old_pickup', ''))
            old_destination = st.text_input("Old Destination", value=move.get('old_destination', ''))
        
        with col2:
            assigned_driver = st.text_input("Assigned Driver", value=move.get('assigned_driver', ''))
            date_assigned = st.date_input("Date Assigned", value=pd.to_datetime(move.get('date_assigned')) if move.get('date_assigned') else None)
            completion_date = st.date_input("Completion Date", value=pd.to_datetime(move.get('completion_date')) if move.get('completion_date') else None)
            miles = st.number_input("Miles", value=float(move.get('miles', 0)), min_value=0.0, step=0.1)
            rate = st.number_input("Rate", value=float(move.get('rate', 2.10)), min_value=0.0, step=0.01)
            factor_fee = st.number_input("Factor Fee", value=float(move.get('factor_fee', 0.03)), min_value=0.0, max_value=1.0, step=0.01)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            received_ppw = st.checkbox("Received PPW", value=bool(move.get('received_ppw', False)))
        with col2:
            processed = st.checkbox("Processed", value=bool(move.get('processed', False)))
        with col3:
            paid = st.checkbox("Paid", value=bool(move.get('paid', False)))
        
        comments = st.text_area("Comments", value=move.get('comments', ''))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save Changes", type="primary"):
                update_data = {
                    'new_trailer': new_trailer,
                    'pickup_location': pickup_location,
                    'destination': destination,
                    'old_trailer': old_trailer,
                    'old_pickup': old_pickup,
                    'old_destination': old_destination,
                    'assigned_driver': assigned_driver,
                    'date_assigned': date_assigned.strftime('%Y-%m-%d') if date_assigned else None,
                    'completion_date': completion_date.strftime('%Y-%m-%d') if completion_date else None,
                    'miles': miles,
                    'rate': rate,
                    'factor_fee': factor_fee,
                    'received_ppw': received_ppw,
                    'processed': processed,
                    'paid': paid,
                    'comments': comments
                }
                
                db.update_trailer_move(move_id, update_data)
                st.success("Move updated successfully!")
                st.session_state['show_edit_form'] = False
                st.rerun()
        
        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state['show_edit_form'] = False
                st.rerun()

def add_new_move():
    """Page for adding a new trailer move"""
    st.title("➕ Add New Trailer Move")
    
    # Get locations and drivers for dropdowns
    locations_df = db.get_all_locations()
    drivers_df = db.get_all_drivers()
    
    with st.form("add_move_form"):
        st.subheader("📦 Trailer Information")
        col1, col2 = st.columns(2)
        
        with col1:
            new_trailer = st.text_input("New Trailer Number *", placeholder="Enter trailer number")
            
            # Pickup location with add new option
            pickup_options = utils.create_location_options(locations_df)
            pickup_location = st.selectbox("Pickup Location *", pickup_options)
            
            if pickup_location == "➕ Add New Location":
                st.info("Add new pickup location:")
                new_pickup_title = st.text_input("Location Name", key="new_pickup_name")
                new_pickup_address = st.text_input("Location Address", key="new_pickup_address")
        
        with col2:
            # Destination with add new option
            dest_options = utils.create_location_options(locations_df)
            destination = st.selectbox("Destination *", dest_options)
            
            if destination == "➕ Add New Location":
                st.info("Add new destination:")
                new_dest_title = st.text_input("Location Name", key="new_dest_name")
                new_dest_address = st.text_input("Location Address", key="new_dest_address")
        
        st.subheader("🔄 Old Trailer Information (Optional)")
        col1, col2 = st.columns(2)
        
        with col1:
            old_trailer = st.text_input("Old Trailer Number", placeholder="Enter old trailer number")
            old_pickup_options = utils.create_location_options(locations_df)
            old_pickup = st.selectbox("Old Pickup Location", old_pickup_options)
            
            if old_pickup == "➕ Add New Location":
                st.info("Add new old pickup location:")
                new_old_pickup_title = st.text_input("Location Name", key="new_old_pickup_name")
                new_old_pickup_address = st.text_input("Location Address", key="new_old_pickup_address")
        
        with col2:
            old_dest_options = utils.create_location_options(locations_df)
            old_destination = st.selectbox("Old Destination", old_dest_options)
            
            if old_destination == "➕ Add New Location":
                st.info("Add new old destination:")
                new_old_dest_title = st.text_input("Location Name", key="new_old_dest_name")
                new_old_dest_address = st.text_input("Location Address", key="new_old_dest_address")
        
        st.subheader("👤 Driver Assignment")
        col1, col2 = st.columns(2)
        
        with col1:
            # Driver with add new option
            driver_options = utils.create_driver_options(drivers_df)
            assigned_driver = st.selectbox("Assigned Driver *", driver_options)
            
            if assigned_driver == "➕ Add New Driver":
                st.info("Add new driver:")
                new_driver_name = st.text_input("Driver Name *", key="new_driver_name")
                new_truck_number = st.text_input("Truck Number", key="new_truck_number")
                new_company_name = st.text_input("Company Name", key="new_company_name")
        
        with col2:
            date_assigned = st.date_input("Date Assigned *", value=date.today())
            completion_date = st.date_input("Completion Date", value=None)
        
        st.subheader("📏 Mileage & Payment")
        
        # Mileage calculation section
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Check for cached mileage or Google Maps
            mileage_source = "Manual Entry"
            suggested_miles = None
            
            if pickup_location and destination and pickup_location != "➕ Add New Location" and destination != "➕ Add New Location":
                # Check cache first
                cached = db.get_cached_mileage(pickup_location, destination)
                if cached:
                    suggested_miles = cached['miles']
                    mileage_source = "Cached"
                    st.info(f"📍 Cached mileage: {suggested_miles} miles")
                elif 'GOOGLE_MAPS_API_KEY' in st.secrets and st.secrets['GOOGLE_MAPS_API_KEY']:
                    # Try Google Maps
                    pickup_addr = locations_df[locations_df['location_title'] == pickup_location]['location_address'].iloc[0] if not locations_df[locations_df['location_title'] == pickup_location].empty else None
                    dest_addr = locations_df[locations_df['location_title'] == destination]['location_address'].iloc[0] if not locations_df[locations_df['location_title'] == destination].empty else None
                    
                    if pickup_addr and dest_addr:
                        one_way, round_trip, status = utils.get_distance(pickup_addr, dest_addr, st.secrets['GOOGLE_MAPS_API_KEY'])
                        if one_way:
                            suggested_miles = one_way
                            mileage_source = "Google Maps"
                            st.info(f"🗺️ Google Maps: {one_way} miles (one-way), {round_trip} miles (round-trip)")
            
            miles = st.number_input(
                f"Miles ({mileage_source}) *",
                value=suggested_miles if suggested_miles else 0.0,
                min_value=0.0,
                step=0.1
            )
            
            if mileage_source != "Cached" and miles > 0:
                save_mileage = st.checkbox("💾 Save mileage for future use")
        
        with col2:
            rate = st.number_input("Rate per Mile", value=2.10, min_value=0.0, step=0.01)
        
        with col3:
            factor_fee = st.number_input("Factor Fee", value=0.03, min_value=0.0, max_value=1.0, step=0.01)
        
        # Calculate and display load pay
        if miles and rate:
            load_pay = utils.calculate_load_pay(miles, rate, factor_fee)
            st.success(f"💰 Calculated Load Pay: {utils.format_currency(load_pay)}")
        
        st.subheader("📋 Status & Notes")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            received_ppw = st.checkbox("Received PPW")
        with col2:
            processed = st.checkbox("Processed")
        with col3:
            paid = st.checkbox("Paid")
        
        comments = st.text_area("Comments", placeholder="Add any notes or comments...")
        
        # Submit button
        submitted = st.form_submit_button("💾 Save Trailer Move", type="primary", use_container_width=True)
        
        if submitted:
            # Validate required fields
            errors = []
            
            # Handle new location creation if needed
            if pickup_location == "➕ Add New Location":
                if new_pickup_title:
                    db.add_location(new_pickup_title, new_pickup_address)
                    pickup_location = new_pickup_title
                else:
                    errors.append("Please enter a name for the new pickup location")
            
            if destination == "➕ Add New Location":
                if new_dest_title:
                    db.add_location(new_dest_title, new_dest_address)
                    destination = new_dest_title
                else:
                    errors.append("Please enter a name for the new destination")
            
            if old_pickup == "➕ Add New Location" and old_pickup:
                if new_old_pickup_title:
                    db.add_location(new_old_pickup_title, new_old_pickup_address)
                    old_pickup = new_old_pickup_title
            
            if old_destination == "➕ Add New Location" and old_destination:
                if new_old_dest_title:
                    db.add_location(new_old_dest_title, new_old_dest_address)
                    old_destination = new_old_dest_title
            
            # Handle new driver creation if needed
            if assigned_driver == "➕ Add New Driver":
                if new_driver_name:
                    driver_data = {
                        'driver_name': new_driver_name,
                        'truck_number': new_truck_number if 'new_truck_number' in locals() else '',
                        'company_name': new_company_name if 'new_company_name' in locals() else ''
                    }
                    db.add_driver(driver_data)
                    assigned_driver = new_driver_name
                else:
                    errors.append("Please enter a name for the new driver")
            
            # Validate required fields
            if not new_trailer:
                errors.append("New Trailer Number is required")
            if not pickup_location or pickup_location == "":
                errors.append("Pickup Location is required")
            if not destination or destination == "":
                errors.append("Destination is required")
            if not assigned_driver or assigned_driver == "":
                errors.append("Assigned Driver is required")
            if not miles or miles <= 0:
                errors.append("Miles must be greater than 0")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Save mileage to cache if requested
                if 'save_mileage' in locals() and save_mileage and miles > 0:
                    db.add_mileage_cache(pickup_location, destination, miles)
                
                # Prepare move data
                move_data = {
                    'new_trailer': new_trailer,
                    'pickup_location': pickup_location,
                    'destination': destination,
                    'old_trailer': old_trailer if old_trailer else '',
                    'old_pickup': old_pickup if old_pickup and old_pickup != "" and old_pickup != "➕ Add New Location" else '',
                    'old_destination': old_destination if old_destination and old_destination != "" and old_destination != "➕ Add New Location" else '',
                    'assigned_driver': assigned_driver,
                    'date_assigned': date_assigned.strftime('%Y-%m-%d'),
                    'completion_date': completion_date.strftime('%Y-%m-%d') if completion_date else None,
                    'received_ppw': received_ppw,
                    'processed': processed,
                    'paid': paid,
                    'miles': miles,
                    'rate': rate,
                    'factor_fee': factor_fee,
                    'comments': comments
                }
                
                # Add the move
                move_id = db.add_trailer_move(move_data)
                st.success(f"✅ Trailer move added successfully! (ID: {move_id})")
                st.balloons()
                
                # Clear form by rerunning
                st.rerun()

def manage_locations():
    """Page for managing locations"""
    st.title("📍 Manage Locations")
    
    tab1, tab2 = st.tabs(["View/Edit Locations", "Add New Location"])
    
    with tab1:
        locations_df = db.get_all_locations()
        
        if not locations_df.empty:
            st.subheader(f"All Locations ({len(locations_df)} total)")
            
            # Make editable data frame
            edited_df = st.data_editor(
                locations_df[['id', 'location_title', 'location_address']],
                column_config={
                    'id': st.column_config.NumberColumn('ID', disabled=True, width=60),
                    'location_title': st.column_config.TextColumn('Location Name', width=200),
                    'location_address': st.column_config.TextColumn('Address', width=400)
                },
                use_container_width=True,
                hide_index=True,
                key="locations_editor"
            )
            
            # Delete location
            st.subheader("Delete Location")
            col1, col2 = st.columns(2)
            with col1:
                location_id = st.number_input("Location ID to delete", min_value=1, step=1)
            with col2:
                if st.button("🗑️ Delete Location", type="secondary"):
                    if location_id in locations_df['id'].values:
                        db.delete_location(location_id)
                        st.success(f"Location {location_id} deleted")
                        st.rerun()
                    else:
                        st.error("Invalid Location ID")
        else:
            st.info("No locations found. Add your first location below.")
    
    with tab2:
        st.subheader("Add New Location")
        with st.form("add_location_form"):
            location_title = st.text_input("Location Name *", placeholder="e.g., Dallas Terminal")
            location_address = st.text_input("Address", placeholder="e.g., 123 Main St, Dallas, TX 75201")
            
            if st.form_submit_button("➕ Add Location", type="primary"):
                if location_title:
                    location_id = db.add_location(location_title, location_address)
                    if location_id:
                        st.success(f"✅ Location '{location_title}' added successfully!")
                        st.rerun()
                    else:
                        st.warning("Location might already exist")
                else:
                    st.error("Location name is required")

def manage_drivers():
    """Page for managing drivers"""
    st.title("👥 Manage Drivers")
    
    tab1, tab2 = st.tabs(["View/Edit Drivers", "Add New Driver"])
    
    with tab1:
        drivers_df = db.get_all_drivers()
        
        if not drivers_df.empty:
            st.subheader(f"All Drivers ({len(drivers_df)} total)")
            
            # Display editable data frame
            display_columns = ['id', 'driver_name', 'truck_number', 'company_name', 'dot', 'mc']
            edited_df = st.data_editor(
                drivers_df[display_columns],
                column_config={
                    'id': st.column_config.NumberColumn('ID', disabled=True, width=60),
                    'driver_name': st.column_config.TextColumn('Driver Name', width=150),
                    'truck_number': st.column_config.TextColumn('Truck #', width=80),
                    'company_name': st.column_config.TextColumn('Company', width=200),
                    'dot': st.column_config.TextColumn('DOT', width=100),
                    'mc': st.column_config.TextColumn('MC', width=100)
                },
                use_container_width=True,
                hide_index=True,
                key="drivers_editor"
            )
            
            # Delete driver
            st.subheader("Delete Driver")
            col1, col2 = st.columns(2)
            with col1:
                driver_id = st.number_input("Driver ID to delete", min_value=1, step=1)
            with col2:
                if st.button("🗑️ Delete Driver", type="secondary"):
                    if driver_id in drivers_df['id'].values:
                        db.delete_driver(driver_id)
                        st.success(f"Driver {driver_id} deleted")
                        st.rerun()
                    else:
                        st.error("Invalid Driver ID")
        else:
            st.info("No drivers found. Add your first driver below.")
    
    with tab2:
        st.subheader("Add New Driver")
        with st.form("add_driver_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                driver_name = st.text_input("Driver Name *", placeholder="John Doe")
                truck_number = st.text_input("Truck Number", placeholder="101")
                company_name = st.text_input("Company Name", placeholder="ABC Transport")
                company_address = st.text_area("Company Address", placeholder="123 Business Blvd...")
            
            with col2:
                dot = st.text_input("DOT Number", placeholder="1234567")
                mc = st.text_input("MC Number", placeholder="123456")
                insurance = st.text_input("Insurance", placeholder="Policy123")
            
            if st.form_submit_button("➕ Add Driver", type="primary"):
                if driver_name:
                    driver_data = {
                        'driver_name': driver_name,
                        'truck_number': truck_number,
                        'company_name': company_name,
                        'company_address': company_address,
                        'dot': dot,
                        'mc': mc,
                        'insurance': insurance
                    }
                    
                    try:
                        driver_id = db.add_driver(driver_data)
                        st.success(f"✅ Driver '{driver_name}' added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding driver: {str(e)}")
                else:
                    st.error("Driver name is required")

def manage_mileage():
    """Page for managing mileage cache"""
    st.title("🛣️ Manage Mileage Cache")
    
    mileage_df = db.get_all_mileage_cache()
    
    if not mileage_df.empty:
        st.subheader(f"Cached Routes ({len(mileage_df)} total)")
        
        # Display mileage cache
        edited_df = st.data_editor(
            mileage_df,
            column_config={
                'id': st.column_config.NumberColumn('ID', disabled=True, width=60),
                'from_location': st.column_config.TextColumn('From', width=200),
                'to_location': st.column_config.TextColumn('To', width=200),
                'miles': st.column_config.NumberColumn('One-Way Miles', width=120),
                'round_trip_miles': st.column_config.NumberColumn('Round Trip', width=120)
            },
            use_container_width=True,
            hide_index=True,
            key="mileage_editor"
        )
        
        # Add new mileage cache
        st.subheader("Add/Update Route")
        with st.form("add_mileage_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                locations_df = db.get_all_locations()
                location_options = locations_df['location_title'].tolist() if not locations_df.empty else []
                from_location = st.selectbox("From Location", [''] + location_options)
            
            with col2:
                to_location = st.selectbox("To Location", [''] + location_options)
            
            with col3:
                miles = st.number_input("One-Way Miles", min_value=0.0, step=0.1)
            
            if st.form_submit_button("💾 Save Route"):
                if from_location and to_location and miles > 0:
                    db.add_mileage_cache(from_location, to_location, miles)
                    st.success("Route saved successfully!")
                    st.rerun()
                else:
                    st.error("Please fill all fields")
        
        # Delete mileage cache
        st.subheader("Delete Route")
        col1, col2 = st.columns(2)
        with col1:
            cache_id = st.number_input("Route ID to delete", min_value=1, step=1)
        with col2:
            if st.button("🗑️ Delete Route", type="secondary"):
                if cache_id in mileage_df['id'].values:
                    db.delete_mileage_cache(cache_id)
                    st.success(f"Route {cache_id} deleted")
                    st.rerun()
                else:
                    st.error("Invalid Route ID")
    else:
        st.info("No cached routes found. Routes will be saved automatically when you add new moves.")

def import_export_page():
    """Page for importing and exporting data"""
    st.title("📁 Import/Export Data")
    
    tab1, tab2, tab3 = st.tabs(["Import Excel", "Export Data", "Backup/Restore"])
    
    with tab1:
        st.subheader("Import from Excel")
        st.info("Upload your existing 'Trailer Move Tracker.xlsx' file to import all data")
        
        uploaded_file = st.file_uploader(
            "Choose Excel file",
            type=['xlsx', 'xls'],
            help="Select your Excel file containing trailer moves, locations, and drivers"
        )
        
        if uploaded_file is not None:
            # Validate file structure
            is_valid, message = data_import.validate_excel_structure(uploaded_file)
            
            if is_valid:
                st.success(f"✅ {message}")
                
                if st.button("📥 Import Data", type="primary"):
                    with st.spinner("Importing data..."):
                        success, import_message, stats = data_import.import_excel_file(uploaded_file)
                        
                        if success:
                            st.success(import_message)
                            if stats:
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Moves Imported", stats['trailer_moves'])
                                with col2:
                                    st.metric("Locations Imported", stats['locations'])
                                with col3:
                                    st.metric("Drivers Imported", stats['drivers'])
                        else:
                            st.error(import_message)
            else:
                st.error(f"❌ {message}")
                st.info("Please ensure your Excel file has the correct structure")
        
        # Download sample template
        st.subheader("Download Sample Template")
        st.write("Need a template? Download a sample Excel file with the correct structure:")
        
        sample_excel = data_import.create_sample_excel()
        st.download_button(
            label="📥 Download Sample Excel Template",
            data=sample_excel,
            file_name="trailer_moves_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with tab2:
        st.subheader("Export to Excel")
        st.write("Export all your data to an Excel file")
        
        # Get all data
        moves_df = db.get_all_trailer_moves()
        locations_df = db.get_all_locations()
        drivers_df = db.get_all_drivers()
        
        # Display counts
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Moves", len(moves_df))
        with col2:
            st.metric("Total Locations", len(locations_df))
        with col3:
            st.metric("Total Drivers", len(drivers_df))
        
        # Export button
        if st.button("📤 Generate Excel Export", type="primary"):
            excel_data = utils.export_to_excel(moves_df, locations_df, drivers_df)
            
            st.download_button(
                label="💾 Download Excel File",
                data=excel_data,
                file_name=f"trailer_moves_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with tab3:
        st.subheader("Database Backup & Restore")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Create Backup**")
            st.write("Save a complete backup of your database")
            
            if st.button("🔒 Create Backup", type="primary"):
                import shutil
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f'trailer_moves_backup_{timestamp}.db'
                
                try:
                    with open('data/trailer_moves.db', 'rb') as f:
                        backup_data = f.read()
                    
                    st.download_button(
                        label="💾 Download Backup",
                        data=backup_data,
                        file_name=backup_path,
                        mime="application/octet-stream"
                    )
                    st.success("Backup created successfully!")
                except Exception as e:
                    st.error(f"Error creating backup: {str(e)}")
        
        with col2:
            st.write("**Restore from Backup**")
            st.write("Replace current database with a backup")
            st.warning("⚠️ This will overwrite all current data!")
            
            backup_file = st.file_uploader(
                "Choose backup file",
                type=['db'],
                key="backup_uploader"
            )
            
            if backup_file is not None:
                if st.button("⚠️ Restore Backup", type="secondary"):
                    try:
                        # Save uploaded file to database location
                        with open('data/trailer_moves.db', 'wb') as f:
                            f.write(backup_file.getbuffer())
                        
                        st.success("✅ Database restored successfully!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error restoring backup: {str(e)}")

if __name__ == "__main__":
    main()