"""
Setup script to create contractor driver profiles
"""

import sqlite3
from datetime import datetime
import hashlib

def get_connection():
    return sqlite3.connect('trailer_moves.db')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_driver_accounts():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Initialize driver tables from driver_pages module
    from driver_pages import init_driver_tables
    init_driver_tables()
    
    # Driver 1: Justin Duckett
    justin_data = {
        'username': 'j_duckett',
        'password': hash_password('duck123'),
        'role': 'driver',
        'full_name': 'Justin Duckett',
        'company_name': 'L&P Solutions',
        'company_phone': '9012184083',
        'company_address': '4496 Meadow Cliff Dr, Memphis TN, 38125',
        'company_email': 'Lpsolutions1623@gmail.com',
        'dot_number': '3978189',
        'mc_number': '1488650',
        'insurance_company': 'Folsom Insurance',
        'insurance_policy_number': 'KSCW4403105-00',
        'insurance_expiry': '2025-11-26',
        'phone': '9012184083'
    }
    
    # Driver 2: Carl Strickland  
    carl_data = {
        'username': 'c_strickland',
        'password': hash_password('strik123'),
        'role': 'driver',
        'full_name': 'Carl Strickland',
        'company_name': 'Cross State Logistics Inc.',
        'company_phone': '9014974055',
        'company_address': 'P.O. Box 402, Collierville, TN 38027',
        'company_email': 'Strick750@gmail.com',
        'dot_number': '3737098',
        'mc_number': '1321459',
        'insurance_company': 'Diversified Solutions Agency Inc',
        'insurance_policy_number': '02TRM061775-01',
        'insurance_expiry': '2025-12-04',
        'phone': '9014974055'
    }
    
    # Add Owner as Driver account
    owner_driver_data = {
        'username': 'brandon_driver',
        'password': hash_password('owner2024'),
        'role': 'owner_driver',
        'full_name': 'Brandon Smith',
        'company_name': 'Smith & Williams Trucking LLC',
        'company_phone': '9015551234',
        'company_address': '1234 Main St, Memphis, TN 38111',
        'company_email': 'brandon@swtrucking.com',
        'dot_number': '1234567',
        'mc_number': '7654321',
        'insurance_company': 'Primary Insurance Co',
        'insurance_policy_number': 'POL-12345',
        'phone': '9015551234'
    }
    
    drivers = [justin_data, carl_data, owner_driver_data]
    
    for driver in drivers:
        try:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (driver['username'],))
            existing = cursor.fetchone()
            
            if not existing:
                # Create user account
                cursor.execute("""
                    INSERT INTO users (username, password, role)
                    VALUES (?, ?, ?)
                """, (driver['username'], driver['password'], driver['role']))
                
                user_id = cursor.lastrowid
                print(f"Created user account for {driver['full_name']} (ID: {user_id})")
            else:
                user_id = existing[0]
                print(f"User {driver['username']} already exists (ID: {user_id})")
            
            # Check if profile exists
            cursor.execute("SELECT id FROM driver_profiles WHERE user_id = ?", (user_id,))
            profile_exists = cursor.fetchone()
            
            if not profile_exists:
                # Create driver profile
                cursor.execute("""
                    INSERT INTO driver_profiles (
                        user_id, full_name, phone, email, 
                        company_name, company_address, company_phone, company_email,
                        mc_number, dot_number, insurance_company, insurance_policy_number,
                        driver_type, payment_method, w9_on_file, bank_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, driver['full_name'], driver['phone'], driver.get('company_email'),
                    driver['company_name'], driver['company_address'], driver['company_phone'], 
                    driver['company_email'], driver['mc_number'], driver['dot_number'],
                    driver['insurance_company'], driver['insurance_policy_number'],
                    'contractor', 'navy_federal_transfer', False, 'Navy Federal'
                ))
                print(f"Created driver profile for {driver['full_name']}")
            else:
                # Update existing profile with company info
                cursor.execute("""
                    UPDATE driver_profiles SET
                        full_name = ?, phone = ?, 
                        company_name = ?, company_address = ?, company_phone = ?, company_email = ?,
                        mc_number = ?, dot_number = ?, insurance_company = ?, insurance_policy_number = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (
                    driver['full_name'], driver['phone'],
                    driver['company_name'], driver['company_address'], driver['company_phone'], 
                    driver['company_email'], driver['mc_number'], driver['dot_number'],
                    driver['insurance_company'], driver['insurance_policy_number'],
                    user_id
                ))
                print(f"Updated driver profile for {driver['full_name']}")
            
            # Set driver as available
            cursor.execute("""
                INSERT OR REPLACE INTO driver_availability (driver_id, driver_name, is_available)
                VALUES (?, ?, 1)
            """, (user_id, driver['full_name']))
            
        except Exception as e:
            print(f"Error processing {driver['username']}: {e}")
    
    conn.commit()
    conn.close()
    print("\n✅ Driver accounts setup complete!")
    print("\nLogin credentials:")
    print("1. Justin Duckett: j_duckett / duck123")
    print("2. Carl Strickland: c_strickland / strik123")  
    print("3. Owner as Driver: brandon_driver / owner2024")

if __name__ == "__main__":
    create_driver_accounts()