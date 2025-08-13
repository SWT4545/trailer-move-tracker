"""
Complete Database Setup for Smith & Williams Trucking System
Ensures all tables exist and are properly connected
"""

import sqlite3
import os
from datetime import datetime

def setup_complete_database():
    """Create and verify all database tables for the entire system"""
    
    # Use the main database
    db_path = 'trailer_tracker_streamlined.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Setting up database: {db_path}")
    
    # 1. USERS AND AUTHENTICATION
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            permissions TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # 2. DRIVERS - Extended with all fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_name TEXT UNIQUE NOT NULL,
            phone_number TEXT,
            email TEXT,
            driver_type TEXT DEFAULT 'Company Driver',
            cdl_number TEXT,
            cdl_state TEXT,
            cdl_class TEXT,
            cdl_expiry DATE,
            medical_cert_expiry DATE,
            hazmat_expiry DATE,
            twic_expiry DATE,
            emergency_contact TEXT,
            emergency_phone TEXT,
            emergency_relationship TEXT,
            home_address TEXT,
            business_address TEXT,
            start_date DATE,
            birth_date DATE,
            years_experience INTEGER,
            status TEXT DEFAULT 'Active',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 3. DRIVER EXTENDED INFO
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers_extended (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER,
            driver_name TEXT,
            company_name TEXT,
            mc_number TEXT,
            dot_number TEXT,
            ein_ssn_last4 TEXT,
            insurance_provider TEXT,
            insurance_policy TEXT,
            insurance_expiry DATE,
            truck_info TEXT,
            trailer_types TEXT,
            preferred_routes TEXT,
            max_daily_moves INTEGER DEFAULT 2,
            bank_name TEXT,
            account_type TEXT,
            routing_number TEXT,
            account_number TEXT,
            payment_method TEXT DEFAULT 'Check',
            w9_on_file INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (driver_id) REFERENCES drivers(id)
        )
    ''')
    
    # 4. TRAILERS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trailers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trailer_number TEXT UNIQUE NOT NULL,
            trailer_type TEXT DEFAULT 'Roller Bed',
            condition TEXT DEFAULT 'Good',
            location TEXT,
            status TEXT DEFAULT 'available',
            owner TEXT,
            notes TEXT,
            last_inspection DATE,
            next_inspection DATE,
            is_reserved INTEGER DEFAULT 0,
            reserved_by_driver TEXT,
            reserved_until TIMESTAMP,
            paired_trailer_id INTEGER,
            swap_location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 5. MOVES
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            move_id TEXT UNIQUE,
            order_number TEXT,
            customer_name TEXT,
            new_trailer TEXT,
            old_trailer TEXT,
            origin TEXT,
            origin_city TEXT,
            origin_state TEXT,
            destination TEXT,
            destination_city TEXT,
            destination_state TEXT,
            pickup_location TEXT,
            delivery_location TEXT,
            pickup_date DATE,
            delivery_date DATE,
            pickup_time TIME,
            delivery_time TIME,
            driver_name TEXT,
            driver_id INTEGER,
            status TEXT DEFAULT 'pending',
            amount REAL,
            payment_status TEXT DEFAULT 'pending',
            payment_received REAL,
            client_actual_payment REAL,
            driver_pay REAL,
            driver_paid INTEGER DEFAULT 0,
            driver_rating REAL,
            payment_date DATE,
            payment_method TEXT,
            total_miles REAL,
            rate_per_mile REAL,
            self_assigned INTEGER DEFAULT 0,
            assigned_at TIMESTAMP,
            assignment_type TEXT,
            pod_uploaded INTEGER DEFAULT 0,
            pod_path TEXT,
            unassigned_at TIMESTAMP,
            unassigned_reason TEXT,
            notes TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (driver_id) REFERENCES drivers(id)
        )
    ''')
    
    # 6. LOCATIONS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_title TEXT UNIQUE,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            is_base_location INTEGER DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 7. DRIVER AVAILABILITY
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS driver_availability (
            driver_id INTEGER PRIMARY KEY,
            driver_name TEXT,
            status TEXT DEFAULT 'available',
            current_move_id TEXT,
            completed_moves_today INTEGER DEFAULT 0,
            max_daily_moves INTEGER DEFAULT 2,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (driver_id) REFERENCES drivers(id)
        )
    ''')
    
    # 8. ASSIGNMENT HISTORY
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            move_id TEXT,
            driver_id INTEGER,
            driver_name TEXT,
            action TEXT,
            action_by TEXT,
            action_type TEXT,
            reason TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 9. NOTIFICATIONS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER,
            move_id TEXT,
            message TEXT,
            type TEXT,
            priority TEXT,
            action_required INTEGER DEFAULT 0,
            read_status INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 10. PAYMENT RECEIPTS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_receipts (
            receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_name TEXT NOT NULL,
            load_number TEXT NOT NULL,
            payment_date TEXT NOT NULL,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            gross_amount REAL NOT NULL,
            deductions REAL DEFAULT 0,
            net_amount REAL NOT NULL,
            rate_per_mile REAL NOT NULL,
            total_miles REAL NOT NULL,
            payment_method TEXT,
            check_number TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT,
            pdf_path TEXT
        )
    ''')
    
    # 11. 1099 TRACKING
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contractor_1099 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_name TEXT NOT NULL,
            tax_year INTEGER NOT NULL,
            ein_ssn TEXT,
            total_payments REAL NOT NULL,
            form_1099_sent INTEGER DEFAULT 0,
            sent_date TEXT,
            filing_status TEXT,
            business_name TEXT,
            business_address TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(driver_name, tax_year)
        )
    ''')
    
    # 12. TAX DOCUMENTS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tax_documents (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_name TEXT NOT NULL,
            document_type TEXT NOT NULL,
            document_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            tax_year INTEGER,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_by TEXT,
            notes TEXT
        )
    ''')
    
    # 13. W9 DOCUMENTS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS w9_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_name TEXT NOT NULL,
            driver_id INTEGER,
            file_name TEXT,
            file_path TEXT,
            file_size INTEGER,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tax_year INTEGER,
            ein_or_ssn TEXT,
            business_name TEXT,
            status TEXT DEFAULT 'active',
            verified_by TEXT,
            verified_date TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (driver_id) REFERENCES drivers(id)
        )
    ''')
    
    # 14. PAYMENT DETAILS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_details (
            detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_id INTEGER,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            FOREIGN KEY (receipt_id) REFERENCES payment_receipts(receipt_id)
        )
    ''')
    
    # 15. AUDIT LOGS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT DEFAULT 'local'
        )
    ''')
    
    # 16. CUSTOMERS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT UNIQUE NOT NULL,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            customer_type TEXT,
            payment_terms TEXT,
            credit_limit REAL,
            notes TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 17. SYSTEM SETTINGS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT,
            setting_type TEXT,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT
        )
    ''')
    
    # 18. ROLE PERMISSIONS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS role_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT NOT NULL,
            permission_key TEXT NOT NULL,
            permission_value INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(role_name, permission_key)
        )
    ''')
    
    # INSERT DEFAULT DATA
    
    # Default locations
    locations_data = [
        ('Fleet Memphis', '123 Main St', 'Memphis', 'TN', '38103', 1),
        ('Nashville Hub', '456 Broadway', 'Nashville', 'TN', '37203', 0),
        ('Little Rock Terminal', '789 Terminal Rd', 'Little Rock', 'AR', '72201', 0),
        ('Jackson Depot', '321 Depot Way', 'Jackson', 'MS', '39201', 0),
        ('Birmingham Station', '555 Station Rd', 'Birmingham', 'AL', '35203', 0)
    ]
    
    for loc in locations_data:
        cursor.execute('''
            INSERT OR IGNORE INTO locations (location_title, address, city, state, zip_code, is_base_location)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', loc)
    
    # Default system settings
    settings_data = [
        ('company_name', 'Smith & Williams Trucking LLC', 'text', 'Company legal name'),
        ('company_phone', '(555) 123-4567', 'text', 'Main company phone'),
        ('company_email', 'dispatch@swtrucking.com', 'text', 'Main company email'),
        ('company_address', '123 Main Street', 'text', 'Company street address'),
        ('company_city', 'Memphis', 'text', 'Company city'),
        ('company_state', 'TN', 'text', 'Company state'),
        ('company_zip', '38103', 'text', 'Company zip code'),
        ('rate_per_mile', '2.10', 'decimal', 'Default driver rate per mile'),
        ('factoring_fee', '0.03', 'decimal', 'Default factoring fee percentage'),
        ('max_daily_moves', '2', 'integer', 'Maximum moves per day per driver'),
        ('reservation_timeout', '30', 'integer', 'Trailer reservation timeout in minutes')
    ]
    
    for setting in settings_data:
        cursor.execute('''
            INSERT OR IGNORE INTO system_settings (setting_key, setting_value, setting_type, description)
            VALUES (?, ?, ?, ?)
        ''', setting)
    
    # Default role permissions
    roles = {
        'Owner': ['*'],  # All permissions
        'Admin': ['view_all', 'edit_all', 'manage_users', 'manage_drivers', 'manage_payments'],
        'Coordinator': ['view_all', 'edit_moves', 'manage_drivers', 'view_reports'],
        'Driver': ['view_own', 'edit_own', 'self_assign', 'upload_documents'],
        'DataEntry': ['view_trailers', 'edit_trailers', 'view_moves', 'edit_moves'],
    }
    
    for role, permissions in roles.items():
        for perm in permissions:
            cursor.execute('''
                INSERT OR IGNORE INTO role_permissions (role_name, permission_key)
                VALUES (?, ?)
            ''', (role, perm))
    
    # Create indexes for better performance
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_moves_driver ON moves(driver_name)',
        'CREATE INDEX IF NOT EXISTS idx_moves_status ON moves(status)',
        'CREATE INDEX IF NOT EXISTS idx_trailers_status ON trailers(status)',
        'CREATE INDEX IF NOT EXISTS idx_drivers_status ON drivers(status)',
        'CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user)',
        'CREATE INDEX IF NOT EXISTS idx_notifications_driver ON notifications(driver_id)',
    ]
    
    for idx in indexes:
        cursor.execute(idx)
    
    # Commit all changes
    conn.commit()
    
    # Verify all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"\n[SUCCESS] Database setup complete!")
    print(f"Total tables created/verified: {len(tables)}")
    print("\nTables in database:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  - {table[0]}: {count} records")
    
    conn.close()
    
    # Also ensure trailer_data.db compatibility
    if os.path.exists('trailer_data.db'):
        conn2 = sqlite3.connect('trailer_data.db')
        cursor2 = conn2.cursor()
        
        # Create essential tables in trailer_data.db too
        for table_sql in [
            '''CREATE TABLE IF NOT EXISTS payment_receipts (
                receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_name TEXT NOT NULL,
                load_number TEXT NOT NULL,
                payment_date TEXT NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                gross_amount REAL NOT NULL,
                deductions REAL DEFAULT 0,
                net_amount REAL NOT NULL,
                rate_per_mile REAL NOT NULL,
                total_miles REAL NOT NULL,
                payment_method TEXT,
                check_number TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                pdf_path TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS contractor_1099 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_name TEXT NOT NULL,
                tax_year INTEGER NOT NULL,
                ein_ssn TEXT,
                total_payments REAL NOT NULL,
                form_1099_sent INTEGER DEFAULT 0,
                sent_date TEXT,
                filing_status TEXT,
                business_name TEXT,
                business_address TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(driver_name, tax_year)
            )''',
            '''CREATE TABLE IF NOT EXISTS tax_documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_name TEXT NOT NULL,
                document_type TEXT NOT NULL,
                document_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                tax_year INTEGER,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploaded_by TEXT,
                notes TEXT
            )'''
        ]:
            cursor2.execute(table_sql)
        
        conn2.commit()
        conn2.close()
        print("\n[SUCCESS] Secondary database (trailer_data.db) also configured")
    
    return True

if __name__ == "__main__":
    setup_complete_database()