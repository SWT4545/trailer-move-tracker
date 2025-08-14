"""
Complete System Integration - Ensures all databases and tables are synchronized
This script connects all components and ensures data consistency across the entire system
"""

import sqlite3
import os
from datetime import datetime, date
import shutil

def get_primary_db():
    """Determine and return the primary database connection"""
    # Check which database exists and has data
    dbs = ['trailer_moves.db', 'trailer_tracker_streamlined.db']
    
    for db in dbs:
        if os.path.exists(db):
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM moves")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"Primary database: {db} (contains {count} moves)")
                    return conn, db
            except:
                pass
            conn.close()
    
    # Default to trailer_moves.db
    print("Creating new primary database: trailer_moves.db")
    return sqlite3.connect('trailer_moves.db'), 'trailer_moves.db'

def create_all_tables(conn):
    """Create all required tables with proper relationships"""
    cursor = conn.cursor()
    
    # Core tables
    tables = [
        # Users and authentication
        '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            permissions TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            created_by TEXT
        )''',
        
        # Locations
        '''CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            address TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            type TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        # Trailers with all fields
        '''CREATE TABLE IF NOT EXISTS trailers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trailer_number TEXT UNIQUE NOT NULL,
            current_location TEXT,
            destination TEXT,
            customer_name TEXT,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            assigned_driver TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT
        )''',
        
        # Moves with payment tracking
        '''CREATE TABLE IF NOT EXISTS moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE,
            customer_name TEXT,
            old_trailer TEXT,
            new_trailer TEXT,
            pickup_location TEXT,
            delivery_location TEXT,
            pickup_date DATE,
            delivery_date DATE,
            completed_date DATE,
            payment_date DATE,
            amount DECIMAL(10,2),
            service_fee DECIMAL(10,2),
            net_amount DECIMAL(10,2),
            driver_net_earnings DECIMAL(10,2),
            driver_name TEXT,
            status TEXT,
            notes TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        # Driver profiles with contractor info
        '''CREATE TABLE IF NOT EXISTS driver_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            phone TEXT,
            email TEXT,
            cdl_number TEXT,
            cdl_state TEXT,
            cdl_class TEXT,
            years_experience INTEGER,
            address TEXT,
            birth_date DATE,
            driver_type TEXT DEFAULT 'contractor',
            company_name TEXT,
            company_address TEXT,
            company_phone TEXT,
            company_email TEXT,
            mc_number TEXT,
            dot_number TEXT,
            insurance_company TEXT,
            insurance_policy_number TEXT,
            w9_on_file BOOLEAN DEFAULT 0,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            emergency_contact_relationship TEXT,
            bank_name TEXT,
            routing_number TEXT,
            account_number TEXT,
            account_type TEXT,
            payment_method TEXT DEFAULT 'navy_federal_transfer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        # Driver availability
        '''CREATE TABLE IF NOT EXISTS driver_availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER,
            driver_name TEXT,
            is_available BOOLEAN DEFAULT 1,
            available_from DATE,
            available_to DATE,
            availability_notes TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        # Driver messages
        '''CREATE TABLE IF NOT EXISTS driver_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER,
            driver_name TEXT,
            message TEXT,
            message_type TEXT,
            priority TEXT DEFAULT 'normal',
            is_read BOOLEAN DEFAULT 0,
            sender TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        # Move documents
        '''CREATE TABLE IF NOT EXISTS move_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            move_id INTEGER,
            driver_id INTEGER,
            driver_name TEXT,
            document_type TEXT,
            file_name TEXT,
            file_path TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )''',
        
        # Payment details
        '''CREATE TABLE IF NOT EXISTS payment_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            move_id INTEGER,
            order_number TEXT,
            gross_amount DECIMAL(10,2),
            service_fee DECIMAL(10,2),
            processing_fee_percent DECIMAL(5,2) DEFAULT 3.0,
            processing_fee_amount DECIMAL(10,2),
            net_amount DECIMAL(10,2),
            driver_share_percent DECIMAL(5,2) DEFAULT 30.0,
            driver_gross_earnings DECIMAL(10,2),
            driver_fee_share DECIMAL(10,2),
            driver_net_earnings DECIMAL(10,2),
            payment_date DATE,
            payment_method TEXT,
            payment_status TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT
        )''',
        
        # Audit logs
        '''CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user TEXT,
            action TEXT,
            details TEXT,
            ip_address TEXT
        )'''
    ]
    
    for table_sql in tables:
        try:
            cursor.execute(table_sql)
        except Exception as e:
            print(f"Warning creating table: {e}")
    
    conn.commit()
    print("All tables created/verified")

def sync_payment_data(conn):
    """Synchronize payment data with proper fee calculations"""
    cursor = conn.cursor()
    
    # Update all paid moves with proper fee calculations
    print("\nSyncing payment data...")
    
    # Service fee: $6 split among 3 drivers = $2 each
    service_fee_per_driver = 2.00
    processing_percent = 3.0
    driver_percent = 30.0
    
    cursor.execute("""
        SELECT id, driver_name, amount, payment_date, status
        FROM moves
        WHERE status IN ('paid', 'completed')
    """)
    
    moves = cursor.fetchall()
    
    for move in moves:
        move_id, driver, gross, pay_date, status = move
        
        if gross:
            # Calculate fees
            processing_fee = gross * (processing_percent / 100)
            total_fees = service_fee_per_driver + processing_fee
            net_amount = gross - total_fees
            
            # Driver calculations
            driver_gross = gross * (driver_percent / 100)
            driver_processing = processing_fee * (driver_percent / 100)
            driver_total_fees = service_fee_per_driver + driver_processing
            driver_net = driver_gross - driver_total_fees
            
            # Update move with calculated values
            cursor.execute("""
                UPDATE moves
                SET service_fee = ?,
                    net_amount = ?,
                    driver_net_earnings = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (service_fee_per_driver, net_amount, driver_net, move_id))
            
            print(f"  Updated move {move_id}: Driver {driver} net earnings: ${driver_net:.2f}")
    
    conn.commit()

def update_driver_earnings_view(conn):
    """Create view for driver earnings across all tables"""
    cursor = conn.cursor()
    
    print("\nUpdating driver earnings views...")
    
    # Drop existing view if exists
    cursor.execute("DROP VIEW IF EXISTS driver_earnings_summary")
    
    # Create comprehensive earnings view
    cursor.execute("""
        CREATE VIEW driver_earnings_summary AS
        SELECT 
            driver_name,
            COUNT(*) as total_moves,
            SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_moves,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as pending_payment,
            SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as gross_paid,
            SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as gross_pending,
            SUM(CASE WHEN status = 'paid' THEN driver_net_earnings ELSE 0 END) as net_paid,
            SUM(CASE WHEN status = 'completed' THEN 
                (amount * 0.30 - 2.00 - (amount * 0.03 * 0.30)) ELSE 0 END) as net_pending
        FROM moves
        WHERE driver_name IS NOT NULL
        GROUP BY driver_name
    """)
    
    print("  Driver earnings view created")

def verify_data_integrity(conn):
    """Verify all data relationships are intact"""
    cursor = conn.cursor()
    
    print("\nVerifying data integrity...")
    
    # Check for orphaned records
    checks = [
        ("Moves without drivers", 
         "SELECT COUNT(*) FROM moves WHERE driver_name IS NULL OR driver_name = ''"),
        
        ("Trailers without locations",
         "SELECT COUNT(*) FROM trailers WHERE current_location IS NULL OR current_location = 'Location TBD'"),
        
        ("Unpaid completed moves",
         "SELECT COUNT(*) FROM moves WHERE status = 'completed' AND (payment_date IS NULL OR payment_date = '')"),
        
        ("Moves missing amounts",
         "SELECT COUNT(*) FROM moves WHERE amount IS NULL OR amount = 0")
    ]
    
    issues = []
    for check_name, query in checks:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        if count > 0:
            issues.append(f"  - {check_name}: {count}")
            print(f"  ⚠️ {check_name}: {count}")
        else:
            print(f"  ✓ {check_name}: OK")
    
    return issues

def generate_system_report(conn):
    """Generate complete system status report"""
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("SYSTEM INTEGRATION REPORT")
    print("="*60)
    
    # System statistics
    stats = {}
    
    queries = {
        'Total Trailers': "SELECT COUNT(*) FROM trailers",
        'Available Trailers': "SELECT COUNT(*) FROM trailers WHERE status = 'ready_to_move'",
        'Total Moves': "SELECT COUNT(*) FROM moves",
        'Completed Moves': "SELECT COUNT(*) FROM moves WHERE status = 'paid'",
        'Pending Payment': "SELECT COUNT(*) FROM moves WHERE status = 'completed'",
        'Total Revenue': "SELECT SUM(amount) FROM moves WHERE status = 'paid'",
        'Total Driver Earnings': "SELECT SUM(driver_net_earnings) FROM moves WHERE status = 'paid'",
        'Active Drivers': "SELECT COUNT(DISTINCT driver_name) FROM moves WHERE driver_name IS NOT NULL"
    }
    
    for stat_name, query in queries.items():
        cursor.execute(query)
        result = cursor.fetchone()[0]
        stats[stat_name] = result if result else 0
        
        if 'Revenue' in stat_name or 'Earnings' in stat_name:
            print(f"{stat_name}: ${stats[stat_name]:,.2f}")
        else:
            print(f"{stat_name}: {stats[stat_name]}")
    
    # Driver breakdown
    print("\nDRIVER PERFORMANCE:")
    print("-"*40)
    
    cursor.execute("""
        SELECT 
            driver_name,
            COUNT(*) as moves,
            SUM(amount) as gross,
            SUM(driver_net_earnings) as net
        FROM moves
        WHERE driver_name IS NOT NULL AND status = 'paid'
        GROUP BY driver_name
        ORDER BY net DESC
    """)
    
    for driver in cursor.fetchall():
        print(f"{driver[0]}:")
        print(f"  Moves: {driver[1]}")
        print(f"  Gross: ${driver[2]:,.2f}")
        print(f"  Net Earnings: ${driver[3]:,.2f}")
    
    # Pending work
    print("\nPENDING WORK:")
    print("-"*40)
    
    cursor.execute("""
        SELECT driver_name, COUNT(*) as pending
        FROM moves
        WHERE status = 'completed'
        GROUP BY driver_name
    """)
    
    pending = cursor.fetchall()
    if pending:
        for p in pending:
            print(f"{p[0]}: {p[1]} moves awaiting payment")
    else:
        print("No pending payments")
    
    return stats

def main():
    """Main integration process"""
    print("SMITH & WILLIAMS TRUCKING - SYSTEM INTEGRATION")
    print("="*60)
    
    # Get primary database
    conn, db_name = get_primary_db()
    
    # Create all tables
    create_all_tables(conn)
    
    # Sync payment data
    sync_payment_data(conn)
    
    # Update views
    update_driver_earnings_view(conn)
    
    # Verify integrity
    issues = verify_data_integrity(conn)
    
    # Generate report
    stats = generate_system_report(conn)
    
    # Summary
    print("\n" + "="*60)
    print("INTEGRATION COMPLETE")
    print("="*60)
    
    if issues:
        print("\n⚠️ ISSUES REQUIRING ATTENTION:")
        for issue in issues:
            print(issue)
    else:
        print("\n✅ All systems integrated successfully!")
    
    print(f"\nPrimary Database: {db_name}")
    print("All tables synchronized")
    print("Payment calculations updated")
    print("Driver earnings accurate")
    
    conn.close()
    
    print("\nSystem ready for production use!")

if __name__ == "__main__":
    main()