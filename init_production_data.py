"""
Initialize Production Data for Smith & Williams Trucking
This version works with both database schemas
"""

import sqlite3
from datetime import date

def init_production_data():
    """Initialize basic production data that works with any schema"""
    try:
        # Use the correct database path
        DB_PATH = 'swt_fleet.db'
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check what tables we have
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Initialize locations if table exists
        if 'locations' in tables:
            cursor.execute("SELECT COUNT(*) FROM locations")
            if cursor.fetchone()[0] == 0:
                # Add Fleet Memphis
                cursor.execute('''
                    INSERT OR IGNORE INTO locations (id, location_title, city, state, location_type, is_base_location)
                    VALUES (1, 'Fleet Memphis', 'Memphis', 'TN', 'base', 1)
                ''')
                
                # Add FedEx locations
                fedex_locations = [
                    ('FedEx Memphis', 'Memphis', 'TN'),
                    ('FedEx Indy', 'Indianapolis', 'IN'),
                    ('FedEx Chicago', 'Chicago', 'IL'),
                    ('FedEx Dallas', 'Dallas', 'TX'),
                    ('FedEx Houston', 'Houston', 'TX'),
                ]
                
                for title, city, state in fedex_locations:
                    cursor.execute('''
                        INSERT OR IGNORE INTO locations (location_title, city, state, location_type, is_base_location)
                        VALUES (?, ?, ?, 'customer', 0)
                    ''', (title, city, state))
        
        # Initialize drivers if table exists
        if 'drivers' in tables:
            cursor.execute("SELECT COUNT(*) FROM drivers")
            if cursor.fetchone()[0] == 0:
                drivers = [
                    ('Brandon Smith', 'active', 'owner'),
                    ('Stephen Williams', 'active', 'owner'),
                    ('Jermichael', 'active', 'driver'),
                    ('Terrance', 'active', 'driver'),
                ]
                
                for name, status, dtype in drivers:
                    cursor.execute('''
                        INSERT OR IGNORE INTO drivers (driver_name, status, driver_type)
                        VALUES (?, ?, ?)
                    ''', (name, status, dtype))
        
        # Initialize trailers if table exists
        if 'trailers' in tables:
            cursor.execute("SELECT COUNT(*) FROM trailers")
            if cursor.fetchone()[0] == 0:
                # Check trailer table structure
                cursor.execute("PRAGMA table_info(trailers)")
                trailer_cols = [col[1] for col in cursor.fetchall()]
                
                # Trailers with locations
                trailers = [
                    ('7155', 'FedEx Houston'), ('7146', 'FedEx Oakland'),
                    ('5955', 'FedEx Indy'), ('6024', 'FedEx Chicago'),
                    ('6061', 'FedEx Dallas'), ('6094', 'Fleet Memphis'),
                    ('6837', 'Fleet Memphis'), ('6017', 'Fleet Memphis'),
                    ('7124', 'Fleet Memphis'), ('7145', 'Fleet Memphis'),
                ]
                
                for trailer_num, location in trailers:
                    if 'current_location_id' in trailer_cols:
                        # Get location_id
                        cursor.execute("SELECT id FROM locations WHERE location_title = ?", (location,))
                        loc_result = cursor.fetchone()
                        loc_id = loc_result[0] if loc_result else 1
                        
                        # Check which columns exist
                        if 'is_new' in trailer_cols and 'trailer_type' in trailer_cols:
                            cursor.execute('''
                                INSERT OR IGNORE INTO trailers (trailer_number, status, current_location_id, is_new, trailer_type)
                                VALUES (?, 'available', ?, 0, 'Roller Bed')
                            ''', (trailer_num, loc_id))
                        elif 'is_new' in trailer_cols:
                            cursor.execute('''
                                INSERT OR IGNORE INTO trailers (trailer_number, status, current_location_id, is_new)
                                VALUES (?, 'available', ?, 0)
                            ''', (trailer_num, loc_id))
                        else:
                            cursor.execute('''
                                INSERT OR IGNORE INTO trailers (trailer_number, status, current_location_id)
                                VALUES (?, 'available', ?)
                            ''', (trailer_num, loc_id))
                    else:
                        # Simple schema with current_location as text
                        cursor.execute('''
                            INSERT OR IGNORE INTO trailers (trailer_number, status, current_location)
                            VALUES (?, 'available', ?)
                        ''', (trailer_num, location))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error initializing data: {str(e)}")
        if conn:
            conn.close()
        return False

if __name__ == "__main__":
    init_production_data()
    print("Production data initialized successfully!")