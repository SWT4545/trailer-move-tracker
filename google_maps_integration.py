"""
Google Maps API Integration for Smith & Williams Trucking
Uses existing API to enhance location data while preserving payout calculations
"""

import sqlite3
import os
from datetime import datetime
import googlemaps
from typing import Dict, Optional, Tuple

class GoogleMapsIntegration:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Google Maps API key from environment or parameter"""
        self.api_key = api_key or os.environ.get('GOOGLE_MAPS_API_KEY')
        self.db_path = "smith_williams_trucking.db"
        
        if self.api_key:
            self.gmaps = googlemaps.Client(key=self.api_key)
            self.enabled = True
        else:
            self.gmaps = None
            self.enabled = False
            print("Google Maps API key not found. Using fallback calculations.")
    
    def geocode_location(self, location_id: int) -> Dict:
        """Get coordinates for a location using Google Maps Geocoding API"""
        if not self.enabled:
            return {'success': False, 'message': 'API not enabled'}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get location details
        cursor.execute('''
            SELECT location_title, address, city, state, zip_code
            FROM locations WHERE id = ?
        ''', (location_id,))
        
        location = cursor.fetchone()
        if not location:
            conn.close()
            return {'success': False, 'message': 'Location not found'}
        
        title, address, city, state, zip_code = location
        
        # Build address string
        if address and address != 'Address TBD':
            full_address = f"{address}, {city}, {state} {zip_code}"
        else:
            full_address = f"{title}, {city}, {state}"
        
        try:
            # Geocode the address
            geocode_result = self.gmaps.geocode(full_address)
            
            if geocode_result:
                lat = geocode_result[0]['geometry']['location']['lat']
                lng = geocode_result[0]['geometry']['location']['lng']
                formatted_address = geocode_result[0]['formatted_address']
                
                # Update database with coordinates
                cursor.execute('''
                    UPDATE locations 
                    SET latitude = ?, longitude = ?
                    WHERE id = ?
                ''', (lat, lng, location_id))
                
                conn.commit()
                conn.close()
                
                return {
                    'success': True,
                    'latitude': lat,
                    'longitude': lng,
                    'formatted_address': formatted_address
                }
        except Exception as e:
            conn.close()
            return {'success': False, 'message': str(e)}
        
        conn.close()
        return {'success': False, 'message': 'Geocoding failed'}
    
    def get_route_distance(self, origin_id: int, destination_id: int) -> Dict:
        """Get actual route distance using Google Maps Distance Matrix API"""
        if not self.enabled:
            return self._get_fallback_distance(origin_id, destination_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get location coordinates or addresses
        cursor.execute('''
            SELECT location_title, address, city, state, zip_code, latitude, longitude
            FROM locations WHERE id IN (?, ?)
        ''', (origin_id, destination_id))
        
        locations = cursor.fetchall()
        if len(locations) != 2:
            conn.close()
            return self._get_fallback_distance(origin_id, destination_id)
        
        # Build origin and destination strings
        origin_data = locations[0] if locations[0][0].startswith('Fleet') else locations[1]
        dest_data = locations[1] if locations[1][0].startswith('FedEx') else locations[0]
        
        # Use coordinates if available, otherwise use address
        if origin_data[5] and origin_data[6]:  # Has lat/lng
            origin = (origin_data[5], origin_data[6])
        else:
            origin = f"{origin_data[1]}, {origin_data[2]}, {origin_data[3]} {origin_data[4]}"
        
        if dest_data[5] and dest_data[6]:  # Has lat/lng
            destination = (dest_data[5], dest_data[6])
        else:
            destination = f"{dest_data[1]}, {dest_data[2]}, {dest_data[3]} {dest_data[4]}"
        
        try:
            # Get distance matrix
            matrix = self.gmaps.distance_matrix(
                origins=[origin],
                destinations=[destination],
                mode="driving",
                units="imperial"
            )
            
            if matrix['status'] == 'OK':
                element = matrix['rows'][0]['elements'][0]
                
                if element['status'] == 'OK':
                    # Get one-way distance
                    distance_text = element['distance']['text']
                    distance_miles = element['distance']['value'] * 0.000621371  # meters to miles
                    duration_text = element['duration']['text']
                    duration_hours = element['duration']['value'] / 3600  # seconds to hours
                    
                    # Calculate round trip
                    round_trip_miles = distance_miles * 2
                    
                    # Get our established payout for this route
                    payout_miles = self._get_payout_miles(origin_data[0], dest_data[0])
                    
                    conn.close()
                    
                    return {
                        'success': True,
                        'actual_miles_one_way': distance_miles,
                        'actual_miles_round_trip': round_trip_miles,
                        'payout_miles': payout_miles,  # Keep our established calculation
                        'duration_one_way': duration_text,
                        'duration_hours': duration_hours,
                        'google_distance_text': distance_text,
                        'note': 'Using established payout miles for earnings calculation'
                    }
        except Exception as e:
            print(f"Google Maps API error: {e}")
        
        conn.close()
        return self._get_fallback_distance(origin_id, destination_id)
    
    def _get_fallback_distance(self, origin_id: int, destination_id: int) -> Dict:
        """Get fallback distance based on established routes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get location names
        cursor.execute('SELECT location_title FROM locations WHERE id = ?', (origin_id,))
        origin = cursor.fetchone()[0] if cursor.fetchone() else 'Unknown'
        
        cursor.execute('SELECT location_title FROM locations WHERE id = ?', (destination_id,))
        dest = cursor.fetchone()[0] if cursor.fetchone() else 'Unknown'
        
        conn.close()
        
        payout_miles = self._get_payout_miles(origin, dest)
        
        return {
            'success': True,
            'actual_miles_one_way': payout_miles / 2,
            'actual_miles_round_trip': payout_miles,
            'payout_miles': payout_miles,
            'duration_one_way': 'N/A',
            'duration_hours': 0,
            'google_distance_text': 'Using established route data',
            'note': 'Google Maps API not available - using established values'
        }
    
    def _get_payout_miles(self, origin: str, destination: str) -> float:
        """Get established payout miles for a route"""
        # These are the EXACT miles needed for correct payouts
        # DO NOT CHANGE - these match the business requirements
        established_routes = {
            ('Fleet Memphis', 'FedEx Memphis'): 95.238095,    # $200 / $2.10
            ('Fleet Memphis', 'FedEx Indy'): 933.333333,      # $1960 / $2.10
            ('Fleet Memphis', 'FedEx Chicago'): 1130.0,       # $2373 / $2.10
            ('Fleet Memphis', 'FedEx Houston'): 650.0,        # Estimated
            ('Fleet Memphis', 'FedEx Dallas'): 550.0,         # Estimated
            ('Fleet Memphis', 'FedEx Oakland'): 1000.0,       # Estimated
            ('Fleet Memphis', 'FedEx Atlanta'): 400.0,        # Estimated
            ('Fleet Memphis', 'FedEx Phoenix'): 800.0,        # Estimated
            ('Fleet Memphis', 'FedEx Denver'): 700.0,         # Estimated
            ('Fleet Memphis', 'FedEx Seattle'): 1200.0,       # Estimated
            ('Fleet Memphis', 'FedEx Miami'): 750.0,          # Estimated
            ('Fleet Memphis', 'FedEx Boston'): 900.0,         # Estimated
            ('Fleet Memphis', 'FedEx Detroit'): 600.0,        # Estimated
            ('Fleet Memphis', 'FedEx Minneapolis'): 650.0,    # Estimated
            ('Fleet Memphis', 'FedEx Kansas City'): 350.0,    # Estimated
            ('Fleet Memphis', 'FedEx Columbus'): 500.0,       # Estimated
            ('Fleet Memphis', 'FedEx Charlotte'): 450.0,      # Estimated
            ('Fleet Memphis', 'FedEx Newark NJ'): 850.0,      # Estimated
            ('Fleet Memphis', 'FedEx Dulles VA'): 700.0,      # Estimated
            ('Fleet Memphis', 'FedEx Hebron KY'): 400.0,      # Estimated
        }
        
        # Try exact match
        if (origin, destination) in established_routes:
            return established_routes[(origin, destination)]
        
        # Try reverse (shouldn't happen but just in case)
        if (destination, origin) in established_routes:
            return established_routes[(destination, origin)]
        
        # Default for unknown routes
        return 450.0
    
    def update_all_locations(self):
        """Geocode all locations that don't have coordinates"""
        if not self.enabled:
            return {'success': False, 'message': 'API not enabled'}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get locations without coordinates
        cursor.execute('''
            SELECT id, location_title 
            FROM locations 
            WHERE (latitude IS NULL OR longitude IS NULL)
            AND address != 'Address TBD'
        ''')
        
        locations = cursor.fetchall()
        conn.close()
        
        results = []
        for loc_id, title in locations:
            result = self.geocode_location(loc_id)
            results.append({
                'location': title,
                'success': result['success'],
                'message': result.get('message', 'Geocoded successfully')
            })
        
        return {
            'success': True,
            'updated': len([r for r in results if r['success']]),
            'failed': len([r for r in results if not r['success']]),
            'details': results
        }
    
    def get_route_suggestions(self, origin_id: int) -> list:
        """Get route suggestions with actual vs payout miles"""
        routes = []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all FedEx locations
        cursor.execute('''
            SELECT id, location_title, city, state
            FROM locations
            WHERE location_type = 'fedex_hub'
            ORDER BY location_title
        ''')
        
        destinations = cursor.fetchall()
        
        for dest_id, title, city, state in destinations:
            distance_info = self.get_route_distance(origin_id, dest_id)
            
            routes.append({
                'destination': f"{title} - {city}, {state}",
                'destination_id': dest_id,
                'google_miles': distance_info.get('actual_miles_round_trip', 0),
                'payout_miles': distance_info.get('payout_miles', 0),
                'earnings': distance_info.get('payout_miles', 0) * 2.10,
                'duration': distance_info.get('duration_one_way', 'N/A')
            })
        
        conn.close()
        
        # Sort by earnings
        routes.sort(key=lambda x: x['earnings'], reverse=True)
        
        return routes

# Helper function to set up API key
def setup_google_maps_api(api_key: str):
    """Save Google Maps API key to environment"""
    os.environ['GOOGLE_MAPS_API_KEY'] = api_key
    
    # Also save to a config file for persistence
    with open('.env', 'a') as f:
        f.write(f"\nGOOGLE_MAPS_API_KEY={api_key}")
    
    return True

if __name__ == "__main__":
    # Initialize integration
    maps = GoogleMapsIntegration()
    
    if maps.enabled:
        print("Google Maps API is enabled!")
        
        # Update all locations with geocoding
        # result = maps.update_all_locations()
        # print(f"Geocoding results: {result}")
        
        # Test route distance
        # Fleet Memphis (1) to FedEx Indy (87)
        distance = maps.get_route_distance(1, 87)
        print(f"\nRoute: Fleet Memphis to FedEx Indy")
        print(f"Google Maps actual miles: {distance.get('actual_miles_round_trip', 0):.2f}")
        print(f"Payout calculation miles: {distance.get('payout_miles', 0):.2f}")
        print(f"Earnings: ${distance.get('payout_miles', 0) * 2.10:.2f}")
    else:
        print("Google Maps API key not configured")
        print("Add GOOGLE_MAPS_API_KEY to environment or .env file")