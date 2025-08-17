"""
Initialize database with complete schema
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = 'swt_fleet.db'

def init_database():
    """Initialize database with all required tables and columns"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create moves table with ALL required columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_id TEXT UNIQUE,
            order_number TEXT,
            driver_name TEXT,
            move_date DATE,
            pickup_date DATE,
            completed_date DATE,
            status TEXT DEFAULT 'active',
            new_trailer TEXT,
            old_trailer TEXT,
            origin_location TEXT,
            destination_location TEXT,
            delivery_location TEXT,
            destination_location_id INTEGER,
            estimated_miles REAL,
            actual_miles REAL,
            estimated_earnings REAL,
            amount REAL,
            client TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create trailers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trailers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trailer_number TEXT UNIQUE,
            type TEXT,
            status TEXT DEFAULT 'available',
            current_location TEXT,
            current_location_id INTEGER,
            last_inspection DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create locations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            type TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create drivers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            phone TEXT,
            email TEXT,
            license_number TEXT,
            hire_date DATE,
            status TEXT DEFAULT 'active',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample locations
    locations = [
        ('MLBL Management - Memphis', '5795 Shelby Oaks Dr', 'Memphis', 'TN', '38118', 'client'),
        ('FedEx Memphis Hub', '2903 Sprankel Ave', 'Memphis', 'TN', '38118', 'client'),
        ('FedEx Olive Branch', '7075 Malco Blvd', 'Olive Branch', 'MS', '38654', 'client'),
        ('FedEx Collierville', '1055 Shady Grove Rd', 'Memphis', 'TN', '38120', 'client'),
        ('Smith & Williams Yard', '1234 Industrial Pkwy', 'Memphis', 'TN', '38116', 'yard'),
        ('Love\'s Travel Stop - West Memphis', '3200 S Service Rd', 'West Memphis', 'AR', '72301', 'fuel'),
        ('Pilot Travel Center - Memphis', '2781 S Mendenhall Rd', 'Memphis', 'TN', '38115', 'fuel'),
    ]
    
    for loc in locations:
        cursor.execute('''
            INSERT OR IGNORE INTO locations (name, address, city, state, zip_code, type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', loc)
    
    # Insert sample drivers
    drivers = [
        ('Brandon Smith', '901-555-0001', 'brandon@swtrucking.com', 'TN123456', '2020-01-15'),
        ('Carl Strickland', '901-555-0002', 'carl@swtrucking.com', 'TN123457', '2021-03-20'),
        ('Justin Duckett', '901-555-0003', 'justin@swtrucking.com', 'TN123458', '2021-06-10'),
        ('Terrance Johnson', '901-555-0004', 'terrance@swtrucking.com', 'TN123459', '2022-01-05'),
        ('Jermichael Williams', '901-555-0005', 'jermichael@swtrucking.com', 'TN123460', '2022-04-15'),
    ]
    
    for driver in drivers:
        cursor.execute('''
            INSERT OR IGNORE INTO drivers (name, phone, email, license_number, hire_date)
            VALUES (?, ?, ?, ?, ?)
        ''', driver)
    
    # Insert sample trailers
    trailers = [
        # Numbers from the actual data
        ('6981', '53ft Dry Van', 'available', 'MLBL Management - Memphis'),
        ('7162', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
        ('7131', '53ft Dry Van', 'available', 'FedEx Olive Branch'),
        ('5906', '53ft Dry Van', 'available', 'MLBL Management - Memphis'),
        ('7144', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
        ('6014', '53ft Dry Van', 'available', 'FedEx Collierville'),
        ('4427', '53ft Dry Van', 'available', 'MLBL Management - Memphis'),
        ('5876', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
        ('5950', '53ft Dry Van', 'available', 'FedEx Olive Branch'),
        ('6837', '53ft Dry Van', 'available', 'MLBL Management - Memphis'),
        ('6094', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
        ('6231', '53ft Dry Van', 'available', 'FedEx Collierville'),
        ('3083', '53ft Dry Van', 'available', 'MLBL Management - Memphis'),
        ('6783', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
        ('7160', '53ft Dry Van', 'available', 'FedEx Olive Branch'),
        ('7153', '53ft Dry Van', 'available', 'MLBL Management - Memphis'),
        ('7728', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
        ('3170', '53ft Dry Van', 'available', 'FedEx Collierville'),
        ('6061', '53ft Dry Van', 'available', 'MLBL Management - Memphis'),
        ('6024', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
        ('6017', '53ft Dry Van', 'available', 'FedEx Olive Branch'),
        ('5955', '53ft Dry Van', 'available', 'MLBL Management - Memphis'),
        ('7124', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
        ('7146', '53ft Dry Van', 'available', 'FedEx Collierville'),
        ('7145', '53ft Dry Van', 'available', 'MLBL Management - Memphis'),
        ('7155', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
        ('6023', '53ft Dry Van', 'available', 'FedEx Olive Branch'),
        ('6015', '53ft Dry Van', 'available', 'MLBL Management - Memphis'),
        ('7126', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
        # FedEx trailers
        ('190011', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
        ('190030', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
        ('18V00298', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
        ('190033', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
        ('190046', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
        ('18V00407', '53ft Dry Van', 'available', 'FedEx Memphis Hub'),
    ]
    
    for trailer in trailers:
        cursor.execute('''
            INSERT OR IGNORE INTO trailers (trailer_number, type, status, current_location)
            VALUES (?, ?, ?, ?)
        ''', trailer)
    
    # Insert sample moves
    today = datetime.now().date()
    moves = [
        # Active moves
        ('SWT-2025-024', 'ORD-2025-024', 'Brandon Smith', today, 'active', '7162', '6981', 
         'MLBL Management - Memphis', 'FedEx Memphis Hub', 'FedEx Memphis Hub', 1, 25, None, 105, None, 'MLBL Management'),
        ('SWT-2025-025', 'ORD-2025-025', 'Carl Strickland', today, 'active', '190011', '6231', 
         'FedEx Memphis Hub', 'FedEx Olive Branch', 'FedEx Olive Branch', 2, 35, None, 147, None, 'FedEx'),
        ('SWT-2025-026', 'ORD-2025-026', 'Justin Duckett', today, 'in_transit', '5906', '7131', 
         'FedEx Olive Branch', 'MLBL Management - Memphis', 'MLBL Management - Memphis', 0, 40, None, 168, None, 'FedEx'),
        
        # Completed moves (from yesterday)
        ('SWT-2025-020', 'ORD-2025-020', 'Brandon Smith', today - timedelta(days=1), 'completed', '6014', '7144', 
         'FedEx Collierville', 'FedEx Memphis Hub', 'FedEx Memphis Hub', 1, 20, 20, 84, 84, 'FedEx'),
        ('SWT-2025-021', 'ORD-2025-021', 'Carl Strickland', today - timedelta(days=1), 'completed', '5876', '4427', 
         'MLBL Management - Memphis', 'FedEx Olive Branch', 'FedEx Olive Branch', 2, 35, 35, 147, 147, 'MLBL Management'),
        ('SWT-2025-022', 'ORD-2025-022', 'Terrance Johnson', today - timedelta(days=2), 'completed', '6837', '5950', 
         'FedEx Memphis Hub', 'FedEx Collierville', 'FedEx Collierville', 3, 15, 15, 63, 63, 'FedEx'),
        ('SWT-2025-023', 'ORD-2025-023', 'Jermichael Williams', today - timedelta(days=2), 'completed', '6094', None, 
         'Smith & Williams Yard', 'FedEx Memphis Hub', 'FedEx Memphis Hub', 1, 30, 30, 126, 126, 'FedEx'),
    ]
    
    for move in moves:
        cursor.execute('''
            INSERT OR IGNORE INTO moves (
                system_id, order_number, driver_name, move_date, status,
                new_trailer, old_trailer, origin_location, destination_location,
                delivery_location, destination_location_id, estimated_miles,
                actual_miles, estimated_earnings, amount, client
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', move)
    
    conn.commit()
    
    # Verify the tables were created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Created tables: {[t[0] for t in tables]}")
    
    # Verify column structure
    cursor.execute("PRAGMA table_info(moves)")
    columns = cursor.fetchall()
    print(f"\nMoves table has {len(columns)} columns including:")
    important_cols = ['delivery_location', 'destination_location', 'new_trailer', 'old_trailer']
    for col in columns:
        if col[1] in important_cols:
            print(f"  [OK] {col[1]} ({col[2]})")
    
    conn.close()
    print("\nDatabase initialized successfully!")

if __name__ == "__main__":
    init_database()