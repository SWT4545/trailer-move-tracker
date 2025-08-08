import googlemaps
from datetime import datetime
import streamlit as st
import pandas as pd

def get_distance(origin_address, destination_address, api_key=None):
    """
    Calculate distance using Google Maps Distance Matrix API
    Returns: (one_way_miles, round_trip_miles, status_message)
    """
    if not api_key:
        return None, None, "No API key provided"
    
    try:
        gmaps = googlemaps.Client(key=api_key)
        result = gmaps.distance_matrix(
            origins=[origin_address],
            destinations=[destination_address],
            mode="driving",
            units="imperial"
        )
        
        if result['rows'][0]['elements'][0]['status'] == 'OK':
            distance = result['rows'][0]['elements'][0]['distance']
            miles = distance['value'] / 1609.34  # Convert meters to miles
            return round(miles, 1), round(miles * 2, 1), "Google Maps"
        else:
            return None, None, "Address not found"
    except Exception as e:
        return None, None, f"API Error: {str(e)}"

def calculate_load_pay(miles, rate=2.10, factor_fee=0.03):
    """Calculate load pay based on miles, rate, and factor fee"""
    if miles and rate:
        return round(miles * rate * (1 - factor_fee), 2)
    return 0

def format_currency(value):
    """Format value as currency"""
    if value is None:
        return "$0.00"
    return f"${value:,.2f}"

def format_date(date_value):
    """Format date for display"""
    if date_value is None:
        return ""
    if isinstance(date_value, str):
        try:
            date_value = datetime.strptime(date_value, "%Y-%m-%d")
        except:
            return date_value
    return date_value.strftime("%m/%d/%Y")

def parse_date(date_string):
    """Parse date string to datetime object"""
    if not date_string:
        return None
    if isinstance(date_string, datetime):
        return date_string
    try:
        # Try common date formats
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"]:
            try:
                return datetime.strptime(date_string, fmt)
            except:
                continue
    except:
        pass
    return None

def highlight_paid_rows(row):
    """Highlight paid rows in green"""
    if row.get('paid', False):
        return ['background-color: #d4edda'] * len(row)
    return [''] * len(row)

def get_color_for_status(status):
    """Get color based on status"""
    colors = {
        'paid': '#d4edda',  # Light green
        'unpaid': '#f8d7da',  # Light red
        'in_progress': '#fff3cd',  # Light yellow
        'completed': '#d1ecf1'  # Light blue
    }
    return colors.get(status, '')

def validate_required_fields(data, required_fields):
    """Validate that required fields are present and not empty"""
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    return True, ""

def clean_excel_data(df):
    """Clean and prepare DataFrame from Excel import"""
    # Remove completely empty rows
    df = df.dropna(how='all')
    
    # Convert date columns
    date_columns = ['date_assigned', 'completion_date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Convert boolean columns
    bool_columns = ['received_ppw', 'processed', 'paid']
    for col in bool_columns:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)
    
    # Convert numeric columns
    numeric_columns = ['miles', 'rate', 'factor_fee', 'load_pay']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Set default values
    if 'rate' in df.columns:
        df['rate'] = df['rate'].fillna(2.10)
    if 'factor_fee' in df.columns:
        df['factor_fee'] = df['factor_fee'].fillna(0.03)
    
    # Clean string columns
    string_columns = df.select_dtypes(include=['object']).columns
    for col in string_columns:
        df[col] = df[col].fillna('').astype(str).str.strip()
    
    return df

def create_location_options(locations_df, include_add_new=True):
    """Create location options for selectbox with Add New option"""
    options = [''] + locations_df['location_title'].tolist()
    if include_add_new:
        options.append('➕ Add New Location')
    return options

def create_driver_options(drivers_df, include_add_new=True):
    """Create driver options for selectbox with Add New option"""
    options = [''] + drivers_df['driver_name'].tolist()
    if include_add_new:
        options.append('➕ Add New Driver')
    return options

def show_success_message(message):
    """Show success message with auto-dismiss"""
    placeholder = st.empty()
    placeholder.success(message)
    import time
    time.sleep(3)
    placeholder.empty()

def show_error_message(message):
    """Show error message"""
    st.error(message)

def show_info_message(message):
    """Show info message"""
    st.info(message)

def export_to_excel(trailer_moves_df, locations_df, drivers_df, filename='trailer_moves_export.xlsx'):
    """Export data to Excel file with multiple sheets"""
    from io import BytesIO
    
    # Create a BytesIO object
    output = BytesIO()
    
    # Create Excel writer
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Write trailer moves
        trailer_moves_df.to_excel(writer, sheet_name='Trailer Moves', index=False)
        
        # Write locations
        locations_df.to_excel(writer, sheet_name='Locations', index=False)
        
        # Write drivers
        drivers_df.to_excel(writer, sheet_name='Drivers', index=False)
    
    # Get the Excel file content
    output.seek(0)
    return output.getvalue()

def create_backup(conn):
    """Create a backup of the database"""
    import sqlite3
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'data/backup_{timestamp}.db'
    
    try:
        shutil.copy2('data/trailer_moves.db', backup_path)
        return True, backup_path
    except Exception as e:
        return False, str(e)

def get_mileage_with_fallback(pickup_location, destination, pickup_address=None, destination_address=None):
    """
    Get mileage with multiple fallback options:
    1. Check cache
    2. Try Google Maps API
    3. Manual entry
    """
    import database as db
    
    # First check cache
    cached = db.get_cached_mileage(pickup_location, destination)
    if cached:
        return cached['miles'], cached['round_trip_miles'], "Cached"
    
    # Try Google Maps if addresses are provided and API key exists
    if pickup_address and destination_address:
        if 'GOOGLE_MAPS_API_KEY' in st.secrets and st.secrets['GOOGLE_MAPS_API_KEY']:
            one_way, round_trip, status = get_distance(
                pickup_address, 
                destination_address, 
                st.secrets['GOOGLE_MAPS_API_KEY']
            )
            if one_way:
                return one_way, round_trip, status
    
    # Fall back to manual entry
    return None, None, "Manual Entry Required"

def format_phone(phone):
    """Format phone number for display"""
    if not phone:
        return ""
    # Remove all non-numeric characters
    phone = ''.join(filter(str.isdigit, str(phone)))
    if len(phone) == 10:
        return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
    return phone

def format_percentage(value):
    """Format value as percentage"""
    if value is None:
        return "0%"
    return f"{value * 100:.1f}%"