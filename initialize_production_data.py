"""
Initialize Production Data for Smith & Williams Trucking
Loads real sample data for the deployed system
"""

import sqlite3
from datetime import datetime, date, timedelta
import random

def initialize_production_data(db_path='smith_williams_trucking.db'):
    """Initialize production database with real sample data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Initializing production data...")
    
    # Create all tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        driver_id INTEGER,
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        FOREIGN KEY (driver_id) REFERENCES drivers(id)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_name TEXT UNIQUE NOT NULL,
        company_name TEXT,
        phone TEXT,
        email TEXT,
        driver_type TEXT DEFAULT 'contractor',
        cdl_number TEXT,
        cdl_expiry DATE,
        insurance_policy TEXT,
        insurance_expiry DATE,
        w9_on_file INTEGER DEFAULT 0,
        w9_upload_date DATE,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_title TEXT UNIQUE NOT NULL,
        address TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        zip_code TEXT,
        latitude REAL,
        longitude REAL,
        location_type TEXT DEFAULT 'customer',
        is_base_location INTEGER DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS trailers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trailer_number TEXT UNIQUE NOT NULL,
        trailer_type TEXT DEFAULT 'Standard',
        current_location_id INTEGER,
        status TEXT DEFAULT 'available',
        is_new INTEGER DEFAULT 0,
        last_move_id INTEGER,
        notes TEXT,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP,
        FOREIGN KEY (current_location_id) REFERENCES locations(id),
        FOREIGN KEY (last_move_id) REFERENCES moves(id)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        system_id TEXT UNIQUE NOT NULL,
        mlbl_number TEXT UNIQUE,
        move_date DATE,
        trailer_id INTEGER NOT NULL,
        origin_location_id INTEGER NOT NULL,
        destination_location_id INTEGER NOT NULL,
        client TEXT,
        driver_id INTEGER,
        driver_name TEXT,
        estimated_miles REAL,
        actual_miles REAL,
        base_rate REAL DEFAULT 2.10,
        estimated_earnings REAL,
        actual_client_payment REAL,
        factoring_fee REAL,
        service_fee REAL,
        driver_net_pay REAL,
        status TEXT DEFAULT 'pending',
        delivery_status TEXT DEFAULT 'Pending',
        delivery_date TIMESTAMP,
        pod_uploaded INTEGER DEFAULT 0,
        photos_uploaded INTEGER DEFAULT 0,
        bol_uploaded INTEGER DEFAULT 0,
        rate_con_uploaded INTEGER DEFAULT 0,
        payment_status TEXT DEFAULT 'pending',
        payment_batch_id TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP,
        FOREIGN KEY (trailer_id) REFERENCES trailers(id),
        FOREIGN KEY (origin_location_id) REFERENCES locations(id),
        FOREIGN KEY (destination_location_id) REFERENCES locations(id),
        FOREIGN KEY (driver_id) REFERENCES drivers(id)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_type TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER,
        move_id INTEGER,
        system_id TEXT,
        mlbl_number TEXT,
        driver_id INTEGER,
        uploaded_by TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_verified INTEGER DEFAULT 0,
        verification_date TIMESTAMP,
        verified_by TEXT,
        notes TEXT,
        FOREIGN KEY (move_id) REFERENCES moves(id),
        FOREIGN KEY (driver_id) REFERENCES drivers(id)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS financials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_batch_id TEXT UNIQUE NOT NULL,
        payment_date DATE,
        client_name TEXT,
        total_client_payment REAL,
        total_factoring_fee REAL,
        total_service_fee REAL,
        total_net_payment REAL,
        num_moves INTEGER,
        num_drivers INTEGER,
        service_fee_per_driver REAL,
        invoice_generated INTEGER DEFAULT 0,
        invoice_path TEXT,
        statements_generated INTEGER DEFAULT 0,
        payment_status TEXT DEFAULT 'pending',
        processed_by TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user TEXT,
        action TEXT,
        table_affected TEXT,
        record_id TEXT,
        old_value TEXT,
        new_value TEXT,
        details TEXT
    )''')
    
    # Insert sample drivers
    drivers_data = [
        ('Brandon Smith', 'Smith & Williams Trucking', '901-555-0001', 'brandon@swtrucking.com', 'owner', 'CDL123456', '2026-01-01', 'POL-SWT-001', '2026-01-01'),
        ('Justin Duckett', 'Duckett Transport LLC', '901-555-0002', 'jduckett@email.com', 'contractor', 'CDL789012', '2025-06-15', 'POL-DT-002', '2025-12-31'),
        ('Carl Strickland', 'Strickland Logistics', '901-555-0003', 'cstrickland@email.com', 'contractor', 'CDL345678', '2025-09-30', 'POL-SL-003', '2025-11-30'),
        ('Mike Johnson', 'Johnson Freight', '901-555-0004', 'mjohnson@email.com', 'contractor', 'CDL901234', '2026-03-15', 'POL-JF-004', '2026-02-28'),
        ('Sarah Williams', 'Williams Transport', '901-555-0005', 'swilliams@email.com', 'company', 'CDL567890', '2025-12-01', 'POL-WT-005', '2025-10-31')
    ]
    
    for driver in drivers_data:
        cursor.execute('''
            INSERT OR IGNORE INTO drivers (
                driver_name, company_name, phone, email, driver_type,
                cdl_number, cdl_expiry, insurance_policy, insurance_expiry,
                w9_on_file, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'active')
        ''', driver)
    
    # Insert sample locations
    locations_data = [
        ('Fleet Memphis', '123 Fleet Way', 'Memphis', 'TN', '38103', 35.1495, -90.0490, 'base', 1),
        ('FedEx Memphis Hub', '456 FedEx Pkwy', 'Memphis', 'TN', '38116', 35.0456, -89.9773, 'customer', 0),
        ('FedEx Indianapolis', '789 Hub Dr', 'Indianapolis', 'IN', '46241', 39.7684, -86.1581, 'customer', 0),
        ('Chicago Terminal', '321 Terminal Rd', 'Chicago', 'IL', '60606', 41.8781, -87.6298, 'customer', 0),
        ('Nashville Hub', '555 Music City Dr', 'Nashville', 'TN', '37203', 36.1627, -86.7816, 'customer', 0),
        ('Atlanta Distribution', '777 Peachtree Way', 'Atlanta', 'GA', '30301', 33.7490, -84.3880, 'customer', 0),
        ('Dallas Warehouse', '999 Lone Star Blvd', 'Dallas', 'TX', '75201', 32.7767, -96.7970, 'customer', 0),
        ('St. Louis Center', '222 Gateway Dr', 'St. Louis', 'MO', '63101', 38.6270, -90.1994, 'customer', 0)
    ]
    
    for loc in locations_data:
        cursor.execute('''
            INSERT OR IGNORE INTO locations (
                location_title, address, city, state, zip_code,
                latitude, longitude, location_type, is_base_location
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', loc)
    
    # Insert sample trailers
    trailers_data = [
        ('TRL-001', 'Standard', 1, 'available'),
        ('TRL-002', 'Standard', 1, 'available'),
        ('TRL-003', 'Refrigerated', 2, 'available'),
        ('TRL-004', 'Standard', 3, 'in_transit'),
        ('TRL-005', 'Flatbed', 1, 'available'),
        ('TRL-006', 'Standard', 4, 'available'),
        ('TRL-007', 'Refrigerated', 5, 'in_transit'),
        ('TRL-008', 'Standard', 1, 'available'),
        ('TRL-009', 'Flatbed', 6, 'available'),
        ('TRL-010', 'Standard', 1, 'maintenance')
    ]
    
    for trailer in trailers_data:
        cursor.execute('''
            INSERT OR IGNORE INTO trailers (
                trailer_number, trailer_type, current_location_id, status
            ) VALUES (?, ?, ?, ?)
        ''', trailer)
    
    # Insert sample moves with real data
    moves_data = [
        ('SWT-2025-01-0001', 'MLBL58064', '2025-01-06', 1, 1, 2, 'FedEx', 2, 'Justin Duckett', 450, 'active', 'In Transit'),
        ('SWT-2025-01-0002', 'MLBL58065', '2025-01-07', 2, 1, 3, 'FedEx', 2, 'Justin Duckett', 385, 'active', 'In Transit'),
        ('SWT-2025-01-0003', 'MLBL58066', '2025-01-08', 3, 1, 4, 'FedEx', 3, 'Carl Strickland', 520, 'active', 'In Transit'),
        ('SWT-2025-01-0004', 'MLBL58067', '2025-01-09', 4, 2, 5, 'FedEx', 1, 'Brandon Smith', 280, 'completed', 'Delivered'),
        ('SWT-2025-01-0005', 'MLBL58068', '2025-01-10', 5, 3, 1, 'UPS', 4, 'Mike Johnson', 610, 'completed', 'Delivered'),
        ('SWT-2025-01-0006', None, '2025-01-11', 6, 4, 6, 'Amazon', 5, 'Sarah Williams', 495, 'assigned', 'Pending'),
        ('SWT-2025-01-0007', None, '2025-01-12', 7, 5, 7, 'FedEx', 2, 'Justin Duckett', 730, 'assigned', 'Pending'),
        ('SWT-2025-01-0008', 'MLBL58069', '2025-01-05', 8, 1, 8, 'UPS', 3, 'Carl Strickland', 340, 'completed', 'Delivered')
    ]
    
    for move in moves_data:
        system_id, mlbl, move_date, trailer_id, origin_id, dest_id, client, driver_id, driver_name, miles, status, delivery_status = move
        earnings = miles * 2.10
        
        # For completed moves, add payment data
        if status == 'completed':
            actual_payment = earnings * 1.05  # 5% markup
            factoring = actual_payment * 0.03
            service = 25.0
            net_pay = actual_payment - factoring - service
            payment_status = 'processed'
        else:
            actual_payment = None
            factoring = None
            service = None
            net_pay = None
            payment_status = 'pending'
        
        cursor.execute('''
            INSERT OR IGNORE INTO moves (
                system_id, mlbl_number, move_date, trailer_id,
                origin_location_id, destination_location_id, client,
                driver_id, driver_name, estimated_miles, base_rate,
                estimated_earnings, actual_client_payment, factoring_fee,
                service_fee, driver_net_pay, status, delivery_status,
                payment_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 2.10, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (system_id, mlbl, move_date, trailer_id, origin_id, dest_id,
              client, driver_id, driver_name, miles, earnings,
              actual_payment, factoring, service, net_pay, status,
              delivery_status, payment_status))
    
    # Add some sample financial records
    financials_data = [
        ('BATCH-20250105-001', '2025-01-05', 'FedEx', 2835.00, 85.05, 50.00, 2699.95, 3, 2, 25.00, 'processed'),
        ('BATCH-20250110-001', '2025-01-10', 'UPS', 1997.00, 59.91, 40.00, 1897.09, 2, 2, 20.00, 'processed')
    ]
    
    for financial in financials_data:
        cursor.execute('''
            INSERT OR IGNORE INTO financials (
                payment_batch_id, payment_date, client_name,
                total_client_payment, total_factoring_fee,
                total_service_fee, total_net_payment,
                num_moves, num_drivers, service_fee_per_driver,
                payment_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', financial)
    
    conn.commit()
    conn.close()
    
    print("Production data initialized successfully!")
    return True

if __name__ == "__main__":
    initialize_production_data()
    print("Database populated with sample production data")