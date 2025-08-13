"""
Create B. Smith Driver Profile
Sets up driver account with self-assignment permissions
"""

import sqlite3
import hashlib
from datetime import datetime
import json

def hash_password(password):
    """Hash password for security"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_driver_profile():
    """Create B. Smith driver profile"""
    
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    try:
        # Driver details
        driver_name = "B. Smith"
        username = "b_smith"
        password = "driver123"
        password_hash = hash_password(password)
        
        print("Creating driver profile for B. Smith...")
        
        # First check and update drivers table structure
        cursor.execute("PRAGMA table_info(drivers)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # Add any missing columns
        columns_to_add = [
            ('username', 'TEXT UNIQUE'),
            ('password_hash', 'TEXT'),
            ('driver_type', "TEXT DEFAULT 'contractor'"),
            ('active', 'BOOLEAN DEFAULT 1'),
            ('can_self_assign', 'BOOLEAN DEFAULT 1'),
            ('phone', 'TEXT'),
            ('email', 'TEXT'),
            ('max_concurrent_moves', 'INTEGER DEFAULT 1'),
            ('preferred_locations', 'TEXT'),
            ('notification_preferences', 'TEXT')
        ]
        
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                cursor.execute(f"ALTER TABLE drivers ADD COLUMN {col_name} {col_type}")
                print(f"Added column: {col_name}")
        
        # Check if driver exists
        cursor.execute("SELECT id FROM drivers WHERE username = ? OR driver_name = ?", (username, driver_name))
        existing = cursor.fetchone()
        
        if existing:
            driver_id = existing[0]
            # Update existing driver
            cursor.execute("""
                UPDATE drivers 
                SET driver_name = ?,
                    username = ?,
                    password_hash = ?,
                    driver_type = ?,
                    active = 1,
                    can_self_assign = 1,
                    phone = ?,
                    email = ?,
                    max_concurrent_moves = ?,
                    preferred_locations = ?,
                    notification_preferences = ?,
                    status = 'available'
                WHERE id = ?
            """, (
                driver_name,
                username,
                password_hash,
                'contractor',
                '555-SMITH-01',
                'b.smith@smithwilliamstrucking.com',
                1,  # 1 concurrent move at a time as requested
                json.dumps(['Memphis', 'Nashville', 'Little Rock', 'Jackson']),
                json.dumps({
                    'email': True,
                    'sms': True,
                    'in_app': True
                }),
                driver_id
            ))
            print(f"Updated existing driver profile (ID: {driver_id})")
        else:
            # Insert new driver
            cursor.execute("""
                INSERT INTO drivers (
                    driver_name, username, password_hash, driver_type,
                    active, can_self_assign, phone, email,
                    max_concurrent_moves, preferred_locations,
                    notification_preferences, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                driver_name,
                username,
                password_hash,
                'contractor',
                1,
                1,
                '555-SMITH-01',
                'b.smith@smithwilliamstrucking.com',
                1,
                json.dumps(['Memphis', 'Nashville', 'Little Rock', 'Jackson']),
                json.dumps({
                    'email': True,
                    'sms': True,
                    'in_app': True
                }),
                'available'
            ))
            driver_id = cursor.lastrowid
            print(f"Created new driver profile (ID: {driver_id})")
        
        # Ensure driver availability record exists
        cursor.execute("""
            INSERT OR IGNORE INTO driver_availability (
                driver_id, status, completed_moves_today, max_daily_moves
            ) VALUES (?, ?, ?, ?)
        """, (driver_id, 'available', 0, 1))
        
        # Also update/create user account for main app login
        # First check users table structure
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [col[1] for col in cursor.fetchall()]
        
        if 'password_hash' not in user_columns and 'password' in user_columns:
            # Use password column instead
            cursor.execute("""
                INSERT OR REPLACE INTO users (
                    username, password, role, name, email, 
                    phone, created_at, active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username,
                password_hash,  # Store hash in password field
                'Driver',
                driver_name,
                'b.smith@smithwilliamstrucking.com',
                '555-SMITH-01',
                datetime.now().isoformat(),
                1
            ))
        elif 'password_hash' in user_columns:
            cursor.execute("""
                INSERT OR REPLACE INTO users (
                    username, password_hash, role, full_name, email, 
                    phone, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username,
                password_hash,
                'Driver',
                driver_name,
                'b.smith@smithwilliamstrucking.com',
                '555-SMITH-01',
                datetime.now().isoformat(),
                1
            ))
        
        conn.commit()
        
        print("\n" + "="*60)
        print("DRIVER PROFILE CREATED SUCCESSFULLY!")
        print("="*60)
        print(f"Driver Name: {driver_name}")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"Phone: 555-SMITH-01")
        print(f"Email: b.smith@smithwilliamstrucking.com")
        print("\nFeatures enabled:")
        print("✓ Self-assignment enabled")
        print("✓ Max 1 concurrent move (as requested)")
        print("✓ Can report trailer locations")
        print("✓ Can track earnings and progress")
        print("\nYou can now login with these credentials!")
        print("="*60)
        
        # Create test data
        print("\nCreating test trailers for self-assignment testing...")
        create_test_trailers(cursor)
        conn.commit()
        print("Test trailers created successfully!")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


def create_test_trailers(cursor):
    """Create test trailers for B. Smith to self-assign"""
    
    # Ensure base location exists
    cursor.execute("""
        INSERT OR IGNORE INTO locations (
            location_title, street_address, city, state, zip_code, is_base_location
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, ('Fleet Memphis', '123 Fleet Way', 'Memphis', 'TN', '38103', 1))
    
    # Add test locations
    locations = [
        ('Nashville Terminal', '456 Music Row', 'Nashville', 'TN', '37203'),
        ('Little Rock Depot', '789 River Rd', 'Little Rock', 'AR', '72201'),
        ('Jackson Hub', '321 Main St', 'Jackson', 'MS', '39201'),
        ('Birmingham Station', '555 Iron Way', 'Birmingham', 'AL', '35203')
    ]
    
    for loc in locations:
        cursor.execute("""
            INSERT OR IGNORE INTO locations (
                location_title, street_address, city, state, zip_code
            ) VALUES (?, ?, ?, ?, ?)
        """, loc)
    
    # Create available trailer pairs for testing
    test_pairs = [
        ('DEMO-NEW-101', 'DEMO-OLD-201', 'Nashville Terminal', 'Ready for pickup'),
        ('DEMO-NEW-102', 'DEMO-OLD-202', 'Little Rock Depot', 'Standard swap'),
        ('DEMO-NEW-103', 'DEMO-OLD-203', 'Jackson Hub', 'Priority move'),
        ('DEMO-NEW-104', 'DEMO-OLD-204', 'Birmingham Station', 'Long haul'),
        ('DEMO-NEW-105', 'DEMO-OLD-205', 'Nashville Terminal', 'Express delivery')
    ]
    
    created_count = 0
    for new_num, old_num, location, notes in test_pairs:
        # Check if trailer already exists
        cursor.execute("SELECT id FROM trailers WHERE trailer_number = ?", (new_num,))
        if not cursor.fetchone():
            # Insert new trailer
            cursor.execute("""
                INSERT INTO trailers (
                    trailer_number, trailer_type, current_location,
                    status, swap_location, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (new_num, 'new', 'Fleet Memphis', 'available', location, notes))
            new_id = cursor.lastrowid
            
            # Insert old trailer
            cursor.execute("""
                INSERT INTO trailers (
                    trailer_number, trailer_type, current_location,
                    status, swap_location, paired_trailer_id, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (old_num, 'old', location, 'available', location, new_id, f"Pair with {new_num}"))
            old_id = cursor.lastrowid
            
            # Update new trailer with pair
            cursor.execute("UPDATE trailers SET paired_trailer_id = ? WHERE id = ?", (old_id, new_id))
            created_count += 1
    
    print(f"Created {created_count} trailer pairs for testing")


if __name__ == "__main__":
    create_driver_profile()