"""
Initialize Production Data for Smith & Williams Trucking
This is a simplified version that can be deployed with the app
"""

import sqlite3
from datetime import date

def init_production_data():
    """Initialize basic production data"""
    conn = sqlite3.connect('smith_williams_trucking.db')
    cursor = conn.cursor()
    
    # Add locations
    locations = [
        (1, 'Fleet Memphis', 'Memphis', 'TN', 'base', 1),
        (2, 'FedEx Memphis', 'Memphis', 'TN', 'customer', 0),
        (3, 'FedEx Indy', 'Indianapolis', 'IN', 'customer', 0),
        (4, 'FedEx Chicago', 'Chicago', 'IL', 'customer', 0),
    ]
    
    for loc in locations:
        cursor.execute('''
            INSERT OR REPLACE INTO locations (id, location_title, city, state, location_type, is_base_location)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', loc)
    
    # Add drivers
    drivers = [
        ('Brandon Smith', 'active', 'owner'),
        ('Justin Duckett', 'active', 'contractor'),
        ('Carl Strickland', 'active', 'contractor'),
    ]
    
    for driver in drivers:
        cursor.execute('''
            INSERT OR IGNORE INTO drivers (driver_name, status, driver_type)
            VALUES (?, ?, ?)
        ''', driver)
    
    # Add trailers at Fleet Memphis
    fleet_trailers = [
        '190046', '18V00407', '7155', '7146', '5955', 
        '6024', '6061', '3170', '7153', '6015'
    ]
    
    for trailer_num in fleet_trailers:
        cursor.execute('''
            INSERT OR IGNORE INTO trailers (trailer_number, status, current_location)
            VALUES (?, 'available', 'Fleet Memphis')
        ''', (trailer_num,))
    
    # Add trailers at FedEx locations
    fedex_trailers = [
        ('190033', 'FedEx Indy'),
        ('18V00298', 'FedEx Indy'),
        ('7728', 'FedEx Chicago'),
        ('190011', 'FedEx Indy'),
        ('190030', 'FedEx Memphis'),
    ]
    
    for trailer_num, location in fedex_trailers:
        cursor.execute('''
            INSERT OR IGNORE INTO trailers (trailer_number, status, current_location)
            VALUES (?, 'available', ?)
        ''', (trailer_num, location))
    
    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    init_production_data()
    print("Production data initialized successfully!")