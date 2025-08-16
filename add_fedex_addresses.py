"""
Add FedEx location addresses to the database
"""

import sqlite3

def add_fedex_addresses():
    """Add known FedEx addresses to database"""
    conn = sqlite3.connect('smith_williams_trucking.db')
    cursor = conn.cursor()
    
    # FedEx locations with addresses (add full addresses as we get them)
    fedex_locations = [
        # Main hubs with addresses we know
        ('FedEx Memphis', '3131 Democrat Rd', 'Memphis', 'TN', '38118'),
        ('FedEx Indianapolis', '6311 Airway Dr', 'Indianapolis', 'IN', '46241'),
        ('FedEx Chicago', '1500 N Mannheim Rd', 'Chicago', 'IL', '60666'),
        ('FedEx Dallas', '3121 W Airfield Dr', 'Dallas', 'TX', '75261'),
        ('FedEx Houston', '16303 Air Cargo Rd', 'Houston', 'TX', '77032'),
        ('FedEx Newark NJ', '65 Brewster Rd', 'Newark', 'NJ', '07114'),
        ('FedEx Oakland', '7001 Metropolitan Ave', 'Oakland', 'CA', '94621'),
        ('FedEx Dulles VA', '23445 Autopilot Dr', 'Dulles', 'VA', '20166'),
        ('FedEx Hebron KY', '1055 Worldwide Blvd', 'Hebron', 'KY', '41048'),
        
        # Additional FedEx locations (need full addresses)
        ('FedEx Atlanta', 'TBD', 'Atlanta', 'GA', 'TBD'),
        ('FedEx Phoenix', 'TBD', 'Phoenix', 'AZ', 'TBD'),
        ('FedEx Denver', 'TBD', 'Denver', 'CO', 'TBD'),
        ('FedEx Seattle', 'TBD', 'Seattle', 'WA', 'TBD'),
        ('FedEx Miami', 'TBD', 'Miami', 'FL', 'TBD'),
        ('FedEx Charlotte', 'TBD', 'Charlotte', 'NC', 'TBD'),
        ('FedEx Detroit', 'TBD', 'Detroit', 'MI', 'TBD'),
        ('FedEx Minneapolis', 'TBD', 'Minneapolis', 'MN', 'TBD'),
        ('FedEx Boston', 'TBD', 'Boston', 'MA', 'TBD'),
        ('FedEx Orlando', 'TBD', 'Orlando', 'FL', 'TBD'),
    ]
    
    # Add or update each location
    for location_title, street_address, city, state, zip_code in fedex_locations:
        # Check if location exists
        cursor.execute("SELECT id FROM locations WHERE location_title = ?", (location_title,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing location with address
            cursor.execute("""
                UPDATE locations 
                SET address = ?, city = ?, state = ?, zip_code = ?
                WHERE location_title = ?
            """, (street_address, city, state, zip_code, location_title))
            print(f"Updated address for {location_title}")
        else:
            # Insert new location
            cursor.execute("""
                INSERT INTO locations (location_title, address, city, state, zip_code, location_type, is_base_location)
                VALUES (?, ?, ?, ?, ?, 'customer', 0)
            """, (location_title, street_address, city, state, zip_code))
            print(f"Added new location: {location_title}")
    
    conn.commit()
    conn.close()
    print("\nAll FedEx addresses have been added/updated!")

if __name__ == "__main__":
    add_fedex_addresses()