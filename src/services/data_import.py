import pandas as pd
import streamlit as st
from datetime import datetime
import database as db
import utils

def import_excel_file(file_path_or_buffer):
    """
    Import data from Excel file
    Returns: (success, message, stats)
    """
    try:
        # Read all sheets
        excel_data = pd.read_excel(file_path_or_buffer, sheet_name=None)
        
        stats = {
            'trailer_moves': 0,
            'locations': 0,
            'drivers': 0,
            'errors': []
        }
        
        # Import Locations first (if sheet exists)
        if 'Locations' in excel_data:
            locations_df = excel_data['Locations']
            stats['locations'] = import_locations(locations_df)
        
        # Import Drivers (if sheet exists)
        if 'Drivers' in excel_data:
            drivers_df = excel_data['Drivers']
            stats['drivers'] = import_drivers(drivers_df)
        
        # Import Trailer Moves (check for different possible sheet names)
        trailer_sheet_names = ['Trailer Move Tracker', 'Trailer Moves', 'Moves', 'Sheet1']
        trailer_moves_df = None
        
        for sheet_name in trailer_sheet_names:
            if sheet_name in excel_data:
                trailer_moves_df = excel_data[sheet_name]
                break
        
        if trailer_moves_df is not None:
            stats['trailer_moves'] = import_trailer_moves(trailer_moves_df)
        
        # Create summary message
        message = f"Import completed: {stats['trailer_moves']} moves, {stats['locations']} locations, {stats['drivers']} drivers"
        
        if stats['errors']:
            message += f"\nWarnings: {', '.join(stats['errors'])}"
        
        return True, message, stats
        
    except Exception as e:
        return False, f"Import failed: {str(e)}", None

def import_locations(df):
    """Import locations from DataFrame"""
    count = 0
    
    # Expected column mappings
    column_mappings = {
        'Location Title': 'location_title',
        'location_title': 'location_title',
        'Location': 'location_title',
        'Name': 'location_title',
        'Location Address': 'location_address',
        'location_address': 'location_address',
        'Address': 'location_address'
    }
    
    # Rename columns based on mappings
    df = df.rename(columns={k: v for k, v in column_mappings.items() if k in df.columns})
    
    # Clean the data
    df = utils.clean_excel_data(df)
    
    # Import each location
    for _, row in df.iterrows():
        if row.get('location_title'):
            try:
                db.add_location(
                    location_title=row['location_title'],
                    location_address=row.get('location_address', '')
                )
                count += 1
            except Exception as e:
                # Skip duplicates silently
                pass
    
    return count

def import_drivers(df):
    """Import drivers from DataFrame"""
    count = 0
    
    # Expected column mappings
    column_mappings = {
        'Driver Name': 'driver_name',
        'driver_name': 'driver_name',
        'Driver': 'driver_name',
        'Name': 'driver_name',
        'Truck Number': 'truck_number',
        'truck_number': 'truck_number',
        'Truck #': 'truck_number',
        'Company Name': 'company_name',
        'company_name': 'company_name',
        'Company': 'company_name',
        'Company Address': 'company_address',
        'company_address': 'company_address',
        'DOT': 'dot',
        'DOT #': 'dot',
        'MC': 'mc',
        'MC #': 'mc',
        'Insurance': 'insurance'
    }
    
    # Rename columns based on mappings
    df = df.rename(columns={k: v for k, v in column_mappings.items() if k in df.columns})
    
    # Clean the data
    df = utils.clean_excel_data(df)
    
    # Import each driver
    for _, row in df.iterrows():
        if row.get('driver_name'):
            try:
                driver_data = {
                    'driver_name': row['driver_name'],
                    'truck_number': row.get('truck_number', ''),
                    'company_name': row.get('company_name', ''),
                    'company_address': row.get('company_address', ''),
                    'dot': row.get('dot', ''),
                    'mc': row.get('mc', ''),
                    'insurance': row.get('insurance', '')
                }
                db.add_driver(driver_data)
                count += 1
            except Exception as e:
                # Skip duplicates silently
                pass
    
    return count

def import_trailer_moves(df):
    """Import trailer moves from DataFrame"""
    count = 0
    
    # Expected column mappings for various possible column names
    column_mappings = {
        # New trailer columns
        'New Trailer': 'new_trailer',
        'new_trailer': 'new_trailer',
        'New Trailer #': 'new_trailer',
        'Trailer': 'new_trailer',
        
        # Pickup location
        'Pickup Location': 'pickup_location',
        'pickup_location': 'pickup_location',
        'Pickup': 'pickup_location',
        'From': 'pickup_location',
        
        # Destination
        'Destination': 'destination',
        'destination': 'destination',
        'Delivery Location': 'destination',
        'To': 'destination',
        
        # Old trailer columns
        'Old Trailer': 'old_trailer',
        'old_trailer': 'old_trailer',
        'Old Trailer #': 'old_trailer',
        'Previous Trailer': 'old_trailer',
        
        # Old pickup
        'Old Pickup': 'old_pickup',
        'old_pickup': 'old_pickup',
        'Old Pickup Location': 'old_pickup',
        
        # Old destination
        'Old Destination': 'old_destination',
        'old_destination': 'old_destination',
        'Old Delivery': 'old_destination',
        
        # Driver
        'Assigned Driver': 'assigned_driver',
        'assigned_driver': 'assigned_driver',
        'Driver': 'assigned_driver',
        'Driver Name': 'assigned_driver',
        
        # Dates
        'Date Assigned': 'date_assigned',
        'date_assigned': 'date_assigned',
        'Assigned Date': 'date_assigned',
        'Completion Date': 'completion_date',
        'completion_date': 'completion_date',
        'Completed Date': 'completion_date',
        
        # Status fields
        'Received PPW': 'received_ppw',
        'received_ppw': 'received_ppw',
        'PPW': 'received_ppw',
        'Processed': 'processed',
        'processed': 'processed',
        'Paid': 'paid',
        'paid': 'paid',
        'Payment Status': 'paid',
        
        # Financial fields
        'Miles': 'miles',
        'miles': 'miles',
        'Distance': 'miles',
        'Rate': 'rate',
        'rate': 'rate',
        'Rate per Mile': 'rate',
        'Factor Fee': 'factor_fee',
        'factor_fee': 'factor_fee',
        'Factor %': 'factor_fee',
        'Load Pay': 'load_pay',
        'load_pay': 'load_pay',
        'Total Pay': 'load_pay',
        'Payment': 'load_pay',
        
        # Comments
        'Comments': 'comments',
        'comments': 'comments',
        'Notes': 'comments'
    }
    
    # Rename columns based on mappings
    df = df.rename(columns={k: v for k, v in column_mappings.items() if k in df.columns})
    
    # Clean the data
    df = utils.clean_excel_data(df)
    
    # Import each trailer move
    for _, row in df.iterrows():
        try:
            # Prepare data dictionary
            move_data = {}
            
            # Add all standard fields
            fields = ['new_trailer', 'pickup_location', 'destination', 
                     'old_trailer', 'old_pickup', 'old_destination',
                     'assigned_driver', 'date_assigned', 'completion_date',
                     'received_ppw', 'processed', 'paid',
                     'miles', 'rate', 'factor_fee', 'load_pay', 'comments']
            
            for field in fields:
                if field in row:
                    value = row[field]
                    
                    # Handle date fields
                    if field in ['date_assigned', 'completion_date']:
                        if pd.notna(value):
                            if isinstance(value, pd.Timestamp):
                                value = value.strftime('%Y-%m-%d')
                            elif isinstance(value, str) and value:
                                parsed_date = utils.parse_date(value)
                                if parsed_date:
                                    value = parsed_date.strftime('%Y-%m-%d')
                        else:
                            value = None
                    
                    # Handle boolean fields
                    elif field in ['received_ppw', 'processed', 'paid']:
                        value = bool(value) if pd.notna(value) else False
                    
                    # Handle numeric fields
                    elif field in ['miles', 'rate', 'factor_fee', 'load_pay']:
                        value = float(value) if pd.notna(value) else None
                        if field == 'rate' and (value is None or value == 0):
                            value = 2.10
                        elif field == 'factor_fee' and (value is None or value == 0):
                            value = 0.03
                    
                    # Handle string fields
                    else:
                        value = str(value) if pd.notna(value) else ''
                    
                    if value is not None and value != '':
                        move_data[field] = value
            
            # Calculate load_pay if not provided
            if 'load_pay' not in move_data or not move_data['load_pay']:
                if 'miles' in move_data and move_data['miles']:
                    rate = move_data.get('rate', 2.10)
                    factor_fee = move_data.get('factor_fee', 0.03)
                    move_data['load_pay'] = utils.calculate_load_pay(
                        move_data['miles'], rate, factor_fee
                    )
            
            # Only import if there's meaningful data
            if any(move_data.get(f) for f in ['new_trailer', 'pickup_location', 'destination']):
                db.add_trailer_move(move_data)
                count += 1
                
        except Exception as e:
            # Log error but continue with other rows
            continue
    
    return count

def validate_excel_structure(file_path_or_buffer):
    """
    Validate Excel file structure before import
    Returns: (is_valid, message)
    """
    try:
        excel_data = pd.read_excel(file_path_or_buffer, sheet_name=None)
        
        # Check if at least one expected sheet exists
        expected_sheets = ['Trailer Move Tracker', 'Trailer Moves', 'Moves', 
                          'Locations', 'Drivers', 'Sheet1']
        
        found_sheets = [sheet for sheet in expected_sheets if sheet in excel_data]
        
        if not found_sheets:
            return False, "No recognized sheets found in Excel file"
        
        # Check for at least some expected columns in main sheet
        main_sheet = None
        for sheet_name in ['Trailer Move Tracker', 'Trailer Moves', 'Moves', 'Sheet1']:
            if sheet_name in excel_data:
                main_sheet = excel_data[sheet_name]
                break
        
        if main_sheet is not None:
            # Check for at least some trailer move columns
            expected_columns = ['New Trailer', 'Pickup Location', 'Destination', 
                              'new_trailer', 'pickup_location', 'destination',
                              'Trailer', 'From', 'To']
            
            found_columns = [col for col in expected_columns if col in main_sheet.columns]
            
            if not found_columns:
                return False, "Main sheet doesn't contain expected trailer move columns"
        
        return True, f"Valid Excel file with sheets: {', '.join(found_sheets)}"
        
    except Exception as e:
        return False, f"Error reading Excel file: {str(e)}"

def create_sample_excel():
    """Create a sample Excel file with the expected structure"""
    # Create sample data
    trailer_moves = pd.DataFrame({
        'New Trailer': ['TR001', 'TR002'],
        'Pickup Location': ['Location A', 'Location B'],
        'Destination': ['Location C', 'Location D'],
        'Old Trailer': ['TR003', 'TR004'],
        'Old Pickup': ['Location E', 'Location F'],
        'Old Destination': ['Location G', 'Location H'],
        'Assigned Driver': ['John Doe', 'Jane Smith'],
        'Date Assigned': [datetime.now().date(), datetime.now().date()],
        'Completion Date': [None, datetime.now().date()],
        'Received PPW': [False, True],
        'Processed': [False, True],
        'Paid': [False, False],
        'Miles': [150.5, 225.0],
        'Rate': [2.10, 2.10],
        'Factor Fee': [0.03, 0.03],
        'Load Pay': [307.27, 459.23],
        'Comments': ['Sample move 1', 'Sample move 2']
    })
    
    locations = pd.DataFrame({
        'Location Title': ['Location A', 'Location B', 'Location C'],
        'Location Address': ['123 Main St, City A', '456 Oak Ave, City B', '789 Pine Rd, City C']
    })
    
    drivers = pd.DataFrame({
        'Driver Name': ['John Doe', 'Jane Smith'],
        'Truck Number': ['101', '102'],
        'Company Name': ['ABC Transport', 'XYZ Logistics'],
        'Company Address': ['100 Business Blvd', '200 Commerce St'],
        'DOT': ['1234567', '7654321'],
        'MC': ['123456', '654321'],
        'Insurance': ['Policy123', 'Policy456']
    })
    
    # Create Excel file in memory
    from io import BytesIO
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        trailer_moves.to_excel(writer, sheet_name='Trailer Move Tracker', index=False)
        locations.to_excel(writer, sheet_name='Locations', index=False)
        drivers.to_excel(writer, sheet_name='Drivers', index=False)
    
    output.seek(0)
    return output.getvalue()