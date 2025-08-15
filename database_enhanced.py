"""
Enhanced Database Schema for Smith & Williams Trucking
Comprehensive database architecture with all 7 tables and interdependencies
"""

import sqlite3
import os
from datetime import datetime
import json

class EnhancedDatabase:
    def __init__(self, db_path='smith_williams_trucking.db'):
        self.db_path = db_path
        self.init_all_tables()
        
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_all_tables(self):
        """Initialize all 7 database tables with proper schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. Users Database - Stores user credentials and roles
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
        
        # 2. Drivers Database - All contractor details including insurance and W9
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
        
        # 3. Locations Database - Master table for all physical locations
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
        
        # 4. Trailers Database - Track each trailer with status updates
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
        
        # 5. Moves Database - Central hub with system-generated ID and MLBL
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
        
        # 6. Documents Database - Store references to all uploaded files
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
        
        # 7. Financials Database - Manage all payment records
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
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_moves_system_id ON moves(system_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_moves_mlbl ON moves(mlbl_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_moves_driver ON moves(driver_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_moves_status ON moves(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_move ON documents(move_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_mlbl ON documents(mlbl_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trailers_status ON trailers(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_financials_batch ON financials(payment_batch_id)')
        
        # Create activity log for audit trail
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
        
        conn.commit()
        conn.close()
    
    def generate_system_id(self):
        """Generate unique system ID in format SWT-YYYY-MM-XXXX"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now()
        year = now.strftime('%Y')
        month = now.strftime('%m')
        
        # Get the last number for this month
        prefix = f"SWT-{year}-{month}-"
        cursor.execute('''
            SELECT system_id FROM moves 
            WHERE system_id LIKE ? 
            ORDER BY system_id DESC 
            LIMIT 1
        ''', (prefix + '%',))
        
        last_id = cursor.fetchone()
        if last_id:
            last_num = int(last_id[0].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        new_id = f"{prefix}{new_num:04d}"
        conn.close()
        return new_id
    
    def add_mlbl_to_move(self, system_id, mlbl_number):
        """Add MLBL number to existing move and make it primary identifier"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Update move with MLBL number
            cursor.execute('''
                UPDATE moves 
                SET mlbl_number = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE system_id = ?
            ''', (mlbl_number, system_id))
            
            # Update related documents to link with MLBL
            cursor.execute('''
                UPDATE documents 
                SET mlbl_number = ? 
                WHERE system_id = ?
            ''', (mlbl_number, system_id))
            
            # Log the activity
            cursor.execute('''
                INSERT INTO activity_log (user, action, table_affected, record_id, new_value, details)
                VALUES (?, 'ADD_MLBL', 'moves', ?, ?, ?)
            ''', (
                'Management',
                system_id,
                mlbl_number,
                f'MLBL {mlbl_number} linked to move {system_id}'
            ))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def create_move(self, trailer_id, origin_id, destination_id, driver_id, client=None):
        """Create a new move with auto-generated system ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            system_id = self.generate_system_id()
            
            # Insert new move
            cursor.execute('''
                INSERT INTO moves (
                    system_id, move_date, trailer_id, origin_location_id, 
                    destination_location_id, driver_id, client, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                system_id,
                datetime.now().date(),
                trailer_id,
                origin_id,
                destination_id,
                driver_id,
                client,
                'assigned'
            ))
            
            move_id = cursor.lastrowid
            
            # Update trailer status
            cursor.execute('''
                UPDATE trailers 
                SET status = 'in_transit', last_move_id = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (move_id, trailer_id))
            
            # Log activity
            cursor.execute('''
                INSERT INTO activity_log (user, action, table_affected, record_id, details)
                VALUES (?, 'CREATE_MOVE', 'moves', ?, ?)
            ''', ('System', system_id, f'New move created with ID {system_id}'))
            
            conn.commit()
            return system_id
        except Exception as e:
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def load_sample_data(self):
        """Load sample data for testing"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if data already exists
        cursor.execute('SELECT COUNT(*) FROM users')
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        # Insert sample users
        users_data = [
            ('Brandon', 'owner123', 'Owner', 1, 1),
            ('admin', 'admin123', 'Admin', None, 1),
            ('manager', 'manager123', 'Manager', None, 1),
            ('coordinator', 'coord123', 'Coordinator', None, 1),
            ('JDuckett', 'driver123', 'Driver', 2, 1),
            ('CStrickland', 'driver123', 'Driver', 3, 1)
        ]
        
        for user in users_data:
            cursor.execute('''
                INSERT OR IGNORE INTO users (username, password, role, driver_id, active)
                VALUES (?, ?, ?, ?, ?)
            ''', user)
        
        # Insert sample drivers
        drivers_data = [
            ('Brandon Smith', 'Smith & Williams Trucking', '901-555-0001', 'brandon@swtrucking.com', 'owner'),
            ('Justin Duckett', 'Duckett Transport LLC', '901-555-0002', 'jduckett@email.com', 'contractor'),
            ('Carl Strickland', 'Strickland Logistics', '901-555-0003', 'cstrickland@email.com', 'contractor')
        ]
        
        for driver in drivers_data:
            cursor.execute('''
                INSERT OR IGNORE INTO drivers (driver_name, company_name, phone, email, driver_type)
                VALUES (?, ?, ?, ?, ?)
            ''', driver)
        
        # Insert sample locations
        locations_data = [
            ('Fleet Memphis', '123 Fleet Way', 'Memphis', 'TN', '38103', 35.1495, -90.0490, 'base', 1),
            ('FedEx Memphis Hub', '456 FedEx Pkwy', 'Memphis', 'TN', '38116', 35.0456, -89.9773, 'customer', 0),
            ('FedEx Indianapolis', '789 Hub Dr', 'Indianapolis', 'IN', '46241', 39.7684, -86.1581, 'customer', 0),
            ('Chicago Terminal', '321 Terminal Rd', 'Chicago', 'IL', '60606', 41.8781, -87.6298, 'customer', 0)
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
            ('TRL-005', 'Flatbed', 1, 'available')
        ]
        
        for trailer in trailers_data:
            cursor.execute('''
                INSERT OR IGNORE INTO trailers (trailer_number, trailer_type, current_location_id, status)
                VALUES (?, ?, ?, ?)
            ''', trailer)
        
        conn.commit()
        conn.close()

# Initialize database
if __name__ == "__main__":
    db = EnhancedDatabase()
    db.load_sample_data()
    print("Enhanced database initialized successfully")