"""
Update B. Smith Profile for Dual Role (Admin/Owner + Driver)
Allows single login with role switching capability
"""

import sqlite3
import hashlib
from datetime import datetime
import json

def hash_password(password):
    """Hash password for security"""
    return hashlib.sha256(password.encode()).hexdigest()

def update_b_smith_profile():
    """Update B. Smith to have dual role capabilities"""
    
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    try:
        print("Updating B. Smith profile for dual role (Admin + Driver)...")
        
        # Get real details from user
        print("\n" + "="*60)
        print("Let's set up your real driver profile details")
        print("="*60)
        
        # Use existing or get new info
        real_name = input("Your full name (press Enter for 'B. Smith'): ").strip() or "B. Smith"
        username = "b_smith"  # Keep existing username
        phone = input("Your phone number: ").strip() or "555-SMITH-01"
        email = input("Your email: ").strip() or "b.smith@smithwilliams.com"
        cdl_number = input("Your CDL number (optional): ").strip() or ""
        truck_number = input("Your truck number (optional): ").strip() or ""
        home_base = input("Your home base (e.g., Memphis, Nashville): ").strip() or "Memphis"
        
        # Ask about password change
        change_password = input("\nChange password? (y/n, default: n): ").strip().lower() == 'y'
        if change_password:
            password = input("New password: ").strip()
            password_hash = hash_password(password)
        else:
            password = "driver123"
            password_hash = hash_password(password)
        
        # Update the main users table for dual role
        cursor.execute("""
            UPDATE users 
            SET role = 'Admin+Driver',
                name = ?,
                email = ?,
                phone = ?,
                is_owner = 1,
                active = 1
            WHERE username = ?
        """, (real_name, email, phone, username))
        
        # If user doesn't exist in users table, create it
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO users (
                    username, password, role, name, email, 
                    phone, is_owner, active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username,
                password_hash,
                'Admin+Driver',
                real_name,
                email,
                phone,
                1,  # is_owner
                1,  # active
                datetime.now().isoformat()
            ))
            print("Created new user account with dual role")
        else:
            # Update password if changed
            if change_password:
                cursor.execute("UPDATE users SET password = ? WHERE username = ?", 
                             (password_hash, username))
            print("Updated existing user account to dual role")
        
        # Update driver profile
        cursor.execute("""
            UPDATE drivers 
            SET driver_name = ?,
                phone = ?,
                email = ?,
                password_hash = ?,
                driver_type = 'owner-operator',
                can_self_assign = 1,
                max_concurrent_moves = 3,
                preferred_locations = ?,
                notification_preferences = ?,
                active = 1
            WHERE username = ?
        """, (
            real_name,
            phone,
            email,
            password_hash if change_password else None,
            json.dumps([home_base, 'Memphis', 'Nashville', 'Little Rock', 'Jackson']),
            json.dumps({
                'email': True,
                'sms': True,
                'in_app': True,
                'urgent_only': False
            }),
            username
        ))
        
        # Get driver ID
        cursor.execute("SELECT id FROM drivers WHERE username = ?", (username,))
        driver_result = cursor.fetchone()
        
        if driver_result:
            driver_id = driver_result[0]
        else:
            # Create driver profile if doesn't exist
            cursor.execute("""
                INSERT INTO drivers (
                    driver_name, username, password_hash, phone, email,
                    driver_type, can_self_assign, active, status,
                    max_concurrent_moves, preferred_locations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                real_name,
                username,
                password_hash,
                phone,
                email,
                'owner-operator',
                1,
                1,
                'available',
                3,
                json.dumps([home_base, 'Memphis', 'Nashville', 'Little Rock'])
            ))
            driver_id = cursor.lastrowid
            print(f"Created driver profile (ID: {driver_id})")
        
        # Ensure driver availability exists
        cursor.execute("""
            INSERT OR IGNORE INTO driver_availability (
                driver_id, status, max_daily_moves
            ) VALUES (?, 'available', 3)
        """, (driver_id,))
        
        # Add extended driver info if provided
        if cdl_number or truck_number:
            # Check if we need to add columns
            cursor.execute("PRAGMA table_info(drivers)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'cdl_number' not in columns:
                cursor.execute("ALTER TABLE drivers ADD COLUMN cdl_number TEXT")
            if 'truck_number' not in columns:
                cursor.execute("ALTER TABLE drivers ADD COLUMN truck_number TEXT")
            if 'home_base' not in columns:
                cursor.execute("ALTER TABLE drivers ADD COLUMN home_base TEXT")
            
            cursor.execute("""
                UPDATE drivers 
                SET cdl_number = ?, truck_number = ?, home_base = ?
                WHERE id = ?
            """, (cdl_number, truck_number, home_base, driver_id))
        
        conn.commit()
        
        print("\n" + "="*60)
        print("DUAL ROLE PROFILE UPDATED SUCCESSFULLY!")
        print("="*60)
        print(f"Name: {real_name}")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"Role: Admin + Driver (Owner-Operator)")
        print(f"Phone: {phone}")
        print(f"Email: {email}")
        if cdl_number:
            print(f"CDL: {cdl_number}")
        if truck_number:
            print(f"Truck: {truck_number}")
        print(f"Home Base: {home_base}")
        print("\n✓ Admin access: Full system control")
        print("✓ Driver access: Self-assignment, earnings, moves")
        print("✓ Can switch between roles in the app")
        print("✓ Single login for everything")
        print("\nYou can now login and switch between Admin and Driver views!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"Error updating profile: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    update_b_smith_profile()