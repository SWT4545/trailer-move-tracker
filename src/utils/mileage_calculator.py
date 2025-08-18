"""
Mileage calculation using Google Maps API or fallback
"""

import os
import database as db

def calculate_mileage_google(from_address, to_address, api_key=None):
    """Calculate mileage using Google Maps API"""
    try:
        import googlemaps
        
        if not api_key:
            api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        
        if not api_key:
            return None, "Google Maps API key not configured"
        
        gmaps = googlemaps.Client(key=api_key)
        
        # Get distance matrix
        result = gmaps.distance_matrix(
            origins=[from_address],
            destinations=[to_address],
            units="imperial"
        )
        
        if result['status'] == 'OK':
            element = result['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                distance_meters = element['distance']['value']
                distance_miles = distance_meters * 0.000621371  # Convert meters to miles
                return round(distance_miles, 1), None
            else:
                return None, f"Route not found: {element.get('status', 'Unknown error')}"
        else:
            return None, f"API error: {result.get('status', 'Unknown error')}"
            
    except ImportError:
        return None, "googlemaps library not installed"
    except Exception as e:
        return None, str(e)

def calculate_mileage_with_cache(from_location, to_location, from_address=None, to_address=None):
    """Calculate mileage with caching support"""
    
    # Check cache first
    cached = get_cached_mileage(from_location, to_location)
    if cached:
        return cached, "cached"
    
    # If we have full addresses, try Google Maps
    if from_address and to_address:
        miles, error = calculate_mileage_google(from_address, to_address)
        if miles:
            # Cache the result
            cache_mileage(from_location, to_location, miles)
            return miles, "calculated"
        else:
            return None, error
    
    # No addresses available
    return None, "Full addresses required for calculation"

def get_cached_mileage(from_location, to_location):
    """Get cached mileage from database"""
    try:
        import sqlite3
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT miles FROM mileage_cache 
        WHERE from_location = ? AND to_location = ?
        ''', (from_location, to_location))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        return None
    except:
        return None

def cache_mileage(from_location, to_location, miles, source="calculated"):
    """Cache mileage in database"""
    try:
        import sqlite3
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO mileage_cache (from_location, to_location, miles, source)
        VALUES (?, ?, ?, ?)
        ''', (from_location, to_location, miles, source))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_location_full_address(location_name):
    """Get full address for a location from database"""
    locations_df = db.get_all_locations()
    if locations_df.empty:
        return None
    
    location = locations_df[locations_df['location_title'] == location_name]
    if location.empty:
        return None
    
    loc = location.iloc[0]
    
    # Check for full_address field first
    if 'full_address' in loc and loc['full_address']:
        return loc['full_address']
    
    # Build from components
    if 'street_address' in loc and loc['street_address']:
        address_parts = []
        if loc.get('street_address'):
            address_parts.append(loc['street_address'])
        if loc.get('city'):
            address_parts.append(loc['city'])
        if loc.get('state'):
            address_parts.append(loc['state'])
        if loc.get('zip_code'):
            address_parts.append(str(loc['zip_code']))
        
        if address_parts:
            return ', '.join(address_parts) + ', USA'
    
    # Fall back to location_address
    if 'location_address' in loc and loc['location_address']:
        return loc['location_address']
    
    return None