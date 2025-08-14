"""
Fix all reported issues in the Trailer Move Tracker system
"""

import sqlite3
import json
from datetime import datetime, date, timedelta
import hashlib
import os

def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

def fix_database_schema():
    """Fix missing tables and columns"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create document_requirements table (fixing the missing table error)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            move_id INTEGER,
            document_type TEXT,
            required INTEGER DEFAULT 1,
            uploaded INTEGER DEFAULT 0,
            upload_date TIMESTAMP,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (move_id) REFERENCES moves(id)
        )
    ''')
    
    # Add missing columns to trailers table
    try:
        cursor.execute("ALTER TABLE trailers ADD COLUMN trailer_type TEXT DEFAULT 'Standard'")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE trailers ADD COLUMN is_new INTEGER DEFAULT 0")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE trailers ADD COLUMN origin_location TEXT")
    except:
        pass
    
    # Add delivery status to moves
    try:
        cursor.execute("ALTER TABLE moves ADD COLUMN delivery_status TEXT DEFAULT 'Pending'")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE moves ADD COLUMN delivery_date TIMESTAMP")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE moves ADD COLUMN delivery_location TEXT")
    except:
        pass
    
    conn.commit()
    conn.close()
    print("[OK] Database schema fixed")

def add_trailer_types():
    """Add new trailer types"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Update existing trailers with type if not set
    cursor.execute("""
        UPDATE trailers 
        SET trailer_type = CASE 
            WHEN trailer_type IS NULL OR trailer_type = '' THEN 'Standard'
            ELSE trailer_type
        END
    """)
    
    conn.commit()
    conn.close()
    print("[OK] Trailer types updated")

def mark_fleet_memphis_as_new():
    """Mark all trailers at Fleet Memphis as new"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Mark Fleet Memphis trailers as new
    cursor.execute("""
        UPDATE trailers 
        SET is_new = 1, origin_location = 'Fleet Memphis'
        WHERE current_location = 'Fleet Memphis'
    """)
    
    # Mark others as old if not already set
    cursor.execute("""
        UPDATE trailers 
        SET is_new = 0
        WHERE current_location != 'Fleet Memphis' AND is_new IS NULL
    """)
    
    conn.commit()
    conn.close()
    print("[OK] Fleet Memphis trailers marked as new")

def populate_driver_data():
    """Ensure driver data is properly populated"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if drivers exist
    cursor.execute("SELECT COUNT(*) FROM drivers")
    driver_count = cursor.fetchone()[0]
    
    if driver_count == 0:
        # Add some default drivers if none exist
        drivers = [
            ('John Smith', 'Smith Trucking', 'john.smith@smithtrucking.com', '555-0001', 1),
            ('Mike Williams', 'Williams Transport', 'mike@williamsTransport.com', '555-0002', 1),
            ('Robert Johnson', 'Independent', 'rjohnson@email.com', '555-0003', 1),
            ('David Brown', 'Brown Logistics', 'dbrown@brownlogistics.com', '555-0004', 1),
            ('James Wilson', 'Wilson Freight', 'jwilson@wilsonfreight.com', '555-0005', 1)
        ]
        
        cursor.executemany('''
            INSERT INTO drivers (name, company, email, phone, active)
            VALUES (?, ?, ?, ?, ?)
        ''', drivers)
        print(f"[OK] Added {len(drivers)} drivers")
    else:
        print(f"[OK] {driver_count} drivers already in system")
    
    conn.commit()
    conn.close()

def clear_dummy_oversight_data():
    """Clear dummy data from oversight tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Remove any test/dummy entries (those with 'test' or 'dummy' in fields)
    cursor.execute("""
        DELETE FROM activity_log 
        WHERE LOWER(action) LIKE '%test%' 
        OR LOWER(action) LIKE '%dummy%'
        OR LOWER(details) LIKE '%test%'
        OR LOWER(details) LIKE '%dummy%'
    """)
    
    deleted = cursor.rowcount
    if deleted > 0:
        print(f"[OK] Cleared {deleted} dummy activity log entries")
    
    conn.commit()
    conn.close()

def update_move_delivery_status():
    """Update move delivery statuses based on actual data"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Mark completed moves as delivered
    cursor.execute("""
        UPDATE moves 
        SET delivery_status = 'Delivered',
            delivery_date = dropoff_date,
            delivery_location = dropoff_location
        WHERE status = 'completed' 
        AND (delivery_status IS NULL OR delivery_status = 'Pending')
    """)
    
    # Mark in_transit moves
    cursor.execute("""
        UPDATE moves 
        SET delivery_status = 'In Transit'
        WHERE status = 'in_transit'
        AND (delivery_status IS NULL OR delivery_status = 'Pending')
    """)
    
    updated = cursor.rowcount
    print(f"[OK] Updated delivery status for {updated} moves")
    
    conn.commit()
    conn.close()

def create_email_config():
    """Create email configuration file"""
    email_config = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": "noreply@smithwilliamstrucking.com",
        "sender_name": "Smith & Williams Trucking",
        "use_tls": True,
        "templates": {
            "move_confirmation": {
                "subject": "Move Confirmation - {move_id}",
                "body": "Your move {move_id} has been confirmed.\n\nDetails:\nPickup: {pickup_location}\nDropoff: {dropoff_location}\nDate: {pickup_date}\n\nThank you for choosing Smith & Williams Trucking."
            },
            "payment_confirmation": {
                "subject": "Payment Processed - {payment_id}",
                "body": "Payment {payment_id} has been processed successfully.\n\nAmount: ${amount}\nDriver: {driver_name}\nDate: {payment_date}\n\nThank you for your service."
            }
        }
    }
    
    with open('email_config.json', 'w') as f:
        json.dump(email_config, f, indent=2)
    
    print("[OK] Email configuration created")

def install_dependencies():
    """Install missing Python dependencies"""
    import subprocess
    import sys
    
    packages = ['graphviz']
    
    for package in packages:
        try:
            __import__(package)
            print(f"[OK] {package} already installed")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"[OK] {package} installed")

def add_error_codes():
    """Create error code mapping file"""
    error_codes = {
        "DB001": "Database connection failed",
        "DB002": "Table not found",
        "DB003": "Query execution failed",
        "AUTH001": "Authentication failed",
        "AUTH002": "Insufficient permissions",
        "AUTH003": "Session expired",
        "VAL001": "Invalid input data",
        "VAL002": "Required field missing",
        "VAL003": "Data format error",
        "SYS001": "System configuration error",
        "SYS002": "File not found",
        "SYS003": "Module import failed",
        "REP001": "Report generation failed",
        "REP002": "No data available for report",
        "REP003": "Template not found"
    }
    
    with open('error_codes.json', 'w') as f:
        json.dump(error_codes, f, indent=2)
    
    print("[OK] Error codes configured")

def main():
    """Run all fixes"""
    print("\n=== Starting System Fixes ===\n")
    
    try:
        fix_database_schema()
        add_trailer_types()
        mark_fleet_memphis_as_new()
        populate_driver_data()
        clear_dummy_oversight_data()
        update_move_delivery_status()
        create_email_config()
        install_dependencies()
        add_error_codes()
        
        print("\n=== All Fixes Completed Successfully ===\n")
        return True
    except Exception as e:
        print(f"\n[ERROR] Error during fixes: {str(e)}")
        return False

if __name__ == "__main__":
    main()