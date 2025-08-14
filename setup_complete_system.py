"""
Complete System Setup
Creates database and loads all production data
"""

import sqlite3
from datetime import datetime
import os

def setup_complete_system():
    print("COMPLETE SYSTEM SETUP")
    print("=" * 70)
    
    # Remove old database if exists
    if os.path.exists('trailers.db'):
        os.remove('trailers.db')
        print("Removed old database")
    
    # Create new database
    conn = sqlite3.connect('trailers.db')
    cursor = conn.cursor()
    
    # Create all tables
    print("Creating database tables...")
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'viewer',
        created_date TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS trailers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trailer_number TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'available',
        location TEXT,
        last_updated TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        move_id TEXT UNIQUE,
        old_trailer TEXT,
        new_trailer TEXT,
        pickup_location TEXT,
        delivery_location TEXT,
        driver_name TEXT,
        status TEXT DEFAULT 'pending',
        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
        total_miles REAL DEFAULT 0,
        estimated_miles REAL,
        actual_client_payment REAL,
        driver_pay REAL DEFAULT 0,
        factoring_fee REAL,
        service_fee REAL,
        payment_status TEXT DEFAULT 'pending',
        payment_date TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_name TEXT UNIQUE NOT NULL,
        company_name TEXT,
        phone TEXT,
        address TEXT,
        city TEXT,
        state TEXT,
        zip TEXT,
        dot_number TEXT,
        mc_number TEXT,
        email TEXT,
        insurance_company TEXT,
        insurance_policy TEXT,
        insurance_exp TEXT,
        cdl_number TEXT,
        cdl_exp TEXT,
        coi_uploaded INTEGER DEFAULT 0,
        w9_uploaded INTEGER DEFAULT 0,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_name TEXT UNIQUE NOT NULL,
        address TEXT,
        city TEXT,
        state TEXT,
        zip TEXT,
        phone TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_name TEXT,
        payment_date TEXT,
        amount REAL,
        service_fee REAL DEFAULT 6.00,
        miles REAL,
        status TEXT DEFAULT 'pending',
        notes TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id TEXT UNIQUE,
        client_payment REAL,
        factoring_fee REAL,
        service_fee REAL,
        num_drivers INTEGER,
        submission_date TEXT,
        payment_date TEXT,
        status TEXT DEFAULT 'pending',
        notes TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS submission_moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id TEXT,
        move_id TEXT,
        driver_name TEXT,
        gross_amount REAL,
        net_amount REAL,
        FOREIGN KEY (submission_id) REFERENCES submissions(submission_id)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS route_pricing (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pickup_location TEXT,
        delivery_location TEXT,
        standard_payment REAL,
        miles REAL,
        last_updated TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS company_info (
        id INTEGER PRIMARY KEY,
        company_name TEXT,
        company_address TEXT,
        company_city TEXT,
        company_state TEXT,
        company_zip TEXT,
        company_phone TEXT,
        company_email TEXT,
        company_website TEXT,
        company_ein TEXT,
        company_dot TEXT,
        company_mc TEXT
    )''')
    
    print("Tables created successfully")
    
    # Add company info
    cursor.execute('DELETE FROM company_info')
    cursor.execute('''INSERT INTO company_info VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (1, 'Smith & Williams Trucking', '7600 N 15th St Suite 150', 'Phoenix', 'AZ', '85020',
         '(951) 437-5474', 'dispatch@smithwilliamstrucking.com', 'www.smithwilliamstrucking.com',
         '88-1234567', 'DOT# 3456789', 'MC# 1234567'))
    print("Added company information")
    
    # Add users
    users = [
        ('admin', 'admin123', 'admin'),
        ('j_duckett', 'duck123', 'driver'),
        ('c_strikland', 'strik123', 'driver'),
        ('b_smith', 'metro123', 'driver'),
        ('dispatch', 'dispatch123', 'coordinator'),
        ('viewer', 'view123', 'viewer')
    ]
    
    for user in users:
        cursor.execute('INSERT OR REPLACE INTO users (username, password, role) VALUES (?, ?, ?)', user)
    print(f"Added {len(users)} users")
    
    # Add locations
    locations = [
        ("Fleet Memphis", "2505 Farrisview Boulevard", "Memphis", "TN", "38114", "7082853823"),
        ("FedEx Memphis", "2903 Sprankle Ave", "Memphis", "TN", "38118", "7082853823"),
        ("FedEx Indy", "6648 South Perimeter Road", "Indianapolis", "IN", "46241", "7082853823"),
        ("FedEx Chicago", "632 West Cargo Road", "Chicago", "IL", "60666", "7082853823")
    ]
    
    for loc in locations:
        cursor.execute('INSERT OR REPLACE INTO locations (location_name, address, city, state, zip, phone) VALUES (?, ?, ?, ?, ?, ?)', loc)
    print(f"Added {len(locations)} locations")
    
    # Add drivers
    drivers = [
        ("Justin Duckett", "L&P Solutions", "9012184083", "4496 Meadow Cliff Dr", "Memphis", "TN", "38125",
         "3978189", "1488650", "Lpsolutions1623@gmail.com", "Folsom insurance", "KSCW4403105-00", "11/26/2025", "", "", 1, 1),
        ("Carl Strikland", "Cross State Logistics Inc.", "9014974055", "P.O. Box 402", "Collierville", "TN", "38027",
         "3737098", "1321459", "Strick750@gmail.com", "Diversified Solutions Agency Inc", "02TRM061775-01", "12/04/2025", "", "", 1, 1),
        ("Brandon Smith", "Metro Logistics", "9015551234", "123 Main St", "Memphis", "TN", "38103",
         "1234567", "7654321", "brandon@metrologistics.com", "Progressive", "POL-12345", "01/15/2026", "", "", 1, 1)
    ]
    
    for driver in drivers:
        cursor.execute('''INSERT OR REPLACE INTO drivers (driver_name, company_name, phone, address, city, state, zip,
                         dot_number, mc_number, email, insurance_company, insurance_policy, insurance_exp,
                         cdl_number, cdl_exp, coi_uploaded, w9_uploaded) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', driver)
    print(f"Added {len(drivers)} drivers")
    
    # Add trailers
    trailers = [
        # New trailers at Fleet Memphis
        ("190010", "available", "Fleet Memphis"),
        ("190033", "available", "Fleet Memphis"),
        ("190046", "available", "Fleet Memphis"),
        ("18V00298", "available", "Fleet Memphis"),
        ("7728", "available", "Fleet Memphis"),
        # Old trailers
        ("7155", "available", "Memphis"),
        ("7146", "available", "Memphis"),
        ("5955", "available", "Memphis"),
        ("6024", "available", "Memphis"),
        ("6061", "available", "Memphis"),
        ("6094", "available", "Memphis"),
        ("3170", "available", "Memphis"),
        ("7153", "available", "Memphis"),
        ("6015", "available", "Memphis"),
        ("7160", "available", "Memphis"),
        ("6783", "available", "Memphis"),
        ("3083", "available", "FedEx Indy"),
        ("6837", "available", "FedEx Indy"),
        ("6231", "available", "FedEx Indy")
    ]
    
    for trailer in trailers:
        cursor.execute('INSERT OR REPLACE INTO trailers (trailer_number, status, location) VALUES (?, ?, ?)', trailer)
    print(f"Added {len(trailers)} trailers")
    
    # Add route pricing
    routes = [
        ('FedEx Memphis', 'Fleet Memphis', 200.00, 10),
        ('Memphis', 'Chicago', 2373.00, 530),
        ('Memphis', 'FedEx Indy', 1960.00, 280),
    ]
    
    for route in routes:
        cursor.execute('''INSERT OR REPLACE INTO route_pricing 
                         (pickup_location, delivery_location, standard_payment, miles, last_updated)
                         VALUES (?, ?, ?, ?, ?)''', 
                      route + (datetime.now().strftime('%Y-%m-%d'),))
    print(f"Added {len(routes)} route prices")
    
    # Add moves with correct payment calculations
    moves = [
        # Justin's moves - Total gross $2,360, Net $2,287.20
        ("MOV-001", "6014", "18V00327", "FedEx Memphis", "Fleet Memphis", "Justin Duckett", 
         "completed", "2025-08-09", 200.00, 193.67, 5.82, 0.67, "paid", "2025-08-13"),
        ("MOV-002", "7144", "190030", "FedEx Memphis", "Fleet Memphis", "Justin Duckett",
         "completed", "2025-08-09", 200.00, 193.67, 5.82, 0.67, "paid", "2025-08-13"),
        ("MOV-003", "7131", "190011", "Memphis", "FedEx Indy", "Justin Duckett",
         "completed", "2025-08-11", 1960.00, 1899.86, 57.14, 0.67, "paid", "2025-08-13"),
        
        # Carl's move - Gross $1,960, Net $1,899.20
        ("MOV-004", "7162", "190033", "Memphis", "FedEx Indy", "Carl Strikland",
         "completed", "2025-08-11", 1960.00, 1899.20, 58.80, 2.00, "paid", "2025-08-13"),
        
        # Brandon's move - Gross $2,373, Net $2,299.81
        ("MOV-005", "5906", "7728", "Memphis", "Chicago", "Brandon Smith",
         "completed", "2025-08-11", 2373.00, 2299.81, 71.19, 2.00, "paid", "2025-08-13"),
        
        # Brandon's in-progress move
        ("MOV-006", "6981", "18V00298", "Memphis", "FedEx Indy", "Brandon Smith",
         "completed", "2025-08-13", None, None, None, None, "pending", None)
    ]
    
    for move in moves:
        cursor.execute('''INSERT INTO moves (move_id, old_trailer, new_trailer, pickup_location, delivery_location,
                         driver_name, status, created_date, actual_client_payment, driver_pay, factoring_fee,
                         service_fee, payment_status, payment_date)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', move)
    print(f"Added {len(moves)} moves")
    
    # Add payment records
    payments = [
        ("Justin Duckett", "2025-08-13", 2287.20, 2.00, 570, "paid", "3 moves completed"),
        ("Carl Strikland", "2025-08-13", 1899.20, 2.00, 280, "paid", "1 move completed"),
        ("Brandon Smith", "2025-08-13", 2299.81, 2.00, 530, "paid", "1 move completed")
    ]
    
    for payment in payments:
        cursor.execute('''INSERT INTO payments (driver_name, payment_date, amount, service_fee, miles, status, notes)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''', payment)
    print(f"Added {len(payments)} payment records")
    
    # Add submission record
    cursor.execute('''INSERT INTO submissions (submission_id, client_payment, factoring_fee, service_fee,
                     num_drivers, submission_date, payment_date, status)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  ("SUB-20250813", 6693.00, 200.79, 6.00, 3, "2025-08-13", "2025-08-13", "paid"))
    print("Added submission record")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 70)
    print("SYSTEM SETUP COMPLETE!")
    print("=" * 70)
    print("\nLogin Credentials:")
    print("  Admin: admin / admin123")
    print("  Drivers: j_duckett / duck123, c_strikland / strik123, b_smith / metro123")
    print("  Dispatch: dispatch / dispatch123")
    print("  Viewer: viewer / view123")

if __name__ == "__main__":
    setup_complete_system()