"""
Route Learning System for Smith & Williams Trucking
Archives route history and learns optimal mileage for consistent payouts
Prepares location data for Google Maps API integration
"""

import sqlite3
from datetime import datetime
import json

class RouteLearningSystem:
    def __init__(self):
        self.db_path = "smith_williams_trucking.db"
        self.init_route_history_table()
    
    def init_route_history_table(self):
        """Create route history table to track and learn from actual payouts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create route history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS route_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin_location_id INTEGER,
                destination_location_id INTEGER,
                route_key TEXT,  -- e.g., "Fleet Memphis->FedEx Indy"
                actual_miles REAL,
                calculated_miles REAL,
                gross_payout REAL,
                rate_per_mile REAL,
                adjusted_miles REAL,  -- Miles adjusted to match payout
                move_date DATE,
                driver_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (origin_location_id) REFERENCES locations(id),
                FOREIGN KEY (destination_location_id) REFERENCES locations(id)
            )
        ''')
        
        # Create route learning table for averages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS route_learning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_key TEXT UNIQUE,  -- e.g., "Fleet Memphis->FedEx Indy"
                origin_location_id INTEGER,
                destination_location_id INTEGER,
                standard_payout REAL,  -- Expected payout for this route
                average_miles REAL,    -- Average miles to achieve payout
                learned_miles REAL,    -- ML-adjusted miles for exact payout
                sample_count INTEGER,  -- Number of moves for this route
                last_updated TIMESTAMP,
                google_maps_distance REAL,  -- Future: actual Google Maps distance
                google_maps_duration INTEGER,  -- Future: driving time in minutes
                FOREIGN KEY (origin_location_id) REFERENCES locations(id),
                FOREIGN KEY (destination_location_id) REFERENCES locations(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_route(self, origin_id, dest_id, miles, payout, driver_name, move_date):
        """Record a completed route for learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get location names for route key
        cursor.execute('SELECT location_title FROM locations WHERE id = ?', (origin_id,))
        origin = cursor.fetchone()[0]
        cursor.execute('SELECT location_title FROM locations WHERE id = ?', (dest_id,))
        dest = cursor.fetchone()[0]
        
        route_key = f"{origin}->{dest}"
        rate_per_mile = 2.10  # Standard rate
        
        # Calculate adjusted miles to match payout exactly
        adjusted_miles = payout / rate_per_mile
        
        # Record in history
        cursor.execute('''
            INSERT INTO route_history 
            (origin_location_id, destination_location_id, route_key, 
             actual_miles, calculated_miles, gross_payout, rate_per_mile, 
             adjusted_miles, move_date, driver_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (origin_id, dest_id, route_key, miles, miles, 
              payout, rate_per_mile, adjusted_miles, move_date, driver_name))
        
        # Update learning table
        self.update_route_learning(origin_id, dest_id, route_key, adjusted_miles, payout)
        
        conn.commit()
        conn.close()
    
    def update_route_learning(self, origin_id, dest_id, route_key, adjusted_miles, payout):
        """Update the learning table with new route data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if route exists in learning table
        cursor.execute('SELECT id, average_miles, sample_count FROM route_learning WHERE route_key = ?', 
                      (route_key,))
        existing = cursor.fetchone()
        
        if existing:
            # Update with weighted average
            learn_id, avg_miles, count = existing
            new_avg = ((avg_miles * count) + adjusted_miles) / (count + 1)
            
            cursor.execute('''
                UPDATE route_learning 
                SET average_miles = ?, learned_miles = ?, 
                    sample_count = ?, standard_payout = ?,
                    last_updated = ?
                WHERE id = ?
            ''', (new_avg, adjusted_miles, count + 1, payout, datetime.now(), learn_id))
        else:
            # Insert new route
            cursor.execute('''
                INSERT INTO route_learning 
                (route_key, origin_location_id, destination_location_id,
                 standard_payout, average_miles, learned_miles, sample_count, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (route_key, origin_id, dest_id, payout, adjusted_miles, 
                  adjusted_miles, 1, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_learned_miles(self, origin_id, dest_id):
        """Get the learned miles for a route to achieve standard payout"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get location names
        cursor.execute('SELECT location_title FROM locations WHERE id = ?', (origin_id,))
        origin = cursor.fetchone()[0]
        cursor.execute('SELECT location_title FROM locations WHERE id = ?', (dest_id,))
        dest = cursor.fetchone()[0]
        
        route_key = f"{origin}->{dest}"
        
        # Get learned miles
        cursor.execute('''
            SELECT learned_miles, standard_payout, sample_count 
            FROM route_learning 
            WHERE route_key = ?
        ''', (route_key,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'miles': result[0],
                'payout': result[1],
                'confidence': min(result[2] / 10, 1.0)  # Confidence based on sample size
            }
        
        # Return default calculations if no learning data
        return self.get_default_miles(origin, dest)
    
    def get_default_miles(self, origin, dest):
        """Get default miles based on known routes"""
        # Established routes with exact payouts
        known_routes = {
            "Fleet Memphis->FedEx Memphis": {'miles': 95.238095, 'payout': 200.00},
            "Fleet Memphis->FedEx Indy": {'miles': 933.333333, 'payout': 1960.00},
            "Fleet Memphis->FedEx Chicago": {'miles': 1130.0, 'payout': 2373.00},
        }
        
        route_key = f"{origin}->{dest}"
        if route_key in known_routes:
            return {
                'miles': known_routes[route_key]['miles'],
                'payout': known_routes[route_key]['payout'],
                'confidence': 1.0  # High confidence for established routes
            }
        
        # Default for unknown routes
        return {
            'miles': 450.0,
            'payout': 945.00,
            'confidence': 0.0  # No confidence for unknown routes
        }
    
    def prepare_for_google_maps(self):
        """Prepare location data for Google Maps API integration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all locations with full addresses
        cursor.execute('''
            SELECT id, location_title, address, city, state, zip_code,
                   latitude, longitude
            FROM locations
            WHERE address != '' AND address != 'Address TBD'
        ''')
        
        locations = []
        for row in cursor.fetchall():
            loc_id, title, address, city, state, zip_code, lat, lng = row
            
            # Format for Google Maps Geocoding API
            full_address = f"{address}, {city}, {state} {zip_code}".strip()
            
            locations.append({
                'id': loc_id,
                'title': title,
                'full_address': full_address,
                'formatted_for_google': full_address.replace(' ', '+'),
                'latitude': lat,
                'longitude': lng,
                'needs_geocoding': lat is None or lng is None
            })
        
        conn.close()
        return locations
    
    def update_google_maps_data(self, location_id, distance_meters, duration_seconds, lat, lng):
        """Update location with Google Maps data (for future integration)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update location coordinates
        cursor.execute('''
            UPDATE locations 
            SET latitude = ?, longitude = ?
            WHERE id = ?
        ''', (lat, lng, location_id))
        
        # Store in route learning for future use
        # Convert meters to miles
        distance_miles = distance_meters * 0.000621371
        
        cursor.execute('''
            UPDATE route_learning 
            SET google_maps_distance = ?, google_maps_duration = ?
            WHERE origin_location_id = ? OR destination_location_id = ?
        ''', (distance_miles, duration_seconds / 60, location_id, location_id))
        
        conn.commit()
        conn.close()
    
    def get_route_analytics(self):
        """Get analytics on route learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get route statistics
        cursor.execute('''
            SELECT route_key, standard_payout, learned_miles, sample_count
            FROM route_learning
            ORDER BY sample_count DESC
        ''')
        
        routes = cursor.fetchall()
        
        analytics = {
            'total_routes': len(routes),
            'well_learned_routes': sum(1 for r in routes if r[3] >= 5),
            'routes': []
        }
        
        for route in routes:
            analytics['routes'].append({
                'route': route[0],
                'standard_payout': route[1],
                'optimized_miles': route[2],
                'samples': route[3],
                'earnings_per_mile': route[1] / route[2] if route[2] > 0 else 0
            })
        
        conn.close()
        return analytics

# Initialize learning system on import
def init_learning_system():
    """Initialize the route learning system"""
    system = RouteLearningSystem()
    print("Route Learning System initialized")
    print("Ready for Google Maps API integration")
    return system

if __name__ == "__main__":
    # Test the system
    system = init_learning_system()
    
    # Example: Record a completed route
    # system.record_route(
    #     origin_id=1,  # Fleet Memphis
    #     dest_id=2,    # FedEx Indy
    #     miles=933.33,
    #     payout=1960.00,
    #     driver_name="Brandon",
    #     move_date="2025-08-15"
    # )
    
    # Get Google Maps ready data
    maps_data = system.prepare_for_google_maps()
    print(f"\nLocations ready for Google Maps API: {len(maps_data)}")
    
    # Get route analytics
    analytics = system.get_route_analytics()
    print(f"\nRoute Learning Analytics:")
    print(f"Total routes tracked: {analytics['total_routes']}")
    print(f"Well-learned routes (5+ samples): {analytics['well_learned_routes']}")