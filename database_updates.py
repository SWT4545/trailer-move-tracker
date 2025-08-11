"""
Database Updates for Enhanced Trailer Move Tracker
Adds new tables and columns for all enhanced features
"""

import sqlite3
from contextlib import contextmanager
import os

DATABASE_PATH = 'data/trailer_moves.db'

@contextmanager
def get_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def update_database():
    """Add new tables and columns for enhanced features"""
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Update drivers table with new fields
        try:
            cursor.execute('''
                ALTER TABLE drivers ADD COLUMN driver_type TEXT DEFAULT 'contractor' 
                CHECK(driver_type IN ('company', 'contractor'))
            ''')
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        try:
            cursor.execute('ALTER TABLE drivers ADD COLUMN phone_number TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE drivers ADD COLUMN email TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE drivers ADD COLUMN cdl_number TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE drivers ADD COLUMN cdl_expiration DATE')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE drivers ADD COLUMN emergency_contact TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE drivers ADD COLUMN employee_id TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE drivers ADD COLUMN hire_date DATE')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE drivers ADD COLUMN home_terminal TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE drivers ADD COLUMN tax_id TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE drivers ADD COLUMN username TEXT UNIQUE')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE drivers ADD COLUMN password_hash TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE drivers ADD COLUMN last_login TIMESTAMP')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE drivers ADD COLUMN is_active BOOLEAN DEFAULT 1')
        except sqlite3.OperationalError:
            pass
        
        # Create driver performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS driver_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_id INTEGER NOT NULL,
                week_start DATE NOT NULL,
                miles_driven INTEGER DEFAULT 0,
                routes_completed INTEGER DEFAULT 0,
                on_time_count INTEGER DEFAULT 0,
                late_count INTEGER DEFAULT 0,
                earnings DECIMAL(10,2) DEFAULT 0,
                performance_score DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (driver_id) REFERENCES drivers(id),
                UNIQUE(driver_id, week_start)
            )
        ''')
        
        # Create driver sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS driver_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                driver_id INTEGER NOT NULL,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (driver_id) REFERENCES drivers(id)
            )
        ''')
        
        # Create location trailer count table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS location_trailer_counts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER NOT NULL,
                location_name TEXT NOT NULL,
                old_trailer_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                days_since_last_pickup INTEGER DEFAULT 0,
                alert_status TEXT DEFAULT 'green' CHECK(alert_status IN ('green', 'yellow', 'red')),
                FOREIGN KEY (location_id) REFERENCES locations(id),
                UNIQUE(location_id)
            )
        ''')
        
        # Create trailer location history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trailer_location_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trailer_id INTEGER NOT NULL,
                location_id INTEGER,
                location_name TEXT,
                arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                departure_time TIMESTAMP,
                status TEXT CHECK(status IN ('at_location', 'picked_up', 'in_transit')),
                FOREIGN KEY (trailer_id) REFERENCES trailers(id),
                FOREIGN KEY (location_id) REFERENCES locations(id)
            )
        ''')
        
        # Create route progress table for detailed tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS route_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id INTEGER NOT NULL,
                milestone TEXT NOT NULL CHECK(milestone IN (
                    'created', 'assigned', 'pickup_arrival', 'pickup_depart', 
                    'delivery_arrival', 'delivery_depart', 'old_pickup', 
                    'fleet_return', 'completed'
                )),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expected_location TEXT,
                confirmed_location TEXT,
                is_reasonable BOOLEAN DEFAULT 1,
                notes TEXT,
                FOREIGN KEY (route_id) REFERENCES trailer_moves(id)
            )
        ''')
        
        # Create route photos table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS route_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id INTEGER NOT NULL,
                photo_type TEXT NOT NULL CHECK(photo_type IN (
                    'new_trailer_front', 'new_trailer_back', 'new_trailer_left',
                    'new_trailer_right', 'new_trailer_inside',
                    'new_delivery_front', 'new_delivery_back', 'new_delivery_left',
                    'new_delivery_right', 'new_delivery_inside',
                    'old_trailer_pickup', 'old_trailer_return',
                    'paperwork_pickup', 'paperwork_delivery', 'pod_fleet'
                )),
                photo_data BLOB,
                photo_url TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                location TEXT,
                notes TEXT,
                FOREIGN KEY (route_id) REFERENCES trailer_moves(id)
            )
        ''')
        
        # Create generic documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generic_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_type TEXT NOT NULL CHECK(document_type IN (
                    'rate_confirmation', 'pod', 'bol', 'invoice', 'other'
                )),
                document_name TEXT NOT NULL,
                file_data BLOB,
                file_path TEXT,
                uploaded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_generic BOOLEAN DEFAULT 0,
                standard_rate DECIMAL(10,2) DEFAULT 2.10,
                expiry_date DATE,
                notes TEXT
            )
        ''')
        
        # Create training system tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_name TEXT NOT NULL,
                role TEXT NOT NULL,
                description TEXT,
                content TEXT,
                order_index INTEGER,
                duration_minutes INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                module_id INTEGER NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                score DECIMAL(5,2),
                attempts INTEGER DEFAULT 1,
                time_spent_seconds INTEGER,
                is_certified BOOLEAN DEFAULT 0,
                FOREIGN KEY (module_id) REFERENCES training_modules(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_demo_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_type TEXT NOT NULL,
                demo_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create company performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_date DATE NOT NULL,
                routes_completed INTEGER DEFAULT 0,
                routes_in_progress INTEGER DEFAULT 0,
                on_time_percentage DECIMAL(5,2),
                average_completion_hours DECIMAL(10,2),
                fleet_utilization DECIMAL(5,2),
                customer_satisfaction DECIMAL(5,2),
                safety_incidents INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(metric_date)
            )
        ''')
        
        # Create status reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS status_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date DATE NOT NULL,
                report_type TEXT NOT NULL,
                report_data TEXT,
                pdf_data BLOB,
                generated_by TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_to TEXT,
                sent_at TIMESTAMP
            )
        ''')
        
        # Add new columns to trailer_moves for enhanced tracking
        try:
            cursor.execute('ALTER TABLE trailer_moves ADD COLUMN driver_link TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE trailer_moves ADD COLUMN link_accessed BOOLEAN DEFAULT 0')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE trailer_moves ADD COLUMN link_accessed_at TIMESTAMP')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE trailer_moves ADD COLUMN rate_confirmation_type TEXT DEFAULT "specific"')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE trailer_moves ADD COLUMN rate_confirmation_id INTEGER')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE trailer_moves ADD COLUMN photos_required INTEGER DEFAULT 12')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE trailer_moves ADD COLUMN photos_captured INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        # Add location address fields if not exists
        try:
            cursor.execute('ALTER TABLE locations ADD COLUMN street_address TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE locations ADD COLUMN city TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE locations ADD COLUMN state TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE locations ADD COLUMN zip_code TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE locations ADD COLUMN location_type TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE locations ADD COLUMN contact_name TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE locations ADD COLUMN contact_phone TEXT')
        except sqlite3.OperationalError:
            pass
        
        conn.commit()
        
        print("Database updated successfully with all new tables and columns!")
        return True

if __name__ == "__main__":
    update_database()