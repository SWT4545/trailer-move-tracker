"""
Enhanced Location Management System for Smith & Williams Trucking
Allows easy addition and management of locations with partial information
"""

import sqlite3
from datetime import datetime

def update_locations():
    conn = sqlite3.connect('smith_williams_trucking.db')
    cursor = conn.cursor()
    
    print("UPDATING LOCATION DATABASE")
    print("=" * 60)
    
    # Define comprehensive list of FedEx locations
    # Some have full addresses, others just names for now
    fedex_locations = [
        # Existing locations with addresses
        {
            'title': 'FedEx Memphis',
            'address': '2903 Sprankle Ave',
            'city': 'Memphis',
            'state': 'TN',
            'zip_code': '38118',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Indy',
            'address': '6648 South Perimeter Road',
            'city': 'Indianapolis',
            'state': 'IN',
            'zip_code': '46241',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Chicago',
            'address': '632 West Cargo Road',
            'city': 'Chicago',
            'state': 'IL',
            'zip_code': '60666',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Houston',
            'address': '1000 Airport Blvd',
            'city': 'Houston',
            'state': 'TX',
            'zip_code': '77032',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Oakland',
            'address': '8500 Pardee Dr',
            'city': 'Oakland',
            'state': 'CA',
            'zip_code': '94621',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Dallas',
            'address': '2400 Aviation Dr',
            'city': 'DFW Airport',
            'state': 'TX',
            'zip_code': '75261',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Dulles VA',
            'address': '45005 Aviation Dr',
            'city': 'Sterling',
            'state': 'VA',
            'zip_code': '20166',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Hebron KY',
            'address': '1113 Worldwide Blvd',
            'city': 'Hebron',
            'state': 'KY',
            'zip_code': '41048',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Newark NJ',
            'address': '100 Haynes Ave',
            'city': 'Newark',
            'state': 'NJ',
            'zip_code': '07114',
            'type': 'fedex_hub'
        },
        # Additional FedEx locations (can add more as needed)
        {
            'title': 'FedEx Atlanta',
            'address': '',  # Address to be added later
            'city': 'Atlanta',
            'state': 'GA',
            'zip_code': '',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Phoenix',
            'address': '',
            'city': 'Phoenix',
            'state': 'AZ',
            'zip_code': '',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Denver',
            'address': '',
            'city': 'Denver',
            'state': 'CO',
            'zip_code': '',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Seattle',
            'address': '',
            'city': 'Seattle',
            'state': 'WA',
            'zip_code': '',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Miami',
            'address': '',
            'city': 'Miami',
            'state': 'FL',
            'zip_code': '',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Boston',
            'address': '',
            'city': 'Boston',
            'state': 'MA',
            'zip_code': '',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Detroit',
            'address': '',
            'city': 'Detroit',
            'state': 'MI',
            'zip_code': '',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Minneapolis',
            'address': '',
            'city': 'Minneapolis',
            'state': 'MN',
            'zip_code': '',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Kansas City',
            'address': '',
            'city': 'Kansas City',
            'state': 'MO',
            'zip_code': '',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Columbus',
            'address': '',
            'city': 'Columbus',
            'state': 'OH',
            'zip_code': '',
            'type': 'fedex_hub'
        },
        {
            'title': 'FedEx Charlotte',
            'address': '',
            'city': 'Charlotte',
            'state': 'NC',
            'zip_code': '',
            'type': 'fedex_hub'
        }
    ]
    
    # Fleet location (base)
    fleet_location = {
        'title': 'Fleet Memphis',
        'address': '2505 Farrisview Boulevard',
        'city': 'Memphis',
        'state': 'TN',
        'zip_code': '38125',
        'type': 'fleet_base',
        'is_base': True
    }
    
    # Insert or update Fleet Memphis first
    cursor.execute('SELECT id FROM locations WHERE location_title = ?', (fleet_location['title'],))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute('''
            UPDATE locations 
            SET address = ?, city = ?, state = ?, zip_code = ?, 
                location_type = ?, is_base_location = ?
            WHERE location_title = ?
        ''', (
            fleet_location['address'],
            fleet_location['city'],
            fleet_location['state'],
            fleet_location['zip_code'],
            fleet_location['type'],
            1,  # is_base_location
            fleet_location['title']
        ))
        print(f"Updated: {fleet_location['title']}")
    else:
        cursor.execute('''
            INSERT INTO locations 
            (location_title, address, city, state, zip_code, location_type, is_base_location, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fleet_location['title'],
            fleet_location['address'],
            fleet_location['city'],
            fleet_location['state'],
            fleet_location['zip_code'],
            fleet_location['type'],
            1,  # is_base_location
            datetime.now()
        ))
        print(f"Added: {fleet_location['title']}")
    
    # Process all FedEx locations
    for loc in fedex_locations:
        cursor.execute('SELECT id FROM locations WHERE location_title = ?', (loc['title'],))
        existing = cursor.fetchone()
        
        if existing:
            # Update if we have more information
            if loc['address']:  # Only update if we have an address
                cursor.execute('''
                    UPDATE locations 
                    SET address = ?, city = ?, state = ?, zip_code = ?, location_type = ?
                    WHERE location_title = ?
                ''', (
                    loc['address'],
                    loc['city'],
                    loc['state'],
                    loc['zip_code'],
                    loc['type'],
                    loc['title']
                ))
                print(f"Updated: {loc['title']}")
            else:
                print(f"Skipped update (no address): {loc['title']}")
        else:
            # Insert new location
            cursor.execute('''
                INSERT INTO locations 
                (location_title, address, city, state, zip_code, location_type, is_base_location, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                loc['title'],
                loc['address'] or 'Address TBD',
                loc['city'],
                loc['state'],
                loc['zip_code'],
                loc['type'],
                0,  # not base location
                datetime.now()
            ))
            print(f"Added: {loc['title']}")
    
    conn.commit()
    
    # Display summary
    print("\n" + "=" * 60)
    print("LOCATION DATABASE SUMMARY:")
    
    cursor.execute('SELECT COUNT(*) FROM locations')
    total = cursor.fetchone()[0]
    print(f"Total locations: {total}")
    
    cursor.execute('SELECT COUNT(*) FROM locations WHERE location_type = "fedex_hub"')
    fedex_count = cursor.fetchone()[0]
    print(f"FedEx locations: {fedex_count}")
    
    cursor.execute('SELECT COUNT(*) FROM locations WHERE address = "" OR address = "Address TBD"')
    no_address = cursor.fetchone()[0]
    print(f"Locations needing address: {no_address}")
    
    print("\nAll locations:")
    cursor.execute('SELECT location_title, city, state, CASE WHEN address = "" OR address = "Address TBD" THEN "⚠️ No address" ELSE "✓" END as status FROM locations ORDER BY location_title')
    for loc in cursor.fetchall():
        print(f"  {loc[0]} - {loc[1]}, {loc[2]} {loc[3]}")
    
    conn.close()
    print("\nUPDATE COMPLETE!")

def add_custom_location(title, city=None, state=None, address=None, zip_code=None):
    """Helper function to add a single custom location"""
    conn = sqlite3.connect('smith_williams_trucking.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM locations WHERE location_title = ?', (title,))
    if cursor.fetchone():
        print(f"Location '{title}' already exists")
        conn.close()
        return False
    
    cursor.execute('''
        INSERT INTO locations 
        (location_title, address, city, state, zip_code, location_type, is_base_location, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        title,
        address or 'Address TBD',
        city or 'City TBD',
        state or '',
        zip_code or '',
        'fedex_hub' if 'FedEx' in title else 'other',
        0,
        datetime.now()
    ))
    
    conn.commit()
    conn.close()
    print(f"Added location: {title}")
    return True

if __name__ == "__main__":
    update_locations()