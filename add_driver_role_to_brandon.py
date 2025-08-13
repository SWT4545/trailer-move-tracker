"""
Add Driver Role to Brandon's Existing Owner Account
Keeps existing login credentials (Brandon / owner123) unchanged
Just adds driver capabilities for dual role functionality
"""

import sqlite3
import hashlib
from datetime import datetime
import json

def add_driver_capabilities_to_brandon():
    """Add driver capabilities to Brandon's existing owner account"""
    
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    try:
        print("Adding driver capabilities to Brandon's owner account...")
        print("Your login credentials remain unchanged: Brandon / owner123")
        print("="*60)
        
        # First, update the users table to show dual role
        cursor.execute("""
            UPDATE users 
            SET role = 'Owner+Driver'
            WHERE username = 'Brandon'
        """)
        
        if cursor.rowcount > 0:
            print("- Updated Brandon's role to Owner+Driver")
        
        # Check if Brandon already has a driver profile
        cursor.execute("""
            SELECT id FROM drivers 
            WHERE username = 'Brandon' OR driver_name = 'Brandon'
        """)
        existing_driver = cursor.fetchone()
        
        if existing_driver:
            driver_id = existing_driver[0]
            print(f"- Found existing driver profile (ID: {driver_id})")
            
            # Update driver profile
            cursor.execute("""
                UPDATE drivers 
                SET driver_type = 'owner-operator',
                    can_self_assign = 1,
                    active = 1,
                    max_concurrent_moves = 3,
                    preferred_locations = ?,
                    notification_preferences = ?
                WHERE id = ?
            """, (
                json.dumps(['Memphis', 'Nashville', 'Little Rock', 'Jackson', 'Birmingham']),
                json.dumps({
                    'email': True,
                    'sms': True,
                    'in_app': True
                }),
                driver_id
            ))
        else:
            # Create driver profile for Brandon
            # Get Brandon's info from users table
            cursor.execute("""
                SELECT name, email, phone, password 
                FROM users WHERE username = 'Brandon'
            """)
            user_info = cursor.fetchone()
            
            if user_info:
                name, email, phone, password_hash = user_info
                
                # Ensure drivers table has all columns
                cursor.execute("PRAGMA table_info(drivers)")
                columns = [col[1] for col in cursor.fetchall()]
                
                required_columns = [
                    ('username', 'TEXT UNIQUE'),
                    ('password_hash', 'TEXT'),
                    ('driver_type', "TEXT DEFAULT 'contractor'"),
                    ('can_self_assign', 'BOOLEAN DEFAULT 1'),
                    ('max_concurrent_moves', 'INTEGER DEFAULT 1'),
                    ('preferred_locations', 'TEXT'),
                    ('notification_preferences', 'TEXT')
                ]
                
                for col_name, col_type in required_columns:
                    if col_name not in columns:
                        cursor.execute(f"ALTER TABLE drivers ADD COLUMN {col_name} {col_type}")
                
                # Insert driver profile
                cursor.execute("""
                    INSERT INTO drivers (
                        driver_name, username, password_hash, phone, email,
                        driver_type, can_self_assign, active, status,
                        max_concurrent_moves, preferred_locations, notification_preferences
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name or 'Brandon',
                    'Brandon',
                    password_hash,
                    phone or '555-OWNER-01',
                    email or 'brandon@smithwilliams.com',
                    'owner-operator',
                    1,  # can_self_assign
                    1,  # active
                    'available',
                    3,  # max_concurrent_moves (owner gets more)
                    json.dumps(['Memphis', 'Nashville', 'Little Rock', 'Jackson', 'Birmingham']),
                    json.dumps({
                        'email': True,
                        'sms': True,
                        'in_app': True
                    })
                ))
                driver_id = cursor.lastrowid
                print(f"- Created driver profile for Brandon (ID: {driver_id})")
            else:
                print("Warning: Brandon user not found, creating minimal driver profile")
                cursor.execute("""
                    INSERT INTO drivers (
                        driver_name, username, driver_type, can_self_assign,
                        active, status, max_concurrent_moves
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ('Brandon', 'Brandon', 'owner-operator', 1, 1, 'available', 3))
                driver_id = cursor.lastrowid
        
        # Ensure driver availability record exists
        cursor.execute("""
            INSERT OR IGNORE INTO driver_availability (
                driver_id, status, max_daily_moves, completed_moves_today
            ) VALUES (?, ?, ?, ?)
        """, (driver_id, 'available', 5, 0))  # Owners get 5 moves per day
        print("- Driver availability record created/verified")
        
        conn.commit()
        
        print("\n" + "="*60)
        print("SUCCESS! Brandon now has dual role capabilities")
        print("="*60)
        print("\nYour Account Details:")
        print("  Username: Brandon (UNCHANGED)")
        print("  Password: owner123 (UNCHANGED)")
        print("  Primary Role: Owner")
        print("  Secondary Role: Driver")
        print("\nNew Capabilities:")
        print("  - Can switch between Owner and Driver modes")
        print("  - Self-assign up to 3 concurrent moves")
        print("  - Track personal driving earnings")
        print("  - Access driver-specific features")
        print("  - Single login for everything")
        print("\nHow to use:")
        print("  1. Login with Brandon / owner123 as usual")
        print("  2. Use role switcher in sidebar to toggle modes")
        print("  3. Owner Mode: Full admin access")
        print("  4. Driver Mode: Self-assignment and driver features")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    add_driver_capabilities_to_brandon()