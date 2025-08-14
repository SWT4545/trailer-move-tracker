"""
Create Test Driver Profile for System Testing
Sets up a driver account with full self-assignment permissions
"""

import sqlite3
import hashlib
from datetime import datetime
import json

def hash_password(password):
    """Hash password for security"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_test_driver():
    """Create test driver profile"""
    
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    try:
        # Driver details
        driver_name = "B. Smith"
        username = "b_smith"
        password = "driver123"
        password_hash = hash_password(password)
        
        # First, ensure the drivers table has all necessary columns
        cursor.execute("PRAGMA table_info(drivers)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # Add missing columns if needed
        if 'user' not in existing_columns:
            cursor.execute("ALTER TABLE drivers ADD COLUMN username TEXT UNIQUE")
        if 'password_hash' not in existing_columns:
            cursor.execute("ALTER TABLE drivers ADD COLUMN password_hash TEXT")
        if 'driver_type' not in existing_columns:
            cursor.execute("ALTER TABLE drivers ADD COLUMN driver_type TEXT DEFAULT 'contractor'")
        if 'active' not in existing_columns:
            cursor.execute("ALTER TABLE drivers ADD COLUMN active BOOLEAN DEFAULT 1")
        if 'can_self_assign' not in existing_columns:
            cursor.execute("ALTER TABLE drivers ADD COLUMN can_self_assign BOOLEAN DEFAULT 1")
        if 'phone' not in existing_columns:
            cursor.execute("ALTER TABLE drivers ADD COLUMN phone TEXT")
        if 'email' not in existing_columns:
            cursor.execute("ALTER TABLE drivers ADD COLUMN email TEXT")
        if 'max_concurrent_moves' not in existing_columns:
            cursor.execute("ALTER TABLE drivers ADD COLUMN max_concurrent_moves INTEGER DEFAULT 1")
        if 'preferred_locations' not in existing_columns:
            cursor.execute("ALTER TABLE drivers ADD COLUMN preferred_locations TEXT")
        if 'notification_preferences' not in existing_columns:
            cursor.execute("ALTER TABLE drivers ADD COLUMN notification_preferences TEXT")
        
        # Check if driver already exists
        cursor.execute("SELECT id FROM drivers WHERE user = ?", (username,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing driver
            driver_id = existing[0]
            cursor.execute("""
                UPDATE drivers 
                SET driver_name = ?,
                    password_hash = ?,
                    driver_type = ?,
                    active = 1,
                    can_self_assign = 1,
                    phone = ?,
                    email = ?,
                    max_concurrent_moves = ?,
                    preferred_locations = ?,
                    notification_preferences = ?
                WHERE id = ?
            """, (
                driver_name,
                password_hash,
                'contractor',
                '555-SMITH-01',
                'b.smith@smithwilliamstrucking.com',
                2,  # Allow 2 concurrent moves for testing
                json.dumps(['Memphis', 'Nashville', 'Little Rock']),
                json.dumps({
                    'email': True,
                    'sms': True,
                    'in_app': True
                }),
                driver_id
            ))
            print(f"Updated existing test driver (ID: {driver_id})")
        else:
            # Insert new driver
            cursor.execute("""
                INSERT INTO drivers (
                    driver_name, username, password_hash, driver_type,
                    active, can_self_assign, phone, email,
                    max_concurrent_moves, preferred_locations,
                    notification_preferences, status, total_miles, total_earnings
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                driver_name,
                username,
                password_hash,
                'contractor',
                1,  # active
                1,  # can_self_assign
                '555-SMITH-01',
                'b.smith@smithwilliamstrucking.com',
                2,  # max_concurrent_moves
                json.dumps(['Memphis', 'Nashville', 'Little Rock']),
                json.dumps({
                    'email': True,
                    'sms': True,
                    'in_app': True
                }),
                'available',
                0,  # total_miles
                0   # total_earnings
            ))
            driver_id = cursor.lastrowid
            print(f"Created new test driver (ID: {driver_id})")
        
        # Ensure driver availability record exists
        cursor.execute("""
            INSERT OR IGNORE INTO driver_availability (
                driver_id, status, completed_moves_today, max_daily_moves
            ) VALUES (?, ?, ?, ?)
        """, (driver_id, 'available', 0, 2))
        
        # Also create a user account for main app login
        cursor.execute("""
            INSERT OR REPLACE INTO users (
                username, password_hash, role, full_name, email, 
                phone, created_at, is_active, permissions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username,
            password_hash,
            'Driver',
            driver_name,
            'b.smith@smithwilliamstrucking.com',
            '555-TEST-001',
            datetime.now(),
            1,
            json.dumps({
                'self_assign': True,
                'view_earnings': True,
                'upload_documents': True,
                'report_trailers': True
            })
        ))
        
        conn.commit()
        
        print("\n" + "="*50)
        print("TEST DRIVER CREATED SUCCESSFULLY!")
        print("="*50)
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"Driver Name: {driver_name}")
        print(f"Phone: 555-SMITH-01")
        print(f"Email: b.smith@smithwilliamstrucking.com")
        print("\nFeatures enabled:")
        print("- Self-assignment: YES")
        print("- Max concurrent moves: 2")
        print("- Preferred locations: Memphis, Nashville, Little Rock")
        print("\nYou can now login to test the self-assignment system!")
        print("="*50)
        
        # Create some test data for realistic testing
        create_test_data = input("\nWould you like to create test trailers and moves? (y/n): ")
        
        if create_test_data.lower() == 'y':
            create_test_trailers_and_moves(cursor)
            conn.commit()
            print("\nTest data created successfully!")
        
        return True
        
    except Exception as e:
        print(f"Error creating test driver: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


def create_test_trailers_and_moves(cursor):
    """Create test trailers and available moves for testing"""
    
    # Ensure Fleet Memphis is set as base location
    cursor.execute("""
        INSERT OR IGNORE INTO locations (
            location_title, street_address, city, state, zip_code, is_base_location
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, ('Fleet Memphis', '123 Fleet Way', 'Memphis', 'TN', '38103', 1))
    
    # Add some test swap locations
    test_locations = [
        ('Nashville Terminal', '456 Music Row', 'Nashville', 'TN', '37203'),
        ('Little Rock Depot', '789 River Rd', 'Little Rock', 'AR', '72201'),
        ('Jackson Hub', '321 Main St', 'Jackson', 'MS', '39201')
    ]
    
    for location in test_locations:
        cursor.execute("""
            INSERT OR IGNORE INTO locations (
                location_title, street_address, city, state, zip_code, is_base_location
            ) VALUES (?, ?, ?, ?, ?, 0)
        """, location)
    
    # Create test trailer pairs
    test_trailers = [
        ('TEST-NEW-001', 'TEST-OLD-001', 'Nashville Terminal'),
        ('TEST-NEW-002', 'TEST-OLD-002', 'Little Rock Depot'),
        ('TEST-NEW-003', 'TEST-OLD-003', 'Jackson Hub'),
        ('TEST-NEW-004', 'TEST-OLD-004', 'Nashville Terminal'),
        ('TEST-NEW-005', 'TEST-OLD-005', 'Little Rock Depot')
    ]
    
    for new_trailer, old_trailer, location in test_trailers:
        # Insert new trailer
        cursor.execute("""
            INSERT OR IGNORE INTO trailers (
                trailer_number, trailer_type, current_location, 
                status, swap_location, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            new_trailer, 'new', 'Fleet Memphis', 
            'available', location, 'Test trailer for demo'
        ))
        new_id = cursor.lastrowid
        
        # Insert old trailer
        cursor.execute("""
            INSERT OR IGNORE INTO trailers (
                trailer_number, trailer_type, current_location,
                status, swap_location, paired_trailer_id, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            old_trailer, 'old', location,
            'available', location, new_id, 'Test trailer for pickup'
        ))
        old_id = cursor.lastrowid
        
        # Update new trailer with pair
        if new_id:
            cursor.execute("""
                UPDATE trailers SET paired_trailer_id = ? WHERE id = ?
            """, (old_id, new_id))
    
    print(f"\nCreated {len(test_trailers)} test trailer pairs")
    print("Locations: Nashville Terminal, Little Rock Depot, Jackson Hub")


if __name__ == "__main__":
    create_test_driver()